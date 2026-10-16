"""
Data-driven interconnected World & Room system.
Includes 10 distinct rooms across 5 atmospheric regions:
- Ashen Sanctuary: 'sanctuary_hub', 'sanctuary_west'
- Sunken Catacombs: 'ruins_nave', 'ruins_warden_arena'
- Weeping Mycelium: 'fungal_grotto', 'fungal_matriarch_arena'
- Astral Citadel: 'citadel_aqueduct', 'citadel_spire', 'citadel_vault'
- The Obsidian Pelorus: 'solar_reliquary'
"""

import math
import pygame
from game.settings import (
    INTERNAL_WIDTH,
    INTERNAL_HEIGHT,
    PALETTE,
    BIOME_PALETTES,
    RELIC_DATA,
)
from game.enemies import create_enemy
from game.bosses import create_boss
from game.dialogue import NPC


# World Map Layout Coordinates for the in-game Map UI
WORLD_MAP_NODES = {
    "sanctuary_west": {"grid": (0, 1), "biome": "sanctuary", "label": "West Overlook"},
    "sanctuary_hub": {"grid": (1, 1), "biome": "sanctuary", "label": "Ashen Sanctuary"},
    "ruins_nave": {"grid": (2, 1), "biome": "ruins", "label": "Sunken Nave"},
    "ruins_warden_arena": {"grid": (3, 1), "biome": "ruins", "label": "Warden's Hall"},
    "fungal_grotto": {"grid": (2, 2), "biome": "fungal", "label": "Weeping Mycelium"},
    "fungal_matriarch_arena": {"grid": (3, 2), "biome": "fungal", "label": "Matriarch's Choir"},
    "citadel_aqueduct": {"grid": (1, 0), "biome": "citadel", "label": "Astral Aqueduct"},
    "citadel_spire": {"grid": (2, 0), "biome": "citadel", "label": "Royal Spire"},
    "citadel_vault": {"grid": (0, 0), "biome": "citadel", "label": "Shadow Vault"},
    "solar_reliquary": {"grid": (3, 0), "biome": "core", "label": "Obsidian Pelorus"},
}


