#!/usr/bin/env python3
import logging

import io
from typing import List, Tuple
from pathlib import Path
from random import sample
from http import HTTPStatus
from datetime import datetime
from dataclasses import dataclass
from flask import request, Blueprint, g

from paths import ROOT_DIR
from model.user.user import User
from model.pkmn import extra_data
from utility.db_manager import db
from model.dlc.dlc import DlcList, Dlc
from model.pkmn.pkmn_info import PkmnInfo
from utility.gsid_utility import GsidUtility
from model.user.user_manager import UserManager
from model.avenue.avenue_data import AvenueVisitor
from utility.le_input_output import LEOutputStream
from model.pkmn.pkmn_reader import Pokemon, SaveFile
from model.player.player_manager import PlayerManager
from model.player.player import Medal, PlayerStatus, Player
from model.player.dream_data import DreamDecor, DreamEncounter, DreamItem

logger = logging.getLogger(__name__)

lang_index = {
    1: "ja",
    2: "en",
    3: "fr",
    4: "it",
    5: "de",
    7: "es",
    8: "ko"
}

@dataclass
class PglRequest:
    p: str
    tok: str
    gsid: str = None
    rom: int = None
    langcode: int = None
    dreamw: int = None

    def __post_init__(self):
        if self.gsid is not None:
            try:
                self.gsid = GsidUtility.stringify_gamesync_id(int(self.gsid))
            except ValueError:
                pass

