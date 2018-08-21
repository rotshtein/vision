"""
Created on Aug 12, 2018

@author: ziv
"""
import threading
from datetime import datetime
from time import sleep

from rx_message import IRXMessage


class HDThread(threading.Thread, IRXMessage):
    def __init__(self, thread_name, logging, fps):
        super().__init__()
        self.thread_name = thread_name
        self.is_exit = False
        self.logging = logging  # type: logging
        self.fps = fps
        self.iteration_time_sec = 0.0
        self.last_measured_time = datetime.now()
        self.in_error = False

    def run(self) -> None:
        while not self.is_exit:
            self._calc_fps()
            try:
                self._run()
            except Exception as e:
                self.logging.info("{} - Exception: {}".format(self.thread_name, e.__str__()))
                self.in_error = True
            if self.fps != 0 and self.iteration_time_sec != 0:
                sleep_time = 1 / self.fps - self.iteration_time_sec
                sleep_time = sleep_time if sleep_time > 0 else 0
                # self.logging.debug("sleep_time={}".format(sleep_time))
                self.logging.debug("{} - Going to sleep {} sec".format(self.thread_name, sleep_time))
                sleep(sleep_time)

    def exit_thread(self):
        self.is_exit = True
        self.logging.info("{} - exiting thread".format(self.thread_name))

    def _calc_fps(self):
        cycle_sec = (datetime.now() - self.last_measured_time).microseconds / 1000000
        last_measured_fps = 1.0 if cycle_sec == 0 else 1 / cycle_sec
        self.logging.debug("{0:s} - last measured fps={1:.2f}".format(self.thread_name, last_measured_fps))
        self.last_measured_time = datetime.now()

    def _run(self):
        pass
