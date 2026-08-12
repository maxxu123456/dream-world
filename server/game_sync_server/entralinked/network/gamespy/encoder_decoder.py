#!/usr/bin/env python3
import io
from typing import Type, Any
from dataclasses import fields, is_dataclass, asdict
from network.gamespy.request import GameSpyKeepAliveRequest, GameSpyLoginRequest, GameSpyLogoutRequest, GameSpyStatusRequest, GameSpyProfileRequest, GameSpyProfileUpdateRequest

class GameSpyMessageEncoder:

    def encode(self, message: object) -> bytes:
        if not hasattr(message, "GS_NAME") or not hasattr(message, "GS_VALUE"):
            raise ValueError(f"Outbound message type '{type(message).__name__}' must have the GameSpyMessage annotation.")
            
        gs_name = getattr(message, "GS_NAME")
        gs_value = getattr(message, "GS_VALUE")
        
        stream = io.BytesIO()
        
        stream.write(b'\\')
        self._write_string(stream, gs_name)
        stream.write(b'\\')
        self._write_string(stream, gs_value)
        
        stream.write(self._serialize(message))
        
        self._write_string(stream, "\\final\\")
        
        return stream.getvalue()

    def _write_string(self, stream: io.BytesIO, string: str) -> None:
        stream.write(string.encode("UTF-8"))

    @staticmethod
    def _to_camel_case(key: str) -> str:
        parts = key.split("_")
        return parts[0] + ''.join(p.title() for p in parts[1:])

    def _serialize(self, message: object) -> bytes:
        if not is_dataclass(message):
            return b''
            
        serialized_data = io.BytesIO()
        
        for key, value in asdict(message).items():
            key = self._to_camel_case(key)
            if value is not None:
                serialized_data.write(f"\\{key}\\{value}".encode("UTF-8"))
                
        return serialized_data.getvalue()
    
class GameSpyRequestDecoder:

    def __init__(self):
        self.request_types = {
            GameSpyKeepAliveRequest.COMMAND: GameSpyKeepAliveRequest,
            GameSpyLoginRequest.COMMAND: GameSpyLoginRequest,
            GameSpyLogoutRequest.COMMAND: GameSpyLogoutRequest,
            GameSpyProfileRequest.COMMAND: GameSpyProfileRequest,
            GameSpyProfileUpdateRequest.COMMAND: GameSpyProfileUpdateRequest,
            GameSpyStatusRequest.COMMAND: GameSpyStatusRequest,
        }

    def decode(self, data: bytes) -> Any:
        stream = io.BytesIO(data)
        
        first_byte = stream.read(1)
        if first_byte != b'\\':
            got = first_byte.decode("UTF-8", errors='ignore') if first_byte else 'EOF'
            raise ValueError(f"Was expecting '\\', got '{got}'.")
            
        type_name = self._parse_string(stream, allow_eoi=False)
        request_type = self.request_types.get(type_name)
        
        if request_type is None:
            raise ValueError(f"Invalid or unimplemented request type '{type_name}'")
            
        remaining_length = len(data) - stream.tell()
        if remaining_length > 0:
            self._parse_string(stream, allow_eoi=True)
            
        remaining_length = len(data) - stream.tell()
        
        if remaining_length > 0:
            raw_bytes = b'\\' + stream.read()
            return self._deserialize(raw_bytes, request_type)
        else:
            return request_type()

    def _parse_string(self, stream: io.BytesIO, allow_eoi: bool):
        builder = bytearray()
        
        while True:
            b = stream.read(1)
            
            if not b:
                if allow_eoi:
                    break
                
            if b == b'\\':
                break
                
            builder.extend(b)
            
        return builder.decode("UTF-8")

    def _deserialize(self, data: bytes, request_type: Type) -> Any:
        
        if not is_dataclass(request_type):
            return request_type()
        
        text = data.decode('utf-8', errors='ignore').strip('\\')
        parts = text.split('\\')
        
        raw_dict = dict(zip(parts[0::2], parts[1::2]))
        
        kwargs = {}
        
        for field in fields(request_type):
            if field.name in raw_dict:
                raw_value = raw_dict[field.name]
                try:
                    kwargs[field.name] = field.type(raw_value)
                except (ValueError, TypeError):
                    kwargs[field.name] = raw_value
                    
        return request_type(**kwargs)
