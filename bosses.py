"""
Three original multi-phase Boss Encounters with distinct silhouettes, attack patterns,
telegraphs, phase transitions, and story rewards:
1. Malakor, The Ashen Warden (Sunken Catacombs)
2. Lyra, Mycelial Matriarch (Weeping Mycelium)
3. Aurelius, The Hollow Sun (The Obsidian Pelorus - Final Boss)
"""

import math
import random
import pygame
from game.settings import PALETTE, GRAVITY, MAX_FALL_SPEED


class Boss:
    """Base multi-phase boss controller."""

    def __init__(
        self,
        boss_id: str,
        name: str,
        subtitle: str,
        x: float,
        y: float,
        width: int,
        height: int,
        max_hp: int,
        echo_reward: int,
        color: tuple,
    ):
        self.boss_id = boss_id
        self.name = name
        self.subtitle = subtitle
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.vx = 0.0
        self.vy = 0.0
        self.facing = -1

        self.max_hp = max_hp
        self.hp = max_hp
        self.echo_reward = echo_reward
        self.contact_damage = 1
        self.color = color
        self.flying = False

        self.phase = 1
        self.state = "IDLE"
        self.state_timer = 1.0
        self.pattern_index = 0
        self.flash_timer = 0.0
        self.anim_timer = 0.0
        self.on_ground = False
        self.reward_granted = False

    @property
    def dead(self) -> bool:
        return self.hp <= 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def check_blocked(self, slash_dir: str, attacker_x: float) -> bool:
        return False

    def get_active_attack_rect(self):
        return None

    def take_damage(self, amount: int, kb_dir: int):
        if self.dead:
            return
        self.hp = max(0, self.hp - amount)
        self.flash_timer = 0.10

    def update(self, dt: float, player, room, combat_manager, audio, particles, camera):
        if self.dead:
            return
        self.anim_timer += dt
        if self.flash_timer > 0:
            self.flash_timer -= dt

        # Check Phase 2 Transition at 50% HP
        if self.phase == 1 and self.hp <= self.max_hp // 2:
            self.phase = 2
            self.state = "PHASE_SHIFT"
            self.state_timer = 0.9
            self.vx = 0.0
            audio.play_sfx("phase_shift")
            camera.add_trauma(0.75)
            particles.emit_burst(
                self.rect.centerx,
                self.rect.centery,
                PALETTE["solar_gold"],
                count=36,
                speed=180,
            )

        self._update_boss_ai(dt, player, room, combat_manager, audio, particles, camera)

        if not self.flying:
            self.vy = min(MAX_FALL_SPEED, self.vy + GRAVITY * dt)

        # Physics collision with arena walls & floor
        self.x += self.vx * dt
        r = self.rect
        for tile in room.solid_rects:
            if r.colliderect(tile):
                if self.vx > 0:
                    self.x = float(tile.left - self.width)
                elif self.vx < 0:
                    self.x = float(tile.right)
                self.vx = 0.0
                r = self.rect

        self.y += self.vy * dt
        r = self.rect
        self.on_ground = False
        for tile in room.solid_rects:
            if r.colliderect(tile):
                if self.vy > 0:
                    self.y = float(tile.top - self.height)
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = float(tile.bottom)
                    self.vy = 0.0
                r = self.rect

    def _update_boss_ai(
        self, dt: float, player, room, combat_manager, audio, particles, camera
    ):
        pass

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        if self.dead:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        col = PALETTE["white"] if self.flash_timer > 0 else self.color
        pygame.draw.rect(surface, col, (sx, sy, self.width, self.height), border_radius=4)
        # Crown / Silhouette Horns
        pygame.draw.polygon(
            surface,
            PALETTE["solar_gold"] if self.phase == 2 else PALETTE["bone"],
            [
                (sx + 2, sy),
                (sx - 3, sy - 8),
                (sx + self.width // 2, sy - 3),
                (sx + self.width + 3, sy - 8),
                (sx + self.width - 2, sy),
            ],
        )
        if self.state.startswith("TELEGRAPH"):
            pygame.draw.rect(
                surface,
                PALETTE["amber"],
                (sx - 3, sy - 3, self.width + 6, self.height + 6),
                1,
            )


class AshenWarden(Boss):
    """
    Boss 1: Malakor, The Ashen Warden.
    Attacks:
      1. Halberd Bull-Charge across arena.
      2. Crushing Leap Slam with shockwave pillars.
      3. Cinder Mortar Barrage (enhanced in Phase 2).
    """

    def __init__(self, x: float, y: float):
        super().__init__(
            boss_id="boss_warden",
            name="MALAKOR, ASHEN WARDEN",
            subtitle="Guardian of the Sunken Catacombs",
            x=x,
            y=y,
            width=26,
            height=36,
            max_hp=220,
            echo_reward=200,
            color=PALETTE["crimson"],
        )

    def _update_boss_ai(
        self, dt: float, player, room, combat_manager, audio, particles, camera
    ):
        dx = player.rect.centerx - self.rect.centerx
        speed_mult = 1.3 if self.phase == 2 else 1.0

        if self.state == "PHASE_SHIFT":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "IDLE"
                self.state_timer = 0.4

        elif self.state == "IDLE":
            self.vx = 0.0
            self.state_timer -= dt * speed_mult
            if self.state_timer <= 0:
                self.facing = 1 if dx >= 0 else -1
                self.pattern_index = (self.pattern_index + 1) % 3
                if self.pattern_index == 0:
                    self.state = "TELEGRAPH_CHARGE"
                    self.state_timer = 0.55 / speed_mult
                elif self.pattern_index == 1:
                    self.state = "TELEGRAPH_LEAP"
                    self.state_timer = 0.50 / speed_mult
                else:
                    self.state = "TELEGRAPH_ERUPT"
                    self.state_timer = 0.55 / speed_mult

        elif self.state == "TELEGRAPH_CHARGE":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "CHARGE"
                self.state_timer = 0.55
                self.vx = self.facing * 235.0 * speed_mult
                audio.play_sfx("dash")

        elif self.state == "CHARGE":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.vx = 0.0
                self.state = "IDLE"
                self.state_timer = 0.75

        elif self.state == "TELEGRAPH_LEAP":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "LEAP"
                self.vy = -310.0
                self.vx = max(-210.0, min(210.0, dx * 1.4))
                audio.play_sfx("jump")

        elif self.state == "LEAP":
            if self.on_ground and self.vy == 0.0:
                self.vx = 0.0
                camera.add_trauma(0.55)
                audio.play_sfx("hit")
                # Spawn ground fire pillars outward
                count = 4 if self.phase == 2 else 2
                for i in range(1, count + 1):
                    for side in (-1, 1):
                        combat_manager.spawn_pillar(
                            self.rect.centerx + side * i * 48,
                            self.rect.bottom,
                            width=20,
                            height=85,
                            damage=1,
                            telegraph_time=0.45,
                            active_time=0.30,
                            color=PALETTE["crimson"],
                        )
                self.state = "IDLE"
                self.state_timer = 0.85

        elif self.state == "TELEGRAPH_ERUPT":
            self.state_timer -= dt
            if self.state_timer <= 0:
                # Fire mortar embers
                num_orbs = 5 if self.phase == 2 else 3
                for i in range(num_orbs):
                    ang = -math.pi * (0.2 + 0.6 * (i / max(1, num_orbs - 1)))
                    combat_manager.spawn_projectile(
                        self.rect.centerx,
                        self.rect.top,
                        math.cos(ang) * 165.0,
                        math.sin(ang) * 165.0,
                        damage=1,
                        team="enemy",
                        color=PALETTE["amber"],
                        radius=5,
                    )
                self.state = "IDLE"
                self.state_timer = 0.8


class MycelialMatriarch(Boss):
    """
    Boss 2: Lyra, Mycelial Matriarch.
    Hovering boss with swooping dives, radial spore rings, and toxic canopy pillars.
    """

    def __init__(self, x: float, y: float):
        super().__init__(
            boss_id="boss_matriarch",
            name="LYRA, MYCELIAL MATRIARCH",
            subtitle="Choir of the Overgrown Sanctuary",
            x=x,
            y=y,
            width=24,
            height=28,
            max_hp=260,
            echo_reward=260,
            color=PALETTE["spore_green"],
        )
        self.flying = True

    def _update_boss_ai(
        self, dt: float, player, room, combat_manager, audio, particles, camera
    ):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        speed_mult = 1.35 if self.phase == 2 else 1.0

        if self.state == "PHASE_SHIFT":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "IDLE"
                self.state_timer = 0.4

        elif self.state == "IDLE":
            # Hover in a figure-eight above the floor
            self.vx = math.cos(self.anim_timer * 2.4) * 70.0 * speed_mult
            self.vy = math.sin(self.anim_timer * 4.8) * 38.0
            self.state_timer -= dt * speed_mult
            if self.state_timer <= 0:
                self.pattern_index = (self.pattern_index + 1) % 3
                self.vx = 0.0
                self.vy = 0.0
                if self.pattern_index == 0:
                    self.state = "TELEGRAPH_RING"
                    self.state_timer = 0.55 / speed_mult
                elif self.pattern_index == 1:
                    self.state = "TELEGRAPH_SWOOP"
                    self.state_timer = 0.50 / speed_mult
                else:
                    self.state = "TELEGRAPH_COLUMNS"
                    self.state_timer = 0.55 / speed_mult

        elif self.state == "TELEGRAPH_RING":
            self.state_timer -= dt
            if self.state_timer <= 0:
                num = 10 if self.phase == 2 else 6
                for i in range(num):
                    ang = (math.tau * i) / num + self.anim_timer
                    combat_manager.spawn_projectile(
                        self.rect.centerx,
                        self.rect.centery,
                        math.cos(ang) * 140.0,
                        math.sin(ang) * 140.0,
                        damage=1,
                        team="enemy",
                        color=PALETTE["spore_green"],
                        radius=4,
                    )
                audio.play_sfx("spell")
                self.state = "IDLE"
                self.state_timer = 1.1

        elif self.state == "TELEGRAPH_SWOOP":
            self.state_timer -= dt
            if self.state_timer <= 0:
                ang = math.atan2(dy, dx)
                self.vx = math.cos(ang) * 235.0 * speed_mult
                self.vy = math.sin(ang) * 235.0 * speed_mult
                self.state = "SWOOP"
                self.state_timer = 0.48
                audio.play_sfx("dash")

        elif self.state == "SWOOP":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.vy = -110.0
                self.state = "IDLE"
                self.state_timer = 0.9

        elif self.state == "TELEGRAPH_COLUMNS":
            self.state_timer -= dt
            if self.state_timer <= 0:
                for offset in (-80, 0, 80):
                    combat_manager.spawn_pillar(
                        player.rect.centerx + offset,
                        236,
                        width=24,
                        height=150,
                        damage=1,
                        telegraph_time=0.55,
                        active_time=0.35,
                        color=PALETTE["spore_green"],
                    )
                self.state = "IDLE"
                self.state_timer = 1.0


class HollowSunAurelius(Boss):
    """
    Boss 3 (Final Boss): Aurelius, The Hollow Sun.
    Phase 1: Radiant Sword Dash, Solar Spear Volley, Judgment Pillars.
    Phase 2 (Eclipse State): Faster chain-telegraphs, full-arena solar lattice, radial nova.
    """

    def __init__(self, x: float, y: float):
        super().__init__(
            boss_id="boss_aurelius",
            name="AURELIUS, THE HOLLOW SUN",
            subtitle="Sovereign of the Fractured Star",
            x=x,
            y=y,
            width=22,
            height=34,
            max_hp=340,
            echo_reward=500,
            color=PALETTE["solar_gold"],
        )

    def _update_boss_ai(
        self, dt: float, player, room, combat_manager, audio, particles, camera
    ):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        speed_mult = 1.4 if self.phase == 2 else 1.0

        if self.state == "PHASE_SHIFT":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.color = PALETTE["void_violet"]
                self.state = "IDLE"
                self.state_timer = 0.35

        elif self.state == "IDLE":
            self.vx = 0.0
            self.state_timer -= dt * speed_mult
            if self.state_timer <= 0:
                self.facing = 1 if dx >= 0 else -1
                self.pattern_index = (self.pattern_index + 1) % 3
                if self.pattern_index == 0:
                    self.state = "TELEGRAPH_BLADE"
                    self.state_timer = 0.48 / speed_mult
                elif self.pattern_index == 1:
                    self.state = "TELEGRAPH_JUDGMENT"
                    self.state_timer = 0.52 / speed_mult
                else:
                    self.state = "TELEGRAPH_NOVA"
                    self.state_timer = 0.55 / speed_mult

        elif self.state == "TELEGRAPH_BLADE":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "BLADE_DASH"
                self.state_timer = 0.38
                self.vx = self.facing * 285.0 * speed_mult
                audio.play_sfx("slash")

        elif self.state == "BLADE_DASH":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.vx = 0.0
                # Fire trailing spears toward player
                ang = math.atan2(dy, dx)
                for spread in (-0.18, 0.0, 0.18):
                    combat_manager.spawn_projectile(
                        self.rect.centerx,
                        self.rect.centery,
                        math.cos(ang + spread) * 200.0,
                        math.sin(ang + spread) * 200.0,
                        damage=1,
                        team="enemy",
                        color=PALETTE["solar_gold"],
                        radius=5,
                    )
                self.state = "IDLE"
                self.state_timer = 0.65

        elif self.state == "TELEGRAPH_JUDGMENT":
            self.state_timer -= dt
            if self.state_timer <= 0:
                spacing = 54 if self.phase == 2 else 72
                offset_shift = random.choice([0, 26])
                for px in range(60 + offset_shift, 420, spacing):
                    combat_manager.spawn_pillar(
                        px,
                        236,
                        width=20,
                        height=190,
                        damage=1,
                        telegraph_time=0.55,
                        active_time=0.32,
                        color=PALETTE["solar_gold"],
                    )
                audio.play_sfx("spell")
                self.state = "IDLE"
                self.state_timer = 0.85

        elif self.state == "TELEGRAPH_NOVA":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.vy = -240.0
                num = 12 if self.phase == 2 else 8
                for i in range(num):
                    ang = (math.tau * i) / num
                    combat_manager.spawn_projectile(
                        self.rect.centerx,
                        self.rect.centery - 8,
                        math.cos(ang) * 165.0,
                        math.sin(ang) * 165.0,
                        damage=1,
                        team="enemy",
                        color=PALETTE["amber"],
                        radius=5,
                    )
                audio.play_sfx("boss_roar")
                self.state = "IDLE"
                self.state_timer = 0.9


def create_boss(boss_id: str, x: float, y: float) -> Boss:
    mapping = {
        "boss_warden": AshenWarden,
        "boss_matriarch": MycelialMatriarch,
        "boss_aurelius": HollowSunAurelius,
    }
    cls = mapping.get(boss_id, AshenWarden)
    return cls(x, y)