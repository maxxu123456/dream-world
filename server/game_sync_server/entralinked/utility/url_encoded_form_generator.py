import urllib.parse
import base64

class UrlEncodedFormGenerator:
    def __init__(self, base64_encode_values=True):
        self.base64_encode_values = base64_encode_values

    def _encode_value(self, value: str) -> str:
        if self.base64_encode_values:
            byte_data = value.encode('latin1')
            
            b64_str = base64.b64encode(byte_data).decode('ascii')
            
            return b64_str.replace('=', '*').replace('+', '.').replace('/', '-')
        else:
            return urllib.parse.quote(value, safe='')

    def generate(self, data: dict) -> str:
        parts = []
        for key, value in data.items():
            encoded_key = urllib.parse.quote(str(key), safe='')
            encoded_value = self._encode_value(str(value))
            parts.append(f"{encoded_key}={encoded_value}")
        
        return "&".join(parts)