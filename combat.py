"""
Combat resolution system: Melee hitboxes, Projectiles, Shockwaves, Pogo physics,
single-hit-per-swing tracking, knockback, and hit-stop feedback.
"""

import math
import pygame
from game.settings import (
    PALETTE,
    POGO_VELOCITY,
    LUMEN_PER_HIT,
    HIT_STOP_DURATION,
)


class MeleeSlashHitbox:
    """Represents a single directional melee swing that hits each target at most once."""

    def __init__(
        self,
        owner,
        direction: str,
        rect: pygame.Rect,
        damage: int,
        duration: float = 0.14,
    ):
        self.owner = owner
        self.direction = direction
        self.rect = rect
        self.damage = damage
        self.duration = duration
        self.hit_targets = set()

    def update(self, dt: float) -> bool:
        self.duration -= dt
        # Follow owner slightly during swing
        if self.direction == "right":
            self.rect.midleft = (self.owner.rect.right - 2, self.owner.rect.centery)
        elif self.direction == "left":
            self.rect.midright = (self.owner.rect.left + 2, self.owner.rect.centery)
        elif self.direction == "up":
            self.rect.midbottom = (self.owner.rect.centerx, self.owner.rect.top + 2)
        elif self.direction == "down":
            self.rect.midtop = (self.owner.rect.centerx, self.owner.rect.bottom - 2)
        return self.duration > 0


