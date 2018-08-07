from protocol.bytes_converter import IBytesConverter


class HDSetWarningMessage(IBytesConverter):

    def __init__(self, warning_id, polygon, object_class, object_min_w_h,
                 object_max_w_h, minimum_confidence, minimum_detection_hits, maximum_detection_hits, is_default) -> None:
        super().__init__()
        self.warning_id = warning_id
        self.polygon = polygon
        self.object_class = object_class
        self.object_min_w_h = object_min_w_h
        self.object_max_w_h = object_max_w_h
        self.minimum_confidence = minimum_confidence
        self.minimum_detection_hits = minimum_detection_hits
        self.maximum_detection_hits = maximum_detection_hits
        self.is_default = is_default

    def to_bytes(self):
        result = bytearray()
        return result

    def from_bytes(self, data):
        pass
        # super().from_bytes(bytearray)

