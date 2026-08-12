#!/usr/bin/env python3
import logging

from typing import List
from pathlib import Path
from dataclasses import dataclass

from entralinked.paths import GAME_SYNC_ROOT
from entralinked.utility import crc16

logger = logging.getLogger(__name__)

@dataclass
class Dlc:
    path: str
    name: str
    game_code: str
    type: str
    index: int
    projected_size: int
    checksum: int
    checksum_embedded: bool

class DlcList:

    data_dir = GAME_SYNC_ROOT / "dlc"

    def __init__(self):
        self.dlc_list: List[Dlc] = []

        if not DlcList.data_dir.exists():
            logger.info("Extracting default DLC files ...")
            DlcList.data_dir = GAME_SYNC_ROOT / "entralinked" / "data" / "dlc_skins"

        for game_code_dir in DlcList.data_dir.iterdir():
            if not game_code_dir.is_dir():
                logger.warning(f"Non-directory '{game_code_dir.name}' in DLC root folder")
                continue

            for dlc_type_dir in game_code_dir.iterdir():
                if not dlc_type_dir.is_dir():
                    logger.warning(f"Non-directory '{dlc_type_dir.name}' in DLC subfolder '{game_code_dir.name}'")

                index = 1

                for dlc_dir in dlc_type_dir.iterdir():
                    name = dlc_dir.name

                    if name in ("none", "custom"):
                        logger.warning(f"DLC '{game_code_dir.name}/{dlc_type_dir.name}/{name}' could not be loaded because it uses a reserved name.")
                        continue

                    dlc = self.load_dlc_file(game_code_dir.name, dlc_type_dir.name, index, dlc_dir)

                    if dlc is not None:
                        self.dlc_list.append(dlc)
                        index += 1

        logger.info(f"Loaded {len(self.dlc_list)} DLC file(s)")

    def load_dlc_file(self, game_code: str, type: str, index: int, dlc_file: Path):
        name = dlc_file.name

        if dlc_file.is_dir():
            logger.warning(f"Directory '{name}' in {game_code} DLC folder")
            return None

        try:
            projected_size = 0
            checksum = 0
            checksum_embedded = True

            file_bytes = dlc_file.read_bytes()
            projected_size = len(file_bytes)
            checksum = crc16.calc(file_bytes, 0, len(file_bytes) - 2)

            checksum_in_file = (file_bytes[len(file_bytes) - 2] & 0xFF) | ((file_bytes[len(file_bytes) - 1] & 0xFF) << 8)

            if checksum != checksum_in_file:
                logger.warning(f"Checksum mismatch in DLC '{name}'")
                projected_size += 2
                checksum = crc16.calc(file_bytes, 0, len(file_bytes))
                checksum_embedded = False

        except IOError:
            logger.error(f"Could not read checksum data for {dlc_file.absolute()}")
            return None

        return Dlc(dlc_file.absolute(), name, game_code, type, index, projected_size, checksum, checksum_embedded)

    def get_dlc_list(self, game_code=None, type=None, index=None):
        if index is not None:
            return [dlc for dlc in self.dlc_list if
                    dlc.game_code == game_code and
                    dlc.type == type and
                    dlc.index == index]

        elif type is not None:
            return [dlc for dlc in self.dlc_list if
                    dlc.game_code == game_code and
                    dlc.type == type]

        elif game_code is not None:
            return [dlc for dlc in self.dlc_list if
                    dlc.game_code == game_code]

        else:
            return self.dlc_list.copy()

    def get_dlc_list_string(self, dlc_list: List[Dlc]):
        string_list = [f"{dlc.name}\t\t{dlc.type}\t{dlc.index}\t\t{dlc.projected_size}\r\n" for dlc in dlc_list]
        return ''.join(string_list)

    def get_dlc(self, game_code: str, type: str, name: str):
        dlc_list = [dlc for dlc in self.get_dlc_list(game_code, type)
                    if dlc.name == name]

        return None if len(dlc_list) == 0 else dlc_list[0]

    def get_dlc_index(self, game_code: str, type: str, name: str):
        dlc = self.get_dlc(game_code, type, name)
        return 0 if dlc is None else dlc.index