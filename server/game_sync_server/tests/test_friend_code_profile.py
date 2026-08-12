import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


GAME_SYNC_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GAME_SYNC_DIR))
sys.path.insert(0, str(GAME_SYNC_DIR / "entralinked"))

from model.user.user_manager import UserManager


class FriendCodeProfileTest(unittest.TestCase):
    def test_fresh_user_receives_configured_profile_id(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"WFC_PROFILE_ID": "34529433"}
        ):
            with patch.object(UserManager, "data_directory", Path(directory)):
                manager = UserManager()
                user = manager.register_user("1234567890123", "password")
                profile = manager.get_or_create_profile_for_login(user, "IRDO")

                self.assertEqual(profile.id, 34529433)
                saved = json.loads(
                    (Path(directory) / "WFC-1234567890123.json").read_text()
                )
                self.assertEqual(saved["profiles"]["IRDO"]["id"], 34529433)

    def test_existing_single_user_is_repaired_before_login_response(self):
        with tempfile.TemporaryDirectory() as directory:
            save_path = Path(directory) / "WFC-1234567890123.json"
            save_path.write_text(
                json.dumps(
                    {
                        "id": "1234567890123",
                        "password": "password",
                        "profiles": {"IRDO": {"id": 999}},
                    }
                )
            )

            with patch.dict(os.environ, {"WFC_PROFILE_ID": "34529433"}):
                with patch.object(UserManager, "data_directory", Path(directory)):
                    manager = UserManager()
                    user = manager.authenticate_user("1234567890123", "password")
                    profile = manager.get_or_create_profile_for_login(user, "IRDO")

            self.assertEqual(profile.id, 34529433)
            self.assertEqual(
                json.loads(save_path.read_text())["profiles"]["IRDO"]["id"],
                34529433,
            )

    def test_multiple_users_are_not_rewritten_without_an_identity_match(self):
        with tempfile.TemporaryDirectory() as directory:
            for user_id, profile_id in [
                ("1234567890123", 111),
                ("9876543210987", 222),
            ]:
                (Path(directory) / f"WFC-{user_id}.json").write_text(
                    json.dumps(
                        {
                            "id": user_id,
                            "password": "password",
                            "profiles": {"IRDO": {"id": profile_id}},
                        }
                    )
                )

            with patch.dict(os.environ, {"WFC_PROFILE_ID": "34529433"}):
                with patch.object(UserManager, "data_directory", Path(directory)):
                    manager = UserManager()
                    user = manager.authenticate_user("9876543210987", "password")
                    profile = manager.get_or_create_profile_for_login(
                        user, "IRDO", requested_id=222
                    )

            self.assertEqual(profile.id, 222)


if __name__ == "__main__":
    unittest.main()
