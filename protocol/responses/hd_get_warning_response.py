from enum import Enum

from bitarray import bitarray
from protocol.bytes_converter import IBytesConverter


class HDGetWarningResponse(IBytesConverter):

    def __init__(self, warnings: []=None, visibility_light_level=None, is_obstructed=None) -> None:
        super().__init__()
        self.warnings = warnings  # type: [bool]
        self.visibility_light_level = visibility_light_level  # type: VisibilityLightLevel
        self.is_obstructed = is_obstructed  # type: bool
        self.opcode = b'xC1'

    def __str__(self):
        return "warnings={}. visibility_light_level={}. is_obstructed={}".format(self.warnings, self.visibility_light_level, self.is_obstructed)

    def to_bytes(self):
        warning_bits1 = bitarray(self.warnings[0:8], endian=IBytesConverter.LITTLE_ENDIAN)
        warning_bits2 = bitarray(self.warnings[8:16], endian=IBytesConverter.LITTLE_ENDIAN)
        is_vision_bit_1 = False
        is_vision_bit_2 = False
        if self.visibility_light_level == VisibilityLightLevel.NO_VISIBILITY_TO_MEDIUM:
            is_vision_bit_1 = True
        elif self.visibility_light_level == VisibilityLightLevel.MEDIUM_TO_FULL:
            is_vision_bit_1 = False
            is_vision_bit_2 = True
        else:
            is_vision_bit_1 = True
            is_vision_bit_2 = True
        vision_bits = bitarray([is_vision_bit_1, is_vision_bit_2, self.is_obstructed, None, None, None, None, None], endian=IBytesConverter.LITTLE_ENDIAN)
        result = warning_bits1 + warning_bits2 + vision_bits
        return result.tobytes()

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        pass

class VisibilityLightLevel(Enum):
    NO_VISIBILITY = 0
    NO_VISIBILITY_TO_MEDIUM = 1
    MEDIUM_TO_FULL = 2
    FULL_VISIBILITY = 3


if __name__ == '__main__':
    response = HDGetWarningResponse([True] * 7)
    print(response.to_bytes())