ROOM_TEMPLATES = {
    # 1. ASHEN SANCTUARY HUB (Starting Village, Bench, Elder Caelum, Smith Orin)
    "sanctuary_hub": {
        "name": "Ashen Sanctuary",
        "biome": "sanctuary",
        "width": 640,
        "height": 270,
        "solids": [
            (0, 224, 640, 46),      # Main Floor
            (0, 0, 640, 16),        # Ceiling
            (0, 16, 16, 140),       # Left upper wall (exit below)
            (624, 16, 16, 140),     # Right upper wall (exit below)
            (220, 172, 80, 12),     # Center Shrine Platform
            (370, 132, 96, 12),     # Upper Spire step
            (260, 84, 90, 12),      # High ledge toward Citadel
        ],
        "one_ways": [
            (120, 184, 64, 6),
            (480, 176, 64, 6),
        ],
        "spikes": [],
        "bounce_pads": [],
        "shadow_gates": [],
        "breakable_floors": [],
        "bench": (140, 208),
        "lore_tablets": [("lore_1", 252, 152)],
        "npcs": [
            ("caelum", "Elder Caelum", "Keeper of Ash", 200, 202, PALETTE["amber"]),
            ("orin", "Smith Orin", "Cindersmith", 430, 202, PALETTE["crimson"]),
        ],
        "enemies": [],
        "boss": None,
        "pickups": [],
        "doors": [
            {"rect": (0, 156, 14, 68), "target": "sanctuary_west", "spawn": (440, 196)},
            {"rect": (626, 156, 14, 68), "target": "ruins_nave", "spawn": (28, 196)},
            {"rect": (275, 16, 60, 18), "target": "citadel_aqueduct", "spawn": (220, 218)},
        ],
    },

    # 2. SANCTUARY WEST OVERLOOK (Teaches platforming + Phase Cloak Shrine + Shadow Gate secret)
    "sanctuary_west": {
        "name": "Western Overlook",
        "biome": "sanctuary",
        "width": 480,
        "height": 270,
        "solids": [
            (0, 224, 480, 46),
            (0, 0, 480, 16),
            (0, 16, 16, 208),
            (464, 16, 16, 140),
            (110, 176, 70, 12),
            (220, 140, 75, 12),
            (330, 108, 90, 12),
            (96, 96, 16, 128),      # Dividing chamber wall
        ],
        "one_ways": [(32, 168, 56, 6)],
        "spikes": [(185, 218, 70, 6)],
        "bounce_pads": [],
        "shadow_gates": [(96, 160, 16, 64)],
        "breakable_floors": [],
        "bench": None,
        "lore_tablets": [("lore_5", 390, 88)],
        "npcs": [],
        "enemies": [("husk", 250, 118), ("husk", 355, 200)],
        "boss": None,
        "pickups": [
            {"id": "ability_shadow_dash", "type": "ability", "value": "shadow_dash", "label": "PHASE CLOAK (Shadow Dash through dark barriers!)", "pos": (356, 92)},
            {"id": "relic_cinder_heart", "type": "relic", "value": "cinder_heart", "label": "RELIC: Cinder Heart (+25% Blade Damage)", "pos": (46, 204)},
        ],
        "doors": [
            {"rect": (466, 156, 14, 68), "target": "sanctuary_hub", "spawn": (28, 196)},
        ],
    },

    # 3. SUNKEN NAVE (Ruins Exploration, Brittle Floor down to Fungal Grotto, East to Warden Boss)
    "ruins_nave": {
        "name": "Sunken Nave",
        "biome": "ruins",
        "width": 720,
        "height": 270,
        "solids": [
            (0, 224, 290, 46),
            (354, 224, 366, 46),
            (0, 0, 720, 16),
            (0, 16, 16, 140),
            (704, 16, 16, 140),
            (150, 172, 95, 12),
            (310, 142, 110, 12),
            (480, 172, 95, 12),
        ],
        "one_ways": [(255, 190, 48, 6)],
        "spikes": [(190, 218, 65, 6), (440, 218, 65, 6)],
        "bounce_pads": [],
        "shadow_gates": [],
        "breakable_floors": [
            {"id": "nave_floor_1", "rect": (290, 224, 64, 18)}
        ],
        "bench": (580, 208),
        "lore_tablets": [("lore_2", 355, 122)],
        "npcs": [],
        "enemies": [
            ("husk", 130, 200),
            ("stalker", 345, 120),
            ("sentinel", 525, 194),
        ],
        "boss": None,
        "pickups": [
            {"id": "mask_nave_1", "type": "max_hp", "value": 1, "label": "ANCIENT MASK (+1 Max Health)", "pos": (520, 152)},
        ],
        "doors": [
            {"rect": (0, 156, 14, 68), "target": "sanctuary_hub", "spawn": (596, 196)},
            {"rect": (706, 156, 14, 68), "target": "ruins_warden_arena", "spawn": (32, 196)},
            {"rect": (290, 250, 64, 20), "target": "fungal_grotto", "spawn": (90, 36)},
        ],
    },

    # 4. WARDEN'S HALL (Boss 1 Arena: Malakor, The Ashen Warden)
    "ruins_warden_arena": {
        "name": "Hall of the Ashen Warden",
        "biome": "ruins",
        "width": 480,
        "height": 270,
        "solids": [
            (0, 224, 480, 46),
            (0, 0, 480, 16),
            (0, 16, 16, 140),
            (464, 16, 16, 208),
        ],
        "one_ways": [
            (85, 168, 68, 6),
            (327, 168, 68, 6),
        ],
        "spikes": [],
        "bounce_pads": [],
        "shadow_gates": [],
        "breakable_floors": [],
        "bench": None,
        "lore_tablets": [],
        "npcs": [],
        "enemies": [],
        "boss": ("boss_warden", 350, 184),
        "boss_reward": {
            "ability": "solar_lance",
            "ability_label": "SOLAR LANCE UNLOCKED (Press L / V to fire piercing Soul spears!) & नीचे Fissure to Weeping Mycelium opened!",
            "relic": "wardens_crest",
        },
        "pickups": [],
        "doors": [
            {"rect": (0, 156, 14, 68), "target": "ruins_nave", "spawn": (676, 196)},
        ],
    },

    # 5. WEEPING MYCELIUM GROTTO (Fungal Region, Bounce Mushrooms, Sister Veyla)
    "fungal_grotto": {
        "name": "Weeping Mycelium",
        "biome": "fungal",
        "width": 640,
        "height": 270,
        "solids": [
            (0, 224, 640, 46),
            (0, 0, 640, 16),
            (0, 16, 16, 208),
            (624, 16, 16, 140),
            (150, 164, 90, 12),
            (320, 134, 100, 12),
            (470, 168, 85, 12),
        ],
        "one_ways": [(52, 112, 70, 6)],
        "spikes": [(220, 218, 120, 6)],
        "bounce_pads": [
            (116, 216, 26, 8),
            (268, 216, 26, 8),
            (420, 216, 26, 8),
        ],
        "shadow_gates": [],
        "breakable_floors": [],
        "bench": (64, 208),
        "lore_tablets": [("lore_3", 360, 114)],
        "npcs": [
            ("veyla", "Sister Veyla", "Spore Choir", 180, 142, PALETTE["spore_green"]),
        ],
        "enemies": [
            ("weaver", 275, 95),
            ("stalker", 360, 110),
            ("weaver", 505, 105),
        ],
        "boss": None,
        "pickups": [
            {"id": "relic_swift_anklet", "type": "relic", "value": "swift_anklet", "label": "RELIC: Gale Anklet (+18% Move Speed & Faster Dash)", "pos": (505, 148)},
        ],
        "doors": [
            {"rect": (52, 16, 68, 18), "target": "ruins_nave", "spawn": (316, 196)},
            {"rect": (626, 156, 14, 68), "target": "fungal_matriarch_arena", "spawn": (32, 196)},
        ],
    },

    # 6. MATRIARCH'S CHOIR (Boss 2 Arena: Lyra, Mycelial Matriarch -> Unlocks Monarch Wings & Abyssal Dive)
    "fungal_matriarch_arena": {
        "name": "Sanctum of the Matriarch",
        "biome": "fungal",
        "width": 480,
        "height": 270,
        "solids": [
            (0, 224, 480, 46),
            (0, 0, 480, 16),
            (0, 16, 16, 140),
            (464, 16, 16, 208),
        ],
        "one_ways": [
            (95, 164, 76, 6),
            (309, 164, 76, 6),
        ],
        "spikes": [],
        "bounce_pads": [(228, 216, 24, 8)],
        "shadow_gates": [],
        "breakable_floors": [],
        "bench": None,
        "lore_tablets": [],
        "npcs": [],
        "enemies": [],
        "boss": ("boss_matriarch", 340, 130),
        "boss_reward": {
            "ability": "monarch_wings",
            "secondary_ability": "abyssal_dive",
            "ability_label": "MONARCH WINGS (Double Jump) & ABYSSAL DIVE (Down + Spell) UNLOCKED!",
            "relic": None,
        },
        "pickups": [],
        "doors": [
            {"rect": (0, 156, 14, 68), "target": "fungal_grotto", "spawn": (596, 196)},
        ],
    },

    # 7. ASTRAL AQUEDUCT (Upper Royal City, leads West to Vault and East to Royal Spire)
    "citadel_aqueduct": {
        "name": "Astral Aqueduct",
        "biome": "citadel",
        "width": 640,
        "height": 270,
        "solids": [
            (0, 236, 190, 34),
            (254, 236, 386, 34),
            (0, 0, 640, 16),
            (0, 16, 16, 150),
            (624, 16, 16, 150),
            (130, 180, 90, 12),
            (290, 144, 110, 12),
            (455, 180, 95, 12),
        ],
        "one_ways": [(195, 206, 56, 6)],
        "spikes": [(340, 230, 90, 6)],
        "bounce_pads": [],
        "shadow_gates": [(110, 16, 16, 164)],
        "breakable_floors": [],
        "bench": None,
        "lore_tablets": [("lore_4", 335, 124)],
        "npcs": [],
        "enemies": [
            ("sentinel", 160, 152),
            ("inquisitor", 345, 116),
            ("sentinel", 510, 206),
        ],
        "boss": None,
        "pickups": [],
        "doors": [
            {"rect": (190, 246, 64, 24), "target": "sanctuary_hub", "spawn": (295, 58)},
            {"rect": (0, 166, 14, 70), "target": "citadel_vault", "spawn": (436, 196)},
            {"rect": (626, 166, 14, 70), "target": "citadel_spire", "spawn": (28, 196)},
        ],
    },

    # 8. SHADOW VAULT (Optional Secret Room in Citadel behind Shadow Gate)
    "citadel_vault": {
        "name": "The Shadow Vault",
        "biome": "citadel",
        "width": 480,
        "height": 270,
        "solids": [
            (0, 224, 480, 46),
            (0, 0, 480, 16),
            (0, 16, 16, 208),
            (464, 16, 16, 140),
            (140, 168, 80, 12),
            (260, 128, 90, 12),
        ],
        "one_ways": [],
        "spikes": [(140, 218, 190, 6)],
        "bounce_pads": [],
        "shadow_gates": [],
        "breakable_floors": [],
        "bench": None,
        "lore_tablets": [],
        "npcs": [],
        "enemies": [("inquisitor", 295, 100)],
        "boss": None,
        "pickups": [
            {"id": "mask_vault_1", "type": "max_hp", "value": 1, "label": "SOVEREIGN MASK (+1 Max Health)", "pos": (80, 202)},
        ],
        "doors": [
            {"rect": (466, 156, 14, 68), "target": "citadel_aqueduct", "spawn": (28, 206)},
        ],
    },

    # 9. ROYAL SPIRE (Archivist Solen, Final Bench, Seal Gate to Obsidian Pelorus)
    "citadel_spire": {
        "name": "Royal Spire Antechamber",
        "biome": "citadel",
        "width": 540,
        "height": 270,
        "solids": [
            (0, 224, 540, 46),
            (0, 0, 540, 16),
            (0, 16, 16, 140),
            (524, 16, 16, 140),
            (210, 166, 120, 12),
        ],
        "one_ways": [],
        "spikes": [],
        "bounce_pads": [],
        "shadow_gates": [],
        "breakable_floors": [],
        "bench": (140, 208),
        "lore_tablets": [],
        "npcs": [
            ("solen", "Archivist Solen", "Royal Chronicler", 260, 144, PALETTE["soul_cyan"]),
        ],
        "enemies": [("inquisitor", 410, 196)],
        "boss": None,
        "pickups": [],
        "doors": [
            {"rect": (0, 156, 14, 68), "target": "citadel_aqueduct", "spawn": (596, 206)},
            {
                "rect": (526, 156, 14, 68),
                "target": "solar_reliquary",
                "spawn": (36, 196),
                "requires_bosses": ["boss_warden", "boss_matriarch"],
            },
        ],
    },

    # 10. THE OBSIDIAN PELORUS (Final Boss Arena: Aurelius, The Hollow Sun)
    "solar_reliquary": {
        "name": "The Obsidian Pelorus",
        "biome": "core",
        "width": 480,
        "height": 270,
        "solids": [
            (0, 224, 480, 46),
            (0, 0, 480, 16),
            (0, 16, 16, 140),
            (464, 16, 16, 208),
        ],
        "one_ways": [
            (95, 166, 70, 6),
            (315, 166, 70, 6),
        ],
        "spikes": [],
        "bounce_pads": [],
        "shadow_gates": [],
        "breakable_floors": [],
        "bench": None,
        "lore_tablets": [],
        "npcs": [],
        "enemies": [],
        "boss": ("boss_aurelius", 355, 186),
        "boss_reward": None,
        "pickups": [],
        "doors": [
            {"rect": (0, 156, 14, 68), "target": "citadel_spire", "spawn": (496, 196)},
        ],
    },
}


