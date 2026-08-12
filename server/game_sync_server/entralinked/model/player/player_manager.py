#!/usr/bin/env python3
import os
import logging
from pathlib import Path

from paths import ROOT_DIR
from utility.db_manager import db
from utility.gsid_utility import GsidUtility
from model.player.player import Player, PlayerStatus

logger = logging.getLogger(__name__)

_GSCD_PATH = ROOT_DIR / "save_data" / "gscd.txt"

# On Linux, since the server must be run with sudo,
# all created files must have their membership adjusted
# so we don't have to be sudo to delete/modify them.
def fix_ownership(path):
    uid = os.environ.get("SUDO_UID")
    gid = os.environ.get("SUDO_GID")

    if uid and gid:
        os.chown(path, int(uid), int(gid))

class PlayerManager:
    def __init__(self):
        logger.info("PlayerManager initialized ...")

    def load_player(self, gscd: str):
        if not GsidUtility.is_valid_gamesync_id(gscd):
            logger.error(f"Invalid Game Sync ID: {gscd}")
            return

        state = db.read_full_state(gscd)

        if state is None:
            logger.error(f"No data found for Game Sync ID: {gscd}")
            return

        player_data, game_sync, sleeping_pokemon = state

        return Player.from_dict(player_data, game_sync, sleeping_pokemon)

    def save_player(self, player: Player):
        try:
            new_player_data, game_sync, sleeper = player.to_dict()

            db.write_gscd(player.game_sync_id)

            db.write_full_state(player.game_sync_id, new_player_data, game_sync, sleeper)

        except Exception as e:
            logger.error(f"Could not save player data for {player.game_sync_id}: {e}")
            return False

        return True

    def register_player(self, game_sync_id: str, rom_code: int, lang_code: int):
        if not GsidUtility.is_valid_gamesync_id(game_sync_id):
            logger.error(f"Attempted to register invalid Game Sync ID: {game_sync_id}")
            return None

        if db.read(game_sync_id, "game_sync") is not None:
            logger.warning(f"Can't register player {game_sync_id} because the data file already exists!")
            return None

        player = Player(game_sync_id)
        player.status = PlayerStatus.AWAKE
        player.rom_code = rom_code
        player.language_code = lang_code

        if not self.save_player(player):
            return None

        self._save_gscd(game_sync_id)
        return player

    def _save_gscd(self, game_sync_id: str):
        try:
            _GSCD_PATH.parent.mkdir(parents=True, exist_ok=True)
            _GSCD_PATH.write_text(game_sync_id)
            fix_ownership(_GSCD_PATH)
            logger.info(f"Saved Game Sync ID to {_GSCD_PATH}")
        except OSError as e:
            logger.warning(f"Could not write gscd.txt for {game_sync_id}: {e}")