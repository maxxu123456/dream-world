#!/usr/bin/env python3

def calc(input_data, offset: int = 0, length = None):
    
    if isinstance(input_data, int):
        input_data = input_data.to_bytes(4, byteorder='little')

    if length is None:
        length = len(input_data)

    crc = 0xFFFF
    for i in range(offset, offset + length):
        crc ^= (input_data[i] << 8)

        for j in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    
    return crc