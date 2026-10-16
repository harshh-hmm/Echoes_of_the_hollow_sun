"""
JSON Save and Load System with schema validation and fault tolerance.
"""

import os
import json
import copy
from game.settings import SAVE_DIR, SAVE_FILE_PATH


DEFAULT_SAVE_DATA = {
    "version": 1,
    "checkpoint_room": "sanctuary_hub",
    "checkpoint_pos": [140, 192],
    "max_hp": 5,
    "hp": 5,
    "lumen": 0,
    "echoes": 0,
    "weapon_level": 1,
    "abilities": {
        "shadow_dash": False,
        "solar_lance": False,
        "abyssal_dive": False,
        "monarch_wings": False,
    },
    "owned_relics": [],
    "equipped_relics": [],
    "lore_unlocked": [],
    "defeated_bosses": [],
    "collected_items": [],
    "visited_rooms": ["sanctuary_hub"],
    "broken_floors": [],
    "quests": {},
    "story_flags": {
        "met_caelum": False,
        "met_orin": False,
        "met_veyla": False,
        "met_solen": False,
        "pelorus_opened": False,
    },
}


class SaveSystem:
    """Manages saving, loading, and validating player progression."""

    @staticmethod
    def get_default_data() -> dict:
        return copy.deepcopy(DEFAULT_SAVE_DATA)

    @staticmethod
    def validate_save(data: dict) -> dict:
        """Ensures loaded JSON contains all required keys with valid types."""
        validated = SaveSystem.get_default_data()
        if not isinstance(data, dict):
            return validated

        for key, default_val in validated.items():
            if key in data:
                val = data[key]
                if isinstance(default_val, dict) and isinstance(val, dict):
                    merged = copy.deepcopy(default_val)
                    merged.update(val)
                    validated[key] = merged
                elif isinstance(default_val, list) and isinstance(val, list):
                    validated[key] = list(val)
                elif isinstance(default_val, int) and isinstance(val, (int, float)):
                    validated[key] = int(val)
                elif isinstance(default_val, str) and isinstance(val, str):
                    validated[key] = val

        validated["max_hp"] = max(3, min(12, validated["max_hp"]))
        validated["hp"] = max(1, min(validated["max_hp"], validated["hp"]))
        validated["weapon_level"] = max(1, min(5, validated["weapon_level"]))
        validated["echoes"] = max(0, validated["echoes"])
        return validated

    @staticmethod
    def save_exists(filepath: str = SAVE_FILE_PATH) -> bool:
        return os.path.isfile(filepath)

    @staticmethod
    def save_game(data: dict, filepath: str = SAVE_FILE_PATH) -> bool:
        """Writes validated save state to disk safely."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            clean_data = SaveSystem.validate_save(data)
            temp_path = filepath + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(clean_data, f, indent=2)
            os.replace(temp_path, filepath)
            return True
        except OSError:
            return False

    @staticmethod
    def load_game(filepath: str = SAVE_FILE_PATH) -> dict:
        """Loads and validates save state from disk, falling back to defaults."""
        if not os.path.isfile(filepath):
            return SaveSystem.get_default_data()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return SaveSystem.validate_save(raw)
        except (OSError, json.JSONDecodeError, ValueError):
            return SaveSystem.get_default_data()