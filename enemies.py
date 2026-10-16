"""
Five distinct enemy archetypes with clear attack telegraphs, state machines,
and behavioral identity:
1. AshHusk ('husk') - Basic melee patroller with telegraphed lunge.
2. GloomStalker ('stalker') - Fast aggressive predator that leaps at the player.
3. SporeWeaver ('weaver') - Hovering ranged caster firing toxic spore orbs.
4. ObsidianSentinel ('sentinel') - Heavily armored knight with frontal shield & cleave.
5. SolarInquisitor ('inquisitor') - Elite adversary with teleport strike & pillar burst.
"""

import math
import pygame
from game.settings import PALETTE, GRAVITY, MAX_FALL_SPEED


class Enemy:
    """Base enemy class handling physics, health, hit-stun, and telegraph timing."""

    def __init__(
        self,
        x: float,
        y: float,
        width: int,
        height: int,
        hp: int,
        echo_reward: int,
        color: tuple,
    ):
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.vx = 0.0
        self.vy = 0.0
        self.facing = -1

        self.max_hp = hp
        self.hp = hp
        self.echo_reward = echo_reward
        self.contact_damage = 1
        self.color = color
        self.flying = False

        # States: PATROL, TELEGRAPH, ATTACK, COOLDOWN, STUNNED, DEAD
        self.state = "PATROL"
        self.state_timer = 0.0
        self.flash_timer = 0.0
        self.anim_timer = 0.0
        self.on_ground = False

    @property
    def dead(self) -> bool:
        return self.state == "DEAD" or self.hp <= 0

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
        self.hp -= amount
        self.flash_timer = 0.12
        self.vx = kb_dir * 115.0
        if not self.flying:
            self.vy = -90.0
        if self.hp <= 0:
            self.state = "DEAD"
        elif self.state != "ATTACK":
            self.state = "STUNNED"
            self.state_timer = 0.16

    def update(self, dt: float, player, room, combat_manager):
        if self.dead:
            return
        self.anim_timer += dt
        if self.flash_timer > 0:
            self.flash_timer -= dt

        if self.state == "STUNNED":
            self.state_timer -= dt
            self.vx *= 0.85
            if self.state_timer <= 0:
                self.state = "PATROL"
        else:
            self._update_ai(dt, player, room, combat_manager)

        if not self.flying:
            self.vy = min(MAX_FALL_SPEED, self.vy + GRAVITY * dt)

        self._apply_physics(dt, room.solid_rects)

    def _update_ai(self, dt: float, player, room, combat_manager):
        pass

    def _apply_physics(self, dt: float, solid_rects: list):
        self.x += self.vx * dt
        r = self.rect
        for tile in solid_rects:
            if r.colliderect(tile):
                if self.vx > 0:
                    self.x = float(tile.left - self.width)
                elif self.vx < 0:
                    self.x = float(tile.right)
                self.vx = -self.vx * 0.5
                self.facing *= -1
                r = self.rect

        self.y += self.vy * dt
        r = self.rect
        self.on_ground = False
        for tile in solid_rects:
            if r.colliderect(tile):
                if self.vy > 0:
                    self.y = float(tile.top - self.height)
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = float(tile.bottom)
                    self.vy = 0.0
                r = self.rect

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        if self.dead:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        col = PALETTE["white"] if self.flash_timer > 0 else self.color
        pygame.draw.rect(surface, col, (sx, sy, self.width, self.height), border_radius=2)

        # Telegraph warning indicator
        if self.state == "TELEGRAPH":
            pygame.draw.circle(
                surface, PALETTE["amber"], (sx + self.width // 2, sy - 6), 3
            )


class AshHusk(Enemy):
    """1. Weak melee creature that patrols and performs a telegraphed short lunge."""

    def __init__(self, x: float, y: float):
        super().__init__(x, y, width=13, height=20, hp=24, echo_reward=8, color=PALETTE["ash"])

    def _update_ai(self, dt: float, player, room, combat_manager):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if self.state == "PATROL":
            self.vx = self.facing * 42.0
            if abs(self.x - self.spawn_x) > 65:
                self.facing = -1 if self.x > self.spawn_x else 1
            if dist < 72 and abs(dy) < 28:
                self.facing = 1 if dx >= 0 else -1
                self.state = "TELEGRAPH"
                self.state_timer = 0.45
                self.vx = 0.0

        elif self.state == "TELEGRAPH":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "ATTACK"
                self.state_timer = 0.25
                self.vx = self.facing * 155.0

        elif self.state == "ATTACK":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "COOLDOWN"
                self.state_timer = 0.65
                self.vx = 0.0

        elif self.state == "COOLDOWN":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "PATROL"


class GloomStalker(Enemy):
    """2. Fast aggressive enemy that pressures the player with leaping pounces."""

    def __init__(self, x: float, y: float):
        super().__init__(
            x, y, width=16, height=14, hp=34, echo_reward=14, color=PALETTE["void_violet"]
        )

    def _update_ai(self, dt: float, player, room, combat_manager):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if self.state == "PATROL":
            if dist < 165 and abs(dy) < 64:
                self.facing = 1 if dx >= 0 else -1
                self.vx = self.facing * 105.0
                if dist < 85 and self.on_ground:
                    self.state = "TELEGRAPH"
                    self.state_timer = 0.30
                    self.vx = 0.0
            else:
                self.vx = self.facing * 60.0
                if abs(self.x - self.spawn_x) > 80:
                    self.facing *= -1

        elif self.state == "TELEGRAPH":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "ATTACK"
                self.state_timer = 0.40
                self.vx = self.facing * 220.0
                self.vy = -195.0

        elif self.state == "ATTACK":
            self.state_timer -= dt
            if self.state_timer <= 0 and self.on_ground:
                self.state = "COOLDOWN"
                self.state_timer = 0.45
                self.vx = 0.0

        elif self.state == "COOLDOWN":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "PATROL"


class SporeWeaver(Enemy):
    """3. Hovering ranged enemy that keeps distance and fires aimed spore projectiles."""

    def __init__(self, x: float, y: float):
        super().__init__(
            x, y, width=16, height=16, hp=32, echo_reward=16, color=PALETTE["spore_green"]
        )
        self.flying = True

    def _update_ai(self, dt: float, player, room, combat_manager):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        self.facing = 1 if dx >= 0 else -1

        if self.state == "PATROL":
            self.vx = math.cos(self.anim_timer * 2.0) * 32.0
            self.vy = math.sin(self.anim_timer * 3.0) * 24.0
            if dist < 190:
                self.state = "TELEGRAPH"
                self.state_timer = 0.55

        elif self.state == "TELEGRAPH":
            self.vx *= 0.9
            self.vy *= 0.9
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "ATTACK"
                self.state_timer = 0.2
                angle = math.atan2(dy, dx)
                combat_manager.spawn_projectile(
                    self.rect.centerx,
                    self.rect.centery,
                    math.cos(angle) * 145.0,
                    math.sin(angle) * 145.0,
                    damage=1,
                    team="enemy",
                    color=PALETTE["spore_green"],
                    radius=4,
                    lifetime=2.4,
                )

        elif self.state == "ATTACK":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "COOLDOWN"
                self.state_timer = 1.15

        elif self.state == "COOLDOWN":
            self.state_timer -= dt
            # Drift slightly back if player is very close
            if dist < 70:
                self.vx = -self.facing * 45.0
            if self.state_timer <= 0:
                self.state = "PATROL"


class ObsidianSentinel(Enemy):
    """4. Heavily armored knight with a frontal shield that blocks front melee attacks."""

    def __init__(self, x: float, y: float):
        super().__init__(
            x, y, width=18, height=26, hp=60, echo_reward=25, color=PALETTE["stone"]
        )

    def check_blocked(self, slash_dir: str, attacker_x: float) -> bool:
        if self.state in ("ATTACK", "COOLDOWN", "STUNNED"):
            return False
        if slash_dir == "down":
            return False
        attacker_in_front = (attacker_x >= self.rect.centerx and self.facing == 1) or (
            attacker_x < self.rect.centerx and self.facing == -1
        )
        return attacker_in_front

    def get_active_attack_rect(self):
        if self.state == "ATTACK":
            if self.facing == 1:
                return pygame.Rect(self.rect.right, self.rect.top, 22, self.height)
            return pygame.Rect(self.rect.left - 22, self.rect.top, 22, self.height)
        return None

    def _update_ai(self, dt: float, player, room, combat_manager):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if self.state == "PATROL":
            if dist < 130 and abs(dy) < 36:
                self.facing = 1 if dx >= 0 else -1
                self.vx = self.facing * 32.0
                if dist < 52:
                    self.state = "TELEGRAPH"
                    self.state_timer = 0.55
                    self.vx = 0.0
            else:
                self.vx = self.facing * 24.0
                if abs(self.x - self.spawn_x) > 55:
                    self.facing *= -1

        elif self.state == "TELEGRAPH":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "ATTACK"
                self.state_timer = 0.28
                self.vx = self.facing * 95.0

        elif self.state == "ATTACK":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "COOLDOWN"
                self.state_timer = 1.1
                self.vx = 0.0

        elif self.state == "COOLDOWN":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "PATROL"

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        super().draw(surface, cam_x, cam_y)
        if self.dead:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        # Draw frontal tower shield
        sh_x = sx + (self.width - 2 if self.facing == 1 else -3)
        pygame.draw.rect(
            surface, PALETTE["amber"], (sh_x, sy + 3, 4, self.height - 4)
        )
        atk_rect = self.get_active_attack_rect()
        if atk_rect:
            pygame.draw.rect(
                surface, PALETTE["crimson"], atk_rect.move(-cam_x, -cam_y)
            )


class SolarInquisitor(Enemy):
    """5. Elite enemy with multiple attacks: solar burst fan and ground pillar invocation."""

    def __init__(self, x: float, y: float):
        super().__init__(
            x, y, width=16, height=24, hp=75, echo_reward=38, color=PALETTE["solar_gold"]
        )
        self.attack_cycle = 0

    def _update_ai(self, dt: float, player, room, combat_manager):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if self.state == "PATROL":
            self.facing = 1 if dx >= 0 else -1
            if dist < 190:
                self.vx = self.facing * 55.0
                if dist < 140:
                    self.state = "TELEGRAPH"
                    self.state_timer = 0.55
                    self.vx = 0.0
            else:
                self.vx = 0.0

        elif self.state == "TELEGRAPH":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "ATTACK"
                self.state_timer = 0.3
                self.attack_cycle = (self.attack_cycle + 1) % 2
                if self.attack_cycle == 0:
                    # Attack A: Triple Solar Orb Fan
                    base_ang = math.atan2(dy, dx)
                    for offset in (-0.25, 0.0, 0.25):
                        a = base_ang + offset
                        combat_manager.spawn_projectile(
                            self.rect.centerx,
                            self.rect.centery - 4,
                            math.cos(a) * 170.0,
                            math.sin(a) * 170.0,
                            damage=1,
                            team="enemy",
                            color=PALETTE["solar_gold"],
                            radius=4,
                        )
                else:
                    # Attack B: Summon Ground Pillar under player + dash step
                    combat_manager.spawn_pillar(
                        player.rect.centerx,
                        self.rect.bottom,
                        width=22,
                        height=90,
                        damage=1,
                        telegraph_time=0.55,
                        active_time=0.30,
                        color=PALETTE["amber"],
                    )
                    self.vx = self.facing * 175.0

        elif self.state == "ATTACK":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "COOLDOWN"
                self.state_timer = 1.0
                self.vx = 0.0

        elif self.state == "COOLDOWN":
            self.state_timer -= dt
            if self.state_timer <= 0:
                self.state = "PATROL"


def create_enemy(enemy_type: str, x: float, y: float) -> Enemy:
    mapping = {
        "husk": AshHusk,
        "stalker": GloomStalker,
        "weaver": SporeWeaver,
        "sentinel": ObsidianSentinel,
        "inquisitor": SolarInquisitor,
    }
    cls = mapping.get(enemy_type, AshHusk)
    return cls(x, y)