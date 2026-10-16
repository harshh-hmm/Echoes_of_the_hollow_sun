"""
Smooth Camera system for Echoes of the Hollow Sun.
Features:
- Smoothed horizontal look-ahead (prevents camera jerking when rapidly turning).
- Vertical peeking when holding Up/Down while grounded to check spikes or high ledges.
- Deadzone damping and frame-independent exponential smoothing.
- Room-boundary clamping so the viewport never shows outside the current room.
- Quadratic trauma-based screen shake for melee impacts, dives, and boss roars.
"""

import math
import random
import pygame
from game.settings import INTERNAL_WIDTH, INTERNAL_HEIGHT, KEY_BINDINGS


class Camera:
    """Tracks the player smoothly within room bounds and applies impact screen shake."""

    def __init__(self):
        self.x = 0.0
        self.y = 0.0

        # Smoothed look-ahead & vertical peek state
        self.current_look_ahead = 0.0
        self.peek_timer = 0.0
        self.current_peek_y = 0.0

        # Screen-shake trauma (0.0 to 1.0)
        self.trauma = 0.0
        self.shake_time = 0.0
        self.shake_offset_x = 0
        self.shake_offset_y = 0

        # Optional arena focal point lock
        self.locked_target = None  # Tuple (x, y) or None

    def snap_to(self, target_rect: pygame.Rect, room_width: int, room_height: int):
        """Instantly centers the camera on the target (used on room transitions)."""
        self.x = float(target_rect.centerx - INTERNAL_WIDTH // 2)
        self.y = float(target_rect.centery - INTERNAL_HEIGHT // 2)
        self.current_look_ahead = 0.0
        self.current_peek_y = 0.0
        self.peek_timer = 0.0
        self._clamp(room_width, room_height)

    def lock_to(self, center_x: float, center_y: float):
        """Locks the camera onto a fixed arena point (e.g., boss intro or cutscene)."""
        self.locked_target = (float(center_x), float(center_y))

    def unlock(self):
        """Releases any fixed arena camera lock back to the player."""
        self.locked_target = None

    def add_trauma(self, amount: float):
        """Adds screen-shake trauma (clamped between 0.0 and 1.0)."""
        self.trauma = max(0.0, min(1.0, self.trauma + amount))

    def _clamp(self, room_width: int, room_height: int):
        """Prevents the camera from scrolling past the edges of the active room."""
        max_x = max(0, room_width - INTERNAL_WIDTH)
        max_y = max(0, room_height - INTERNAL_HEIGHT)
        self.x = max(0.0, min(float(max_x), self.x))
        self.y = max(0.0, min(float(max_y), self.y))

    def _update_vertical_peek(self, dt: float):
        """Allows the player to hold Up or Down to pan the camera vertically."""
        if not pygame.get_init():
            return

        keys = pygame.key.get_pressed()
        up_held = any(keys[k] for k in KEY_BINDINGS["up"])
        down_held = any(keys[k] for k in KEY_BINDINGS["down"])
        moving_horiz = any(keys[k] for k in KEY_BINDINGS["left"]) or any(
            keys[k] for k in KEY_BINDINGS["right"]
        )

        # Only trigger vertical peek when standing still and holding Up or Down
        if not moving_horiz and (up_held ^ down_held):
            self.peek_timer += dt
            if self.peek_timer >= 0.35:
                target_peek = -42.0 if up_held else 46.0
                self.current_peek_y += (target_peek - self.current_peek_y) * min(
                    1.0, 6.0 * dt
                )
        else:
            self.peek_timer = 0.0
            self.current_peek_y += (0.0 - self.current_peek_y) * min(1.0, 10.0 * dt)

    def update(
        self,
        dt: float,
        target_rect: pygame.Rect,
        facing: int,
        room_width: int,
        room_height: int,
    ):
        """Updates smooth follow position, room clamping, and trauma shake decay."""
        self.shake_time += dt

        if self.locked_target is not None:
            focus_x, focus_y = self.locked_target
            target_x = focus_x - INTERNAL_WIDTH // 2
            target_y = focus_y - INTERNAL_HEIGHT // 2
        else:
            # Smoothly interpolate horizontal look-ahead so turning doesn't snap
            desired_look_ahead = facing * 26.0
            self.current_look_ahead += (
                desired_look_ahead - self.current_look_ahead
            ) * min(1.0, 5.0 * dt)

            self._update_vertical_peek(dt)

            target_x = (
                target_rect.centerx + self.current_look_ahead - INTERNAL_WIDTH // 2
            )
            target_y = (
                target_rect.centery
                - 12.0
                + self.current_peek_y
                - INTERNAL_HEIGHT // 2
            )

        # Frame-independent smooth follow
        lerp_x = min(1.0, 7.5 * dt)
        lerp_y = min(1.0, 8.5 * dt)
        self.x += (target_x - self.x) * lerp_x
        self.y += (target_y - self.y) * lerp_y

        self._clamp(room_width, room_height)

        # Quadratic trauma decay for punchy, non-linear screen shake
        if self.trauma > 0.0:
            self.trauma = max(0.0, self.trauma - 2.4 * dt)
            shake_mag = (self.trauma ** 2) * 9.0
            angle = self.shake_time * 45.0 + random.uniform(-0.8, 0.8)
            self.shake_offset_x = int(math.cos(angle) * shake_mag)
            self.shake_offset_y = int(math.sin(angle * 1.3) * shake_mag)
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0

    def get_offset(self) -> tuple:
        """Returns the integer (cam_x, cam_y) offset used by all draw calls."""
        return int(round(self.x)) + self.shake_offset_x, int(round(self.y)) + self.shake_offset_y