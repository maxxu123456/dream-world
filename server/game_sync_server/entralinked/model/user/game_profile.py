#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass
class GameProfile:
    id: int
    first_name: str = None
    last_name: str = None
    aim_name: str = None
    zip_code: str = None
