from protocol.bytes_converter import IBytesConverter


class HDSetupMessage(IBytesConverter):

    def __init__(self, rotate_image_cycle, obstruction_threshold, no_visibility_threshold, medium_visibility_threshold,
                 full_visibility_threshold, minimum_obstruction_hits, maximum_obstruction_hits) -> None:
        super().__init__()
        self.rotate_image_cycle = rotate_image_cycle
        self.obstruction_threshold = obstruction_threshold
        self.no_visibility_threshold = no_visibility_threshold
        self.medium_visibility_threshold = medium_visibility_threshold
        self.full_visibility_threshold = full_visibility_threshold
        self.minimum_obstruction_hits = minimum_obstruction_hits
        self.maximum_obstruction_hits = maximum_obstruction_hits

    def to_bytes(self):
        result = bytearray()
        return result

    def from_bytes(self, data):
        pass
        # super().from_bytes(bytearray)

