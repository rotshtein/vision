from enum import Enum
from protocol.bytes_converter import IBytesConverter


class HDWarningResponse(IBytesConverter):

    def __init__(self, hd_fw_version, warnings, visibility_light_level, is_obstructed) -> None:
        super().__init__()
        self.hd_fw_version = hd_fw_version
        self.warnings = warnings
        self.visibility_light_level = visibility_light_level
        self.is_obstructed = is_obstructed

    def to_bytes(self):
        result = bytearray()
        return result

    def from_bytes(self, data):
        pass
        # super().from_bytes(bytearray)


class VisibilityLightLevel(Enum):
    NO_VISIBILITY = 0
    NO_VISIBILITY_TO_MEDIUM = 1
    MEDIUM_TO_FULL = 2
    FULL_VISIBILITY = 3

