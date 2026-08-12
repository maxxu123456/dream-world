#!/usr/bin/env python3
import logging

import re
import json
import random
import hashlib
from typing import Dict
from dataclasses import asdict
from datetime import datetime, timedelta

from model.user.user import User
from model.user.game_profile import GameProfile
from model.user.service import ServiceCredentials, ServiceSession
from utility.credential_generator import CredentialGenerator

from entralinked.paths import ROOT_DIR

logger = logging.getLogger(__name__)

class UserManager:

    user_id_pattern = re.compile("[0-9]{13}")
    data_directory = ROOT_DIR / "save_data"

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.service_sessions: Dict[str, ServiceSession] = {}

        logger.info("Loading user and profile data ...")

        for file in self.data_directory.iterdir():
            if "WFC" not in file.stem:
                continue
            self.load_user(file)

        logger.info(f"Loaded {len(self.users)} user")

    @staticmethod
    def is_valid_user_id(id: str):
        return bool(UserManager.user_id_pattern.fullmatch(id))

    def load_user(self, input_file):
        with open(input_file, "r", encoding="UTF-8") as f:
            data = json.load(f)

        user = User(data["id"], data["password"])
        for branch_code, profile_data in data.get("profiles", {}).items():
            user.add_profile(branch_code, GameProfile(**profile_data))

        self.users[user.id] = user

    def save_users(self):
        for user in self.users.values():
            self.save_user(user)

    def save_user(self, user: User):
        user_data = {
            "id": user.id,
            "password": user.password,
            "profiles": {k: asdict(v) for k, v in user.profiles.items()},
            "dlcOverrides": {k: asdict(v) for k, v in user.dlc_overrides.items()},
            "profileIdOverride": user.profile_id_override
        }

        with open(self.data_directory / f"WFC-{user.id}.json", "w+") as f:
            json.dump(user_data, f, indent=2, ensure_ascii=False)

        return True

    def create_service_session(self, user: User, service: str, branch_code: str):
        auth_token: str = "NDS" + CredentialGenerator.generate_auth_token(96)
        raw_challenge: str = CredentialGenerator.generate_challenge(8)

        challenge = hashlib.md5(raw_challenge.encode("UTF-8")).hexdigest()

        expires_at = datetime.now() + timedelta(minutes=30)

        session = ServiceSession(user, service, branch_code, challenge, expires_at)

        self.service_sessions[auth_token] = session

        return ServiceCredentials(auth_token, raw_challenge)

    def get_service_session(self, auth_token: str, service: str):
        session = self.service_sessions.get(auth_token)

        if session is None:
            return None

        if session.has_expired():
            del self.service_sessions[auth_token]
            return None

        return session if session.service == service else None

    def register_user(self, user_id: str, plain_password: str):
        if user_id in self.users:
            logger.warning(f"Attempted to register user with duplicate ID: {user_id}")

        user = User(user_id, plain_password)

        if not self.save_user(user):
            return None

        self.users[user_id] = user
        return user

    def authenticate_user(self, user_id: str, password: str):
        user = self.users.get(user_id)
        return None if user is None or user.password != password else user

    def create_profile_for_user(self, user: User, branch_code: str):
        if user.get_profile(branch_code) is not None:
            logger.warning(f"Attempted to create duplicate profile {branch_code} in user {user.id}")

        profile_id = random.randint(0, 2 ** 31 - 1)
        profile = GameProfile(profile_id)
        user.add_profile(branch_code, profile)

        if not self.save_user(user):
            user.remove_profile(branch_code)
            return None

        return profile

    def does_user_exist(self, id: str):
        return id in self.users

    def get_users(self):
        return self.users.values()
