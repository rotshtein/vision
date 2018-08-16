from enum import Enum
from protocol.bytes_converter import IBytesConverter


class HDGetStatusResponse(IBytesConverter):

    def __init__(self, sw_version=None, fw_version=None) -> None:
        super().__init__()
        self.sw_version = sw_version
        self.fw_version = fw_version
        self.opcode = b'xC4'

    def to_bytes(self):
        sw_version = int.to_bytes(self.sw_version, 2, byteorder=IBytesConverter.LITTLE_ENDIAN)
        fw_version = int.to_bytes(self.fw_version, 2, byteorder=IBytesConverter.LITTLE_ENDIAN)
        result = sw_version + fw_version
        return result

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        temp_offset = 4
        start_index = 4
        num_of_bytes = 2
        sw_version = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 6
        num_of_bytes = 2
        fw_version = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 8
        num_of_bytes = 1
        checksum = int.from_bytes(data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
                                  byteorder=IBytesConverter.LITTLE_ENDIAN)
        return cls(sw_version, fw_version)
