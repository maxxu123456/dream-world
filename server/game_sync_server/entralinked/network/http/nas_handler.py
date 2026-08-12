#!/usr/bin/env python3
import logging

from enum import Enum
from datetime import datetime
from flask import request, Blueprint
from dataclasses import field, asdict, dataclass

from configuration import Configuration
from model.user.user_manager import UserManager
from utility.url_encoded_form_parser import UrlEncodedFormParser
from utility.url_encoded_form_generator import UrlEncodedFormGenerator

logger = logging.getLogger(__name__)

class NasReturnCode(Enum):
    SUCCESS = 1
    INTERNAL_SERVER_ERROR = 100
    REGISTRATION_SUCCESS = 2
    BAD_REQUEST = 102
    USER_ALREADY_EXISTS = 104
    USER_EXPIRED = 108
    USER_NOT_FOUND = 204

    @property
    def formatted_client_id(self) -> str:
        return f"{self.value:03d}"
    
    def __str__(self):
        return self.formatted_client_id

@dataclass
class NasResponse:
    returncd: str = str(NasReturnCode.SUCCESS)
    datetime: str = field(default_factory=lambda: datetime.now().strftime("%y%m%d%H%M%S"))

@dataclass
class NasLoginResponse(NasResponse):
    locator: str = None
    token: str = None
    challenge: str = None

@dataclass
class NasRequest:
    userid: str
    passwd: str
    macadr: str
    action: str

    gamecd: str = None
    makercd: str = None
    unitcd: str = None
    sdkver: str = None
    lang: str = None

    bssid: str = None
    apinfo: str = None
    devname: str = None
    birth: str = None
    devtime: str = field(default_factory=lambda: datetime.now().strftime("%y%m%d%H%M%S"))

    gsbrcd: str = None
    svc: str = None

@dataclass
class NasServiceLocationResponse(NasResponse):
    statusdata: bool = None
    svchost: str = None
    servicetoken: str = None
    
class NasHandler:
    def __init__(self, context):
        self.context = context

        self.configuration: Configuration = self.context.configuration
        self.user_manager: UserManager = self.context.user_manager

    def add_handlers(self):
        blueprint = Blueprint('nas', __name__)

        @blueprint.post('/ac')
        def nas_post():
            return self.handle_nas_request()

        return blueprint

    def handle_nas_request(self):
        raw_data = request.get_data(as_text=True)

        parser = UrlEncodedFormParser(base64_decode_values=True)
        parsed_data = parser.decode(raw_data)

        req = NasRequest(**parsed_data)
        logger.debug(f"Received {req}")
        if req.action == "login":
            return self.handle_login(req)
        elif req.action == "acctcreate":
            return self.handle_create_account(req)
        elif req.action == "SVCLOC":
            return self.handle_retrieve_service_location(req)
        else:
            raise ValueError(f"Invalid POST request action: {req.action}")

    def handle_login(self, req: NasRequest):
        if req.gsbrcd is None:
            logger.debug("Rejecting NAS login request because no branch code is present")
            return self.result(NasReturnCode.BAD_REQUEST)
        
        user = self.user_manager.authenticate_user(req.userid, req.passwd)

        if user is None:
            if not self.configuration.allow_wfc_registration_through_login:
                return self.result(NasReturnCode.USER_NOT_FOUND)
            
            if (not self.user_manager.is_valid_user_id(req.userid) or
                    self.user_manager.does_user_exist(req.userid) or
                    self.user_manager.register_user(req.userid, req.passwd) is None):
                return self.result(NasReturnCode.USER_NOT_FOUND)
            
            user = self.user_manager.authenticate_user(req.userid, req.passwd)
            logger.info(f"Created account for user {user.get_redacted_id()}")

        credentials = self.user_manager.create_service_session(user, "gamespy", req.gsbrcd)
        logger.info(f"Created GameSpy session for user {user.get_redacted_id()}")
        return self.result(NasLoginResponse(locator="gamespy.com", token=credentials.auth_token, challenge=credentials.challenge))

    def handle_create_account(self, req: NasRequest):
        if not self.user_manager.is_valid_user_id(req.userid) or self.user_manager.does_user_exist(req.userid):
            return self.result(NasReturnCode.USER_ALREADY_EXISTS)
        
        user = self.user_manager.register_user(req.userid, req.passwd)

        if user is None:
            return self.result(NasReturnCode.INTERNAL_SERVER_ERROR)
        
        logger.info(f"Created account for user {user.get_redacted_id()}")
        return self.result(NasReturnCode.REGISTRATION_SUCCESS)

    def handle_retrieve_service_location(self, req: NasRequest):
        user = self.user_manager.authenticate_user(req.userid, req.passwd)

        if user is None:
            return self.result(NasReturnCode.USER_NOT_FOUND)
        
        if req.svc == "0000":
            service = "external"
        elif req.svc == "9000":
            service = "dls1.nintendowifi.net"
        else:
            raise ValueError(f"Invalid service type: {req.svc}")
        
        credentials = self.user_manager.create_service_session(user, service, None)
        logger.info(f"Created {'PGL' if req.svc == '0000' else 'DSL1'} sessions for user {user.get_redacted_id()}")

        return self.result(NasServiceLocationResponse(statusdata='Y', svchost=service, servicetoken=credentials.auth_token))

    def result(self, response):
        if isinstance(response, NasReturnCode):
            return self.result(NasResponse(returncd=response))
        
        response = {k: v for k, v in asdict(response).items() if v is not None}
        
        generator = UrlEncodedFormGenerator(base64_encode_values=True)
        encoded_body = generator.generate(response)

        return encoded_body, 200, {"Content-Type": "application/x-www-form-urlencoded"}
