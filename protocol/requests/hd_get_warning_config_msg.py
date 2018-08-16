from protocol.bytes_converter import IBytesConverter


class HDGetWarningConfigMessage(IBytesConverter):
    def __init__(self, warning_id) -> None:
        super().__init__()
        self.warning_id = warning_id
        self.opcode = b'xB9'

    def to_bytes(self):
        warning_id = int.to_bytes(self.warning_id, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
        return warning_id

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        pass
