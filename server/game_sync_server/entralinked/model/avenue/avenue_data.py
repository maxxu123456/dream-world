#!/usr/bin/env python3
from enum import Enum, auto
from dataclasses import dataclass

class AvenueShopType(Enum):
    RAFFLE = 0
    FLORIST = auto()
    SALON = auto()
    ANTIQUE = auto()
    DOJO = auto()
    CAFE = auto()
    MARKET = auto()

class AvenueVisitorType(Enum):
    YOUNGSTER = ("Youngster", 0)
    LASS = ("Lass", 0, True)
    
    ACE_TRAINER_MALE = ("Ace Trainer♂", 1)
    ACE_TRAINER_FEMALE = ("Ace Trainer♀", 1, True)
    
    RANGER_MALE = ("Pokémon Ranger♂", 2)
    RANGER_FEMALE = ("Pokémon Ranger♀", 2, True)
    
    BREEDER_MALE = ("Pokémon Breeder♂", 3)
    BREEDER_FEMALE = ("Pokémon Breeder♀", 3, True)
    
    SCIENTIST_MALE = ("Scientist♂", 4)
    SCIENTIST_FEMALE = ("Scientist♀", 4, True)
    
    HIKER = ("Hiker", 5)
    PARASOL_LADY = ("Parasol Lady", 5, True)
    
    ROUGHNECK = ("Roughneck", 6)
    NURSE = ("Nurse", 6, True)
    
    PRESCHOOLER_MALE = ("Preschooler♂", 7)
    PRESCHOOLER_FEMALE = ("Preschooler♀", 7, True)

    def __init__(self, display_name: str, client_id: int, female: bool = False):
        self.display_name = display_name
        self.client_id = client_id
        self.female = female

@dataclass
class AvenueVisitor:
    name: str
    type: AvenueVisitorType
    shop_type: AvenueShopType
    game_language_code: int
    game_rom_code: int
    country_code: int
    state_province_code: int
    personality: int
    dreamer_species: int
