"""Static utility methods"""


def parse_32bit_little_endian(data: bytes) -> int:
    return data[0] | data[1] << 8 | data[2] << 16 | data[3] << 24
