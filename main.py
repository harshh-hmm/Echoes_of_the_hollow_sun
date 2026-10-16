"""
Main entry point for ECHOES OF THE HOLLOW SUN.
Run via VS Code terminal:
    python main.py
"""

import sys
import pygame
from game.settings import (
    GAME_TITLE,
    INTERNAL_WIDTH,
    INTERNAL_HEIGHT,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    FPS,
    KEY_BINDINGS,
)
from game.save_system import SaveSystem
from game.audio import AudioManager
from game.particles import ParticleManager
from game.camera import Camera
from game.combat import CombatManager
from game.player import Player
from game.dialogue import DialogueManager
from game.world import WorldManager
from game.ui import UIManager


class Game:
    """Top-level game controller managing window, states, and main loop."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        self.fullscreen = False
        self.window = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE
        )
        self.canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.anim_time = 0.0

        # Initialize Core Subsystems
        self.audio = AudioManager()
        self.particles = ParticleManager()
        self.camera = Camera()
        self.combat = CombatManager(self.audio, self.particles, self.camera)
        self.dialogue = DialogueManager(self.audio)
        self.world = WorldManager(
            self.audio, self.particles, self.camera, self.combat, self.dialogue
        )
        self.ui = UIManager()
        self.player = Player(140, 192, self.audio, self.particles)

        # States: TITLE, INTRO, PLAY, INVENTORY, PAUSE, GAME_OVER, VICTORY
        self.state = "TITLE"
        self.title_index = 0
        self.pause_index = 0
        self.audio.play_music("title")

    def start_game(self, load_existing: bool):
        if load_existing and SaveSystem.save_exists():
            save_data = SaveSystem.load_game()
            self.player.load_from_save_dict(save_data)
            self.world.load_room(
                self.player.checkpoint_room,
                self.player,
                tuple(self.player.checkpoint_pos),
            )
            self.state = "PLAY"
        else:
            fresh = SaveSystem.get_default_data()
            self.player.load_from_save_dict(fresh)
            SaveSystem.save_game(fresh)
            self.world.load_room(
                self.player.checkpoint_room,
                self.player,
                tuple(self.player.checkpoint_pos),
            )
            self.state = "INTRO"

    def save_progress(self):
        SaveSystem.save_game(self.player.to_save_dict())

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(
                (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE
            )

    def handle_events(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                    continue

                if self.state == "TITLE":
                    self._handle_title_key(event.key)
                elif self.state == "INTRO":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_j, pygame.K_z):
                        self.state = "PLAY"
                elif self.state == "PLAY":
                    self._handle_play_keydown(event.key, keys)
                elif self.state == "INVENTORY":
                    self._handle_inventory_key(event.key)
                elif self.state == "PAUSE":
                    self._handle_pause_key(event.key)
                elif self.state == "GAME_OVER":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_j):
                        self.start_game(load_existing=True)
                elif self.state == "VICTORY":
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                        self.world.victory_triggered = False
                        self.state = "TITLE"
                        self.audio.play_music("title")

            elif event.type == pygame.KEYUP and self.state == "PLAY":
                if event.key in KEY_BINDINGS["jump"]:
                    self.player.release_jump_input()

    def _handle_title_key(self, key: int):
        if key in (pygame.K_w, pygame.K_UP):
            self.title_index = (self.title_index - 1) % 3
            self.audio.play_sfx("npc_talk")
        elif key in (pygame.K_s, pygame.K_DOWN):
            self.title_index = (self.title_index + 1) % 3
            self.audio.play_sfx("npc_talk")
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_j, pygame.K_z):
            if self.title_index == 0:
                self.start_game(load_existing=SaveSystem.save_exists())
            elif self.title_index == 1:
                self.start_game(load_existing=False)
            else:
                self.running = False

    def _handle_play_keydown(self, key: int, keys):
        if self.dialogue.active:
            self.dialogue.handle_key(key)
            return

        if key in KEY_BINDINGS["pause"]:
            self.state = "PAUSE"
            self.pause_index = 0
            return
        if key in KEY_BINDINGS["inventory"]:
            self.state = "INVENTORY"
            return
        if key in KEY_BINDINGS["jump"]:
            self.player.trigger_jump_input()
        elif key in KEY_BINDINGS["dash"]:
            self.player.trigger_dash_input()
        elif key in KEY_BINDINGS["attack"]:
            self.player.trigger_attack_input(keys, self.combat)
        elif key in KEY_BINDINGS["spell"]:
            self.player.trigger_spell_input(keys, self.combat)
        elif key in KEY_BINDINGS["interact"]:
            self.world.try_interact(self.player, self.save_progress)

    def _handle_inventory_key(self, key: int):
        if key in KEY_BINDINGS["inventory"] or key in KEY_BINDINGS["pause"]:
            self.state = "PLAY"
        elif key in (pygame.K_a, pygame.K_LEFT):
            self.ui.inventory_tab = (self.ui.inventory_tab - 1) % 3
            self.audio.play_sfx("npc_talk")
        elif key in (pygame.K_d, pygame.K_RIGHT):
            self.ui.inventory_tab = (self.ui.inventory_tab + 1) % 3
            self.audio.play_sfx("npc_talk")
        elif self.ui.inventory_tab == 1:
            if key in (pygame.K_w, pygame.K_UP):
                self.ui.selected_relic_idx = (self.ui.selected_relic_idx - 1) % 4
            elif key in (pygame.K_s, pygame.K_DOWN):
                self.ui.selected_relic_idx = (self.ui.selected_relic_idx + 1) % 4
            elif key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_j):
                from game.settings import RELIC_DATA
                r_key = list(RELIC_DATA.keys())[self.ui.selected_relic_idx]
                if r_key in self.player.owned_relics:
                    if r_key in self.player.equipped_relics:
                        self.player.equipped_relics.remove(r_key)
                    else:
                        self.player.equipped_relics.append(r_key)
                    self.audio.play_sfx("pickup")

    def _handle_pause_key(self, key: int):
        if key in KEY_BINDINGS["pause"]:
            self.state = "PLAY"
        elif key in (pygame.K_w, pygame.K_UP):
            self.pause_index = (self.pause_index - 1) % 5
            self.audio.play_sfx("npc_talk")
        elif key in (pygame.K_s, pygame.K_DOWN):
            self.pause_index = (self.pause_index + 1) % 5
            self.audio.play_sfx("npc_talk")
        elif key in (pygame.K_a, pygame.K_LEFT):
            if self.pause_index == 1:
                self.audio.set_music_volume(self.audio.music_volume - 0.1)
            elif self.pause_index == 2:
                self.audio.set_sfx_volume(self.audio.sfx_volume - 0.1)
        elif key in (pygame.K_d, pygame.K_RIGHT):
            if self.pause_index == 1:
                self.audio.set_music_volume(self.audio.music_volume + 0.1)
            elif self.pause_index == 2:
                self.audio.set_sfx_volume(self.audio.sfx_volume + 0.1)
        elif key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_j):
            if self.pause_index == 0:
                self.state = "PLAY"
            elif self.pause_index == 3:
                self.audio.toggle_mute()
            elif self.pause_index == 4:
                self.save_progress()
                self.state = "TITLE"
                self.audio.play_music("title")

    def update(self, dt: float):
        self.anim_time += dt
        if self.state != "PLAY":
            return

        if self.dialogue.active:
            self.dialogue.update(dt)
            return

        if self.combat.hit_stop_timer > 0:
            self.combat.hit_stop_timer -= dt
            return

        keys = pygame.key.get_pressed()
        room = self.world.current_room

        self.player.update(dt, keys, room, self.camera)
        self.world.update(dt, self.player)
        self.combat.update(
            dt, self.player, room.enemies, room.bosses, room
        )
        self.camera.update(
            dt, self.player.rect, self.player.facing, room.width, room.height
        )
        cam_x, cam_y = self.camera.get_offset()
        self.particles.update(dt, cam_x, cam_y, room.biome)

        if self.player.dead:
            self.state = "GAME_OVER"
        elif self.world.victory_triggered:
            self.save_progress()
            self.audio.play_music("victory")
            self.state = "VICTORY"

    def render(self):
        if self.state == "TITLE":
            self.ui.draw_title_screen(
                self.canvas, self.title_index, SaveSystem.save_exists()
            )
        elif self.state == "INTRO":
            self.ui.draw_intro_screen(self.canvas)
        elif self.state in ("PLAY", "INVENTORY", "PAUSE"):
            cam_x, cam_y = self.camera.get_offset()
            self.world.draw_background(self.canvas, cam_x, cam_y)
            self.world.draw_room(
                self.canvas, cam_x, cam_y, self.player, self.anim_time
            )
            self.combat.draw(self.canvas, cam_x, cam_y)
            self.player.draw(self.canvas, cam_x, cam_y)
            self.particles.draw(self.canvas, cam_x, cam_y)
            self.ui.draw_hud(self.canvas, self.player, self.world)
            self.dialogue.draw(self.canvas)

            if self.state == "INVENTORY":
                self.ui.draw_inventory_screen(
                    self.canvas, self.player, self.world.current_room.room_id
                )
            elif self.state == "PAUSE":
                self.ui.draw_pause_menu(self.canvas, self.pause_index, self.audio)
        elif self.state == "GAME_OVER":
            self.ui.draw_game_over(self.canvas)
        elif self.state == "VICTORY":
            self.ui.draw_victory_screen(self.canvas, self.player)

        win_size = self.window.get_size()
        pygame.transform.scale(self.canvas, win_size, self.window)
        pygame.display.flip()

    def run(self):
        while self.running:
            dt = min(0.033, self.clock.tick(FPS) / 1000.0)
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    game = Game()
    game.run()