class PglHandler:
    """HTTP handler for requests made to `en.pokemon-gl.com`"""

    username = "pokemon"
    password = "2Phfv9MY"
    sleepy_list = set(range(1, 650))

    def __init__(self, context):
        self.context = context

        self.configuration = self.context.configuration
        self.dlc_list = self.context.dlc_list
        self.user_manager = self.context.user_manager
        self.player_manager = self.context.player_manager

    # -------------------
    # Handlers
    # -------------------

    def add_handlers(self) -> Blueprint:
        blueprint = Blueprint('pgl', __name__)

        @blueprint.before_request
        def before_request_hook():
            return self.authorize_pgl_request()

        @blueprint.get('/dsio/gw')
        def pgl_get():
            return self.handle_pgl_get_request()

        @blueprint.post('/dsio/gw')
        def pgl_post():
            return self.handle_pgl_post_request()

        return blueprint

    def authorize_pgl_request(self):
        """
        BEFORE handler for `/dsio/gw` that serves to deserialize and authenticate
        the request. The deserialized request will be stored in a context attribute
        named `pgl_request` and may be retrieved by subsequent handlers.
        """
        credentials = request.authorization

        if (credentials is None) or (credentials.username != PglHandler.username) or (credentials.password != PglHandler.password):
            logger.debug("Rejecting PGL request because the auth credentials were incorrect")
            return HTTPStatus.UNAUTHORIZED

        req = PglRequest(
            p = request.args["p"],
            tok = request.args["tok"],
            gsid = request.args.get("gsid"),
            rom = int(request.args["rom"]) if "rom" in request.args else None,
            langcode = int(request.args["langcode"]) if "langcode" in request.args else None,
            dreamw = int(request.args["dreamw"]) if "dreamw" in request.args else None
        )
        logger.debug(f"Received {req}")

        session = self.user_manager.get_service_session(req.tok, "external")

        if session is None:
            logger.debug("Rejecting PGL request because the service session has expired")
            return HTTPStatus.UNAUTHORIZED

        g.pgl_request = req
        g.pgl_user = session.user

    def handle_pgl_get_request(self):
        req: PglRequest = g.pgl_request
        buffer = io.BytesIO()
        output = LEOutputStream(buffer)

        handlers = {
            "sleepily.bitlist": self.handle_get_sleepy_list,
            "account.playstatus": self.handle_get_account_status,
            "savedata.download": self.handle_download_save_data,
            "savedata.getbw": self.handle_memory_link
        }

        handler = handlers.get(req.p)

        if handler is None:
            logger.error(f"Invalid GET request type: {req.p}")
            return HTTPStatus.BAD_REQUEST

        handler(req, output)
        return buffer.getvalue(), HTTPStatus.OK, {"Content-Type": "application/octet-stream"}

    def handle_get_sleepy_list(self, req: PglRequest, output: LEOutputStream):

        if not db.does_gsid_exists(req.gsid):
            self.write_status_code(output, 1)
            return

        bit_list = bytearray(128)

        for sleepy in self.sleepy_list:
            byte_offset = sleepy // 8
            bit_offset = sleepy % 8

            bit_list[byte_offset] |= 1 << bit_offset

        self.write_status_code(output, 0)
        output.write(bit_list)

    def handle_get_account_status(self, req: PglRequest, output: LEOutputStream):
        player: Player = self.player_manager.load_player(req.gsid)

        if player is None:
            self.write_status_code(output, 8)
            return

        self.write_status_code(output, 0)
        player_status = db.read(player.game_sync_id, "player_data")["member"]["play_status"]
        output.write_short(player_status)

    def handle_download_save_data(self, req: PglRequest, output: LEOutputStream):
        player: Player = self.player_manager.load_player(req.gsid)
        user = g.pgl_user

        if player is None:
            self.write_status_code(output, 1)
            return

        logger.info(f"Player {player.gsid} is downloading save data")

        self.write_status_code(output, 0)

        if player.status == PlayerStatus.AWAKE:
            return

        is_version_2 = True if player.rom_code in (22, 23) else False

        decor_list = self._get_localized_decor(player.language_code)

        self._write_dream_counter(output, player)
        self._write_encounters(output, player.encounters)

        output.write_short(player.levels_gained)
        output.write(0)

        self._write_dlc_indices(output, user, player, is_version_2)

        output.write(0 if len(decor_list) == 0 else 1)
        output.write(0)

        self._write_items(output, player.items)
        self._write_decor(output, decor_list)

        output.write_short(0)

        if is_version_2:
            self._write_avenue_visitors(output, player.avenue_visitors)


    def handle_memory_link(self, req: PglRequest, output: LEOutputStream):
        if not GsidUtility.is_valid_gamesync_id(req.gsid):
            self.write_status_code(output, 8)
            return

        player: Player = self.player_manager.load_player(req.gsid)
        user = g.pgl_user

        if player is None:
            self.write_status_code(output, 8)
            return

        if player.rom_code == 0:
            self.write_status_code(output, 5)
            return

        if player.rom_code in (22, 23):
            self.write_status_code(output, 10)
            return

        if getattr(player, "raw_save_data", None) is None:
            self.write_status_code(output, 5)
            return

        logger.info(f"User {user.get_redacted_id()} is Memory Linking with player {player.id}")

        self.write_status_code(output, 0)

        #output.write(player.raw_save_data)

    def handle_pgl_post_request(self):
        req = g.pgl_request
        buffer = io.BytesIO()
        output = LEOutputStream(buffer)

        handlers = {
            "savedata.upload": self.handle_upload_save_data,
            "savedata.download.finish": self.handle_download_save_data_finish,
            "account.create.upload": self.handle_create_account,
            "account.createdata": self.handle_create_data
        }

        handler = handlers.get(req.p)

        if handler is None:
            logger.error(f"Invalid POST request type: {req.p}")
            return '', HTTPStatus.BAD_REQUEST

        handler(req, output)
        return buffer.getvalue(), HTTPStatus.OK, {"Content-Type": "application/octet-stream"}

    def handle_download_save_data_finish(self, req: PglRequest, output: LEOutputStream):
        player: Player = self.player_manager.load_player(req.gsid)

        if player is None:
            self.write_status_code(output, 1)
            return

        if self.configuration.clear_player_dream_info_on_wake:
            player.reset_dream_info()

            if not self.player_manager.save_player(player):
                logger.warning(f"Save data failure for player {player.game_sync_id}")
                return HTTPStatus.INTERNAL_SERVER_ERROR

        self.write_status_code(output, 0)

    def handle_upload_save_data(self, req: PglRequest, output: LEOutputStream):
        player: Player = self.player_manager.load_player(req.gsid)

        if player is None:
            request.stream.read()
            self.write_status_code(output, 1)
            return

        logger.info(f"Player {player.game_sync_id} is uploading save data")

        if player.status != PlayerStatus.AWAKE:
            logger.warning(f"Player {player.game_sync_id} is not AWAKE -- existing dream information will be overwritten!")

        if (player.rom_code != 0) and (req.rom != player.rom_code):
            logger.warning(f"Player {player.game_sync_id}'s game version changed from {player.rom_code} to {req.rom}")

        # loading save data
        save_data_bytes = request.get_data()
        save_stream = io.BytesIO(save_data_bytes)
        save = SaveFile(save_stream)

        # processing trainer data
        trainer_data = save.trainer()

        player.name = trainer_data.name
        player.country_id = trainer_data.country_id
        player.num_badges = trainer_data.num_badges

        player.played_hours = trainer_data.played_hours
        player.played_minutes = trainer_data.played_minutes

        player.loblolly_decor = trainer_data.loblolly_decor

        player.status = PlayerStatus.SLEEPING
        player.rom_code = req.rom
        player.language_code = req.langcode
        player.dreamer_info = self._extract_dreamer_info(save)

        is_version_2 = True if player.rom_code in (22, 23) else False

        if is_version_2:
            player.medals = self._get_localized_medals(save, player.language_code)

        if not self.player_manager.save_player(player):
            logger.warning(f"Save data failure for player {player.game_sync_id}")
            return HTTPStatus.INTERNAL_SERVER_ERROR

        self._update_dream_db_entry(player)

        self.write_status_code(output, 0)

    def handle_create_account(self, req: PglRequest, output: LEOutputStream):
        if not GsidUtility.is_valid_gamesync_id(req.gsid):
            self.write_status_code(output, 8)
            return

        if db.does_gsid_exists(req.gsid):
            self.write_status_code(output, 2)
            return

        player = self.player_manager.register_player(req.gsid, req.rom, req.langcode)

        if player is None:
            self.write_status_code(output, 3)
            return

        self.write_status_code(output, 0)

    def handle_create_data(self, req: PglRequest, output: LEOutputStream):
        raw_body = request.get_data(as_text=True).replace("\u0000", "")
        game_sync_id = GsidUtility.stringify_gamesync_id(int(raw_body))

        if not GsidUtility.is_valid_gamesync_id(game_sync_id):
            logger.debug(f"[account.createdata] Rejecting invalid Game Sync ID: {game_sync_id} ({raw_body})")
            self.write_status_code(output, 8)
            return

        if db.does_gsid_exists(game_sync_id):
            self.write_status_code(output, 2)
            return

        if self.player_manager.register_player(game_sync_id, None, None) is None:
            self.write_status_code(output, 3)
            return

        self.write_status_code(output, 0)

    # -------------------
    # Private helpers
    # -------------------

    def _write_dream_counter(self, output: LEOutputStream, player: Player) -> None:
        """Writes a 4-byte integer used as a counter for total tuck-ins."""

        sleep_pokemon_count = db.read(player.game_sync_id, "player_data")["member"]["sleep_pokemon_count"]
        output.write_int(sleep_pokemon_count)

    def _write_encounters(self, output: LEOutputStream, encounters: List[DreamEncounter]) -> None:
        """Writes up to 10 Entree Forest encounters."""

        for encounter in encounters:
            output.write_short(encounter.species)
            output.write_short(encounter.move)
            output.write(encounter.form)
            output.write(encounter.gender)
            output.write(encounter.animation.value)
            output.write(0)

        output.write_bytes(0, (10 - len(encounters)) * 8)

    def _write_dlc_indices(self, output: LEOutputStream, user: User, player: Player, is_version_2: bool) -> None:
        """Writes DLC indices for musical, C-Gear skin, and Pokédex skin."""
        output.write(self.get_dlc_index(user, player.musical, "MUSICAL", player.get_file("musical.bin")))
        output.write(self.get_dlc_index(user, player.cgear_skin, "CGEAR2" if is_version_2 else "CGEAR", player.get_file("cgear.bin")))
        output.write(self.get_dlc_index(user, player.dex_skin, "ZUKAN", player.get_file("zukan.bin")))

    def _write_items(self, output: LEOutputStream, items: List[DreamItem]) -> None:
        """Writes up to 20 item IDs followed by up to 20 item quantities."""
        for item in items:
            output.write_short(item.pokeitem_id)

        output.write_bytes(0, (20 - len(items)) * 2)

        for item in items:
            output.write(item.item_cnt)

        output.write_bytes(0, (20 - len(items)))

    def _write_decor(self, output: LEOutputStream, decor_list: List[DreamDecor]) -> None:
        """Writes up to 5 Decor entries. Missing entries use 0x7E."""
        for decor in decor_list:
            output.write_short(decor.id)

            name_bytes = decor.name.encode("UTF-16-LE")

            output.write(name_bytes, 0, min(len(name_bytes), 24))
            output.write_bytes(-1, 24 - len(name_bytes))

        for _ in range(5 - len(decor_list)):
            output.write_short(0x7E)
            output.write_bytes(0, 24)

    def _write_avenue_visitors(self, output: LEOutputStream, visitors: List[AvenueVisitor]) -> None:
        """For Black 2/White 2 only: writes up to 12 Join Avenue visitors."""

        for visitor in visitors:
            name_bytes = visitor.name.encode("UTF-16-LE")
            output.write(name_bytes, 0, min(14, len(name_bytes)))
            output.write_bytes(-1, 16 - len(name_bytes))

            visitor_type = visitor.type.client_id + visitor.personality * 8
            output.write(visitor_type)
            output.write(visitor.shop_type.value + (7 - visitor_type * 2 % 7))

            output.write_short(0)
            output.write_int(1)
            output.write(visitor.country_code)
            output.write(visitor.state_province_code)
            output.write(visitor.game_language_code)
            output.write(visitor.game_rom_code)
            output.write(1 if visitor.type.female else 0)
            output.write(0)
            output.write_short(visitor.dreamer_species)

        output.write_bytes(0, (12 - len(visitors)) * 32)
        output.write_int(0)

    def _extract_dreamer_info(self, save: SaveFile) -> PkmnInfo:
        """Extracts the tucked-in Pokémon data from the save file."""
        pkmn_data = save.get_dreamer_pokemon()

        dreamer_info = PkmnInfo(
            pokemon_no        = pkmn_data.natdex,
            form_no           = pkmn_data.form,
            type1             = pkmn_data.type1,
            type2             = pkmn_data.type2,
            pokemon_nickname  = pkmn_data.nickname,
            oyaname           = pkmn_data.trainer_name,
            level             = pkmn_data.level,
            sex               = pkmn_data.gender,
            personality       = pkmn_data.nature,
            ball_name         = pkmn_data.ball,
            trainer_id        = pkmn_data.trainer_id,
            trainer_secret_id = pkmn_data.trainer_id_secret
        )

        return dreamer_info


    def _update_dream_db_entry(self, player: Player) -> None:
        """Updates the database record for this session."""

        now_local = datetime.now().astimezone()

        p = db.read(player.game_sync_id, "player_data")

        p["member"].update({
            "sleeping_flag":            1,
            "sleep_pokemon_count":      p["member"]["sleep_pokemon_count"] + 1,
            "pdw_copied_at":            now_local.strftime("%Y-%m-%d %H:%M:%S"),
            "last_up_time":             now_local.strftime("%m/%d/%y %H:%M"),
            "last_up_time_strict":      now_local.strftime("%Y-%m-%d %H:%M:%S"),
            "last_started_at_timezone": int(now_local.timestamp()),
        })

        db.write(player.game_sync_id, "player_data", p)

    # -------------------
    # Utility
    # -------------------

    def _get_localized_medals(self, save: SaveFile, player_lang: str) -> List[Medal]:
        """Generates a list of the obtained Medals, localized to the player's cart language."""
        medal_list = []

        with open(ROOT_DIR / "raw_text" / lang_index[player_lang] / "medal.txt", "r", encoding = "UTF-8") as f:
            medal_names = f.read().splitlines()

        medal_data = save.medal()
        for medal_id in medal_data.medal_list:
            medal = Medal(medal_id, medal_names[medal_id], False)
            if medal_data.favorite_medal == medal_id:
                medal.is_recommend = True

            medal_list.append(medal)

        return medal_list


    def _get_localized_decor(self, player_lang: str) -> List[DreamDecor]:
        """Generates a list of the 5 Loblolly Decor, localized to the player's cart language."""
        decor_list = []

        with open(ROOT_DIR / "raw_text" / lang_index[player_lang] / "decor.txt", "r", encoding = "UTF-8") as f:
            decor_names = f.read().splitlines()

        for decor_id in sample([1, 2, 3, 4, 6], 5):
            decor = DreamDecor(decor_id, decor_names[decor_id])
            decor_list.append(decor)

        return decor_list

    def write_status_code(self, output: LEOutputStream, status: int):
        output.write_int(status)
        output.write_bytes(0, 124)

    def get_dlc_index(self, user: User, name: str, type: str, custom_file: Path):
        if name == "custom":
            user.set_dlc_override(type, Dlc(custom_file.absolute(),
                                            name, "IRAO", type, 1,
                                            custom_file.stat().st_size, 0, True))
            return 1
        else:
            user.remove_dlc_override(type)
            return self.dlc_list.get_dlc_index("IRAO", type, name)