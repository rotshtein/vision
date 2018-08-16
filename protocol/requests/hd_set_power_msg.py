from protocol.bytes_converter import IBytesConverter


class HDSetPowerMessage(IBytesConverter):
    def __init__(self, power_cmd) -> None:
        super().__init__()
        self.power_cmd = power_cmd
        self.opcode = b'xB7'

    def to_bytes(self):
        power_cmd = bool.to_bytes(self.power_cmd, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
        return power_cmd

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        pass
