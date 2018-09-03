"""
Created on Aug 12, 2018

@author: ziv
"""
import math
import queue

import numpy as np
import cv2
from datetime import datetime
import threading

from protocol.requests.hd_get_setup_config_msg import HDGetSetupConfigMessage
from protocol.requests.hd_get_status_msg import HDGetStatusMessage
from protocol.requests.hd_get_warning_config_msg import HDGetWarningConfigMessage
from protocol.requests.hd_remove_all_warnings_except_default_msg import HDRemoveAllWarningsExceptDefaultMessage
from protocol.requests.hd_remove_all_warnings_msg import HDRemoveAllWarningsMessage
from protocol.requests.hd_remove_warning_msg import HDRemoveWarningMessage
from protocol.requests.hd_set_power_msg import HDSetPowerMessage
from protocol.requests.hd_set_warning_msg import HDSetWarningMessage
from protocol.requests.hd_set_warning_to_default_msg import HDSetWarningToDefaultMessage
from protocol.requests.hd_setup_msg import HDSetupMessage
from protocol.responses.hd_get_setup_config_response import HDGetSetupConfigResponse
from protocol.responses.hd_get_status_response import HDGetStatusResponse
from protocol.responses.hd_get_warning_config_response import HDGetWarningConfigResponse
from protocol.responses.hd_get_warning_response import HDGetWarningResponse
from utils.hd_threading import HDThread
from utils.image_rotator import ImageRotator
from utils.point_in_polygon import is_point_in_polygon, Point, rotate_and_translate_polygon
from warning import HDWarning, HDWarningResult

DNN_TH_SLEEP_SEC = 0
HEIGHT_THR = 150


