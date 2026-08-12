#!/usr/bin/env python3
from typing import ClassVar
from dataclasses import dataclass

class GameSpyKeepAliveRequest:
    COMMAND: ClassVar[str] = "ka"

    def process(self, handler):
        pass

@dataclass
class GameSpyLoginRequest:
    COMMAND: ClassVar[str] = "login"

    response: str
    challenge: str
    authtoken: str
    id: int

    userid: str = None
    gamename: str = None
    profileid: int = None
    namespaceid: int = None
    partnerid: int = None
    productid: int = None
    sdkrevision: int = None
    firewall: int = None
    port: int = None
    quiet: int = None

    def process(self, handler):
        return handler.handle_login_request(self)

    def to_string(self):
        return f"GameSpyLoginRequest[sequenceId={self.id}, gameName={self.gamename}, profileId={self.profileid}, namespaceId={self.namespaceid}, partnerId={self.partnerid}, productId={self.productid}, sdkRevision={self.sdkrevision}, firewall={self.firewall}, port={self.port}, quiet={self.quiet}]"
    
@dataclass
class GameSpyLogoutRequest:
    COMMAND: ClassVar[str] = "logout"
    
    sesskey: int

    def process(self, handler):
        if handler.validate_session_key(self.sesskey):
            return handler.handle_logout()

    def to_string(self):
        return "GameSpyLogoutRequest[]"
    
@dataclass
class GameSpyProfileRequest:
    COMMAND: ClassVar[str] = "getprofile"

    sesskey: int
    id: int
    profileid: int

    def process(self, handler):
        if handler.validate_session_key(self.sesskey, self.id):
            return handler.handle_profile_request(self)

    def to_string(self):
        return f"GameSpyProfileRequest[sequenceId={self.id}, profileId={self.profileid}]"
    
@dataclass
class GameSpyProfileUpdateRequest:
    COMMAND: ClassVar[str] = "updatepro"

    sesskey: int
    partnerid: int

    firstname: str = None
    lastname: str = None
    aim: str = None
    zipcode: str = None

    def process(self, handler):
        if handler.validate_session_key(self.sesskey):
            return handler.handle_update_profile_request(self)

    def to_string(self):
        return f"GameSpyProfileUpdateRequest[partnerId={self.partnerid}]"
    
@dataclass
class GameSpyStatusRequest:
    COMMAND: ClassVar[str] = "status"

    sesskey: int
    statstring: str = None
    locstring: str = None

    def process(self, handler):
        return handler.validate_session_key(self.sesskey)
    
    def to_string(self):
        return "GameSpyStatusRequest[]"