#!/usr/bin/env python3
from typing import List
from random import randint
from enum import Enum, auto
from datetime import datetime
from dataclasses import dataclass, asdict

from paths import GAME_SYNC_ROOT
from utility.db_manager import db
from model.pkmn import extra_data
from model.pkmn.pkmn_info import PkmnInfo
from model.player.dream_data import DreamEncounter, DreamDecor, DreamItem
from model.avenue.avenue_data import AvenueVisitor

class PlayerStatus(Enum):
    AWAKE = 0
    SLEEPING = auto()
    DREAMING = auto()
    WAKE_READY = auto()

@dataclass
class Medal:
    medal_id: int
    medal_name: str
    is_recommend: bool

class Player:
    def __init__(self, game_sync_id: str):
        self.game_sync_id = game_sync_id
        self.gsid = 0
        self.encounters = []
        self.items = []
        self.avenue_visitors = []
        self.decor = []

        self.medals = []

        self.name = None
        self.num_badges = None
        self.country_id = None

        self.played_hours = 0
        self.played_minutes = 0

        self.status = PlayerStatus.AWAKE

        self.rom_code = 0
        self.language_code = 0

        self.dreamer_info = None
        self.levels_gained = 0

        self.loblolly_decor = None

        self.cgear_skin = None
        self.dex_skin = None
        self.musical = None
        self.custom_cgear_skin = None
        self.custom_dex_skin = None
        self.custom_musical = None

        self.data_directory = GAME_SYNC_ROOT / "data"

    @staticmethod
    def _empty_player_data() -> dict:
        empty_data = {
            "member": {
                "member_id":            randint(3_000_000, 3_500_000),
                "pgl_name":             None,
                "country_id":           None,
                "special_flag":         0,
                "bridge_flag":          0,
                "special_disp_flag":    0,
                "member_created_at":    datetime.now().strftime("%Y-%m-%d"),
                "disclosure_flag":      0,    # privacy settings stuff
                "list_disclosure_flag": 0,    # privacy settings stuff
                "member_savedata_id":   None,
                "gsid":                 None,
                "sleep_time":           0,
                "sleep_pokemon_count":  0,
                "send_pokemon_count":   0,
                "island_id":            201,
                "shelf_id":             301,
                "disable_flag":         0,
                "wateringpot_id":       1,
                "avator_id":            4,
                "first_flag":           1,    # 0 = first time playing, 1 = not first time
                "trial_flag":           0,
                "sleeping_flag":        0,
                "rom_id":               None,
                "pokemon_no":           None,
                "form_no":              None,
                "player_badge_num":     None,
                "last_started_at":      None,
                "last_logined_at":      None,
                "deleted_at":           None,
                "pdw_copied_at":        None,
                "pgl_copied_at":        None,
                "item_deleted_flag":    0,
                "world_id":             1,
                "avator_name":          None,
                "gsid_count":           1,
                "point":                0,
                "experiment_point":     0,
                "is_initializing":      0,
                "langcode":             None,
                "player_name":          None,
                "play_status":          PlayerStatus.AWAKE.value,
                "isin_sleep_pokemon":   1,
                "last_up_time":         None,
                "last_up_time_strict":  None,
                "rom_name":             None,
                "alter_rom_name":       None,
                "pokemon_name":         None,
                "type1":                None,
                "type2":                None,
                "gscd":                 None,
                "is_downloaded":        0,
                "nextstart_remaintime": 0,
                "last_started_at_timezone": None,
                "unread_mail_count":    0
            },
            "token": None
        }
        return empty_data

    @classmethod
    def from_dict(cls, player_data: dict, game_sync: dict, sleeper: dict):
        member_data = player_data["member"]

        player = cls(member_data["gscd"])

        player.gsid = member_data["gsid"]

        player.rom_code = member_data["rom_id"]
        player.language_code = member_data["langcode"]
        player.dreamer_info = PkmnInfo(**sleeper) if sleeper else None
        player.levels_gained = game_sync["levels_gained"]

        player.loblolly_decor = game_sync["loblolly_decor"]

        player.name = member_data["player_name"]
        player.num_badges = member_data["player_badge_num"]

        player.country_id = member_data["country_id"]

        player.played_hours = game_sync["hours_played"]
        player.played_minutes = game_sync["minutes_played"]

        player.cgear_skin = game_sync["cgear_skin"]
        player.dex_skin = game_sync["dex_skin"]
        player.musical = game_sync["musical"]
        player.custom_cgear_skin = game_sync["custom_cgear_skin"]
        player.custom_dex_skin = game_sync["custom_dex_skin"]
        player.custom_musical = game_sync["custom_musical"]

        player.status = PlayerStatus(member_data["play_status"])

        player.encounters = [DreamEncounter(**e) for e in game_sync.get("encounters", [])]
        player.items = [DreamItem(**i) for i in game_sync.get("items", [])]
        player.avenue_visitors = [AvenueVisitor(**v) for v in game_sync.get("avenue_visitors", [])]
        player.decor = [DreamDecor(**d) for d in game_sync.get("decor", [])]

        player.medals = [Medal(**m) for m in player_data.get("medals", [])]

        return player

    def to_dict(self):
        now = datetime.now().astimezone()

        player_data = db.read(self.game_sync_id, "player_data") or Player._empty_player_data()

        player_data["member"].update({
            "pgl_name":            self.name,
            "country_id":          self.country_id,

            "member_savedata_id":  player_data["member"]["member_id"],
            "gsid":                self.gsid,

            "sleeping_flag":       1,
            "rom_id":              self.rom_code,
            "pokemon_no":          self.dreamer_info.pokemon_no if self.dreamer_info else None,
            "form_no":             self.dreamer_info.form_no if self.dreamer_info else None,
            "player_badge_num":    self.num_badges,

            "pgl_copied_at":       now.strftime("%Y-%m-%d %H:%M:%S"),

            "langcode":            self.language_code,
            "player_name":         self.name,
            "play_status":         PlayerStatus.SLEEPING.value,

            "alter_rom_name":      "Shiro*" if self.rom_code in (20, 22) else "Kuro*",
            "pokemon_name":        self.dreamer_info.pokemon_no if self.dreamer_info else None,
            "type1":               self.dreamer_info.type1 if self.dreamer_info else None,
            "type2":               self.dreamer_info.type2 if self.dreamer_info else None,
            "gscd":                self.game_sync_id
        })

        if self.rom_code in (22, 23):
            player_data.update({"medals": [asdict(medal) for medal in self.medals]})

        game_sync = {
            "levels_gained": self.levels_gained,
            "hours_played": self.played_hours,
            "minutes_played": self.played_minutes,
            "cgear_skin": self.cgear_skin,
            "dex_skin": self.dex_skin,
            "musical": self.musical,
            "custom_cgear_skin": self.custom_cgear_skin,
            "custom_dex_skin": self.custom_dex_skin,
            "custom_musical": self.custom_musical,
            "encounters": [asdict(encounter) for encounter in self.encounters],
            "items": [asdict(item) for item in self.items],
            "avenue_visitors": [asdict(visitor) for visitor in self.avenue_visitors],
            "decor": [asdict(decor) for decor in self.decor],
            "loblolly_decor": self.loblolly_decor
        }

        sleeper = asdict(self.dreamer_info) if self.dreamer_info is not None else None

        return (player_data, game_sync, sleeper)

    def reset_dream_info(self):
        self.status = PlayerStatus.AWAKE
        self.dreamer_info = None
        self.encounters.clear()
        self.items.clear()
        self.avenue_visitors.clear()
        self.decor.clear()
        self.levels_gained = 0
        self.cgear_skin = None
        self.dex_skin = None
        self.musical = None

    def set_encounters(self, encounters: List[DreamEncounter]):
        if len(encounters) <= 10:
            self.encounters.clear()
            self.encounters.extend(encounters)

    def get_encounters(self):
        return self.encounters.copy()

    def set_items(self, items: List[DreamItem]):
        if len(items) <= 20:
            self.items.clear()
            self.items.extend(items)

    def get_items(self):
        return self.items.copy()

    def set_avenue_visitors(self, avenue_visitors: List[AvenueVisitor]):
        if len(avenue_visitors) <= 12:
            self.avenue_visitors.clear()
            self.avenue_visitors.extend(avenue_visitors)

    def get_avenue_visitors(self):
        return self.avenue_visitors.copy()

    def set_decor(self, decor: List[DreamDecor]):
        if len(decor) <= 5:
            self.decor.clear()
            self.decor.extend(decor)

    def get_file(self, filename: str):
        """Valid files are `data.json`, `save.bin`, `cgear.bin`, `zukan.bin`, and `musical.bin`"""
        return self.data_directory / filename