class HumanDetection(HDThread):
    def __init__(self, thread_name, logging, img_queue, target_fps, show, num_of_frames_to_rotate, sw_version,
                 fw_version, debug_img_queue):
        super().__init__(thread_name, logging, target_fps)
        self.logging.info("{} - Init.".format(thread_name))
        self.rotate_counter = 0
        self.img_queue = img_queue  # type: queue.Queue
        self.debug_img_queue = debug_img_queue  # type: queue.Queue
        self.show = show
        self.num_of_frames_to_rotate = num_of_frames_to_rotate
        self.sw_version = sw_version
        self.fw_version = fw_version

        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]
        self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))
        # load our serialized protocol from disk
        logging.debug("loading detection protocol...")
        self.net = cv2.dnn.readNetFromCaffe('data/caffemodels/MobileNetSSD_deploy.prototxt.txt',
                                            'data/caffemodels/MobileNetSSD_deploy.caffemodel')

        self.rotate_counter = 0
        self.warnings = {}  # type: {} warning_id:HDWarning

        # warnings_results does not keep all 16 warnings but only warnings that were set.
        # the response message is always initialized with 16 False bits and iterates over warnings_results
        self.warnings_results = {}  # type: {}
        self.lock = threading.Lock()

    def _run(self) -> None:
        self.logging.debug("{} - _run() - queue size={}".format(self.thread_name, self.img_queue.qsize()))
        image = self.img_queue.get()
        self.__dnn(image)

    def is_module_in_error(self):
        return self.in_error

    def __dnn(self, image):
        self.logging.debug("{} - Start.".format(self.thread_name))

        if image is None:
            self.logging.debug("{} - Image is none".format(self.thread_name))
            return

        is_rotate = False
        if self.rotate_counter >= self.num_of_frames_to_rotate:
            is_rotate = True

        process_start = temp_time = datetime.now()
        (h, w) = image.shape[:2]
        resized_image = cv2.resize(image, (300, 300))

        if is_rotate:
            self.logging.debug("{} - Rotating image by 90 deg...".format(self.thread_name))
            temp_time = datetime.now()
            image_rotator = ImageRotator()
            image_rotated = image_rotator.rotate_image(resized_image, 90)
            resized_image = image_rotator.crop_around_center(image_rotated,
                                                             *image_rotator.largest_rotated_rect(w, h,
                                                                                                 math.radians(90)))
            self.rotate_counter = 0
            self.logging.debug("{} - Rotating image Duration={}".format(self.thread_name, datetime.now() - temp_time))

        blob = cv2.dnn.blobFromImage(resized_image, 0.007843, (300, 300), 127.5)
        self.logging.debug(
            "{} - blobFromImage Resize. Duration={}".format(self.thread_name, datetime.now() - temp_time))

        # pass the blob through the network and obtain the detections and predictions
        self.logging.debug("{} - Computing object detections...".format(self.thread_name))
        temp_time = datetime.now()
        self.net.setInput(blob)
        detections = self.net.forward()
        self.logging.debug(
            "{} - setInput() + forward(). Duration={}".format(self.thread_name, datetime.now() - temp_time))

        for warning in self.warnings.values():  # type: HDWarning
            result_is_hit = False
            for i in np.arange(0, detections.shape[2]):
                if result_is_hit:
                    break
                # extract the confidence (i.e., probability) associated with the prediction
                confidence = 100 * detections[0, 0, i, 2]
                # extract the index of the class label from the `detections`,
                # then compute the (x, y)-coordinates of the bounding box for the object
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([300, 300, 300, 300])
                (startX, startY, endX, endY) = box.astype("int")
                # display the prediction
                classes_idx_ = self.CLASSES[idx]
                label = "{}: {:.2f}%".format(classes_idx_, confidence)
                self.logging.debug("{} - {}".format(self.thread_name, label))

                object_w = abs(startX - endX)
                object_h = abs(startY - endY)

                polygon = warning.polygon
                if is_rotate:
                    polygon = self.rotate_polygon(polygon)

                if self.show:
                    self.draw_warning_polygon(polygon, warning.warning_id, resized_image)
                # if and polygon inside
                minimum_confidence = warning.minimum_confidence
                if confidence > minimum_confidence and \
                        classes_idx_ in warning.object_class_holder.obj_names and \
                        warning.object_min_w_h < object_w and warning.object_min_w_h < object_h and \
                        warning.object_max_w_h > object_w and warning.object_max_w_h > object_h and \
                        (self.is_warning_polygon_in_detection_box(startX, startY, endX, endY,
                                                                  polygon) or self.is_points_in_polygon(startX, startY,
                                                                                                        endX, endY,
                                                                                                        polygon)):
                    # set result counter up
                    if self.show:
                        self.draw_detection(resized_image, startX, startY, endX, endY, idx, label)
                    self.set_result_counter(warning.warning_id, True)
                    self.logging.debug("{} - Detection in warning {}".format(self.thread_name, warning.warning_id))
                    result_is_hit = True
            if not result_is_hit:
                self.set_result_counter(warning.warning_id, False)

        iteration_time = datetime.now() - process_start
        self.iteration_time_sec = iteration_time.microseconds * 1000000
        self.logging.debug("{} - End. Duration={}. ".format(self.thread_name, datetime.now() - process_start))
        self.rotate_counter += 1
        if self.show:
            self.debug_img_queue.put(resized_image)

    def rotate_polygon(self, polygon):
        return rotate_and_translate_polygon(polygon, 90)

    def is_warning_polygon_in_detection_box(self, startX, startY, endX, endY, polygon):
        detected_box = [Point(startX, startY), Point(startX, endY), Point(endX, endY), Point(endX, startY)]
        if is_point_in_polygon(polygon[0], detected_box):
            return True
        if is_point_in_polygon(polygon[1], detected_box):
            return True
        if is_point_in_polygon(polygon[2], detected_box):
            return True
        if is_point_in_polygon(polygon[3], detected_box):
            return True
        return False

    def is_points_in_polygon(self, startX, startY, endX, endY, polygon):
        if is_point_in_polygon(Point(startX, startY), polygon):
            return True
        if is_point_in_polygon(Point(startX, endY), polygon):
            return True
        if is_point_in_polygon(Point(endX, endY), polygon):
            return True
        if is_point_in_polygon(Point(endX, startY), polygon):
            return True
        return False

    def draw_detection(self, image, startX, startY, endX, endY, idx, label):
        cv2.rectangle(image, (startX, startY), (endX, endY), self.COLORS[idx], 2)
        y = startY - 15 if startY - 15 > 15 else startY + 15
        # cv2.putText(image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)

    def draw_warning_polygon(self, polygon, warning_id, image):
        pts = np.array([[polygon[0].x, polygon[0].y], [polygon[1].x, polygon[1].y],
                        [polygon[2].x, polygon[2].y], [polygon[3].x, polygon[3].y]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, self.COLORS[warning_id])
        font = cv2.FONT_HERSHEY_SIMPLEX
        x = int((polygon[0].x + polygon[1].x + polygon[2].x + polygon[3].x) / 4) - 20
        y = int((polygon[0].y + polygon[1].y + polygon[2].y + polygon[3].y) / 4)

        cv2.putText(image, "w{}".format(warning_id), (x, y), font, 0.5,
                    self.COLORS[warning_id], 2)
        # 2, cv2.LINE_AA)

    def is_module_in_error(self):
        return self.in_error

    def on_setup_message(self, message: HDSetupMessage):
        self.logging.info("{} - on_setup_message={}".format(self.thread_name, message))
        self.num_of_frames_to_rotate = message.rotate_image_cycle

    def on_set_warning_msg(self, message: HDSetWarningMessage):
        self.logging.info(
            "{} - on_set_warning_msg={}".format(self.thread_name, message))
        warning = HDWarning(message.warning_id, message.polygon, message.object_class_holder, message.object_min_w_h,
                            message.object_max_w_h, message.minimum_confidence, message.minimum_detection_hits,
                            message.maximum_detection_hits, message.is_default)
        self.lock.acquire()
        try:
            self.warnings[message.warning_id] = warning
            self.warnings_results[message.warning_id] = HDWarningResult()
        finally:
            self.lock.release()

    def on_remove_warning_msg(self, message: HDRemoveWarningMessage):
        self.lock.acquire()
        try:
            if message.warning_id in self.warnings:
                del self.warnings[message.warning_id]
                del self.warnings_results[message.warning_id]
            else:
                raise Exception("{} - on_remove_warning_msg - No warning id to remove {}".format(self.thread_name, message.warning_id))
        finally:
            self.lock.release()

    def on_remove_all_warnings_msg(self):
        self.lock.acquire()
        try:
            self.warnings.clear()
            self.warnings_results.clear()
        finally:
            self.lock.release()

    def on_remove_all_warnings_except_defaults_msg(self):
        warnings_id_to_remove = []
        self.lock.acquire()
        try:
            for warning_id, warning in self.warnings.items():  # type: HDWarning
                if not warning.is_default:
                    warnings_id_to_remove.append(warning_id)

            for id in warnings_id_to_remove:
                del self.warnings[id]
                del self.warnings_results[id]
        finally:
            self.lock.release()

    def on_set_warning_to_default_msg(self, message: HDSetWarningToDefaultMessage):
        self.lock.acquire()
        try:
            if message.all_warnings:
                for warning in self.warnings.values():  # type: HDWarning
                    warning.is_default = True
            elif message.warning_id in self.warnings:
                warning = self.warnings[message.warning_id]  # type: HDWarning
                warning.is_default = True
        finally:
            self.lock.release()

    def on_set_power_msg(self, message: HDSetPowerMessage):
        # todo - need to implement ????
        # assuming it will be already parsed by ST
        pass

    def on_get_warning_msg(self):
        warning_res = [False] * 16
        self.lock.acquire()
        try:
            for warning_id, res in self.warnings_results.items():
                warning_res.__setitem__(warning_id, res.result)
            # warning_res = warning_res[::-1]
        finally:
            self.lock.release()
        self.logging.info("{} - on_get_warning_msg={}".format(self.thread_name, warning_res))
        return HDGetWarningResponse(warning_res, None, None)

    def on_get_warning_config_msg(self, message: HDGetWarningConfigMessage):
        self.lock.acquire()
        try:
            warning = self.warnings.get(message.warning_id)  # type: HDWarning
        finally:
            self.lock.release()
        return HDGetWarningConfigResponse(warning.warning_id, warning.polygon, warning.object_class_holder,
                                          warning.object_min_w_h, warning.object_max_w_h, warning.minimum_confidence,
                                          warning.minimum_detection_hits, warning.maximum_detection_hits,
                                          warning.is_default)

    def on_get_setup_config_msg(self) -> HDGetSetupConfigResponse:
        config_response = HDGetSetupConfigResponse(self.num_of_frames_to_rotate, None, None, None, None, None, None)
        self.logging.info("{} - on_get_setup_config_msg={}".format(self.thread_name, config_response))
        return config_response

    def on_get_status_msg(self):
        return HDGetStatusResponse(self.sw_version, self.fw_version)

    def set_result_counter(self, warning_id, is_hit):
        self.lock.acquire()
        try:
            warning = self.warnings[warning_id]  # type: HDWarning
            warning_result = self.warnings_results[warning_id]  # type: HDWarningResult
            if is_hit:
                if warning_result.counter < warning.maximum_detection_hits:
                    warning_result.counter += 1
            else:  # decrease
                if warning_result.counter > 0:
                    warning_result.counter -= 1
            # update_result_to_response
            if warning_result.counter >= warning.minimum_detection_hits:
                self.logging.info(
                    "{} - Detection in warning {} above min. hits.".format(self.thread_name, warning.warning_id))
                warning_result.result = True
            else:
                warning_result.result = False
        finally:
            self.lock.release()
