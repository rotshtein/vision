from protocol.bytes_converter import IBytesConverter


class HDGetSetupConfigMessage(IBytesConverter):
    def __init__(self) -> None:
        super().__init__()
        self.opcode = b'xBA'

    def to_bytes(self):
        result = bytearray()
        return result

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        pass
        # super().from_bytes(bytearray)
