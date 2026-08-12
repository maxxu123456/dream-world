#!/usr/bin/env python3
import logging

import io
import json
from http import HTTPStatus
from flask import request, Blueprint, g
from dataclasses import dataclass

from model.dlc.dlc import DlcList
from model.user.user_manager import UserManager
from utility.le_input_output import LEOutputStream

logger = logging.getLogger(__name__)

@dataclass
class DlsRequest:
    userid: str
    passwd: str
    macadr: str
    token: str
    action: str

    rhgamecd: str = None
    apinfo: str = None

    gamecd: str = None
    contents: str = None
    attr1: str = None
    attr2: int = None
    offset: int = None
    num: int = None

class DlsHandler:
    def __init__(self, context):
        self.context = context

        self.dlc_list = self.context.dlc_list
        self.user_manager = self.context.user_manager

    def add_handlers(self) -> Blueprint:
        blueprint = Blueprint('dls', __name__)

        @blueprint.post('/download')
        def dls_post():
            return self.handle_download_request()

        return blueprint

    def handle_download_request(self):
        req = json.loads(request.get_data(as_text=True).replace("%2A", "*"))

        req = DlsRequest(
            userid = req["userid"],
            passwd = req["passwd"],
            macadr = req["macadr"],
            token = req["token"],
            action = req["action"],
            rhgamecd = req.get("rhgamecd"),
            apinfo = req.get("apinfo"),
            gamecd = req.get("gamecd"),
            contents = req.get("contents"),
            attr1 = req.get("attr1"),
            attr2 = int(req["attr2"]) if "attr2" in req else None,
            offset = int(req["offset"]) if "offset" in req else None,
            num = int(req["num"]) if "num" in req else None
        )
        logger.debug(f"Received {req}")

        session = self.user_manager.get_service_session(req.token, "dls1.nintendowifi.net")

        if session is None:
            logger.debug("Rejecting DLS request because the service session has expired")
            return HTTPStatus.UNAUTHORIZED

        g.session_user = session.user

        handlers = {
            "list": self.handle_retrieve_dlc_list,
            "contents": self.handle_retrieve_dlc_content
        }

        handler = handlers.get(req.action)

        if handler is None:
            logger.error(f"Invalid POST request type: {req.action}")
            return HTTPStatus.BAD_REQUEST

        return handler(req)

    def handle_retrieve_dlc_list(self, req: DlsRequest):
        user = g.session_user
        game_code = self.get_dlc_game_code(req.gamecd)
        dlc_type = self.get_regionless_dlc_type(req.attr1)

        if user.has_dlc_override(dlc_type):
            override = user.get_dlc_override(dlc_type)
            result = self.dlc_list.get_dlc_list_string([override])
            return result

        return_list = self.dlc_list.get_dlc_list(game_code, dlc_type, req.attr2)
        return self.dlc_list.get_dlc_list_string(return_list)

    def handle_retrieve_dlc_content(self, req: DlsRequest):
        user = g.session_user
        game_code = self.get_dlc_game_code(req.gamecd)
        dlc_type = self.get_regionless_dlc_type(req.attr1)

        dlc = user.get_dlc_override(dlc_type) if user.has_dlc_override(dlc_type) else self.dlc_list.get_dlc(game_code, dlc_type, req.contents)

        if dlc is None:
            return HTTPStatus.NOT_FOUND

        output = LEOutputStream(io.BytesIO())
        with open(dlc.path, "rb") as input_stream:
            output.write(input_stream.read())

        if not dlc.checksum_embedded:
            output.write_short(dlc.checksum)

    def get_dlc_game_code(self, game_code: str):
        if game_code in ("IRAJ", "IRAK"):
            return "IRAO"
        else:
            return game_code

    def get_regionless_dlc_type(self, dlc_type: str):
        if dlc_type.startswith("CGEAR2"):
            return "CGEAR2"
        elif dlc_type.startswith("CGEAR"):
            return "CGEAR"
        elif dlc_type.startswith("ZUKAN"):
            return "ZUKAN"
        elif dlc_type.startswith("MUSICAL"):
            return "MUSICAL"
        else:
            return dlc_type
