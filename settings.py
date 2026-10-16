"""
Global configuration, constants, palettes, lore entries, relics, and quest data.
"""

import os
import pygame

# Base Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_DIR = os.path.join(BASE_DIR, "saves")
SAVE_FILE_PATH = os.path.join(SAVE_DIR, "save_slot_1.json")

# Display & Timing
GAME_TITLE = "ECHOES OF THE HOLLOW SUN"
INTERNAL_WIDTH = 480
INTERNAL_HEIGHT = 270
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
TILE_SIZE = 16

# Physics & Movement Constants
GRAVITY = 960.0
MAX_FALL_SPEED = 400.0
PLAYER_SPEED = 135.0
PLAYER_ACCEL = 1500.0
PLAYER_FRICTION = 1300.0
PLAYER_AIR_ACCEL = 1100.0

JUMP_VELOCITY = -290.0
JUMP_CUT_MULTIPLIER = 0.45
DOUBLE_JUMP_VELOCITY = -265.0
COYOTE_TIME = 0.11
JUMP_BUFFER_TIME = 0.12

WALL_SLIDE_SPEED = 65.0
WALL_JUMP_VX = 190.0
WALL_JUMP_VY = -275.0

DASH_SPEED = 330.0
DASH_DURATION = 0.16
DASH_COOLDOWN = 0.55

# Combat Constants
ATTACK_DURATION = 0.16
ATTACK_COOLDOWN = 0.26
POGO_VELOCITY = -255.0
INVULN_DURATION = 0.95
HURT_STUN_DURATION = 0.22
HIT_STOP_DURATION = 0.045

MAX_LUMEN = 100
LUMEN_PER_HIT = 12
HEAL_LUMEN_COST = 33
HEAL_CHANNEL_TIME = 0.80
HEAL_AMOUNT = 1

SPELL_LUMEN_COST = 25
SOLAR_LANCE_SPEED = 360.0
ABYSSAL_DIVE_SPEED = 420.0

# Core Dark-Fantasy Color Palette
PALETTE = {
    "void": (10, 11, 16),
    "obsidian": (18, 20, 30),
    "slate": (36, 40, 58),
    "stone": (64, 70, 92),
    "ash": (140, 148, 168),
    "bone": (225, 228, 236),
    "white": (250, 250, 255),
    "amber": (245, 175, 65),
    "solar_gold": (255, 215, 95),
    "crimson": (210, 55, 75),
    "blood": (135, 25, 42),
    "soul_cyan": (95, 220, 245),
    "void_violet": (155, 90, 235),
    "spore_green": (90, 225, 145),
    "mycelium_teal": (45, 155, 140),
    "shadow": (6, 7, 10),
}

# Biome Visual Profiles
BIOME_PALETTES = {
    "sanctuary": {
        "name": "Ashen Sanctuary",
        "bg_top": (14, 16, 26),
        "bg_bottom": (28, 32, 48),
        "tile_main": (52, 58, 78),
        "tile_trim": (86, 96, 122),
        "ambient_particle": (185, 195, 215),
        "music": "sanctuary",
    },
    "ruins": {
        "name": "Sunken Catacombs",
        "bg_top": (18, 14, 24),
        "bg_bottom": (38, 26, 44),
        "tile_main": (64, 48, 70),
        "tile_trim": (110, 82, 115),
        "ambient_particle": (235, 160, 85),
        "music": "ruins",
    },
    "fungal": {
        "name": "Weeping Mycelium",
        "bg_top": (10, 22, 24),
        "bg_bottom": (20, 48, 46),
        "tile_main": (34, 72, 68),
        "tile_trim": (75, 175, 140),
        "ambient_particle": (110, 240, 175),
        "music": "fungal",
    },
    "citadel": {
        "name": "Astral Citadel",
        "bg_top": (14, 18, 36),
        "bg_bottom": (32, 42, 78),
        "tile_main": (58, 70, 110),
        "tile_trim": (135, 160, 220),
        "ambient_particle": (130, 210, 255),
        "music": "citadel",
    },
    "core": {
        "name": "The Obsidian Pelorus",
        "bg_top": (26, 12, 16),
        "bg_bottom": (58, 22, 24),
        "tile_main": (72, 32, 36),
        "tile_trim": (225, 135, 65),
        "ambient_particle": (255, 185, 80),
        "music": "citadel",
    },
}

