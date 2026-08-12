import os
import json
import sqlite3
import threading
from pathlib import Path
from itertools import product

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

def fix_ownership(path):
    uid = os.environ.get("SUDO_UID")
    gid = os.environ.get("SUDO_GID")

    if uid and gid:
        os.chown(path, int(uid), int(gid))

class DBManager:
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._local = threading.local()

        conn = self._make_conn()

        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS player_saves (
                    gscd TEXT PRIMARY KEY,
                    player_data TEXT,
                    sleeping_pokemon TEXT,
                    game_sync TEXT,
                    crop_data TEXT,
                    chest_data TEXT
                )""")

        fix_ownership(self._db_path)

        conn.close()

    def _make_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=10.0)

        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

        conn.row_factory = sqlite3.Row

        return conn

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._make_conn()
        return self._local.conn

    def _validate_column(self, column: str):
        valid_columns = [
            "player_data", "sleeping_pokemon", "game_sync",
            "wfc_profile", "crop_data", "chest_data"
        ]
        if column not in valid_columns:
            raise ValueError(f"Invalid column name: '{column}'")

    def write_gscd(self, gscd: str):
        empty_crop = {
            "croft_list": [
                {
                    "my_croft_id": 1000 + i,
                    "x": x + 1,
                    "y": y + 1,
                }
                for i, (y, x) in enumerate(product(range(2), range(3)))
            ],
            "diglett_flag": 0,
        }

        empty_chest = {
            "cnt": 64,
            "list": [
                {
                    "pokeitem_id": berry_id + 148,
                    "item_cnt": 99,
                    "date": "2000-01-01"
                }
                for berry_id in range(1, 65)
            ]
        }

        query = "INSERT OR IGNORE INTO player_saves (gscd, crop_data, chest_data) VALUES (?, ?, ?)"
        with self._conn:
            self._conn.execute(query,
                               (str(gscd),
                                json.dumps(empty_crop, indent=2),
                                json.dumps(empty_chest, indent=2))
                                )

    def write(self, gscd: str, column: str, data: dict):
        self._validate_column(column)
        query = f"""
            INSERT INTO player_saves (gscd, {column})
            VALUES (?, ?)
            ON CONFLICT(gscd) DO UPDATE SET {column} = excluded.{column};
        """
        with self._conn:
            if data is None:
                self._conn.execute(query, (str(gscd), None))
            else:
                self._conn.execute(query, (str(gscd), json.dumps(data, indent=2, ensure_ascii=False)))

    def read(self, gscd: str, column: str) -> dict | None:
        self._validate_column(column)

        query = f"SELECT {column} FROM player_saves WHERE gscd = ?"

        cursor = self._conn.execute(query, (str(gscd),))
        row = cursor.fetchone()

        if row and row[column]:
            return json.loads(row[column])

        return None

    def does_gsid_exists(self, gsid: str) -> bool:
        query = "SELECT 1 FROM player_saves WHERE gscd = ? LIMIT 1"
        cursor = self._conn.execute(query, (gsid,))
        return cursor.fetchone() is not None

    def write_full_state(self, gscd: str, player_data: dict, game_sync: dict, sleeping_pokemon: dict):
        query = """
            INSERT INTO player_saves (gscd, player_data, game_sync, sleeping_pokemon)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(gscd) DO UPDATE SET
                player_data = excluded.player_data,
                game_sync = excluded.game_sync,
                sleeping_pokemon = excluded.sleeping_pokemon
        """
        with self._conn:
            self._conn.execute(query, (
                str(gscd),
                json.dumps(player_data, indent=2, ensure_ascii=False),
                json.dumps(game_sync, indent=2, ensure_ascii=False),
                json.dumps(sleeping_pokemon, indent=2, ensure_ascii=False)
            ))

    def read_full_state(self, gscd: str) -> dict | None:
        query = "SELECT player_data, game_sync, sleeping_pokemon FROM player_saves WHERE gscd = ?"
        cursor = self._conn.execute(query, (str(gscd),))
        row = cursor.fetchone()
        if row:
            return [
                json.loads(row["player_data"]) if row["player_data"] else None,
                json.loads(row["game_sync"]) if row["game_sync"] else None,
                json.loads(row["sleeping_pokemon"]) if row["sleeping_pokemon"] else None,
            ]
        return None

    def close(self):
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

Path(ROOT_DIR / "save_data").mkdir(exist_ok=True)
fix_ownership(Path(ROOT_DIR / "save_data"))
db = DBManager(Path(ROOT_DIR / "save_data" / "pokemon_saves.db"))