"""
Created on Aug 12, 2018

@author: ziv
"""
import threading
from datetime import datetime
from time import sleep
import os

from rx_message import IRXMessage


class HDThread(threading.Thread, IRXMessage):
    def __init__(self, thread_name, logging, target_fps):
        super().__init__()
        self.thread_name = thread_name
        self.is_exit = False
        self.logging = logging  # type: logging
        self.target_fps = target_fps
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
            if self.target_fps != 0 and self.iteration_time_sec != 0:
                sleep_time = 1 / self.target_fps - self.iteration_time_sec
                sleep_time = sleep_time if sleep_time > 0 else 0
                # self.logging.debug("sleep_time={}".format(sleep_time))
                self.logging.debug("{} - Going to sleep {} sec".format(self.thread_name, sleep_time))
                sleep(sleep_time)

    def exit_thread(self):
        self.is_exit = True
        self.logging.info("{} - exiting thread".format(self.thread_name))

    def measure_temp(self):
        temp = os.popen("vcgencmd measure_temp").readline()
        return temp.replace("temp=", "").rstrip("\n\r")
        
    def _calc_fps(self):
        time = datetime.now() - self.last_measured_time
        cycle_sec = time.microseconds / 1000000 + time.seconds
        last_measured_fps = 1.0 if cycle_sec == 0 else 1 / cycle_sec
        self.logging.info("{0:s} - last measured fps={1:.2f}. Temperature={2:s}".format(self.thread_name, last_measured_fps, self.measure_temp()))
        self.last_measured_time = datetime.now()
        return last_measured_fps

    def _run(self):
        pass
