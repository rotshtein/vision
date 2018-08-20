from protocol.bytes_converter import IBytesConverter
from utils.point_in_polygon import Point
from warning import ObjectClassConverter, ObjectClassHolder


class HDSetWarningMessage(IBytesConverter):
    def __init__(self, warning_id, polygon, object_class_holder, object_min_w_h,
                 object_max_w_h, minimum_confidence, minimum_detection_hits, maximum_detection_hits,
                 is_default) -> None:
        super().__init__()
        self.warning_id = warning_id
        self.polygon = polygon  # type: [Point]
        self.object_class_holder = object_class_holder  # type: ObjectClassHolder
        self.object_min_w_h = object_min_w_h
        self.object_max_w_h = object_max_w_h
        self.minimum_confidence = minimum_confidence
        self.minimum_detection_hits = minimum_detection_hits
        self.maximum_detection_hits = maximum_detection_hits
        self.is_default = is_default
        self.opcode = b'xB2'

    def __str__(self):
        return str(["warning_id={}".format(self.warning_id),
                    "polygon={}".format(', '.join([str(x) for x in self.polygon])),
                    "object_class={}".format(self.object_class_holder.obj_names),
                    "object_min_w_h={}".format(self.object_min_w_h),
                    "object_max_w_h={}".format(self.object_max_w_h),
                    "minimum_confidence={}".format(self.minimum_confidence),
                    "minimum_detection_hits={}".format(self.minimum_detection_hits),
                    "maximum_detection_hits={}".format(self.maximum_detection_hits),
                    "is_default={}".format(self.is_default)])

    def to_bytes(self):
        # full_visibility_threshold = bytearray(struct.pack("{}f".format(IBytesConverter.LITTLE_ENDIAN_SIGN), self.full_visibility_threshold))
        warning_id = int.to_bytes(self.warning_id, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)

        polygon = bytearray()
        for point in self.polygon:
            polygon += int.to_bytes(point.x, 2, byteorder=IBytesConverter.LITTLE_ENDIAN)
            polygon += int.to_bytes(point.y, 2, byteorder=IBytesConverter.LITTLE_ENDIAN)

        object_class = ObjectClassConverter.to_bytes(self.object_class_holder.convert_to_bool_array())
        object_min_w_h = int.to_bytes(self.object_min_w_h, 2,
                                      byteorder=IBytesConverter.LITTLE_ENDIAN)
        object_max_w_h = int.to_bytes(self.object_max_w_h, 2,
                                      byteorder=IBytesConverter.LITTLE_ENDIAN)
        minimum_confidence = int.to_bytes(self.minimum_confidence, 1,
                                          byteorder=IBytesConverter.LITTLE_ENDIAN)
        minimum_detection_hits = int.to_bytes(self.minimum_detection_hits, 1,
                                              byteorder=IBytesConverter.LITTLE_ENDIAN)
        maximum_detection_hits = int.to_bytes(self.maximum_detection_hits, 1,
                                              byteorder=IBytesConverter.LITTLE_ENDIAN)
        is_default = bool.to_bytes(self.is_default, 1, byteorder=IBytesConverter.LITTLE_ENDIAN)
        result = warning_id + polygon + object_class + object_min_w_h + object_max_w_h + minimum_confidence + \
                 minimum_detection_hits + maximum_detection_hits + is_default
        return result

    @classmethod
    def from_bytes(cls, data_bytes, length=0, offset=0):
        temp_offset = 4
        start_index = 4
        num_of_bytes = 1
        warning_id = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)

        # start_index = 5
        # num_of_bytes = 16
        polygon = []
        for i in range(4):
            start_index = 5 + i * 4
            num_of_bytes = 2
            point_x = int.from_bytes(
                data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
                byteorder=IBytesConverter.LITTLE_ENDIAN)

            start_index = start_index + num_of_bytes
            point_y = int.from_bytes(
                data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
                byteorder=IBytesConverter.LITTLE_ENDIAN)
            point = Point(point_x, point_y)
            polygon.append(point)

        start_index = 21
        num_of_bytes = 1
        object_class_bytes = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        object_class_holder = ObjectClassHolder(ObjectClassConverter.from_bytes(object_class_bytes))
        start_index = 22
        num_of_bytes = 2
        object_min_w_h = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 24
        num_of_bytes = 2
        object_max_w_h = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 26
        num_of_bytes = 1
        minimum_confidence = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 27
        num_of_bytes = 1
        minimum_detection_hits = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 28
        num_of_bytes = 1
        maximum_detection_hits = int.from_bytes(
            data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
            byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 29
        num_of_bytes = 1
        is_default = bool.from_bytes(data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
                                     byteorder=IBytesConverter.LITTLE_ENDIAN)
        start_index = 30
        num_of_bytes = 1
        checksum = int.from_bytes(data_bytes[start_index - temp_offset:start_index - temp_offset + num_of_bytes],
                                  byteorder=IBytesConverter.LITTLE_ENDIAN)

        return cls(warning_id, polygon, object_class_holder, object_min_w_h, object_max_w_h, minimum_confidence,
                   minimum_detection_hits, maximum_detection_hits, is_default)

