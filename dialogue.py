"""
NPC entities, progressive dialogue state trees, quest rewards, and Smith Orin's forge shop.
"""

import pygame
from game.settings import (
    INTERNAL_WIDTH,
    INTERNAL_HEIGHT,
    PALETTE,
    LORE_ENTRIES,
    QUEST_DATA,
)


class NPC:
    """Interactive NPC with progressive story dialogue and optional quest/shop hooks."""

    def __init__(self, npc_id: str, name: str, role: str, x: float, y: float, color: tuple):
        self.npc_id = npc_id
        self.name = name
        self.role = role
        self.x = float(x)
        self.y = float(y)
        self.width = 14
        self.height = 22
        self.color = color

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def draw(self, surface: pygame.Surface, cam_x: int, cam_y: int, player_near: bool):
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        pygame.draw.rect(surface, self.color, (sx, sy + 6, self.width, 16), border_radius=2)
        pygame.draw.circle(surface, PALETTE["bone"], (sx + self.width // 2, sy + 4), 4)
        if player_near:
            pygame.draw.polygon(
                surface,
                PALETTE["solar_gold"],
                [(sx + 4, sy - 8), (sx + 10, sy - 8), (sx + 7, sy - 3)],
            )


class DialogueManager:
    """Manages active dialogue boxes, typewriter text reveal, quests, and forge upgrades."""

    def __init__(self, audio):
        self.audio = audio
        self.active = False
        self.speaker = ""
        self.pages = []
        self.page_index = 0
        self.char_index = 0.0
        self.choices = []  # List of (label, callback)
        self.selected_choice = 0
        self._font_title = None
        self._font_body = None

    def _ensure_fonts(self):
        if self._font_title is None:
            pygame.font.init()
            self._font_title = pygame.font.SysFont("consolas", 13, bold=True)
            self._font_body = pygame.font.SysFont("consolas", 11)

    def start_dialogue(self, speaker: str, pages: list, choices: list = None):
        self.active = True
        self.speaker = speaker
        self.pages = pages if pages else ["..."]
        self.page_index = 0
        self.char_index = 0.0
        self.choices = choices if choices else []
        self.selected_choice = 0
        self.audio.play_sfx("npc_talk")

    def open_lore_tablet(self, lore_id: str, player):
        entry = LORE_ENTRIES.get(lore_id)
        if not entry:
            return
        if lore_id not in player.lore_unlocked:
            player.lore_unlocked.append(lore_id)
            self.audio.play_sfx("secret")
        self.start_dialogue(entry["title"], [entry["text"]])

    def interact_with_npc(self, npc: NPC, player):
        """Constructs context-sensitive dialogue & quest progression for each of the 4 NPCs."""
        nid = npc.npc_id

        # 1. Elder Caelum (Sanctuary)
        if nid == "caelum":
            player.story_flags["met_caelum"] = True
            if "boss_warden" not in player.defeated_bosses:
                if "quest_bell" not in player.quests:
                    player.quests["quest_bell"] = "active"
                self.start_dialogue(
                    "ELDER CAELUM, KEEPER OF ASH",
                    [
                        "Ah, a Vessel-Scribe awakens at last. The Hollow Sun above us flickers on its final ember.",
                        "King Aurelius sacrificed everything to cage the star and shield us from the Eternal Frost.",
                        "Descend into the Sunken Catacombs to the east. Defeat Malakor, the Ashen Warden, and claim his Seal.",
                    ],
                )
            elif player.quests.get("quest_bell") == "active":
                player.quests["quest_bell"] = "completed"
                player.echoes += QUEST_DATA["quest_bell"]["reward_echoes"]
                self.audio.play_sfx("pickup")
                self.start_dialogue(
                    "ELDER CAELUM, KEEPER OF ASH",
                    [
                        "The grieving bells in the Catacombs have fallen silent... You have granted Malakor peace.",
                        "Take these 150 Echoes I preserved from the old age. Yet beware the Weeping Mycelium below—and the Citadel above.",
                    ],
                )
            else:
                self.start_dialogue(
                    "ELDER CAELUM, KEEPER OF ASH",
                    [
                        "Once both Seals—Warden and Matriarch—are yours, the Obsidian Pelorus east of the Citadel shall open.",
                        "Do not believe the cynics in the Royal Spire. Our King acted out of mercy... did he not?",
                    ],
                )

        # 2. Smith Orin (Sanctuary Forge & Upgrades)
        elif nid == "orin":
            player.story_flags["met_orin"] = True
            w_cost = player.weapon_level * 80
            hp_cost = (player.max_hp - 3) * 90

            def upgrade_blade():
                if player.weapon_level >= 5:
                    self.start_dialogue("SMITH ORIN", ["Your Cinderblade already burns at peak sovereign temper!"])
                elif player.echoes >= w_cost:
                    player.echoes -= w_cost
                    player.weapon_level += 1
                    self.audio.play_sfx("pickup")
                    self.start_dialogue(
                        "SMITH ORIN",
                        [f"Strike true! Cinderblade tempered to Level {player.weapon_level}!"],
                    )
                else:
                    self.start_dialogue("SMITH ORIN", [f"You need {w_cost} Echoes to temper the blade."])

            def upgrade_mask():
                if player.max_hp >= 9:
                    self.start_dialogue("SMITH ORIN", ["Your vessel cannot hold any further Mask Shards."])
                elif player.echoes >= hp_cost:
                    player.echoes -= hp_cost
                    player.max_hp += 1
                    player.hp = player.max_hp
                    self.audio.play_sfx("heal")
                    self.start_dialogue(
                        "SMITH ORIN",
                        [f"A new Vessel Mask forged! Maximum Health is now {player.max_hp}."],
                    )
                else:
                    self.start_dialogue("SMITH ORIN", [f"You need {hp_cost} Echoes to forge a Vessel Mask."])

            self.start_dialogue(
                "ORIN, THE BLIND CINDERSMITH",
                [
                    "Caelum preaches of royal mercy, yet my hammer remembers forging chains for the common folk.",
                    "Bring me Echoes harvested from the husks, and I will temper your Cinderblade or reinforce your Mask.",
                ],
                choices=[
                    (f"Temper Cinderblade (+4 DMG) [{w_cost} Echoes]", upgrade_blade),
                    (f"Forge Vessel Mask (+1 Max HP) [{hp_cost} Echoes]", upgrade_mask),
                    ("Leave the Forge", lambda: None),
                ],
            )

        # 3. Sister Veyla (Weeping Mycelium)
        elif nid == "veyla":
            player.story_flags["met_veyla"] = True
            if "boss_matriarch" not in player.defeated_bosses:
                if "quest_spores" not in player.quests:
                    player.quests["quest_spores"] = "active"
                self.start_dialogue(
                    "SISTER VEYLA OF THE SPORE CHOIR",
                    [
                        "Tread softly, Scribe. The glowing fungi drink the leaked warmth of the captive sun.",
                        "Our mentor, Scholar Lyra, merged with the root-heart to escape the King's harvest. Now she attacks all who near.",
                        "Please—venture into her sanctum below and sever her torment.",
                    ],
                )
            elif player.quests.get("quest_spores") == "active":
                player.quests["quest_spores"] = "completed"
                player.echoes += QUEST_DATA["quest_spores"]["reward_echoes"]
                self.audio.play_sfx("pickup")
                self.start_dialogue(
                    "SISTER VEYLA OF THE SPORE CHOIR",
                    [
                        "Her song is clear again... Thank you, Scribe. Accept these 200 Echoes from our reliquary.",
                        "With her Abyssal Dive, you can shatter brittle stone floors across the kingdom.",
                    ],
                )
            else:
                self.start_dialogue(
                    "SISTER VEYLA OF THE SPORE CHOIR",
                    [
                        "Even in death, Lyra's spores whisper the truth: the Sun was never dying until Aurelius caged it.",
                    ],
                )

        # 4. Archivist Solen (Astral Citadel)
        elif nid == "solen":
            player.story_flags["met_solen"] = True
            if player.quests.get("quest_truth") != "completed":
                if "quest_truth" not in player.quests:
                    player.quests["quest_truth"] = "active"
                if len(player.lore_unlocked) >= 3:
                    player.quests["quest_truth"] = "completed"
                    player.echoes += QUEST_DATA["quest_truth"]["reward_echoes"]
                    if "soul_catcher" not in player.owned_relics:
                        player.owned_relics.append("soul_catcher")
                        player.equipped_relics.append("soul_catcher")
                    self.audio.play_sfx("pickup")
                    self.start_dialogue(
                        "ARCHIVIST SOLEN",
                        [
                            "You have read three tablets of the forbidden chronicle! The lie is laid bare.",
                            "King Aurelius did not save Heliosthome—he siphoned every citizen's soul into the Pelorus to make himself immortal.",
                            "Take 250 Echoes and the [Lumen Catcher] Relic. Ascend to the Obsidian Pelorus and end his stagnant reign!",
                        ],
                    )
                else:
                    self.start_dialogue(
                        "ARCHIVIST SOLEN",
                        [
                            f"Welcome to the Astral Citadel, Scribe. You have deciphered {len(player.lore_unlocked)}/3 Lore Tablets needed to reconstruct the Royal Ledger.",
                            "Elder Caelum repeats palace propaganda. Find at least 3 Lore Tablets and return to me.",
                        ],
                    )
            else:
                self.start_dialogue(
                    "ARCHIVIST SOLEN",
                    [
                        "The Pelorus Gate to the east responds to the Seals of Malakor and Lyra. Confront the Hollow Sun!",
                    ],
                )

    def update(self, dt: float):
        if not self.active:
            return
        current_text = self.pages[self.page_index]
        if self.char_index < len(current_text):
            self.char_index = min(float(len(current_text)), self.char_index + 55.0 * dt)

    def handle_key(self, key: int):
        if not self.active:
            return
        current_text = self.pages[self.page_index]
        on_last_page = self.page_index == len(self.pages) - 1

        if key in (pygame.K_w, pygame.K_UP) and on_last_page and self.choices:
            self.selected_choice = (self.selected_choice - 1) % len(self.choices)
            self.audio.play_sfx("npc_talk")
            return
        if key in (pygame.K_s, pygame.K_DOWN) and on_last_page and self.choices:
            self.selected_choice = (self.selected_choice + 1) % len(self.choices)
            self.audio.play_sfx("npc_talk")
            return

        if key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_j, pygame.K_z):
            if self.char_index < len(current_text):
                self.char_index = float(len(current_text))
            elif not on_last_page:
                self.page_index += 1
                self.char_index = 0.0
                self.audio.play_sfx("npc_talk")
            else:
                if self.choices:
                    _, callback = self.choices[self.selected_choice]
                    self.active = False
                    callback()
                else:
                    self.active = False

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return
        self._ensure_fonts()

        box = pygame.Rect(24, INTERNAL_HEIGHT - 86, INTERNAL_WIDTH - 48, 74)
        pygame.draw.rect(surface, PALETTE["obsidian"], box, border_radius=4)
        pygame.draw.rect(surface, PALETTE["amber"], box, 1, border_radius=4)

        title_surf = self._font_title.render(self.speaker, False, PALETTE["solar_gold"])
        surface.blit(title_surf, (box.x + 10, box.y + 6))

        full_text = self.pages[self.page_index]
        shown_text = full_text[: int(self.char_index)]

        # Word wrap
        words = shown_text.split(" ")
        lines = []
        curr = ""
        for w in words:
            test = (curr + " " + w).strip()
            if self._font_body.size(test)[0] <= box.width - 20:
                curr = test
            else:
                lines.append(curr)
                curr = w
        if curr:
            lines.append(curr)

        for i, line in enumerate(lines[:3]):
            line_surf = self._font_body.render(line, False, PALETTE["bone"])
            surface.blit(line_surf, (box.x + 10, box.y + 24 + i * 13))

        on_last_page = self.page_index == len(self.pages) - 1
        if on_last_page and self.choices and int(self.char_index) >= len(full_text):
            choice_box = pygame.Rect(box.x + 18, box.y - 56, box.width - 36, 52)
            pygame.draw.rect(surface, PALETTE["void"], choice_box, border_radius=4)
            pygame.draw.rect(surface, PALETTE["soul_cyan"], choice_box, 1, border_radius=4)
            for idx, (label, _) in enumerate(self.choices):
                col = PALETTE["solar_gold"] if idx == self.selected_choice else PALETTE["ash"]
                prefix = "> " if idx == self.selected_choice else "  "
                c_surf = self._font_body.render(prefix + label, False, col)
                surface.blit(c_surf, (choice_box.x + 8, choice_box.y + 5 + idx * 15))