#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass
class Configuration:
    host_name: str = "local"
    clear_player_dream_info_on_wake: bool = True
    allow_wfc_registration_through_login: bool = True
