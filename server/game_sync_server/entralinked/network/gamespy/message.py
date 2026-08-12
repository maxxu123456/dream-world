#!/usr/bin/env python3
from typing import ClassVar
from dataclasses import dataclass

@dataclass
class GameSpyChallengeMessage:
    GS_NAME: ClassVar[str] = "lc"
    GS_VALUE: ClassVar[str] = "1"

    challenge: str
    id: int

@dataclass
class GameSpyErrorMessage:
    GS_NAME: ClassVar[str] = "error"
    GS_VALUE: ClassVar[str] = ""

    error_code: int
    error_message: str
    fatal: int
    id: int

@dataclass
class GameSpyLoginResponse:
    GS_NAME: ClassVar[str] = "lc"
    GS_VALUE: ClassVar[str] = "2"

    userid: str
    profileid: int
    proof: str
    sesskey: int
    id: int

@dataclass
class GameSpyProfileResponse:
    GS_NAME: ClassVar[str] = "pi"
    GS_VALUE: ClassVar[str] = ""

    profileid: int
    firstname: str
    lastname: str
    aim: str
    zipcode: str
    sig: str
    id: int