"""
Particle effects, slash trails, floating damage indicators, and ambient biome motes.
"""

import math
import random
import pygame
from game.settings import INTERNAL_WIDTH, INTERNAL_HEIGHT, PALETTE, BIOME_PALETTES


class Particle:
    """Single lightweight particle for bursts, sparks, and environmental motes."""

    __slots__ = (
        "x",
        "y",
        "vx",
        "vy",
        "color",
        "size",
        "lifetime",
        "max_lifetime",
        "gravity",
        "glow",
    )

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: tuple,
        size: float = 2.0,
        lifetime: float = 0.4,
        gravity: float = 120.0,
        glow: bool = False,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = max(0.01, lifetime)
        self.gravity = gravity
        self.glow = glow

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        return True


class SlashArc:
    """Visual crescent slash trail for melee attacks."""

    def __init__(
        self, x: float, y: float, direction: str, color: tuple, radius: int = 24
    ):
        self.x = x
        self.y = y
        self.direction = direction
        self.color = color
        self.radius = radius
        self.lifetime = 0.14
        self.max_lifetime = 0.14

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        ratio = max(0.0, self.lifetime / self.max_lifetime)
        cx = int(self.x - cam_x)
        cy = int(self.y - cam_y)
        r = int(self.radius * (1.1 - 0.2 * ratio))

        points = []
        if self.direction == "right":
            angles = (-0.9, -0.45, 0.0, 0.45, 0.9)
        elif self.direction == "left":
            angles = (math.pi - 0.9, math.pi - 0.45, math.pi, math.pi + 0.45, math.pi + 0.9)
        elif self.direction == "up":
            angles = (-math.pi * 0.85, -math.pi * 0.65, -math.pi * 0.5, -math.pi * 0.35, -math.pi * 0.15)
        else:  # down
            angles = (math.pi * 0.15, math.pi * 0.35, math.pi * 0.5, math.pi * 0.65, math.pi * 0.85)

        for a in angles:
            px = cx + int(math.cos(a) * r)
            py = cy + int(math.sin(a) * r)
            points.append((px, py))

        for a in reversed(angles):
            inner_r = int(r * (0.45 + 0.35 * (1.0 - ratio)))
            px = cx + int(math.cos(a) * inner_r)
            py = cy + int(math.sin(a) * inner_r)
            points.append((px, py))

        if len(points) >= 3:
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, PALETTE["white"], points, 1)


class FloatingText:
    """Floating combat number or short status text."""

    def __init__(self, x: float, y: float, text: str, color: tuple):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.lifetime = 0.65

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        self.y -= 24.0 * dt
        return self.lifetime > 0


class ParticleManager:
    """Centralized manager for combat particles, ambient dust, and slash trails."""

    def __init__(self):
        self.particles = []
        self.slashes = []
        self.floating_texts = []
        self.ambient_timer = 0.0
        self._font = None

    def _get_font(self):
        if self._font is None:
            pygame.font.init()
            self._font = pygame.font.SysFont("consolas", 11, bold=True)
        return self._font

    def emit_burst(
        self,
        x: float,
        y: float,
        color: tuple,
        count: int = 12,
        speed: float = 95.0,
        size: float = 2.5,
        lifetime: float = 0.4,
        gravity: float = 160.0,
        glow: bool = True,
    ):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd
            self.particles.append(
                Particle(
                    x,
                    y,
                    vx,
                    vy,
                    color,
                    size=random.uniform(max(1.0, size - 1.0), size + 1.0),
                    lifetime=random.uniform(lifetime * 0.6, lifetime * 1.2),
                    gravity=gravity,
                    glow=glow,
                )
            )

    def emit_directional_sparks(
        self,
        x: float,
        y: float,
        dir_x: float,
        dir_y: float,
        color: tuple,
        count: int = 10,
    ):
        base_angle = math.atan2(dir_y, dir_x)
        for _ in range(count):
            a = base_angle + random.uniform(-0.6, 0.6)
            spd = random.uniform(70.0, 175.0)
            self.particles.append(
                Particle(
                    x,
                    y,
                    math.cos(a) * spd,
                    math.sin(a) * spd,
                    color,
                    size=2.5,
                    lifetime=random.uniform(0.18, 0.36),
                    gravity=220.0,
                    glow=True,
                )
            )

    def emit_slash(
        self, x: float, y: float, direction: str, color: tuple, radius: int = 24
    ):
        self.slashes.append(SlashArc(x, y, direction, color, radius))

    def emit_floating_text(self, x: float, y: float, text: str, color: tuple):
        self.floating_texts.append(FloatingText(x, y, text, color))

    def update(self, dt: float, cam_x: int = 0, cam_y: int = 0, biome: str = "sanctuary"):
        self.particles = [p for p in self.particles if p.update(dt)]
        self.slashes = [s for s in self.slashes if s.update(dt)]
        self.floating_texts = [ft for ft in self.floating_texts if ft.update(dt)]

        # Spawn drifting ambient motes
        self.ambient_timer += dt
        if self.ambient_timer >= 0.08 and len(self.particles) < 160:
            self.ambient_timer = 0.0
            b_info = BIOME_PALETTES.get(biome, BIOME_PALETTES["sanctuary"])
            px = cam_x + random.uniform(0, INTERNAL_WIDTH)
            py = cam_y + random.uniform(0, INTERNAL_HEIGHT)
            self.particles.append(
                Particle(
                    px,
                    py,
                    random.uniform(-12, 12),
                    random.uniform(-18, -5),
                    b_info["ambient_particle"],
                    size=random.choice([1.0, 2.0]),
                    lifetime=random.uniform(1.5, 3.0),
                    gravity=-2.0,
                    glow=True,
                )
            )

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        for s in self.slashes:
            s.draw(surface, cam_x, cam_y)

        for p in self.particles:
            sx = int(p.x - cam_x)
            sy = int(p.y - cam_y)
            if -10 <= sx <= INTERNAL_WIDTH + 10 and -10 <= sy <= INTERNAL_HEIGHT + 10:
                ratio = max(0.1, p.lifetime / p.max_lifetime)
                r = max(1, int(p.size * ratio))
                pygame.draw.circle(surface, p.color, (sx, sy), r)

        font = self._get_font()
        for ft in self.floating_texts:
            sx = int(ft.x - cam_x)
            sy = int(ft.y - cam_y)
            img = font.render(ft.text, False, ft.color)
            surface.blit(img, (sx - img.get_width() // 2, sy))