from enum import Enum
from protocol.bytes_converter import IBytesConverter


class HDGetSetupConfigResponse(IBytesConverter):

    def __init__(self, rotate_image_cycle=None, obstruction_threshold=None, no_visibility_threshold=None,
                 medium_visibility_threshold=None, full_visibility_threshold=None, minimum_obstruction_hits=None,
                 maximum_obstruction_hits=None, logging_debug=None, show_images=None, save_images_to_disk=None,
                 draw_polygons=None, activate_buzzer=None, rotate_degree=None) -> None:
        super().__init__()
        # human detection fields:
        self.rotate_image_cycle = rotate_image_cycle

        # vision fields:
        self.obstruction_threshold = obstruction_threshold
        self.no_visibility_threshold = no_visibility_threshold
        self.medium_visibility_threshold = medium_visibility_threshold
        self.full_visibility_threshold = full_visibility_threshold
        self.minimum_obstruction_hits = minimum_obstruction_hits
        self.maximum_obstruction_hits = maximum_obstruction_hits
        self.logging_debug = logging_debug
        self.show_images = show_images
        self.save_images_to_disk = save_images_to_disk

        self.draw_polygons = draw_polygons
        self.activate_buzzer = activate_buzzer
        self.rotate_degree = rotate_degree

        self.opcode = b'xC3'

    def __str__(self):
        return str([self.rotate_image_cycle, self.obstruction_threshold, self.no_visibility_threshold,
                    self.medium_visibility_threshold, self.full_visibility_threshold, self.minimum_obstruction_hits,
                    self.maximum_obstruction_hits, self.logging_debug, self.show_images, self.save_images_to_disk,
                    self.draw_polygons, self.activate_buzzer, self.rotate_degree])

    def to_bytes(self):
        rotate_image_cycle = int.to_bytes(self.rotate_image_cycle, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
        obstruction_threshold = int.to_bytes(self.obstruction_threshold, 2, byteorder=IBytesConverter.LITTLE_ENDIAN)
        no_visibility_threshold = int.to_bytes(self.no_visibility_threshold, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
        medium_visibility_threshold = int.to_bytes(self.medium_visibility_threshold, 1,
                                                   byteorder=IBytesConverter.LITTLE_ENDIAN)
        full_visibility_threshold = int.to_bytes(self.full_visibility_threshold, 1,
                                                 byteorder=IBytesConverter.LITTLE_ENDIAN)
        minimum_obstruction_hits = int.to_bytes(self.minimum_obstruction_hits, 1,
                                                byteorder=IBytesConverter.LITTLE_ENDIAN)
        maximum_obstruction_hits = int.to_bytes(self.maximum_obstruction_hits, 1,
                                                byteorder=IBytesConverter.LITTLE_ENDIAN)
        logging_debug = bool.to_bytes(self.logging_debug, 1,
                                      byteorder=IBytesConverter.LITTLE_ENDIAN)
        show_images = bool.to_bytes(self.show_images, 1,
                                    byteorder=IBytesConverter.LITTLE_ENDIAN)
        save_images_to_disk = bool.to_bytes(self.save_images_to_disk, 1,
                                            byteorder=IBytesConverter.LITTLE_ENDIAN)
        draw_polygons = bool.to_bytes(self.draw_polygons, 1,
                                      byteorder=IBytesConverter.LITTLE_ENDIAN)
        activate_buzzer = bool.to_bytes(self.activate_buzzer, 1,
                                        byteorder=IBytesConverter.LITTLE_ENDIAN)
        rotate_degree = bool.to_bytes(self.rotate_degree, 1,
                                      byteorder=IBytesConverter.LITTLE_ENDIAN)
        result = rotate_image_cycle + obstruction_threshold + no_visibility_threshold + medium_visibility_threshold \
                 + full_visibility_threshold + minimum_obstruction_hits + maximum_obstruction_hits + logging_debug \
                 + show_images + save_images_to_disk + draw_polygons + activate_buzzer + rotate_degree
        # result = bytearray([self.rotate_image_cycle, self.obstruction_threshold, self.no_visibility_threshold,
        #                     self.medium_visibility_threshold, self.full_visibility_threshold,
        #                     self.minimum_obstruction_hits, self.maximum_obstruction_hits])
        return result

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        temp_offset = 4
        start_index = 4
        num_of_bytes = 1
        rotate_image_cycle = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 5
        num_of_bytes = 2
        obstruction_threshold = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 7
        num_of_bytes = 1
        no_visibility_threshold = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 8
        num_of_bytes = 1
        medium_visibility_threshold = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 9
        num_of_bytes = 1
        full_visibility_threshold = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 10
        num_of_bytes = 1
        minimum_obstruction_hits = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 11
        num_of_bytes = 1
        maximum_obstruction_hits = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 12
        num_of_bytes = 1
        logging_debug = int.from_bytes(data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
                                       byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 13
        num_of_bytes = 1
        show_images = int.from_bytes(data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
                                     byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 14
        num_of_bytes = 1
        save_images_to_disk = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 15
        num_of_bytes = 1
        draw_polygons = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 16
        num_of_bytes = 1
        activate_buzzer = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 17
        num_of_bytes = 1
        rotate_degree = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 18
        num_of_bytes = 1
        checksum = int.from_bytes(data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
                                  byteorder=IBytesConverter.LITTLE_ENDIAN)
        return cls(rotate_image_cycle, obstruction_threshold, no_visibility_threshold, medium_visibility_threshold,
                   full_visibility_threshold, minimum_obstruction_hits, maximum_obstruction_hits, logging_debug,
                   show_images, save_images_to_disk, draw_polygons, activate_buzzer, rotate_degree)
