"""
User Interface system: HUD (Health Masks, Lumen Orb, Echoes, Active Abilities),
Boss Health Bar, Area Banner, Tabbed Inventory/Map/Journal/Quests Menu,
Pause/Settings Screen, Title Screen, Intro Narrative, Game Over, and Ending/Credits.
"""

import pygame
from game.settings import (
    INTERNAL_WIDTH,
    INTERNAL_HEIGHT,
    GAME_TITLE,
    PALETTE,
    LORE_ENTRIES,
    RELIC_DATA,
    QUEST_DATA,
)
from game.world import WORLD_MAP_NODES


class UIManager:
    """Renders all HUD elements, menus, maps, and narrative overlays."""

    def __init__(self):
        pygame.font.init()
        self.font_lg = pygame.font.SysFont("consolas", 18, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 12, bold=True)
        self.font_sm = pygame.font.SysFont("consolas", 10)
        self.inventory_tab = 0  # 0=Map, 1=Relics & Stats, 2=Journal & Quests
        self.selected_relic_idx = 0

    def draw_hud(self, surface: pygame.Surface, player, world):
        # 1. Lumen Vessel Orb (Top-Left)
        orb_center = (22, 22)
        pygame.draw.circle(surface, PALETTE["obsidian"], orb_center, 14)
        fill_ratio = player.lumen / max(1, player.max_lumen)
        if fill_ratio > 0:
            fill_r = max(2, int(12 * fill_ratio))
            col = PALETTE["soul_cyan"] if player.lumen >= 25 else PALETTE["slate"]
            pygame.draw.circle(surface, col, orb_center, fill_r)
        pygame.draw.circle(surface, PALETTE["bone"], orb_center, 14, 1)

        # 2. Health Masks
        for i in range(player.max_hp):
            mx = 44 + i * 13
            my = 12
            rect = pygame.Rect(mx, my, 10, 12)
            if i < player.hp:
                pygame.draw.rect(surface, PALETTE["bone"], rect, border_radius=3)
                pygame.draw.rect(surface, PALETTE["obsidian"], (mx + 2, my + 4, 2, 3))
                pygame.draw.rect(surface, PALETTE["obsidian"], (mx + 6, my + 4, 2, 3))
            else:
                pygame.draw.rect(surface, PALETTE["slate"], rect, 1, border_radius=3)

        # 3. Echoes Counter & Weapon Level
        echo_txt = self.font_sm.render(
            f"ECHOES: {player.echoes}   BLADE LV.{player.weapon_level}",
            False,
            PALETTE["amber"],
        )
        surface.blit(echo_txt, (44, 28))

        # 4. Unlocked Ability Badges (Top-Right)
        badges = [
            ("shadow_dash", "CLOAK", PALETTE["void_violet"]),
            ("solar_lance", "LANCE", PALETTE["soul_cyan"]),
            ("abyssal_dive", "DIVE", PALETTE["amber"]),
            ("monarch_wings", "WINGS", PALETTE["solar_gold"]),
        ]
        bx = INTERNAL_WIDTH - 48
        for key, label, col in badges:
            if player.abilities.get(key):
                pygame.draw.rect(surface, PALETTE["obsidian"], (bx, 8, 40, 13))
                pygame.draw.rect(surface, col, (bx, 8, 40, 13), 1)
                t_surf = self.font_sm.render(label, False, col)
                surface.blit(t_surf, (bx + 4, 9))
                bx -= 44

        # 5. Area Banner
        if world.banner_timer > 0:
            b_surf = self.font_md.render(world.banner_text, False, PALETTE["bone"])
            bx = INTERNAL_WIDTH // 2 - b_surf.get_width() // 2
            pygame.draw.rect(
                surface,
                PALETTE["obsidian"],
                (bx - 12, 42, b_surf.get_width() + 24, 20),
                border_radius=3,
            )
            pygame.draw.rect(
                surface,
                PALETTE["amber"],
                (bx - 12, 42, b_surf.get_width() + 24, 20),
                1,
                border_radius=3,
            )
            surface.blit(b_surf, (bx, 46))

        # 6. Active Boss Health Bar (Bottom Center)
        if world.current_room:
            for boss in world.current_room.bosses:
                if not boss.dead:
                    bar_w = 260
                    bar_x = (INTERNAL_WIDTH - bar_w) // 2
                    bar_y = INTERNAL_HEIGHT - 26
                    name_s = self.font_sm.render(boss.name, False, PALETTE["bone"])
                    surface.blit(
                        name_s,
                        (INTERNAL_WIDTH // 2 - name_s.get_width() // 2, bar_y - 13),
                    )
                    pygame.draw.rect(
                        surface, PALETTE["obsidian"], (bar_x - 2, bar_y - 2, bar_w + 4, 10)
                    )
                    hp_w = int(bar_w * (boss.hp / max(1, boss.max_hp)))
                    pygame.draw.rect(
                        surface, PALETTE["crimson"], (bar_x, bar_y, hp_w, 6)
                    )
                    pygame.draw.rect(
                        surface, PALETTE["amber"], (bar_x - 2, bar_y - 2, bar_w + 4, 10), 1
                    )

    def draw_title_screen(
        self, surface: pygame.Surface, selected_idx: int, has_save: bool
    ):
        surface.fill(PALETTE["void"])
        pygame.draw.circle(
            surface, PALETTE["amber"], (INTERNAL_WIDTH // 2, 78), 34, 2
        )
        pygame.draw.circle(
            surface, PALETTE["obsidian"], (INTERNAL_WIDTH // 2, 78), 28
        )

        t_surf = self.font_lg.render(GAME_TITLE, False, PALETTE["solar_gold"])
        surface.blit(
            t_surf, (INTERNAL_WIDTH // 2 - t_surf.get_width() // 2, 122)
        )
        sub_surf = self.font_sm.render(
            "A Dark-Fantasy Action RPG in Pure Python", False, PALETTE["ash"]
        )
        surface.blit(
            sub_surf, (INTERNAL_WIDTH // 2 - sub_surf.get_width() // 2, 144)
        )

        options = ["CONTINUE VESSEL" if has_save else "NEW PILGRIMAGE", "NEW PILGRIMAGE (RESET)", "QUIT TO DESKTOP"]
        for i, opt in enumerate(options):
            col = PALETTE["solar_gold"] if i == selected_idx else PALETTE["bone"]
            prefix = "> " if i == selected_idx else "  "
            o_surf = self.font_md.render(prefix + opt, False, col)
            surface.blit(
                o_surf, (INTERNAL_WIDTH // 2 - o_surf.get_width() // 2, 178 + i * 20)
            )

        hint = self.font_sm.render(
            "W/S or Arrows: Navigate   |   Enter / Space / J: Confirm",
            False,
            PALETTE["stone"],
        )
        surface.blit(hint, (INTERNAL_WIDTH // 2 - hint.get_width() // 2, 248))

    def draw_intro_screen(self, surface: pygame.Surface):
        surface.fill(PALETTE["void"])
        lines = [
            "PROLOGUE: THE CAGED STAR",
            "",
            "When the surface froze, King Aurelius bound the dying Sun",
            "deep beneath Heliosthome inside the Obsidian Pelorus.",
            "",
            "Yet a star was never meant to be caged.",
            "Time fractured. Citizens withered into hollow ash, while",
            "their severed memories manifested as restless wraiths.",
            "",
            "Awaken, Vesper—last of the Vessel-Scribes.",
            "Harvest the Echoes. Claim the Two Seals. Shatter the Hollow Sun.",
            "",
            "[ Press SPACE or ENTER to Awaken ]",
        ]
        for i, line in enumerate(lines):
            col = (
                PALETTE["solar_gold"]
                if i in (0, len(lines) - 1)
                else PALETTE["bone"]
            )
            s = self.font_sm.render(line, False, col)
            surface.blit(s, (INTERNAL_WIDTH // 2 - s.get_width() // 2, 26 + i * 17))

    def draw_inventory_screen(self, surface: pygame.Surface, player, current_room_id: str):
        overlay = pygame.Rect(20, 18, INTERNAL_WIDTH - 40, INTERNAL_HEIGHT - 36)
        pygame.draw.rect(surface, PALETTE["obsidian"], overlay, border_radius=4)
        pygame.draw.rect(surface, PALETTE["amber"], overlay, 1, border_radius=4)

        tabs = ["[1] WORLD MAP", "[2] RELICS & ABILITIES", "[3] JOURNAL & QUESTS"]
        for i, t_name in enumerate(tabs):
            col = PALETTE["solar_gold"] if i == self.inventory_tab else PALETTE["ash"]
            ts = self.font_sm.render(t_name, False, col)
            surface.blit(ts, (36 + i * 140, 26))

        pygame.draw.line(
            surface, PALETTE["slate"], (30, 42), (INTERNAL_WIDTH - 30, 42), 1
        )

        # TAB 0: WORLD MAP
        if self.inventory_tab == 0:
            for rid, info in WORLD_MAP_NODES.items():
                gx, gy = info["grid"]
                rx = 65 + gx * 92
                ry = 72 + gy * 48
                visited = rid in player.visited_rooms
                rect = pygame.Rect(rx, ry, 78, 30)
                if visited:
                    pygame.draw.rect(surface, PALETTE["slate"], rect, border_radius=3)
                    border_c = (
                        PALETTE["solar_gold"]
                        if rid == current_room_id
                        else PALETTE["bone"]
                    )
                    pygame.draw.rect(surface, border_c, rect, 1, border_radius=3)
                    lbl = self.font_sm.render(info["label"][:11], False, border_c)
                    surface.blit(lbl, (rx + 4, ry + 9))
                else:
                    pygame.draw.rect(surface, PALETTE["void"], rect, 1, border_radius=3)

            legend = self.font_sm.render(
                "Gold Border = Current Location   |   A/D or Left/Right: Switch Tab   |   Tab/Esc: Close",
                False,
                PALETTE["ash"],
            )
            surface.blit(legend, (34, INTERNAL_HEIGHT - 36))

        # TAB 1: RELICS & STATS
        elif self.inventory_tab == 1:
            stat_str = (
                f"HP: {player.hp}/{player.max_hp}   |   "
                f"Blade Lv.{player.weapon_level} (DMG: {player.get_melee_damage()})   |   "
                f"Echoes: {player.echoes}"
            )
            surface.blit(
                self.font_sm.render(stat_str, False, PALETTE["soul_cyan"]), (36, 50)
            )
            surface.blit(
                self.font_sm.render(
                    "RELICS (W/S to select, SPACE/ENTER to Toggle Equip):",
                    False,
                    PALETTE["amber"],
                ),
                (36, 70),
            )
            all_keys = list(RELIC_DATA.keys())
            for idx, r_key in enumerate(all_keys):
                r_info = RELIC_DATA[r_key]
                owned = r_key in player.owned_relics
                equipped = r_key in player.equipped_relics
                prefix = "> " if idx == self.selected_relic_idx else "  "
                status = "[EQUIPPED]" if equipped else ("[OWNED]" if owned else "[LOCKED]")
                name_txt = r_info["name"] if owned else "???"
                desc_txt = r_info["desc"] if owned else "Explore Heliosthome to uncover this relic."
                col = (
                    PALETTE["solar_gold"]
                    if idx == self.selected_relic_idx
                    else (PALETTE["bone"] if owned else PALETTE["stone"])
                )
                line = f"{prefix}{name_txt} {status} - {desc_txt}"
                surface.blit(self.font_sm.render(line[:64], False, col), (36, 90 + idx * 24))

        # TAB 2: LORE JOURNAL & QUESTS
        else:
            surface.blit(
                self.font_sm.render("ACTIVE & COMPLETED QUESTS:", False, PALETTE["amber"]),
                (36, 50),
            )
            qy = 66
            if not player.quests:
                surface.blit(
                    self.font_sm.render(
                        "Speak with NPCs in the Sanctuary, Mycelium, and Citadel.",
                        False,
                        PALETTE["ash"],
                    ),
                    (36, qy),
                )
                qy += 16
            else:
                for qid, status in player.quests.items():
                    qinfo = QUEST_DATA.get(qid)
                    if qinfo:
                        col = (
                            PALETTE["spore_green"]
                            if status == "completed"
                            else PALETTE["bone"]
                        )
                        surface.blit(
                            self.font_sm.render(
                                f"- {qinfo['title']} [{status.upper()}]: {qinfo['desc'][:44]}...",
                                False,
                                col,
                            ),
                            (36, qy),
                        )
                        qy += 15

            surface.blit(
                self.font_sm.render(
                    f"DECIPHERED LORE TABLETS ({len(player.lore_unlocked)}/5):",
                    False,
                    PALETTE["soul_cyan"],
                ),
                (36, 122),
            )
            ly = 138
            for lid in player.lore_unlocked:
                entry = LORE_ENTRIES.get(lid)
                if entry:
                    surface.blit(
                        self.font_sm.render(
                            f"* {entry['title']}: {entry['text'][:52]}...",
                            False,
                            PALETTE["bone"],
                        ),
                        (36, ly),
                    )
                    ly += 16

    def draw_pause_menu(self, surface: pygame.Surface, selected_idx: int, audio):
        box = pygame.Rect(120, 56, 240, 158)
        pygame.draw.rect(surface, PALETTE["obsidian"], box, border_radius=4)
        pygame.draw.rect(surface, PALETTE["amber"], box, 1, border_radius=4)

        title = self.font_md.render("PAUSED / SETTINGS", False, PALETTE["solar_gold"])
        surface.blit(title, (INTERNAL_WIDTH // 2 - title.get_width() // 2, 68))

        items = [
            "RESUME GAME",
            f"MUSIC VOLUME: {int(audio.music_volume * 100)}%",
            f"SFX VOLUME: {int(audio.sfx_volume * 100)}%",
            f"MUTE AUDIO: {'ON' if audio.muted else 'OFF'}",
            "SAVE & QUIT TO TITLE",
        ]
        for i, label in enumerate(items):
            col = PALETTE["solar_gold"] if i == selected_idx else PALETTE["bone"]
            prefix = "> " if i == selected_idx else "  "
            s = self.font_sm.render(prefix + label, False, col)
            surface.blit(s, (142, 96 + i * 20))

    def draw_game_over(self, surface: pygame.Surface):
        surface.fill(PALETTE["void"])
        t = self.font_lg.render("VESSEL SHATTERED", False, PALETTE["crimson"])
        surface.blit(t, (INTERNAL_WIDTH // 2 - t.get_width() // 2, 95))
        sub = self.font_sm.render(
            "Press SPACE or ENTER to reawaken at the last Cinder Shrine",
            False,
            PALETTE["bone"],
        )
        surface.blit(sub, (INTERNAL_WIDTH // 2 - sub.get_width() // 2, 138))

    def draw_victory_screen(self, surface: pygame.Surface, player):
        surface.fill(PALETTE["void"])
        true_ending = len(player.lore_unlocked) >= 3
        heading = (
            "ENDING A: DAWN OF UNBOUND STARS (TRUE ENDING)"
            if true_ending
            else "ENDING B: THE SILENT EMBER"
        )
        lines = [
            heading,
            "",
            "With Aurelius vanquished, the Obsidian Pelorus fractures open.",
            "The captive star's warmth floods the subterranean halls,",
            "releasing the trapped memories of Heliosthome to ascend.",
            "",
            (
                "Having uncovered the Royal Archive's truth, you shatter the"
                if true_ending
                else "Without the full chronicle, you take the King's place"
            ),
            (
                "siphon forever—restoring true daylight to the waking world."
                if true_ending
                else "to guard the fading warmth for one final age."
            ),
            "",
            f"Echoes Gathered: {player.echoes}   |   Lore Tablets: {len(player.lore_unlocked)}/5   |   Relics: {len(player.owned_relics)}/4",
            "",
            "Created in Pure Python & Pygame — Thank you for playing!",
            "[ Press ENTER or ESCAPE to Return to Title ]",
        ]
        for i, line in enumerate(lines):
            col = (
                PALETTE["solar_gold"]
                if i in (0, len(lines) - 1)
                else PALETTE["bone"]
            )
            s = self.font_sm.render(line, False, col)
            surface.blit(s, (INTERNAL_WIDTH // 2 - s.get_width() // 2, 22 + i * 18))