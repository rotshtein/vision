"""
Created on Aug 12, 2018

@author: ziv
"""
from datetime import datetime

import cv2

from protocol.requests.hd_get_setup_config_msg import HDGetSetupConfigMessage
from protocol.requests.hd_get_warning_msg import HDGetWarningMessage
from protocol.requests.hd_setup_msg import HDSetupMessage
from protocol.responses.hd_get_setup_config_response import HDGetSetupConfigResponse
from protocol.responses.hd_get_warning_response import HDGetWarningResponse, VisibilityLightLevel
from utils.hd_threading import HDThread
from utils.obstruction_detector import ObstructionDetector


class Vision(HDThread):
    def __init__(self, thread_name, logging, img_queue, fps):
        super().__init__(thread_name, logging, fps)
        self.obs_detector = ObstructionDetector(logging)
        self.logging.info("{} - Init. fps={}, Variance Threshold={}".format(thread_name, fps, self.obs_detector.variance_threshold))
        self.img_queue = img_queue
        self.is_obstructed = True
        self.visibility_light_level = VisibilityLightLevel.FULL_VISIBILITY

    def _run(self) -> None:
        image = self.img_queue.get()
        self._vision(image)

    def _vision(self, img):
        start_time = datetime.now()
        self.logging.info("{} - Start.".format(self.thread_name))
        gray_image = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        tiles_to_ignore = []
        obstructed_tiles = self.obs_detector.is_last_frames_obstructed(gray_image, tiles_to_ignore)
        if obstructed_tiles.__len__() != 0:
            self.logging.info("{} - WARNING! Camera is being Obstructed by Tiles:{}.".format(self.thread_name, obstructed_tiles))
            self.is_obstructed = True
        else:
            self.is_obstructed = False
        iteration_time = datetime.now() - start_time
        self.iteration_time_sec = iteration_time.microseconds/1000000
        self.logging.info("{} - End. Total Duration={}".format(self.thread_name, iteration_time))

    def on_setup_message(self, message: HDSetupMessage):
        self.obs_detector.set_obstruction_threshold(message.obstruction_threshold)
        self.obs_detector.set_obstruction_min_max_hits(message.minimum_obstruction_hits, message.maximum_obstruction_hits)
        self.obs_detector.set_visibility_thresholds(message.no_visibility_threshold, message.medium_visibility_threshold, message.full_visibility_threshold)

    def on_get_warning_msg(self):
        return HDGetWarningResponse(None, self.visibility_light_level, self.is_obstructed)

    def on_get_setup_config_msg(self, message: HDGetSetupConfigMessage):
        return HDGetSetupConfigResponse(None, self.obs_detector.variance_threshold,
                                        self.obs_detector.no_visibility_threshold,
                                        self.obs_detector.medium_visibility_threshold,
                                        self.obs_detector.full_visibility_threshold,
                                        self.obs_detector.min_obstruction_hits,
                                        self.obs_detector.max_obstruction_hits,
                                        )

