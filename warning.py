from enum import Enum

from bitarray import bitarray

from protocol.bytes_converter import IBytesConverter


class HDWarning():
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


class ObjectClass(Enum):
    PERSON = {0: ["person"]}
    ANIMAL = {1: ["cat", "dog"]}
    FURNITURE = {2: ["sofa", "diningtable", "chair", "tvmonitor"]}
    TOYS = {3: ["aeroplane", "boat", "cow", "train"]}
    VEHICLE = {4: ["bicycle", "motorbike", "car", "bus"]}


class ObjectClassHolder:
    def __init__(self, bool_array=None) -> None:
        super().__init__()
        self.objects = set()  # type: set(ObjectClass)
        self.obj_names = []
        if bool_array is not None:
            bool_array = bool_array[::-1]
            for i in range(len(bool_array)):
                is_break = False
                if bool_array[i]:
                    for e in ObjectClass:
                        if is_break:
                            break
                        for key, value in e.value.items():
                            if key == i:
                                self.objects.add(e)
                                is_break = True
                                break
            self.update_objects_names()

    def __str__(self) -> str:
        return str(self.obj_names)

    def update_objects_names(self):
        self.obj_names = []
        for e_obj in self.objects:
            for key, value in e_obj.value.items():
                self.obj_names += value

    def add_object(self, item_: ObjectClass):
        self.objects.add(item_)
        self.update_objects_names()

    def add_objects(self, items_: [ObjectClass]):
        for it in items_:
            self.objects.add(it)
        self.update_objects_names()

    def remove_object(self, item_: ObjectClass):
        self.objects.remove(item_)
        self.update_objects_names()

    def convert_to_bool_array(self):
        bool_result = [False] * 8
        for _obj in self.objects:  # type: ObjectClass
            for key, value in _obj.value.items():
                bool_result[key] = True
                break
        return bool_result[::-1]


class ObjectClassConverter(object):
    def __init__(self, ) -> None:
        super().__init__()

    @classmethod
    def to_bytes(cls, objects_array: [bool]):
        a = bitarray(objects_array)
        return a.tobytes()

    @classmethod
    def from_bytes(cls, data) -> [bool]:
        # convert byte to [bool]
        range_ = [bool(data & (1 << n)) for n in range(8)]
        # reverse list
        return range_[::-1]


class HDWarningResult(object):
    def __init__(self) -> None:
        super().__init__()
        self.counter = 0  # type: int
        self.result = False  # type: bool