# Controls Configuration
KEY_BINDINGS = {
    "left": [pygame.K_a, pygame.K_LEFT],
    "right": [pygame.K_d, pygame.K_RIGHT],
    "up": [pygame.K_w, pygame.K_UP],
    "down": [pygame.K_s, pygame.K_DOWN],
    "jump": [pygame.K_SPACE, pygame.K_z],
    "attack": [pygame.K_j, pygame.K_x],
    "dash": [pygame.K_k, pygame.K_c],
    "spell": [pygame.K_l, pygame.K_v],
    "heal": [pygame.K_h, pygame.K_f],
    "interact": [pygame.K_e, pygame.K_UP],
    "inventory": [pygame.K_TAB, pygame.K_i],
    "pause": [pygame.K_ESCAPE, pygame.K_p],
}

# Lore Entries Database
LORE_ENTRIES = {
    "lore_1": {
        "title": "I. Edict of the Golden Cage",
        "text": (
            "By decree of King Aurelius: The sun does not abandon us; we "
            "shall bind its dying ember within the Obsidian Pelorus. Let no "
            "citizen look skyward again."
        ),
    },
    "lore_2": {
        "title": "II. Warden Malakor's Oath",
        "text": (
            "I sealed the Sunken Catacombs when the first echoes began to walk. "
            "Our memories detached from our minds, wearing armor of ash. Even "
            "my own oath grows heavy to recall."
        ),
    },
    "lore_3": {
        "title": "III. Scholar Lyra's Botanical Note",
        "text": (
            "The mycelium feeds upon leaked solar resonance. It remembers the "
            "warmth of the surface better than we do. Soon I shall root myself "
            "into the choir and never freeze again."
        ),
    },
    "lore_4": {
        "title": "IV. The Conflicting Testimony",
        "text": (
            "Elder Caelum claims the King sacrificed himself to save us. Yet "
            "the Citadel archives show the Royal Court drained the populace's "
            "Lumen to fuel a throne that only sheltered one soul."
        ),
    },
    "lore_5": {
        "title": "V. Rite of the Vessel-Scribes",
        "text": (
            "Created from hollow ash and tempered cinder, the Scribes were "
            "forged for a single duty: should the Pelorus stagnate, harvest "
            "the seals and shatter the false sun."
        ),
    },
}

# Unlockable Relics (Charms / Passive Upgrades)
RELIC_DATA = {
    "cinder_heart": {
        "name": "Cinder Heart",
        "desc": "Increases melee Cinderblade damage by +25%.",
        "cost": 1,
    },
    "soul_catcher": {
        "name": "Lumen Catcher",
        "desc": "Gain +6 extra Lumen with every melee strike.",
        "cost": 1,
    },
    "swift_anklet": {
        "name": "Gale Anklet",
        "desc": "Increases movement speed by 18% and reduces Dash cooldown.",
        "cost": 1,
    },
    "wardens_crest": {
        "name": "Warden's Crest",
        "desc": "Extends invulnerability frames after taking damage.",
        "cost": 1,
    },
}

# Quests Database
QUEST_DATA = {
    "quest_bell": {
        "title": "Silence in the Catacombs",
        "giver": "Elder Caelum",
        "desc": "Defeat Malakor, the Ashen Warden in the Sunken Catacombs to quiet the grieving bells.",
        "reward_echoes": 150,
    },
    "quest_spores": {
        "title": "Mercy for the Matriarch",
        "giver": "Sister Veyla",
        "desc": "Free Scholar Lyra from her fungal madness deep within the Weeping Mycelium.",
        "reward_echoes": 200,
    },
    "quest_truth": {
        "title": "The Shattered Archive",
        "giver": "Archivist Solen",
        "desc": "Discover at least 3 Lore Tablets across Heliosthome and report back to Solen.",
        "reward_echoes": 250,
    },
}