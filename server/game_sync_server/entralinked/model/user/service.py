#!/usr/bin/env python3
from datetime import datetime
from dataclasses import dataclass

from model.user.user import User

@dataclass
class ServiceCredentials:
    auth_token: str
    challenge: str

@dataclass
class ServiceSession:
    user: User
    service: str
    branch_code: str
    challenge_hash: str
    expiry: datetime

    def has_expired(self):
        return datetime.now() > self.expiry
