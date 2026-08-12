#!/usr/bin/env python3
import secrets

class CredentialGenerator:

    CHALLENGE_CHARTABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    
    def __init__(self):
        pass

    @staticmethod
    def generate_challenge(length: int):
        challenge = []

        for i in range(length):
            challenge.append(CredentialGenerator.CHALLENGE_CHARTABLE[secrets.randbelow(len(CredentialGenerator.CHALLENGE_CHARTABLE))])

        return ''.join(challenge)
    
    @staticmethod
    def generate_auth_token(length: int):
        return secrets.token_urlsafe(length)