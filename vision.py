"""
Created on Aug 12, 2018

@author: ziv
"""
from datetime import datetime
from queue import Queue

import cv2

from protocol.requests.hd_setup_msg import HDSetupMessage
from protocol.responses.hd_get_setup_config_response import HDGetSetupConfigResponse
from protocol.responses.hd_get_warning_response import HDGetWarningResponse, VisibilityLightLevel
from utils.hd_threading import HDThread
from utils.obstruction_detector import ObstructionDetector


class Vision(HDThread):
    def __init__(self, thread_name, logging, img_queue, target_fps):
        super().__init__(thread_name, logging, target_fps)
        self.obs_detector = ObstructionDetector(logging)
        self.logging.info(
            "{} - Init. ".format(thread_name))
        self.img_queue = img_queue  # type: Queue
        self.is_obstructed = True
        self.visibility_light_level = VisibilityLightLevel.FULL_VISIBILITY

    def _run(self) -> None:
        image = self.img_queue.get()
        self._vision(image)

    def is_module_in_error(self):
        return self.in_error

    def _vision(self, img):
        start_time = datetime.now()
        self.logging.debug("{} - Start.".format(self.thread_name))
        gray_image = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        tiles_to_ignore = []
        obstructed_tiles = self.obs_detector.is_last_frames_obstructed(gray_image, tiles_to_ignore, self.thread_name)
        if obstructed_tiles.__len__() != 0:
            self.logging.debug(
                "{} - WARNING! Camera is being Obstructed by Tiles:{}.".format(self.thread_name, obstructed_tiles))
            self.is_obstructed = True
        else:
            self.is_obstructed = False
        self.visibility_light_level = self.obs_detector.get_frame_light_level(self.thread_name)
        iteration_time = datetime.now() - start_time
        self.iteration_time_sec = iteration_time.microseconds / 1000000
        self.logging.debug("{} - End. Total Duration={}".format(self.thread_name, iteration_time))

    def on_setup_message(self, message: HDSetupMessage):
        self.logging.info("{} - on_setup_message={}".format(self.thread_name, message))
        self.obs_detector.set_obstruction_threshold(message.obstruction_threshold)
        self.obs_detector.set_obstruction_min_max_hits(message.minimum_obstruction_hits,
                                                       message.maximum_obstruction_hits)
        self.obs_detector.set_visibility_thresholds(message.no_visibility_threshold,
                                                    message.medium_visibility_threshold,
                                                    message.full_visibility_threshold)

    def on_get_warning_msg(self):
        self.logging.info(
            "{} - on_get_warning_msg={}".format(self.thread_name, [self.visibility_light_level, self.is_obstructed]))
        return HDGetWarningResponse(None, self.visibility_light_level, self.is_obstructed)

    def on_get_setup_config_msg(self):
        response = HDGetSetupConfigResponse(None, self.obs_detector.variance_threshold,
                                            self.obs_detector.no_visibility_threshold,
                                            self.obs_detector.medium_visibility_threshold,
                                            self.obs_detector.full_visibility_threshold,
                                            self.obs_detector.min_obstruction_hits,
                                            self.obs_detector.max_obstruction_hits,
                                            None,
                                            None,
                                            None)
        self.logging.info("{} - on_get_setup_config_msg={}".format(self.thread_name, response))
        return response
