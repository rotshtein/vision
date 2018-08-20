from protocol.bytes_converter import IBytesConverter


class HDRemoveWarningMessage(IBytesConverter):
    def __init__(self, warning_id) -> None:
        super().__init__()
        self.warning_id = warning_id
        self.opcode = b'xB3'

    def to_bytes(self):
        warning_id = int.to_bytes(self.warning_id, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
        return warning_id

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        temp_offset = 4
        start_index = 4
        num_of_bytes = 1
        warning_id = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        return cls(warning_id)
