"""
Player entity featuring a complete state machine, responsive platforming with coyote time,
jump buffering, wall-sliding/jumping, directional melee attacks (with downward Pogo),
Shadow Dash, Solar Lance, Abyssal Dive, and Focus healing.
"""

import math
import pygame
from game.settings import (
    PALETTE,
    GRAVITY,
    MAX_FALL_SPEED,
    PLAYER_SPEED,
    PLAYER_ACCEL,
    PLAYER_FRICTION,
    PLAYER_AIR_ACCEL,
    JUMP_VELOCITY,
    JUMP_CUT_MULTIPLIER,
    DOUBLE_JUMP_VELOCITY,
    COYOTE_TIME,
    JUMP_BUFFER_TIME,
    WALL_SLIDE_SPEED,
    WALL_JUMP_VX,
    WALL_JUMP_VY,
    DASH_SPEED,
    DASH_DURATION,
    DASH_COOLDOWN,
    ATTACK_DURATION,
    ATTACK_COOLDOWN,
    POGO_VELOCITY,
    INVULN_DURATION,
    HURT_STUN_DURATION,
    MAX_LUMEN,
    HEAL_LUMEN_COST,
    HEAL_CHANNEL_TIME,
    HEAL_AMOUNT,
    SPELL_LUMEN_COST,
    SOLAR_LANCE_SPEED,
    ABYSSAL_DIVE_SPEED,
    KEY_BINDINGS,
)


