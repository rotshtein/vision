"""
Created on Aug 12, 2018

@author: ziv
"""
import cv2
from datetime import datetime
from utils.hd_threading import HDThread
import queue

FROM_CAMERA_TH_SLEEP_SEC = 0.12


class Camera(HDThread):
    def __init__(self, thread_name, logging, detection_queue, vision_queue, target_fps):
        super().__init__(thread_name, logging, target_fps)
        self.detection_queue = detection_queue  # type: queue.Queue
        self.vision_queue = vision_queue
        self.logging.info("{} - Start Init PiCamera...".format(thread_name))
        try:
            from picamera import PiCamera
            from picamera.array import PiRGBArray
            self.camera = PiCamera()
            self.camera.resolution = (640, 480)
            self.rawCapture = PiRGBArray(self.camera)
            self.picamera_mode = True
            self.logging.info("{} - Init PiCamera success".format(thread_name))
        except:
            self.logging.info("{} - Start Init VideoCapture...".format(thread_name))
            self.camera = cv2.VideoCapture(0)
            self.logging.info("{} - Init VideoCapture success".format(thread_name))
            self.picamera_mode = False

    def _run(self) -> None:
        image = self._from_camera()
        # wait until queue is empty
        if self.detection_queue.full():
            self.detection_queue.get()
        self.detection_queue.put(image)
        if self.vision_queue.full():
            self.vision_queue.get()
        self.vision_queue.put(image)

    def is_module_in_error(self):
        return self.in_error

    def _from_camera(self):
        temp_time = start_time = datetime.now()
        self.logging.debug("{} - Start.".format(self.thread_name))
        if self.picamera_mode:
            self.camera.capture(self.rawCapture, format="bgr", use_video_port=True)
            img = self.rawCapture.array
        else:
            ret, img = self.camera.read()
        self.logging.debug("{} - Capturing image. Duration={}".format(self.thread_name, datetime.now() - temp_time))

        if self.picamera_mode:
            temp_time = datetime.now()
            self.rawCapture.truncate(0)
            self.logging.debug(
                "{} - Capturing truncate Duration={}".format(self.thread_name, datetime.now() - temp_time))

        iteration_time = datetime.now() - start_time
        self.iteration_time_sec = iteration_time.microseconds / 1000000
        self.logging.debug("{} - End. Total Duration={}".format(self.thread_name, iteration_time))
        return img
