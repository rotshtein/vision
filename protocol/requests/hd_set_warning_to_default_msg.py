from protocol.bytes_converter import IBytesConverter


class HDSetWarningToDefaultMessage(IBytesConverter):
    def __init__(self, warning_id, all_warnings) -> None:
        super().__init__()
        self.warning_id = warning_id
        self.all_warnings = all_warnings
        self.opcode = b'xB6'

    def to_bytes(self):
        warning_id = int.to_bytes(self.warning_id, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
        all_warnings = bool.to_bytes(self.all_warnings, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
        return warning_id + all_warnings

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        pass
        # super().from_bytes(bytearray)