class Player:
    """Controllable Vessel-Scribe protagonist Vesper."""

    WIDTH = 12
    HEIGHT = 22

    def __init__(self, x: float, y: float, audio, particles):
        self.audio = audio
        self.particles = particles

        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1  # 1 = Right, -1 = Left

        # State Machine: IDLE, RUN, JUMP, FALL, WALL_SLIDE, DASH, ATTACK, DIVE, HEAL, HURT, DEAD
        self.state = "IDLE"
        self.anim_timer = 0.0

        # Platforming State
        self.on_ground = False
        self.on_wall = 0  # -1 left wall, 1 right wall, 0 none
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.can_double_jump = False
        self.can_air_dash = True
        self.last_safe_pos = (float(x), float(y))

        # Timers
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.attack_timer = 0.0
        self.attack_cooldown_timer = 0.0
        self.invuln_timer = 0.0
        self.hurt_timer = 0.0
        self.heal_timer = 0.0
        self.dive_shockwave_timer = 0.0
        self.dive_hit_targets = set()

        # RPG Stats & Progression
        self.max_hp = 5
        self.hp = 5
        self.max_lumen = MAX_LUMEN
        self.lumen = 0
        self.echoes = 0
        self.weapon_level = 1

        self.abilities = {
            "shadow_dash": False,
            "solar_lance": False,
            "abyssal_dive": False,
            "monarch_wings": False,
        }
        self.owned_relics = []
        self.equipped_relics = []
        self.lore_unlocked = []
        self.defeated_bosses = []
        self.collected_items = []
        self.visited_rooms = ["sanctuary_hub"]
        self.broken_floors = []
        self.quests = {}
        self.story_flags = {
            "met_caelum": False,
            "met_orin": False,
            "met_veyla": False,
            "met_solen": False,
            "pelorus_opened": False,
        }
        self.checkpoint_room = "sanctuary_hub"
        self.checkpoint_pos = [140, 192]

    @property
    def dead(self) -> bool:
        return self.state == "DEAD" or self.hp <= 0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.WIDTH, self.HEIGHT)

    def load_from_save_dict(self, data: dict):
        self.checkpoint_room = data["checkpoint_room"]
        self.checkpoint_pos = list(data["checkpoint_pos"])
        self.x, self.y = float(self.checkpoint_pos[0]), float(self.checkpoint_pos[1])
        self.last_safe_pos = (self.x, self.y)
        self.max_hp = data["max_hp"]
        self.hp = data["hp"]
        self.lumen = data["lumen"]
        self.echoes = data["echoes"]
        self.weapon_level = data["weapon_level"]
        self.abilities.update(data["abilities"])
        self.owned_relics = list(data["owned_relics"])
        self.equipped_relics = list(data["equipped_relics"])
        self.lore_unlocked = list(data["lore_unlocked"])
        self.defeated_bosses = list(data["defeated_bosses"])
        self.collected_items = list(data["collected_items"])
        self.visited_rooms = list(data["visited_rooms"])
        self.broken_floors = list(data["broken_floors"])
        self.quests = dict(data["quests"])
        self.story_flags.update(data["story_flags"])
        self.state = "IDLE"
        self.vx = 0.0
        self.vy = 0.0

    def to_save_dict(self) -> dict:
        return {
            "version": 1,
            "checkpoint_room": self.checkpoint_room,
            "checkpoint_pos": list(self.checkpoint_pos),
            "max_hp": self.max_hp,
            "hp": self.hp,
            "lumen": self.lumen,
            "echoes": self.echoes,
            "weapon_level": self.weapon_level,
            "abilities": dict(self.abilities),
            "owned_relics": list(self.owned_relics),
            "equipped_relics": list(self.equipped_relics),
            "lore_unlocked": list(self.lore_unlocked),
            "defeated_bosses": list(self.defeated_bosses),
            "collected_items": list(self.collected_items),
            "visited_rooms": list(self.visited_rooms),
            "broken_floors": list(self.broken_floors),
            "quests": dict(self.quests),
            "story_flags": dict(self.story_flags),
        }

    def get_melee_damage(self) -> int:
        base = 8 + (self.weapon_level - 1) * 4
        if "cinder_heart" in self.equipped_relics:
            base = int(round(base * 1.25))
        return base

    def gain_lumen(self, amount: int):
        self.lumen = min(self.max_lumen, self.lumen + amount)

    def apply_pogo_bounce(self):
        self.vy = POGO_VELOCITY
        self.can_air_dash = True
        if self.abilities.get("monarch_wings"):
            self.can_double_jump = True

    def trigger_jump_input(self):
        self.jump_buffer_timer = JUMP_BUFFER_TIME

    def release_jump_input(self):
        if self.vy < -60.0 and self.state in ("JUMP", "ATTACK"):
            self.vy *= JUMP_CUT_MULTIPLIER

    def trigger_dash_input(self):
        if self.dead or self.state in ("HURT", "DASH", "DIVE"):
            return
        if self.dash_cooldown_timer <= 0 and (self.on_ground or self.can_air_dash):
            self.state = "DASH"
            self.dash_timer = DASH_DURATION
            cd = DASH_COOLDOWN * (0.78 if "swift_anklet" in self.equipped_relics else 1.0)
            self.dash_cooldown_timer = cd
            if not self.on_ground:
                self.can_air_dash = False
            self.vx = self.facing * DASH_SPEED
            self.vy = 0.0
            if self.abilities.get("shadow_dash"):
                self.invuln_timer = max(self.invuln_timer, DASH_DURATION + 0.05)
            self.audio.play_sfx("dash")
            color = (
                PALETTE["void_violet"]
                if self.abilities.get("shadow_dash")
                else PALETTE["bone"]
            )
            self.particles.emit_burst(
                self.rect.centerx, self.rect.centery, color, count=10, speed=85
            )

    def trigger_attack_input(self, keys, combat_manager):
        if self.dead or self.state in ("HURT", "DASH", "DIVE", "HEAL"):
            return
        if self.attack_cooldown_timer > 0:
            return

        up_held = any(keys[k] for k in KEY_BINDINGS["up"])
        down_held = any(keys[k] for k in KEY_BINDINGS["down"])

        if up_held:
            direction = "up"
            hb_rect = pygame.Rect(self.rect.centerx - 15, self.rect.top - 22, 30, 24)
        elif down_held and not self.on_ground:
            direction = "down"
            hb_rect = pygame.Rect(self.rect.centerx - 15, self.rect.bottom - 2, 30, 24)
        elif self.facing == 1:
            direction = "right"
            hb_rect = pygame.Rect(self.rect.right - 2, self.rect.top - 3, 26, 26)
        else:
            direction = "left"
            hb_rect = pygame.Rect(self.rect.left - 24, self.rect.top - 3, 26, 26)

        self.attack_timer = ATTACK_DURATION
        self.attack_cooldown_timer = ATTACK_COOLDOWN
        self.state = "ATTACK"
        combat_manager.spawn_player_slash(
            self, direction, hb_rect, self.get_melee_damage()
        )

    def trigger_spell_input(self, keys, combat_manager):
        if self.dead or self.state in ("HURT", "DASH", "DIVE"):
            return
        if self.lumen < SPELL_LUMEN_COST:
            return

        down_held = any(keys[k] for k in KEY_BINDINGS["down"])

        # Down + Spell = Abyssal Dive (if unlocked)
        if down_held and self.abilities.get("abyssal_dive"):
            self.lumen -= SPELL_LUMEN_COST
            self.state = "DIVE"
            self.vx = 0.0
            self.vy = ABYSSAL_DIVE_SPEED
            self.invuln_timer = max(self.invuln_timer, 0.5)
            self.dive_hit_targets.clear()
            self.audio.play_sfx("spell")
            self.particles.emit_burst(
                self.rect.centerx,
                self.rect.centery,
                PALETTE["void_violet"],
                count=14,
                speed=110,
            )
            return

        # Neutral Spell = Solar Lance (if unlocked)
        if self.abilities.get("solar_lance"):
            self.lumen -= SPELL_LUMEN_COST
            self.audio.play_sfx("spell")
            dmg = self.get_melee_damage() * 2 + 4
            combat_manager.spawn_projectile(
                self.rect.centerx + self.facing * 10,
                self.rect.centery - 2,
                self.facing * SOLAR_LANCE_SPEED,
                0.0,
                dmg,
                team="player",
                color=PALETTE["soul_cyan"],
                radius=6,
                lifetime=1.2,
                piercing=True,
            )
            self.vx = -self.facing * 90.0
            self.particles.emit_burst(
                self.rect.centerx,
                self.rect.centery,
                PALETTE["soul_cyan"],
                count=12,
                speed=100,
            )

    def take_damage(self, amount: int, source_x: float) -> bool:
        if self.dead or self.invuln_timer > 0 or self.state == "DIVE":
            return False

        self.hp = max(0, self.hp - amount)
        extra_i = 0.35 if "wardens_crest" in self.equipped_relics else 0.0
        self.invuln_timer = INVULN_DURATION + extra_i
        self.hurt_timer = HURT_STUN_DURATION
        self.heal_timer = 0.0

        kb_dir = -1 if source_x > self.rect.centerx else 1
        self.vx = kb_dir * 165.0
        self.vy = -175.0

        self.audio.play_sfx("player_hurt")
        self.particles.emit_burst(
            self.rect.centerx,
            self.rect.centery,
            PALETTE["crimson"],
            count=18,
            speed=130,
        )

        if self.hp <= 0:
            self.state = "DEAD"
            self.vx = 0.0
            self.vy = 0.0
        else:
            self.state = "HURT"
        return True

    def update(self, dt: float, keys, room, camera):
        self.anim_timer += dt
        if self.dead:
            return

        # Decrement timers
        if self.coyote_timer > 0:
            self.coyote_timer -= dt
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= dt
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= dt
        if self.invuln_timer > 0:
            self.invuln_timer -= dt
        if self.dive_shockwave_timer > 0:
            self.dive_shockwave_timer -= dt

        # Hurt stun state
        if self.state == "HURT":
            self.hurt_timer -= dt
            if self.hurt_timer <= 0:
                self.state = "IDLE"

        # Abyssal Dive state
        elif self.state == "DIVE":
            self.vx = 0.0
            self.vy = ABYSSAL_DIVE_SPEED
            if self.on_ground:
                self.state = "IDLE"
                self.dive_shockwave_timer = 0.22
                camera.add_trauma(0.55)
                self.audio.play_sfx("hit")
                self.particles.emit_burst(
                    self.rect.centerx,
                    self.rect.bottom,
                    PALETTE["void_violet"],
                    count=24,
                    speed=160,
                )
                room.try_break_floors(self.rect.inflate(36, 18), self)

        # Dash state
        elif self.state == "DASH":
            self.dash_timer -= dt
            self.vy = 0.0
            if self.dash_timer <= 0:
                self.state = "IDLE"
                self.vx *= 0.5

        # Normal controllable states
        else:
            move_dir = 0
            if keys is not None:
                if any(keys[k] for k in KEY_BINDINGS["left"]):
                    move_dir -= 1
                if any(keys[k] for k in KEY_BINDINGS["right"]):
                    move_dir += 1

            # Focus Healing check
            heal_held = keys is not None and any(keys[k] for k in KEY_BINDINGS["heal"])
            if (
                heal_held
                and self.on_ground
                and move_dir == 0
                and self.hp < self.max_hp
                and self.lumen >= HEAL_LUMEN_COST
                and self.attack_timer <= 0
            ):
                self.state = "HEAL"
                self.vx = 0.0
                self.heal_timer += dt
                if int(self.heal_timer * 20) % 2 == 0:
                    self.particles.emit_burst(
                        self.rect.centerx,
                        self.rect.bottom - 4,
                        PALETTE["soul_cyan"],
                        count=2,
                        speed=40,
                        gravity=-90,
                    )
                if self.heal_timer >= HEAL_CHANNEL_TIME:
                    self.heal_timer = 0.0
                    self.lumen -= HEAL_LUMEN_COST
                    self.hp = min(self.max_hp, self.hp + HEAL_AMOUNT)
                    self.audio.play_sfx("heal")
                    self.particles.emit_burst(
                        self.rect.centerx,
                        self.rect.centery,
                        PALETTE["soul_cyan"],
                        count=18,
                        speed=110,
                    )
            else:
                self.heal_timer = 0.0
                if self.state == "HEAL":
                    self.state = "IDLE"

                # Horizontal Acceleration
                max_spd = PLAYER_SPEED * (
                    1.18 if "swift_anklet" in self.equipped_relics else 1.0
                )
                accel = PLAYER_ACCEL if self.on_ground else PLAYER_AIR_ACCEL
                if move_dir != 0:
                    self.facing = move_dir
                    self.vx += move_dir * accel * dt
                    self.vx = max(-max_spd, min(max_spd, self.vx))
                else:
                    if abs(self.vx) <= PLAYER_FRICTION * dt:
                        self.vx = 0.0
                    else:
                        self.vx -= math.copysign(PLAYER_FRICTION * dt, self.vx)

            # Jump Execution (Ground, Coyote, Wall Jump, or Monarch Double Jump)
            if self.jump_buffer_timer > 0:
                if self.coyote_timer > 0:
                    self.vy = JUMP_VELOCITY
                    self.on_ground = False
                    self.coyote_timer = 0.0
                    self.jump_buffer_timer = 0.0
                    self.audio.play_sfx("jump")
                    self.particles.emit_burst(
                        self.rect.centerx,
                        self.rect.bottom,
                        PALETTE["ash"],
                        count=6,
                        speed=55,
                    )
                elif self.on_wall != 0 and not self.on_ground:
                    self.vy = WALL_JUMP_VY
                    self.vx = -self.on_wall * WALL_JUMP_VX
                    self.facing = -self.on_wall
                    self.jump_buffer_timer = 0.0
                    self.audio.play_sfx("jump")
                    self.particles.emit_burst(
                        self.rect.centerx,
                        self.rect.centery,
                        PALETTE["bone"],
                        count=8,
                        speed=75,
                    )
                elif self.can_double_jump and self.abilities.get("monarch_wings"):
                    self.vy = DOUBLE_JUMP_VELOCITY
                    self.can_double_jump = False
                    self.jump_buffer_timer = 0.0
                    self.audio.play_sfx("jump")
                    self.particles.emit_burst(
                        self.rect.centerx,
                        self.rect.bottom,
                        PALETTE["solar_gold"],
                        count=12,
                        speed=85,
                    )

            # Attack timer update
            if self.attack_timer > 0:
                self.attack_timer -= dt

        # Gravity
        if self.state not in ("DASH", "DIVE"):
            self.vy = min(MAX_FALL_SPEED, self.vy + GRAVITY * dt)
            if self.on_wall != 0 and not self.on_ground and self.vy > WALL_SLIDE_SPEED:
                self.vy = WALL_SLIDE_SPEED

        # Move and resolve collisions
        self._move_and_collide(dt, room, keys)

        # Update State label for animation
        if self.state not in ("DASH", "DIVE", "HURT", "HEAL", "DEAD"):
            if self.attack_timer > 0:
                self.state = "ATTACK"
            elif not self.on_ground:
                if self.on_wall != 0 and self.vy > 0:
                    self.state = "WALL_SLIDE"
                elif self.vy < 0:
                    self.state = "JUMP"
                else:
                    self.state = "FALL"
            elif abs(self.vx) > 8.0:
                self.state = "RUN"
            else:
                self.state = "IDLE"

    def _move_and_collide(self, dt: float, room, keys):
        solids = list(room.solid_rects) + list(room.get_active_breakable_rects(self))
        # Shadow Gates block movement unless player is currently Shadow Dashing
        if not (self.state == "DASH" and self.abilities.get("shadow_dash")):
            solids.extend(room.shadow_gate_rects)

        # Horizontal step
        self.x += self.vx * dt
        r = self.rect
        self.on_wall = 0
        for tile in solids:
            if r.colliderect(tile):
                if self.vx > 0:
                    self.x = float(tile.left - self.WIDTH)
                    self.on_wall = 1
                elif self.vx < 0:
                    self.x = float(tile.right)
                    self.on_wall = -1
                self.vx = 0.0
                r = self.rect

        # Vertical step
        prev_bottom = self.rect.bottom
        self.y += self.vy * dt
        r = self.rect
        self.on_ground = False

        for tile in solids:
            if r.colliderect(tile):
                if self.vy > 0:
                    self.y = float(tile.top - self.HEIGHT)
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0:
                    self.y = float(tile.bottom)
                    self.vy = 0.0
                r = self.rect

        # One-way platforms (drop through when holding Down)
        drop_down = keys is not None and any(keys[k] for k in KEY_BINDINGS["down"])
        if self.vy >= 0 and not drop_down:
            for plat in room.one_way_rects:
                if r.colliderect(plat) and prev_bottom <= plat.top + 6:
                    self.y = float(plat.top - self.HEIGHT)
                    self.vy = 0.0
                    self.on_ground = True
                    r = self.rect

        # Refresh grounded abilities & record last safe ledge
        if self.on_ground:
            self.coyote_timer = COYOTE_TIME
            self.can_air_dash = True
            if self.abilities.get("monarch_wings"):
                self.can_double_jump = True
            if not any(r.colliderect(sp) for sp in room.spike_rects):
                self.last_safe_pos = (self.x, self.y)

        # Bouncing Fungal Pads
        for pad in room.bounce_pad_rects:
            if r.colliderect(pad):
                self.vy = -370.0
                self.on_ground = False
                self.can_air_dash = True
                if self.abilities.get("monarch_wings"):
                    self.can_double_jump = True
                self.audio.play_sfx("jump")
                self.particles.emit_burst(
                    pad.centerx, pad.top, PALETTE["spore_green"], count=12, speed=95
                )

        # Spikes / Acid Hazards (deal 1 damage and respawn at last safe ledge)
        for spike in room.spike_rects:
            if r.colliderect(spike):
                if self.take_damage(1, spike.centerx) and not self.dead:
                    self.x, self.y = self.last_safe_pos
                    self.vx, self.vy = 0.0, 0.0
                break

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        if self.invuln_timer > 0 and int(self.invuln_timer * 20) % 2 == 1:
            return

        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)

        # Subtle cloak wave
        bob = int(math.sin(self.anim_timer * 10.0) * 1.5) if self.state == "RUN" else 0
        cloak_col = (
            PALETTE["void_violet"]
            if (self.state == "DASH" and self.abilities.get("shadow_dash"))
            else (44, 52, 78)
        )

        # Flowing Cloak polygon
        flare = -self.facing * (5 if self.state in ("RUN", "DASH") else 2)
        cloak_pts = [
            (sx + 3, sy + 7),
            (sx + self.WIDTH - 3, sy + 7),
            (sx + self.WIDTH + flare, sy + self.HEIGHT - 2 + bob),
            (sx + flare, sy + self.HEIGHT - 2 - bob),
        ]
        pygame.draw.polygon(surface, cloak_col, cloak_pts)

        # Body core
        pygame.draw.rect(
            surface, PALETTE["obsidian"], (sx + 3, sy + 8, self.WIDTH - 6, 11)
        )

        # Horned Vessel Mask / Head
        head_rect = pygame.Rect(sx + 2, sy + 1 + bob, 8, 8)
        pygame.draw.rect(surface, PALETTE["bone"], head_rect, border_radius=2)
        # Horns
        pygame.draw.line(surface, PALETTE["bone"], (sx + 2, sy + 2), (sx, sy - 2), 2)
        pygame.draw.line(
            surface, PALETTE["bone"], (sx + 9, sy + 2), (sx + 11, sy - 2), 2
        )

        # Glowing Eye
        eye_x = sx + (7 if self.facing == 1 else 3)
        pygame.draw.rect(surface, PALETTE["amber"], (eye_x, sy + 4 + bob, 2, 2))

        # Cinderblade on back / hand
        blade_x = sx + (10 if self.facing == 1 else 1)
        pygame.draw.line(
            surface,
            PALETTE["amber"] if self.weapon_level > 1 else PALETTE["ash"],
            (blade_x, sy + 11),
            (blade_x - self.facing * 6, sy + 3),
            2,
        )