class Room:
    """Instantiated room containing geometry, entities, pickups, and interactive objects."""

    def __init__(self, room_id: str, template: dict, player):
        self.room_id = room_id
        self.name = template["name"]
        self.biome = template["biome"]
        self.width = template["width"]
        self.height = template["height"]

        self.solid_rects = [pygame.Rect(*r) for r in template["solids"]]
        self.one_way_rects = [pygame.Rect(*r) for r in template["one_ways"]]
        self.spike_rects = [pygame.Rect(*r) for r in template["spikes"]]
        self.bounce_pad_rects = [pygame.Rect(*r) for r in template["bounce_pads"]]
        self.shadow_gate_rects = [pygame.Rect(*r) for r in template["shadow_gates"]]
        self.breakable_floors = [
            {"id": bf["id"], "rect": pygame.Rect(*bf["rect"])}
            for bf in template["breakable_floors"]
        ]

        self.bench_pos = template["bench"]
        self.lore_tablets = [
            {"id": lid, "rect": pygame.Rect(lx, ly, 14, 20)}
            for (lid, lx, ly) in template["lore_tablets"]
        ]
        self.npcs = [
            NPC(nid, nname, nrole, nx, ny, ncol)
            for (nid, nname, nrole, nx, ny, ncol) in template["npcs"]
        ]
        self.enemies = [
            create_enemy(etype, ex, ey) for (etype, ex, ey) in template["enemies"]
        ]

        self.bosses = []
        self.boss_reward = template.get("boss_reward")
        if template["boss"]:
            bid, bx, by = template["boss"]
            if bid not in player.defeated_bosses:
                self.bosses.append(create_boss(bid, bx, by))
                # Seal left exit while boss is alive
                self.solid_rects.append(pygame.Rect(0, 140, 16, 90))

        self.pickups = [
            dict(p, rect=pygame.Rect(p["pos"][0], p["pos"][1], 14, 14))
            for p in template["pickups"]
            if p["id"] not in player.collected_items
        ]
        self.doors = [
            dict(d, rect=pygame.Rect(*d["rect"])) for d in template["doors"]
        ]

    def get_active_breakable_rects(self, player) -> list:
        # Note: Defeating the Ashen Warden also fractures the nave fissure so players can reach Fungal Grotto
        if "boss_warden" in player.defeated_bosses and "nave_floor_1" not in player.broken_floors:
            player.broken_floors.append("nave_floor_1")
        return [
            bf["rect"]
            for bf in self.breakable_floors
            if bf["id"] not in player.broken_floors
        ]

    def try_break_floors(self, impact_rect: pygame.Rect, player):
        for bf in self.breakable_floors:
            if bf["id"] not in player.broken_floors and impact_rect.colliderect(
                bf["rect"]
            ):
                player.broken_floors.append(bf["id"])


