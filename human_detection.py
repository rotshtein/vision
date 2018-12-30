"""
Created on Aug 12, 2018

@author: ziv
"""
import math
import pickle
import queue
import threading
from datetime import datetime

import cv2
import numpy as np

from protocol.requests.hd_get_warning_config_msg import HDGetWarningConfigMessage
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

SETUP_PKL_FILE_NAME = 'setup.pkl'
WARNINGS_PKL_FILE_NAME = 'warnings.pkl'

DNN_TH_SLEEP_SEC = 0
HEIGHT_THR = 150


class HumanDetection(HDThread):
    def __init__(self, thread_name, logging, img_queue, target_fps, show, num_of_frames_to_rotate, sw_version,
                 fw_version, debug_img_queue, save_images_to_disk=False, debug_save_img_queue=None,
                 draw_polygons_on_image=False, rotating_angle=90):
        super().__init__(thread_name, logging, target_fps)
        self.rotate_counter = 0
        self.img_queue = img_queue  # type: queue.Queue
        self.debug_img_queue = debug_img_queue  # type: queue.Queue
        self.debug_save_img_queue = debug_save_img_queue  # type: queue.Queue
        self.show = show
        self.num_of_frames_to_rotate = num_of_frames_to_rotate
        self.sw_version = sw_version
        self.fw_version = fw_version
        self.is_logging_debug = self.logging.getLogger().level == self.logging.DEBUG
        self.save_images_to_disk = save_images_to_disk
        self.draw_polygons_on_image = draw_polygons_on_image
        self.rotating_angle = int(rotating_angle)

        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]
        self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))
        # load our serialized protocol from disk
        logging.debug("{} - Loading the detection protocol - readNetFromCaffe...".format(self.thread_name))
        self.net = cv2.dnn.readNetFromCaffe('data/caffemodels/MobileNetSSD_deploy.prototxt.txt',
                                            'data/caffemodels/MobileNetSSD_deploy.caffemodel')

        self.rotate_counter = 0
        self.is_frame_rotated = False
        self.cycle_counter = 0
        self.warnings = {}  # type: {} warning_id:HDWarning

        # warnings_results does not keep all 16 warnings but only warnings that were set.
        # the response message is always initialized with 16 False bits and iterates over warnings_results
        self.warnings_results = {}  # type: {}
        self.lock = threading.Lock()

    def _run(self) -> None:
        self.logging.debug("{} - _run() - queue size={}".format(self.thread_name, self.img_queue.qsize()))
        image = self.img_queue.get()
        self.__dnn(image)

    def _calc_fps(self):
        from utils import global_vars
        global_vars.dnn_fps.append(super()._calc_fps())

    def is_module_in_error(self):
        return self.in_error

    def __dnn(self, image):
        self.logging.debug("{} - Start.".format(self.thread_name))

        if image is None:
            self.logging.debug("{} - Image is none".format(self.thread_name))
            return

        if self.rotate_counter == self.num_of_frames_to_rotate and self.num_of_frames_to_rotate != 0:
            self.is_frame_rotated = True
        else:
            self.is_frame_rotated = False

        process_start = temp_time = datetime.now()
        (h, w) = image.shape[:2]
        resized_image = cv2.resize(image, (300, 300))
        if self.is_frame_rotated:
            self.logging.info("{} - Rotating image by 90 deg...".format(self.thread_name))
            temp_time = datetime.now()
            image_rotator = ImageRotator()
            image_rotated = image_rotator.rotate_image(resized_image, self.rotating_angle)
            resized_image = image_rotator.crop_around_center(image_rotated,
                                                             *image_rotator.largest_rotated_rect(w, h,
                                                                                                 math.radians(
                                                                                                     self.rotating_angle)))
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
            # if need to ignore due to is_rotated filter - skip setting the result counter
            if warning.is_rotated != self.is_frame_rotated:
                continue
            for i in np.arange(0, detections.shape[2]):
                # extract the confidence (i.e., probability) associated with the prediction
                confidence = 100 * detections[0, 0, i, 2]
                # extract the index of the class label from the `detections`,
                # then compute the (x, y)-coordinates of the bounding box for the object
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([300, 300, 300, 300])
                (startX, startY, endX, endY) = box.astype("int")
                # display the prediction
                try:
                    classes_idx_ = self.CLASSES[idx]
                except:
                    continue
                label = "{}: {:.2f}%".format(classes_idx_, confidence)
                self.logging.debug("{} - {}".format(self.thread_name, label))

                object_w = abs(startX - endX)
                object_h = abs(startY - endY)

                polygon = warning.polygon
                if self.is_frame_rotated:
                    polygon = self.rotate_polygon(polygon, self.rotating_angle)

                if self.draw_polygons_on_image:
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
                    if self.draw_polygons_on_image:
                        self.draw_detection(resized_image, startX, startY, endX, endY, idx, label)
                    self.logging.info("{} - Detection in warning {}".format(self.thread_name, warning.warning_id))
                    result_is_hit = True
                    break
            self.set_result_counter(warning.warning_id, result_is_hit)

        iteration_time = datetime.now() - process_start
        self.iteration_time_sec = iteration_time.microseconds * 1000000
        self.logging.debug("{} - End. Duration={}. ".format(self.thread_name, datetime.now() - process_start))
        self.rotate_counter += 1
        self.set_cycle_counter()
        if self.save_images_to_disk:
            self.debug_save_img_queue.put(resized_image)
        if self.show:
            self.debug_img_queue.put(resized_image)

    def set_cycle_counter(self):
        self.cycle_counter += 1
        self.cycle_counter = self.cycle_counter % 16

    def rotate_polygon(self, polygon, rotating_angle):
        return rotate_and_translate_polygon(polygon, rotating_angle)

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

    def get_color(self, idx):
        if idx > len(self.COLORS) - 1:
            idx = 0
        return self.COLORS[idx]

    def draw_detection(self, image, startX, startY, endX, endY, idx, label):
        cv2.rectangle(image, (startX, startY), (endX, endY), self.get_color(idx), 2)
        y = startY - 15 if startY - 15 > 15 else startY + 15
        # cv2.putText(image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)

    def draw_warning_polygon(self, polygon, warning_id, image):
        pts = np.array([[polygon[0].x, polygon[0].y], [polygon[1].x, polygon[1].y],
                        [polygon[2].x, polygon[2].y], [polygon[3].x, polygon[3].y]], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, self.get_color(warning_id))
        font = cv2.FONT_HERSHEY_SIMPLEX
        x = int((polygon[0].x + polygon[1].x + polygon[2].x + polygon[3].x) / 4) - 20
        y = int((polygon[0].y + polygon[1].y + polygon[2].y + polygon[3].y) / 4)

        cv2.putText(image, "w{}".format(warning_id), (x, y), font, 0.5,
                    self.get_color(warning_id), 2)
        # 2, cv2.LINE_AA)

    def handle_log_level_change(self):
        level = self.logging.INFO
        if self.is_logging_debug:
            level = self.logging.DEBUG
        logger = self.logging.getLogger()
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)

    def on_setup_message(self, message: HDSetupMessage, is_save_to_fs=True):
        self.logging.info("{} - on_setup_message={}".format(self.thread_name, message))
        if is_save_to_fs:
            self.save_setup_to_fs(message)
        self.num_of_frames_to_rotate = message.rotate_image_cycle

        self.is_logging_debug = message.logging_debug
        self.handle_log_level_change()

        self.show = message.show_images
        self.save_images_to_disk = message.save_images_to_disk
        self.draw_polygons_on_image = message.draw_polygons
        self.rotating_angle = int(message.rotate_degree)

    def on_set_warning_msg(self, message: HDSetWarningMessage):
        self.logging.info(
            "{} - on_set_warning_msg={}".format(self.thread_name, message))
        if message.warning_id > 15 or message.warning_id < 0:
            self.logging.info(
                "{} - Error - warning_id is illegal. warning_id={}".format(self.thread_name, message.warning_id))
        warning = HDWarning(message.warning_id, message.polygon, message.object_class_holder, message.object_min_w_h,
                            message.object_max_w_h, message.minimum_confidence, message.minimum_detection_hits,
                            message.maximum_detection_hits, message.is_default, message.is_rotated)
        self.lock.acquire()
        try:
            self.warnings[message.warning_id] = warning
            self.warnings_results[message.warning_id] = HDWarningResult()
            self.save_warnings_to_fs()
        finally:
            self.lock.release()

    def save_setup_to_fs(self, message):
        try:
            with open(SETUP_PKL_FILE_NAME, 'wb') as output:
                pickle.dump(message, output, pickle.HIGHEST_PROTOCOL)
        except Exception as ex:
            self.logging.info("{} - Failed to save setup to file... {}".format(self.thread_name, ex.__str__()))

    def save_warnings_to_fs(self):
        try:
            with open(WARNINGS_PKL_FILE_NAME, 'wb') as output:
                pickle.dump(self.warnings, output, pickle.HIGHEST_PROTOCOL)
        except Exception as ex:
            self.logging.info("{} - Failed to save warnings to file... {}".format(self.thread_name, ex.__str__()))

    def load_configuration_from_fs(self):
        self.load_warnings_from_fs()
        self.load_setup_from_fs()

    def load_warnings_from_fs(self):
        try:
            with open(WARNINGS_PKL_FILE_NAME, 'rb') as input:
                self.warnings = pickle.load(input)
            for warning in self.warnings:
                self.logging.info("{} - Loaded warning: {}".format(self.thread_name, self.warnings[warning]))
                self.warnings_results[warning] = HDWarningResult()
            self.logging.info("{} - Loaded warnings from file Successfully...".format(self.thread_name))
        except Exception as ex:
            self.logging.info("{} - Failed to load warnings from file... {}".format(self.thread_name, ex.__str__()))

    def load_setup_from_fs(self):
        try:
            with open(SETUP_PKL_FILE_NAME, 'rb') as input:
                setup_message = pickle.load(input)
            self.on_setup_message(setup_message, False)
            self.logging.info("{} - Loaded setup from file Successfully...".format(self.thread_name))
        except Exception as ex:
            self.logging.info("{} - Failed to load setup from file... {}".format(self.thread_name, ex.__str__()))

    def on_remove_warning_msg(self, message: HDRemoveWarningMessage):
        self.lock.acquire()
        try:
            if message.warning_id in self.warnings:
                del self.warnings[message.warning_id]
                del self.warnings_results[message.warning_id]
                self.save_warnings_to_fs()
            else:
                raise Exception("{} - on_remove_warning_msg - No warning id to remove {}".format(self.thread_name,
                                                                                                 message.warning_id))
        finally:
            self.lock.release()

    def on_remove_all_warnings_msg(self):
        self.lock.acquire()
        try:
            self.warnings.clear()
            self.warnings_results.clear()
            self.save_warnings_to_fs()
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
            self.save_warnings_to_fs()
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
            self.save_warnings_to_fs()
        finally:
            self.lock.release()

    def on_set_power_msg(self, message: HDSetPowerMessage):
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
        return HDGetWarningResponse(warning_res, None, None, self.is_frame_rotated, self.cycle_counter)

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
        config_response = HDGetSetupConfigResponse(self.num_of_frames_to_rotate, None, None, None, None, None, None,
                                                   self.is_logging_debug, self.show, self.save_images_to_disk,
                                                   self.draw_polygons_on_image, None, self.rotating_angle)
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
