#!/usr/bin/env python3
import logging
import secrets
import hashlib
import socket
import socketserver

from model.user.user import User
from model.user.user_manager import UserManager
from model.user.game_profile import GameProfile

from network.gamespy.message import (
    GameSpyChallengeMessage,
    GameSpyErrorMessage,
    GameSpyLoginResponse,
    GameSpyProfileResponse
)
from network.gamespy.request import (
    GameSpyLoginRequest,
    GameSpyProfileRequest,
    GameSpyProfileUpdateRequest
)
from utility.credential_generator import CredentialGenerator
from network.gamespy.encoder_decoder import GameSpyMessageEncoder, GameSpyRequestDecoder

logger = logging.getLogger(__name__)

class GameSpyHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.user_manager: UserManager = self.server.context.user_manager
        
        self.server_challenge: str = None
        self.session_key: int = -1
        self.user: User = None
        self.profile: GameProfile = None

        self.decoder = GameSpyRequestDecoder()
        self.encoder = GameSpyMessageEncoder()

        logger.info("Sending GameSpy server challenge")
        
        self.server_challenge = CredentialGenerator.generate_challenge(10)
        
        self.send_message(GameSpyChallengeMessage(self.server_challenge, 1))

    def handle(self):
        self.request.settimeout(180.0) 
        
        buffer = bytearray()
        delimiter = b"\\final\\"
        
        try:
            while True:
                data = self.request.recv(512) 
                
                if not data:
                    break
                    
                buffer.extend(data)
                
                while delimiter in buffer:
                    message_bytes, _, remaining_buffer = buffer.partition(delimiter)
                    
                    buffer = remaining_buffer
                    
                    full_message_bytes = message_bytes + delimiter
                    
                    request_obj = self.decoder.decode(full_message_bytes)
                    if request_obj:
                        request_obj.process(self)

        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            user_id = self.user.get_redacted_id() if self.user else None
            logger.info(f"User {user_id} timed out or connection was reset")
        
        except Exception as e:
            logger.error("Exception caught in GameSpy handler", exc_info=e)
            self.send_error_message(0x100, "An internal error occurred on the server.", 0, fatal=True)
    
    def finish(self):
        user_id = self.user.get_redacted_id() if self.user else None
        logger.info(f"User {user_id} disconnected from GameSpy server")
        
        self.server_challenge = None
        self.session_key = -1
        self.user = None
        self.profile = None

    def handle_login_request(self, req: GameSpyLoginRequest):
        auth_token = req.authtoken
        client_challenge = req.challenge
        
        session = self.user_manager.get_service_session(auth_token, "gamespy")
        
        if session is None:
            logger.info("Rejecting GameSpy login request because the partner token is invalid")
            self.send_error_message(0x200, "Invalid partner token.", req.id)
            return

        partner_challenge_hash = session.challenge_hash
        expected_response = self.create_credential_hash(
            partner_challenge_hash, auth_token, client_challenge, self.server_challenge
        )
        
        if expected_response != req.response:
            logger.info("Rejecting GameSpy login request because the challenge response is invalid")
            self.send_error_message(0x202, "Invalid response.", req.id)
            return

        self.user = session.user
        self.profile = self.user.get_profile(session.branch_code)
        
        if self.profile is None:
            self.profile = self.user_manager.create_profile_for_user(self.user, session.branch_code)
            
            if self.profile is None:
                self.send_error_message(0x203, "Profile creation failed due to an error.", req.id)
                return

        profile_id_override = self.user.profile_id_override
        
        if profile_id_override > 0:
            self.profile.set_id(profile_id_override)
            self.user.set_profile_id_override(0)
            self.user_manager.save_user(self.user)

        logger.info(f"User {self.user.get_redacted_id()} logged in with profile {self.profile.id}")

        self.session_key = secrets.randbits(31) 
        proof = self.create_credential_hash(
            partner_challenge_hash, auth_token, self.server_challenge, client_challenge
        )
        
        self.send_message(GameSpyLoginResponse(
            self.user.id,
            self.profile.id, 
            proof, 
            self.session_key,
            req.id
        ))

    def handle_profile_request(self, req: GameSpyProfileRequest):
        self.send_message(GameSpyProfileResponse(
            self.profile.id,
            self.profile.first_name,
            self.profile.last_name,
            self.profile.aim_name,
            self.profile.zip_code,
            "signature",
            req.id
        ))

    def handle_update_profile_request(self, req: GameSpyProfileUpdateRequest):
        profile_changed = False

        if req.firstname is not None and req.firstname != self.profile.first_name:
            self.profile.first_name = req.firstname
            profile_changed = True
            
        if req.lastname is not None and req.lastname != self.profile.last_name:
            self.profile.last_name = req.lastname
            profile_changed = True
            
        if req.aim is not None and req.aim != self.profile.aim_name:
            self.profile.aim_name = req.aim
            profile_changed = True
            
        if req.zipcode is not None and req.zipcode != self.profile.zip_code:
            self.profile.zip_code = req.zipcode
            profile_changed = True

        if profile_changed:
            self.user_manager.save_user(self.user)

    def create_credential_hash(self, password_hash: str, user: str, in_challenge: str, out_challenge: str) -> str:
        padding = " " * 48
        raw_string = f"{password_hash}{padding}{user}{in_challenge}{out_challenge}{password_hash}"
        return hashlib.md5(raw_string.encode("UTF-8")).hexdigest()

    def handle_logout(self):
        user_id = self.user.get_redacted_id() if self.user else None
        profile_id = self.profile.id if self.profile else None
        logger.info(f"User {user_id} logged out of profile {profile_id}")
        self.session_key = -1

    def validate_session_key(self, session_key: int, id: int = 0) -> bool:
        if session_key < 0 or self.session_key != session_key:
            self.send_error_message(0x201, "Invalid session key.", id)
            return False
        return True

    def send_message(self, message: object):
        try:
            data_bytes = self.encoder.encode(message)
            self.request.sendall(data_bytes)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def send_error_message(self, error_code: int, error_message: str, id: int, fatal: bool = False):
        self.send_message(GameSpyErrorMessage(
            error_code, 
            error_message, 
            1 if fatal else 0, 
            id
        ))

    def close(self):
        try:
            self.request.shutdown(socket.SHUT_RDWR)
            self.request.close()
        except OSError:
            pass
