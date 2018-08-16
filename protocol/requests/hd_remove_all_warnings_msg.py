from protocol.bytes_converter import IBytesConverter


class HDRemoveAllWarningsMessage(IBytesConverter):
    def __init__(self) -> None:
        super().__init__()
        self.opcode = b'xB4'

    def to_bytes(self):
        result = bytearray()
        return result

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        pass
        # super().from_bytes(bytearray)
