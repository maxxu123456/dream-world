#!/usr/bin/env python3
import re
from typing import Dict

from model.user.game_profile import GameProfile
from model.dlc.dlc import Dlc

class User:
    def __init__(self, id: str, password: str, profiles = None, dlc_overrides = None, profile_id_override: int = 0):
        self.id = id
        self.password = password
        self.profiles: Dict[str, GameProfile] = profiles or {}
        self.dlc_overrides: Dict[str, Dlc] = dlc_overrides or {}
        self.profile_id_override = profile_id_override

    def get_formatted_id(self):
        return re.sub(r'(.{4})(?!$)', r'\1-', f"{self.id}000")

    def get_redacted_id(self):
        return f"{self.id[:4]}-XXXX-XXXX-XXXX"

    def add_profile(self, branch_code: str, profile: GameProfile):
        self.profiles[branch_code] = profile

    def remove_profile(self, branch_code: str):
        del self.profiles[branch_code]

    def get_profile(self, branch_code: str):
        return self.profiles.get(branch_code)

    def get_profiles(self):
        return self.profiles.values()

    def get_profile_map(self):
        return self.profiles.copy()

    def set_dlc_override(self, type: str, target: Dlc):
        if target is None:
            self.dlc_overrides.pop(type, None)
        else:
            self.dlc_overrides[type] = target

    def remove_dlc_override(self, type: str):
        self.dlc_overrides.pop(type, None)

    def has_dlc_override(self, type: str):
        return type in self.dlc_overrides

    def get_dlc_override(self, type: str):
        return self.dlc_overrides.get(type)



