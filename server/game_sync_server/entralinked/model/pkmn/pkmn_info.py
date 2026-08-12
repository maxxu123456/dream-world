#!/usr/bin/env python3
from dataclasses import dataclass

@dataclass
class PkmnInfo:
    pokemon_no: int
    #pokemon_name: str
    form_no: int
    type1: int
    type2: int
    pokemon_nickname: str
    oyaname: str
    level: int
    sex: int
    personality: int
    ball_name: int
    trainer_id: int
    trainer_secret_id: int

    def is_shiny(self):
        p1 = (self.personality >> 16) & 0xFFFF
        p2 = self.personality & 0xFFFF
        return (self.trainer_id ^ self.trainer_secret_id ^ p1 ^ p2) < 8