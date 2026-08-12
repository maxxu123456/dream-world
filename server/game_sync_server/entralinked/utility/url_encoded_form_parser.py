#!/usr/bin/env python3
import base64
import logging
from typing import Dict, Any
from urllib.parse import unquote_plus

logger = logging.getLogger(__name__)

class UrlEncodedFormParser:
    def __init__(self, base64_decode_values: bool = True):
        self.base64_decode_values = base64_decode_values

    def decode(self, data: str) -> Dict[str, Any]:
        parsed_data = {}
        
        if not data:
            return parsed_data

        pairs = data.split('&')
        
        for pair in pairs:
            if '=' not in pair:
                continue
                
            key, value = pair.split('=', 1)
            
            decoded_key = unquote_plus(key)
            decoded_value = unquote_plus(value)
            
            if self.base64_decode_values:
                encoded_value = decoded_value.replace('*', '=')
                try:
                    decoded_value = base64.b64decode(encoded_value).decode('utf-8')
                except Exception:
                    pass
            
            parsed_data[decoded_key] = decoded_value
            
        return parsed_data