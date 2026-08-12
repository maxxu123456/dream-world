#!/usr/bin/env python3
import struct

class LEInputStream:

    def __init__(self, stream):
        self.stream = stream

    def read_short(self):
        return struct.unpack('<h', self.stream.read(2))

    def read_int(self):
        return struct.unpack('<i', self.stream.read(4))

    def read_float(self):
        return struct.unpack('<f', self.stream.read(4))

    def read_long(self):
        return struct.unpack('<q', self.stream.read(8))

    def read_double(self):
        return struct.unpack('<d', self.stream.read(8))

    def read_utf16(self, length: int) -> str:
        chars = []
        read = 0
        
        for _ in range(length):
            c = struct.unpack('<H', self.stream.read(2))
            
            if c == 0xFFFF:
                break
                
            chars.append(chr(c))
            read += 1
            
        remaining_bytes = (length - (read + 1)) * 2
        if remaining_bytes > 0:
            self.stream.read(remaining_bytes)
            
        return "".join(chars)


class LEOutputStream:
    
    def __init__(self, stream):
        self.stream = stream

    def write(self, data, offset=0, length=None):
        if isinstance(data, int):
            self.stream.write(bytes([data & 0xFF]))
        else:
            if length is not None:
                self.stream.write(bytes(data[offset:offset + length]))
            else:
                self.stream.write(bytes(data[offset:]))

    def write_bytes(self, value: int, amount: int):
        self.stream.write(bytes([value & 0xFF]) * amount)

    def write_short(self, value: int):
        self.stream.write(struct.pack('<h', value))

    def write_int(self, value: int):
        self.stream.write(struct.pack('<i', value))

    def write_float(self, value: float):
        self.stream.write(struct.pack('<f', value))

    def write_long(self, value: int):
        self.stream.write(struct.pack('<q', value))

    def write_double(self, value: float):
        self.stream.write(struct.pack('<d', value))