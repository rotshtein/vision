class IBytesConverter(object):
    """
    Interface only
    """

    LITTLE_ENDIAN = 'little'
    LITTLE_ENDIAN_SIGN = '<'
    BIG_ENDIAN = 'big'
    BIG_ENDIAN_SIGN = '>'

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        pass


def calc_checksum(data):
    crc = 0
    for i in range(len(data)):
        crc += data[i]
        i += 1
    crc = ~crc % 256
    return int.to_bytes(crc, 1, byteorder=IBytesConverter.LITTLE_ENDIAN, signed=False)
