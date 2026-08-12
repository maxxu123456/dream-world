#!/usr/bin/env python3
from dataclasses import dataclass
from enum import Enum, auto

class DreamAnimation(Enum):
    LOOK_AROUND = 0
    WALK_AROUND = auto()
    WALK_LOOK_AROUND = auto()
    WALK_VERTICALLY = auto()
    WALK_HORIZONTALLY = auto()
    WALK_LOOK_HORIZONTALLY = auto()
    SPIN_RIGHT = auto()
    SPIN_LEFT = auto()

@dataclass
class DreamDecor:
    id: int
    name: str

@dataclass
class DreamEncounter:
    species: int
    move: int
    form: int
    gender: int
    animation: DreamAnimation

@dataclass
class DreamItem:
    pokeitem_id: int
    item_cnt: int
