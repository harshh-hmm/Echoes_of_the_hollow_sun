"""
Automated headless unit tests for critical non-graphical systems:
- Save/Load validation and corruption recovery
- Combat single-hit-per-swing invariant & pogo bounce physics
- Enemy directional shield blocking (Obsidian Sentinel)
- World room graph & door target integrity
- Procedural WAV audio synthesis buffer generation
"""

import os
import tempfile
import unittest
import numpy as np
import pygame

from game.save_system import SaveSystem
from game.audio import AudioManager
from game.particles import ParticleManager
from game.camera import Camera
from game.combat import CombatManager
from game.player import Player
from game.enemies import AshHusk, ObsidianSentinel
from game.dialogue import DialogueManager
from game.world import ROOM_TEMPLATES, WorldManager


class TestGameSystems(unittest.TestCase):
    def setUp(self):
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        pygame.init()
        self.audio = AudioManager()
        self.particles = ParticleManager()
        self.camera = Camera()
        self.combat = CombatManager(self.audio, self.particles, self.camera)
        self.dialogue = DialogueManager(self.audio)
        self.world = WorldManager(
            self.audio, self.particles, self.camera, self.combat, self.dialogue
        )
        self.player = Player(140, 192, self.audio, self.particles)

    def test_save_and_load_validation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "test_save.json")
            data = SaveSystem.get_default_data()
            data["echoes"] = 320
            data["max_hp"] = 7
            data["abilities"]["shadow_dash"] = True
            self.assertTrue(SaveSystem.save_game(data, save_path))

            loaded = SaveSystem.load_game(save_path)
            self.assertEqual(loaded["echoes"], 320)
            self.assertEqual(loaded["max_hp"], 7)
            self.assertTrue(loaded["abilities"]["shadow_dash"])

            # Test corrupted file recovery
            with open(save_path, "w", encoding="utf-8") as f:
                f.write("{corrupted_json")
            fallback = SaveSystem.load_game(save_path)
            self.assertEqual(fallback["max_hp"], 5)

    def test_single_hit_per_swing_and_pogo(self):
        self.world.load_room("sanctuary_hub", self.player)
        room = self.world.current_room
        husk = AshHusk(160, 192)
        initial_hp = husk.hp
        room.enemies.append(husk)

        # Spawn a downward slash overlapping the enemy
        hb_rect = pygame.Rect(150, 185, 30, 30)
        self.combat.spawn_player_slash(self.player, "down", hb_rect, damage=10)

        # Frame 1: Deals damage once and triggers pogo bounce
        self.combat.update(0.016, self.player, room.enemies, room.bosses, room)
        self.assertEqual(husk.hp, initial_hp - 10)
        self.assertLess(self.player.vy, -200.0)

        # Frame 2 (same swing still active): Must NOT deal damage a second time
        self.combat.update(0.016, self.player, room.enemies, room.bosses, room)
        self.assertEqual(husk.hp, initial_hp - 10)

    def test_sentinel_directional_shield(self):
        sentinel = ObsidianSentinel(200, 190)
        sentinel.facing = -1  # Facing left toward x=150
        # Frontal attack from x=150 is blocked
        self.assertTrue(sentinel.check_blocked("right", attacker_x=150))
        # Downward pogo attack is never blocked
        self.assertFalse(sentinel.check_blocked("down", attacker_x=150))
        # Back attack from x=240 is not blocked
        self.assertFalse(sentinel.check_blocked("left", attacker_x=240))

    def test_world_room_connectivity(self):
        for room_id, template in ROOM_TEMPLATES.items():
            self.world.load_room(room_id, self.player)
            for door in template["doors"]:
                self.assertIn(
                    door["target"],
                    ROOM_TEMPLATES,
                    f"Room {room_id} has door pointing to missing room {door['target']}",
                )

    def test_procedural_wav_synthesis(self):
        samples = np.sin(np.linspace(0, 2 * np.pi, 1000, dtype=np.float32))
        wav_bytes = AudioManager.make_wav_bytes(samples)
        self.assertTrue(wav_bytes.startswith(b"RIFF"))
        self.assertGreater(len(wav_bytes), 2000)


if __name__ == "__main__":
    unittest.main()