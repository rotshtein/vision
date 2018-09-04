"""
Created on Aug 14, 2018

@author: ziv
"""
import queue
from datetime import datetime

import cv2
import os

from utils.hd_threading import HDThread

MAX_FILES = 40
DEBUG_FOLDER_NAME = 'debug'


class FilesSaver(HDThread):
    def __init__(self, thread_name, logging, debug_save_img_queue):
        super().__init__(thread_name, logging, 0)
        self.logging.info("{} - Init.".format(thread_name))
        self.debug_save_img_queue = debug_save_img_queue  # type: queue.Queue
        num_of_files = len(os.listdir(DEBUG_FOLDER_NAME))
        self.logging.info("{} - Counted {} images.".format(thread_name, num_of_files))
        counter = num_of_files
        while counter > MAX_FILES:
            self.remove_oldest_file()
            counter -= 1

    def _run(self) -> None:
        self._file_saver()

    def _file_saver(self):
        image = self.debug_save_img_queue.get()
        self.logging.info(
            "{} - save file... queue_size={}".format(self.thread_name, self.debug_save_img_queue.qsize()))
        time = datetime.now().strftime('%d_%m_%Y_%H_%M_%S')
        cv2.imwrite(os.path.join(DEBUG_FOLDER_NAME, 'HD_{}.bmp'.format(time)), image)
        files_count = len(os.listdir(DEBUG_FOLDER_NAME))
        self.logging.info("added file. files_count={}".format(files_count))

        # if necessary - move to a new thread - delete old files if above size
        if files_count > MAX_FILES:
            self.remove_oldest_file()

    def remove_oldest_file(self):
        list_of_files = os.listdir(DEBUG_FOLDER_NAME)
        if len(list_of_files) == 0:
            return
        full_path = ["{}/{}".format(DEBUG_FOLDER_NAME, x) for x in list_of_files]
        oldest_file = min(full_path, key=os.path.getctime)
        os.remove(os.path.abspath(oldest_file))
        self.logging.info("removed file. files_count={}".format(len(list_of_files)))