class Projectile:
    """Ranged projectile fired by player (Solar Lance) or enemies/bosses."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        damage: int,
        team: str,
        color: tuple,
        radius: int = 5,
        lifetime: float = 2.5,
        piercing: bool = False,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.damage = damage
        self.team = team  # "player" or "enemy"
        self.color = color
        self.radius = radius
        self.lifetime = lifetime
        self.piercing = piercing
        self.hit_targets = set()

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def update(self, dt: float, solid_rects: list) -> bool:
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False
        self.x += self.vx * dt
        self.y += self.vy * dt

        if not self.piercing:
            r = self.rect
            for tile in solid_rects:
                if r.colliderect(tile):
                    return False
        return True

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        pygame.draw.circle(surface, self.color, (sx, sy), self.radius + 2)
        pygame.draw.circle(surface, PALETTE["white"], (sx, sy), max(2, self.radius - 1))


class ShockwavePillar:
    """Hazard pillar or ground eruption used by elite enemies and bosses."""

    def __init__(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        damage: int,
        telegraph_time: float,
        active_time: float,
        color: tuple,
    ):
        self.rect = pygame.Rect(int(x - width // 2), int(y - height), width, height)
        self.damage = damage
        self.telegraph_time = telegraph_time
        self.max_telegraph = max(0.01, telegraph_time)
        self.active_time = active_time
        self.color = color
        self.has_hit_player = False

    @property
    def is_active(self) -> bool:
        return self.telegraph_time <= 0 and self.active_time > 0

    def update(self, dt: float) -> bool:
        if self.telegraph_time > 0:
            self.telegraph_time -= dt
            return True
        self.active_time -= dt
        return self.active_time > 0

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        draw_rect = self.rect.move(-cam_x, -cam_y)
        if self.telegraph_time > 0:
            ratio = 1.0 - (self.telegraph_time / self.max_telegraph)
            warn_w = max(2, int(draw_rect.width * (0.2 + 0.8 * ratio)))
            warn_rect = pygame.Rect(
                draw_rect.centerx - warn_w // 2,
                draw_rect.bottom - 6,
                warn_w,
                6,
            )
            pygame.draw.rect(surface, self.color, warn_rect)
            pygame.draw.line(
                surface,
                self.color,
                (draw_rect.centerx, draw_rect.top),
                (draw_rect.centerx, draw_rect.bottom),
                1,
            )
        else:
            pygame.draw.rect(surface, self.color, draw_rect)
            inner = draw_rect.inflate(-6, 0)
            if inner.width > 0:
                pygame.draw.rect(surface, PALETTE["white"], inner)


class CombatManager:
    """Orchestrates all active hitboxes, projectiles, shockwaves, and damage events."""

    def __init__(self, audio, particles, camera):
        self.audio = audio
        self.particles = particles
        self.camera = camera
        self.melee_hitboxes = []
        self.projectiles = []
        self.pillars = []
        self.hit_stop_timer = 0.0

    def clear_room_transients(self):
        self.melee_hitboxes.clear()
        self.projectiles.clear()
        self.pillars.clear()

    def spawn_player_slash(
        self, player, direction: str, rect: pygame.Rect, damage: int
    ) -> MeleeSlashHitbox:
        hb = MeleeSlashHitbox(player, direction, rect, damage)
        self.melee_hitboxes.append(hb)
        cx, cy = rect.center
        self.particles.emit_slash(cx, cy, direction, PALETTE["amber"], radius=22)
        self.audio.play_sfx("slash")
        return hb

    def spawn_projectile(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        damage: int,
        team: str,
        color: tuple,
        radius: int = 5,
        lifetime: float = 2.5,
        piercing: bool = False,
    ):
        self.projectiles.append(
            Projectile(x, y, vx, vy, damage, team, color, radius, lifetime, piercing)
        )

    def spawn_pillar(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        damage: int,
        telegraph_time: float = 0.65,
        active_time: float = 0.35,
        color: tuple = PALETTE["amber"],
    ):
        self.pillars.append(
            ShockwavePillar(
                x, y, width, height, damage, telegraph_time, active_time, color
            )
        )

    def update(self, dt: float, player, enemies: list, bosses: list, room):
        if self.hit_stop_timer > 0:
            self.hit_stop_timer -= dt

        self.melee_hitboxes = [hb for hb in self.melee_hitboxes if hb.update(dt)]

        alive_projectiles = []
        for proj in self.projectiles:
            if proj.update(dt, room.solid_rects):
                alive_projectiles.append(proj)
            else:
                self.particles.emit_burst(
                    proj.x, proj.y, proj.color, count=6, speed=60, size=2.0
                )
        self.projectiles = alive_projectiles

        self.pillars = [p for p in self.pillars if p.update(dt)]

        hostiles = [e for e in enemies if not e.dead] + [
            b for b in bosses if not b.dead
        ]

        # 1. Resolve Player Melee Slashes
        for hb in self.melee_hitboxes:
            # Check pogo on room spikes!
            if hb.direction == "down" and "spikes" not in hb.hit_targets:
                for spike in room.spike_rects:
                    if hb.rect.colliderect(spike):
                        hb.hit_targets.add("spikes")
                        player.apply_pogo_bounce()
                        self.audio.play_sfx("hit")
                        self.particles.emit_burst(
                            hb.rect.centerx,
                            spike.top,
                            PALETTE["bone"],
                            count=8,
                            speed=90,
                        )
                        break

            # Check hitting enemies & bosses
            for target in hostiles:
                if id(target) in hb.hit_targets:
                    continue
                if hb.rect.colliderect(target.rect):
                    hb.hit_targets.add(id(target))

                    # Check directional shield block (Obsidian Sentinel)
                    blocked = target.check_blocked(hb.direction, player.rect.centerx)
                    if blocked:
                        self.audio.play_sfx("slash")
                        self.particles.emit_burst(
                            target.rect.centerx,
                            target.rect.centery,
                            PALETTE["bone"],
                            count=10,
                            speed=110,
                        )
                        self.particles.emit_floating_text(
                            target.rect.centerx,
                            target.rect.top - 6,
                            "BLOCKED",
                            PALETTE["ash"],
                        )
                        if hb.direction == "down":
                            player.apply_pogo_bounce()
                        else:
                            player.vx = -player.facing * 140.0
                        continue

                    # Deal damage
                    kb_dir = 1 if target.rect.centerx >= player.rect.centerx else -1
                    target.take_damage(hb.damage, kb_dir)
                    self.audio.play_sfx("hit")
                    self.camera.add_trauma(0.26)
                    self.hit_stop_timer = HIT_STOP_DURATION

                    lumen_gain = LUMEN_PER_HIT + (
                        6 if "soul_catcher" in player.equipped_relics else 0
                    )
                    player.gain_lumen(lumen_gain)

                    self.particles.emit_directional_sparks(
                        target.rect.centerx,
                        target.rect.centery,
                        kb_dir,
                        -0.3,
                        PALETTE["amber"],
                        count=12,
                    )
                    self.particles.emit_floating_text(
                        target.rect.centerx,
                        target.rect.top - 4,
                        str(hb.damage),
                        PALETTE["solar_gold"],
                    )

                    if hb.direction == "down":
                        player.apply_pogo_bounce()

        # 2. Resolve Projectiles
        remaining_proj = []
        for proj in self.projectiles:
            consumed = False
            if proj.team == "player":
                for target in hostiles:
                    if id(target) in proj.hit_targets:
                        continue
                    if proj.rect.colliderect(target.rect):
                        proj.hit_targets.add(id(target))
                        kb_dir = 1 if proj.vx >= 0 else -1
                        target.take_damage(proj.damage, kb_dir)
                        self.audio.play_sfx("hit")
                        self.camera.add_trauma(0.3)
                        self.particles.emit_burst(
                            proj.x,
                            proj.y,
                            PALETTE["soul_cyan"],
                            count=14,
                            speed=120,
                        )
                        self.particles.emit_floating_text(
                            target.rect.centerx,
                            target.rect.top - 4,
                            str(proj.damage),
                            PALETTE["soul_cyan"],
                        )
                        if not proj.piercing:
                            consumed = True
                            break
            else:
                if not player.dead and proj.rect.colliderect(player.rect):
                    if player.take_damage(proj.damage, proj.x):
                        self.camera.add_trauma(0.45)
                    if not proj.piercing:
                        consumed = True

            if not consumed:
                remaining_proj.append(proj)
        self.projectiles = remaining_proj

        # 3. Resolve Pillars / Eruptions
        for pillar in self.pillars:
            if (
                pillar.is_active
                and not pillar.has_hit_player
                and not player.dead
                and pillar.rect.colliderect(player.rect)
            ):
                pillar.has_hit_player = True
                if player.take_damage(pillar.damage, pillar.rect.centerx):
                    self.camera.add_trauma(0.5)

        # 4. Resolve Player Abyssal Dive shockwave against enemies
        if player.state == "DIVE" and player.dive_shockwave_timer > 0:
            dive_rect = player.rect.inflate(44, 16)
            for target in hostiles:
                if id(target) not in player.dive_hit_targets and dive_rect.colliderect(
                    target.rect
                ):
                    player.dive_hit_targets.add(id(target))
                    kb_dir = 1 if target.rect.centerx >= player.rect.centerx else -1
                    dmg = player.get_melee_damage() * 2
                    target.take_damage(dmg, kb_dir)
                    self.particles.emit_floating_text(
                        target.rect.centerx,
                        target.rect.top - 6,
                        str(dmg),
                        PALETTE["void_violet"],
                    )

        # 5. Resolve Contact & Active Attack Boxes from Enemies & Bosses
        if not player.dead:
            for target in hostiles:
                attack_rect = target.get_active_attack_rect()
                if attack_rect and attack_rect.colliderect(player.rect):
                    if player.take_damage(target.contact_damage, target.rect.centerx):
                        self.camera.add_trauma(0.45)
                elif target.rect.colliderect(player.rect):
                    if player.take_damage(1, target.rect.centerx):
                        self.camera.add_trauma(0.4)

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        for pillar in self.pillars:
            pillar.draw(surface, cam_x, cam_y)
        for proj in self.projectiles:
            proj.draw(surface, cam_x, cam_y)