class IBytesConverter(object):
    """
    Interface only
    """
    def to_bytes(self):
        pass

    def from_bytes(self, data):
        pass


def calc_checksum(data):
    crc = 0
    for i in range(data.len):
        crc+= data[i]
        i += 1
    return ~crc