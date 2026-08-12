#!/usr/bin/env python3
from utility import crc16

class GsidUtility:

    GSID_CHARTABLE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    @staticmethod
    def stringify_gamesync_id(gsid: int):
        output = []

        checksum = crc16.calc(gsid)
        ugsid = gsid | (checksum << 32)

        for i in range(10):
            index = ((ugsid >> (5 * i)) & 0x1F)
            output.append(GsidUtility.GSID_CHARTABLE[index])

        return ''.join(output)

    @staticmethod
    def is_valid_gamesync_id(gsid: str):
        if gsid is None:
            return False

        length = len(gsid)
        ugsid = 0

        if length != 10:
            return False

        for i, char in enumerate(gsid):
            index = GsidUtility.GSID_CHARTABLE.find(char)

            if index == -1:
                return False

            ugsid |= index << (5 * i)

        output = ugsid & 0xFFFFFFFF
        checksum = ((ugsid >> 32) & 0xFFFF)

        return output < 0x80000000 and crc16.calc(output) == checksum