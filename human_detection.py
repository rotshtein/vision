"""
Created on Aug 12, 2018

@author: ziv
"""
import math
import queue

import numpy as np
import cv2
from datetime import datetime

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
from utils.point_in_polygon import is_point_in_polygon, Point
from warning import HDWarning, HDWarningResult

DNN_TH_SLEEP_SEC = 0
HEIGHT_THR = 150


class HumanDetection(HDThread):
    def __init__(self, thread_name, logging, img_queue, fps, min_confidence, show, num_of_frames_to_rotate, debug,
                 sw_version, fw_version):
        super().__init__(thread_name, logging, fps)
        self.logging.info("{} - Init. fps={}".format(thread_name, fps))
        self.rotate_counter = 0
        self.img_queue = img_queue  # type: queue.Queue
        self.min_confidence = min_confidence
        self.show = show
        self.num_of_frames_to_rotate = num_of_frames_to_rotate
        self.debug = debug
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

    def _run(self) -> None:
        self.logging.info("{} - _run() - queue size={}".format(self.thread_name, self.img_queue.qsize()))
        image = self.img_queue.get()
        self.__dnn(image)

    def __dnn(self, image):
        self.logging.info("{} - Start.".format(self.thread_name))
        process_start = temp_time = datetime.now()
        (h, w) = image.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
        self.logging.debug(
            "{} - blobFromImage Resize. Duration={}".format(self.thread_name, datetime.now() - temp_time))

        if self.rotate_counter >= self.num_of_frames_to_rotate:
            self.logging.debug("{} - Rotating image by 90 deg...".format(self.thread_name))
            temp_time = datetime.now()
            image_rotator = ImageRotator()
            image_rotated = image_rotator.rotate_image(image, 90)
            image = image_rotator.crop_around_center(image_rotated,
                                                     *image_rotator.largest_rotated_rect(w, h, math.radians(90)))
            self.rotate_counter = 0
            self.logging.debug("{} - Rotating image Duration={}".format(self.thread_name, datetime.now() - temp_time))

        # pass the blob through the network and obtain the detections and predictions
        self.logging.debug("{} - Computing object detections...".format(self.thread_name))
        temp_time = datetime.now()
        self.net.setInput(blob)
        detections = self.net.forward()
        self.logging.debug(
            "{} - setInput() + forward(). Duration={}".format(self.thread_name, datetime.now() - temp_time))

        # loop over the detections
        for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the prediction
            confidence = detections[0, 0, i, 2]
            # extract the index of the class label from the `detections`,
            # then compute the (x, y)-coordinates of the bounding box for the object
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            # display the prediction
            label = "{}: {:.2f}% {} {}".format(self.CLASSES[idx], confidence * 100, startX, startY)
            self.logging.debug("{} - {}".format(self.thread_name, label))

            object_w = abs(startX - endX)
            object_h = abs(startY - endY)

            center = Point(object_w/2, object_h/2)

            for warning in self.warnings:  # type: HDWarning
                # if and polygon inside
                if confidence > warning.minimum_confidence and \
                        self.CLASSES[idx] in warning.object_class_holder.obj_names and \
                        warning.object_min_w_h < object_w and warning.object_min_w_h < object_h and \
                        warning.object_max_w_h > object_w and warning.object_min_w_h > object_h and \
                        is_point_in_polygon(center, warning.polygon):
                    # set result counter up
                    self.set_result_counter(warning.warning_id, True)
                    self.logging.info("DNN - Send Stop Message to Robot")
                else:
                    self.set_result_counter(warning.warning_id, False)

                # todo - draw polygons (if self.show...)

            if self.show:
                cv2.rectangle(image, (startX, startY), (endX, endY),
                              self.COLORS[idx], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)

        if self.show:
            cv2.imshow('detect', image)
            k = cv2.waitKey(1)
            if k % 256 == 27:
                # ESC pressed
                self.logging.debug("{} - Escape hit, closing...".format(self.thread_name))
                return

        iteration_time = datetime.now() - process_start
        self.iteration_time_sec = iteration_time.microseconds * 1000000
        self.logging.info("{} - End. Duration={}. ".format(self.thread_name, datetime.now() - process_start))
        self.rotate_counter += 1

    def on_setup_message(self, message: HDSetupMessage):
        self.rotate_counter = message.rotate_image_cycle

    def on_set_warning_msg(self, message: HDSetWarningMessage):
        warning = HDWarning(message.warning_id, message.polygon, message.object_class_holder, message.object_min_w_h,
                            message.object_max_w_h, message.minimum_confidence, message.minimum_detection_hits,
                            message.maximum_detection_hits, message.is_default)
        self.warnings[message.warning_id] = warning
        self.warnings_results[message.warning_id] = HDWarningResult()

    def on_remove_warning_msg(self, message: HDRemoveWarningMessage):
        if message.warning_id in self.warnings:
            del self.warnings[message.warning_id]
            del self.warnings_results[message.warning_id]

    def on_remove_all_warnings_msg(self, message: HDRemoveAllWarningsMessage):
        self.warnings.clear()
        self.warnings_results.clear()

    def on_remove_all_warnings_except_defaults_msg(self, message: HDRemoveAllWarningsExceptDefaultMessage):
        for warning in self.warnings:  # type: HDWarning
            if not warning.is_default:
                del self.warnings[warning.warning_id]
                del self.warnings_results[warning.warning_id]

    def on_set_warning_to_default_msg(self, message: HDSetWarningToDefaultMessage):
        if message.all_warnings:
            for warning in self.warnings:  # type: HDWarning
                warning.is_default = True
        elif message.warning_id in self.warnings:
            warning = self.warnings[message.warning_id]  # type: HDWarning
            warning.is_default = True

    def on_set_power_msg(self, message: HDSetPowerMessage):
        # todo - need to implement ????
        # assuming it will be already parsed by ST
        pass

    def on_get_warning_msg(self):
        warning_res = [False]*16
        for res in self.warnings_results:  # type: HDWarningResult
            warning_res.append(res.result)
        return HDGetWarningResponse(warning_res, None, None)

    def on_get_warning_config_msg(self, message: HDGetWarningConfigMessage):
        warning = self.warnings.get(message.warning_id)  # type: HDWarning
        return HDGetWarningConfigResponse(warning.warning_id, warning.polygon, warning.object_class_holder,
                                          warning.object_min_w_h, warning.object_max_w_h, warning.minimum_confidence,
                                          warning.minimum_detection_hits, warning.maximum_detection_hits)

    def on_get_setup_config_msg(self, message: HDGetSetupConfigMessage) -> HDGetSetupConfigResponse:
        return HDGetSetupConfigResponse(self.num_of_frames_to_rotate, None, None, None, None, None, None)

    def on_get_status_msg(self, message: HDGetStatusMessage):
        return HDGetStatusResponse(self.sw_version, self.fw_version)

    def set_result_counter(self, warning_id, is_hit):
        warning = self.warnings[warning_id]  # type: HDWarning
        warning_result = self.warnings_results[warning_id]  # type: HDWarningResult
        if is_hit:
            if warning_result.counter <= warning.maximum_detection_hits:
                warning_result.counter += 1
        else:  # decrease
            if warning_result.counter >= 0:
                warning_result.counter -= 1
        # update_result_to_response
        if warning_result.counter >= warning.minimum_confidence:
            warning_result.result = True
        else:
            warning_result.result = False