class WorldManager:
    """Manages active room, parallax background rendering, transitions, and world pickups."""

    def __init__(self, audio, particles, camera, combat_manager, dialogue_manager):
        self.audio = audio
        self.particles = particles
        self.camera = camera
        self.combat_manager = combat_manager
        self.dialogue = dialogue_manager

        self.current_room = None
        self.banner_timer = 0.0
        self.banner_text = ""
        self.victory_triggered = False

    def load_room(self, room_id: str, player, spawn_pos: tuple = None):
        template = ROOM_TEMPLATES.get(room_id, ROOM_TEMPLATES["sanctuary_hub"])
        self.current_room = Room(room_id, template, player)
        self.combat_manager.clear_room_transients()

        if room_id not in player.visited_rooms:
            player.visited_rooms.append(room_id)

        if spawn_pos:
            player.x, player.y = float(spawn_pos[0]), float(spawn_pos[1])
            player.last_safe_pos = (player.x, player.y)

        self.camera.snap_to(player.rect, self.current_room.width, self.current_room.height)
        self.banner_text = self.current_room.name.upper()
        self.banner_timer = 2.4

        # Select music
        if self.current_room.bosses:
            self.audio.play_music("boss")
        else:
            b_info = BIOME_PALETTES.get(
                self.current_room.biome, BIOME_PALETTES["sanctuary"]
            )
            self.audio.play_music(b_info["music"])

    def update(self, dt: float, player):
        room = self.current_room
        if not room:
            return

        if self.banner_timer > 0:
            self.banner_timer -= dt

        # Update Enemies
        for enemy in room.enemies:
            was_alive = not enemy.dead
            enemy.update(dt, player, room, self.combat_manager)
            if was_alive and enemy.dead:
                player.echoes += enemy.echo_reward
                self.audio.play_sfx("enemy_death")
                self.particles.emit_burst(
                    enemy.rect.centerx,
                    enemy.rect.centery,
                    enemy.color,
                    count=18,
                    speed=130,
                )
                self.particles.emit_floating_text(
                    enemy.rect.centerx,
                    enemy.rect.top,
                    f"+{enemy.echo_reward} ECHOES",
                    PALETTE["amber"],
                )

        # Update Bosses
        for boss in room.bosses:
            was_alive = not boss.dead
            boss.update(
                dt,
                player,
                room,
                self.combat_manager,
                self.audio,
                self.particles,
                self.camera,
            )
            if was_alive and boss.dead and not boss.reward_granted:
                boss.reward_granted = True
                player.echoes += boss.echo_reward
                if boss.boss_id not in player.defeated_bosses:
                    player.defeated_bosses.append(boss.boss_id)

                # Unseal arena door
                room.solid_rects = [
                    r for r in room.solid_rects if r != pygame.Rect(0, 140, 16, 90)
                ]
                self.audio.play_sfx("boss_roar")
                self.camera.add_trauma(0.95)
                self.particles.emit_burst(
                    boss.rect.centerx,
                    boss.rect.centery,
                    PALETTE["solar_gold"],
                    count=55,
                    speed=200,
                )

                b_info = BIOME_PALETTES.get(room.biome, BIOME_PALETTES["sanctuary"])
                self.audio.play_music(b_info["music"])

                # Grant Boss Reward or Trigger Final Ending
                if boss.boss_id == "boss_aurelius":
                    self.victory_triggered = True
                elif room.boss_reward:
                    ab = room.boss_reward.get("ability")
                    if ab:
                        player.abilities[ab] = True
                    ab2 = room.boss_reward.get("secondary_ability")
                    if ab2:
                        player.abilities[ab2] = True
                    rel = room.boss_reward.get("relic")
                    if rel and rel not in player.owned_relics:
                        player.owned_relics.append(rel)
                        player.equipped_relics.append(rel)
                    if boss.boss_id == "boss_warden" and "nave_floor_1" not in player.broken_floors:
                        player.broken_floors.append("nave_floor_1")
                    self.dialogue.start_dialogue(
                        f"{boss.name} VANQUISHED",
                        [room.boss_reward["ability_label"]],
                    )

        # Pickups Collection
        remaining_pickups = []
        for p in room.pickups:
            if player.rect.colliderect(p["rect"]):
                player.collected_items.append(p["id"])
                self.audio.play_sfx("pickup")
                if p["type"] == "ability":
                    player.abilities[p["value"]] = True
                elif p["type"] == "relic":
                    if p["value"] not in player.owned_relics:
                        player.owned_relics.append(p["value"])
                        player.equipped_relics.append(p["value"])
                elif p["type"] == "max_hp":
                    player.max_hp += p["value"]
                    player.hp = player.max_hp
                self.dialogue.start_dialogue("ARTIFACT DISCOVERED", [p["label"]])
            else:
                remaining_pickups.append(p)
        room.pickups = remaining_pickups

        # Room Transitions (only when no active boss locks the room)
        active_boss = any(not b.dead for b in room.bosses)
        if not active_boss:
            for d in room.doors:
                if player.rect.colliderect(d["rect"]):
                    req = d.get("requires_bosses", [])
                    if any(b_id not in player.defeated_bosses for b_id in req):
                        player.x = float(d["rect"].left - player.WIDTH - 4)
                        self.dialogue.start_dialogue(
                            "SEALED OBSIDIAN GATE",
                            [
                                "Two ancient seals bar the Pelorus: defeat both the Ashen Warden in the Catacombs and the Matriarch in the Mycelium."
                            ],
                        )
                    else:
                        self.load_room(d["target"], player, d["spawn"])
                    break

    def try_interact(self, player, save_callback) -> bool:
        """Handles pressing E / Interact near Benches, Lore Tablets, or NPCs."""
        room = self.current_room
        if not room:
            return False

        # 1. Check Bench (Rest & Save)
        if room.bench_pos:
            bx, by = room.bench_pos
            bench_rect = pygame.Rect(bx - 14, by - 16, 28, 22)
            if player.rect.colliderect(bench_rect.inflate(16, 16)):
                player.hp = player.max_hp
                player.lumen = player.max_lumen
                player.checkpoint_room = room.room_id
                player.checkpoint_pos = [bx, by - 10]
                save_callback()
                self.audio.play_sfx("checkpoint")
                self.particles.emit_burst(
                    bx, by - 4, PALETTE["amber"], count=22, speed=95
                )
                self.dialogue.start_dialogue(
                    "CINDER SHRINE",
                    ["Vessel restored and memories inscribed. Progress saved."],
                )
                return True

        # 2. Check Lore Tablets
        for lt in room.lore_tablets:
            if player.rect.colliderect(lt["rect"].inflate(16, 16)):
                self.dialogue.open_lore_tablet(lt["id"], player)
                return True

        # 3. Check NPCs
        for npc in room.npcs:
            if player.rect.colliderect(npc.rect.inflate(20, 16)):
                self.dialogue.interact_with_npc(npc, player)
                return True

        return False

    def draw_background(self, surface: pygame.Surface, cam_x: int, cam_y: int):
        room = self.current_room
        b_info = BIOME_PALETTES.get(room.biome, BIOME_PALETTES["sanctuary"])

        # Vertical gradient sky/cavern backdrop
        top_c = b_info["bg_top"]
        bot_c = b_info["bg_bottom"]
        band_h = 18
        for y in range(0, INTERNAL_HEIGHT, band_h):
            t = y / INTERNAL_HEIGHT
            col = (
                int(top_c[0] + (bot_c[0] - top_c[0]) * t),
                int(top_c[1] + (bot_c[1] - top_c[1]) * t),
                int(top_c[2] + (bot_c[2] - top_c[2]) * t),
            )
            pygame.draw.rect(surface, col, (0, y, INTERNAL_WIDTH, band_h))

        # Parallax gothic pillars & arches
        par_x1 = int(cam_x * 0.25)
        for i in range(-1, 8):
            px = i * 96 - (par_x1 % 96)
            pygame.draw.rect(
                surface,
                (max(0, bot_c[0] - 6), max(0, bot_c[1] - 6), max(0, bot_c[2] - 6)),
                (px, 24, 24, INTERNAL_HEIGHT - 24),
            )

    def draw_room(
        self, surface: pygame.Surface, cam_x: int, cam_y: int, player, anim_time: float
    ):
        room = self.current_room
        b_info = BIOME_PALETTES.get(room.biome, BIOME_PALETTES["sanctuary"])

        # Solid Tiles
        for r in room.solid_rects:
            dr = r.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, b_info["tile_main"], dr)
            pygame.draw.rect(surface, b_info["tile_trim"], dr, 1)

        # Breakable Floors
        for bf in room.breakable_floors:
            if bf["id"] not in player.broken_floors:
                dr = bf["rect"].move(-cam_x, -cam_y)
                pygame.draw.rect(surface, PALETTE["amber"], dr)
                pygame.draw.line(
                    surface, PALETTE["void"], (dr.left + 8, dr.top), (dr.centerx, dr.bottom), 2
                )

        # One-Way Platforms
        for r in room.one_way_rects:
            dr = r.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, b_info["tile_trim"], dr)

        # Shadow Gates
        for r in room.shadow_gate_rects:
            dr = r.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, PALETTE["void_violet"], dr, 1)
            for y_off in range(dr.top, dr.bottom, 6):
                pygame.draw.line(
                    surface,
                    PALETTE["void_violet"],
                    (dr.left + 3, y_off),
                    (dr.right - 3, y_off + 3),
                    1,
                )

        # Bounce Pads (Glowing Mushrooms)
        for r in room.bounce_pad_rects:
            dr = r.move(-cam_x, -cam_y)
            pygame.draw.ellipse(surface, PALETTE["spore_green"], dr.inflate(4, 4))

        # Spikes
        for r in room.spike_rects:
            dr = r.move(-cam_x, -cam_y)
            for sx in range(dr.left, dr.right, 6):
                pygame.draw.polygon(
                    surface,
                    PALETTE["crimson"],
                    [(sx, dr.bottom), (sx + 3, dr.top), (sx + 6, dr.bottom)],
                )

        # Bench / Cinder Shrine
        if room.bench_pos:
            bx = int(room.bench_pos[0] - cam_x)
            by = int(room.bench_pos[1] - cam_y)
            pygame.draw.rect(surface, PALETTE["stone"], (bx - 12, by + 6, 24, 10))
            flame_h = 8 + int(math.sin(anim_time * 8.0) * 2)
            pygame.draw.polygon(
                surface,
                PALETTE["amber"],
                [(bx - 4, by + 6), (bx, by + 6 - flame_h), (bx + 4, by + 6)],
            )

        # Lore Tablets
        for lt in room.lore_tablets:
            dr = lt["rect"].move(-cam_x, -cam_y)
            pygame.draw.rect(surface, PALETTE["slate"], dr, border_radius=3)
            pygame.draw.rect(surface, PALETTE["soul_cyan"], dr.inflate(-6, -6))

        # Pickups
        for p in room.pickups:
            dr = p["rect"].move(-cam_x, -cam_y)
            bob = int(math.sin(anim_time * 5.0) * 3)
            pygame.draw.circle(
                surface, PALETTE["solar_gold"], (dr.centerx, dr.centery + bob), 6
            )
            pygame.draw.circle(
                surface, PALETTE["white"], (dr.centerx, dr.centery + bob), 3
            )

        # NPCs
        for npc in room.npcs:
            near = player.rect.colliderect(npc.rect.inflate(20, 16))
            npc.draw(surface, cam_x, cam_y, near)

        # Enemies & Bosses
        for enemy in room.enemies:
            enemy.draw(surface, cam_x, cam_y)
        for boss in room.bosses:
            boss.draw(surface, cam_x, cam_y)