"""
Created on Aug 14, 2018

@author: ziv
"""
import argparse
import glob
import logging
import os
import queue

import cv2

from camera import Camera
from communication import Communication
from file_saver import FilesSaver
from human_detection import HumanDetection
from messages_receiver_handler import MessagesReceiverHandler
from protocol.requests.hd_set_warning_msg import HDSetWarningMessage
from utils.point_in_polygon import Point
from vision import Vision
from warning import ObjectClassHolder

SW_VERSION = "0.1"
FW_VERSION = "0.1"

THREAD_COMMUNICATION = "Thread_Communication"
THREAD_VISION = "Thread_Vision"
THREAD_DNN = "Thread_DNN"
THREAD_CAMERA = "Thread_Camera"
THREAD_FILES_SAVER = "Thread_Files_Saver"


def start_threads(show, port, baudrate, thread_names, save_images_to_disk, simulate_warnings):
    # max size = 2 - we don't want old images!
    detection_queue = queue.Queue(1)
    vision_queue = queue.Queue(1)
    debug_queue = queue.Queue(1)
    debug_save_img_queue = queue.Queue()
    threads = []
    messages_receiver_handler = MessagesReceiverHandler()
    thread = None
    for tName in thread_names:
        if tName == THREAD_CAMERA:
            target_fps = 4
            thread = Camera(tName, logging, detection_queue, vision_queue, target_fps)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_DNN:
            num_of_frames_to_rotate = 9
            target_fps = 0
            thread = HumanDetection(tName, logging, detection_queue, target_fps, show, num_of_frames_to_rotate, SW_VERSION,
                                    FW_VERSION, debug_queue, save_images_to_disk, debug_save_img_queue)
            if simulate_warnings:  # only for debugging purpose - init app with a warning
                create_dummy_warning(thread)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_VISION:
            target_fps = 2
            thread = Vision(tName, logging, vision_queue, target_fps)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_COMMUNICATION:
            # no fps since it's blocking
            thread = Communication(tName, logging, messages_receiver_handler, port, baudrate)

        elif tName == THREAD_FILES_SAVER:
            # no fps since it's blocking
            thread = FilesSaver(tName, logging, debug_save_img_queue)

        thread.start()
        threads.append(thread)

    is_exit = False
    # if show:
    while not is_exit:
        cv2.imshow('detect', debug_queue.get())
        k = cv2.waitKey(1)
        if k % 256 == 27:
            # ESC pressed
            logging.debug("Escape hit, closing...")
            is_exit = True
            cv2.destroyAllWindows()

    # Wait for all threads to complete
    for t in threads:
        # t.exit_thread()
        t.join()

    print("Exiting Main Thread")

def create_dummy_warning(hd_thread):
    # set a single warning - start...
    hd_thread.num_of_frames_to_rotate = 3
    polygon_arr = [Point(0, 0), Point(0, 300), Point(300, 300), Point(300, 0)]
    object_class_holder = ObjectClassHolder([False, False, False, False, False, False, False, True])
    warning_message = HDSetWarningMessage(2, polygon_arr, object_class_holder, 0, 300, 20, 1, 1, True)
    hd_thread.on_set_warning_msg(warning_message)

def main():
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="path to input image")
    ap.add_argument("-s", "--show", required=False, default=False, action='store_true',
                    help="Whether to show the processed image")
    # ap.add_argument("-c", "--confidence", type=float, default=0.2, help="minimum probability to filter weak detections")
    ap.add_argument("-d", "--debug", required=False, default=False, action='store_true',
                    help="change log level to DEBUG")
    ap.add_argument("-l", "--loggingFileName", required=False, default="", help="log to a file")
    ap.add_argument("-p", "--port", required=False, help="serial port")
    ap.add_argument("-b", "--baudrate", required=False, help="serial baudrate")
    ap.add_argument("-v", "--saveimages", required=False, default=False, action='store_true', help="save images to disk")
    ap.add_argument("-m", "--simulate", required=False, default=False, action='store_true', help="simulate warnings on startup")
    args = vars(ap.parse_args())

    debug_level = logging.INFO
    args_debug = args["debug"]
    args_show = args["show"]
    args_image = args["image"]
    # args_confidence = args["confidence"]
    args_port = args["port"]
    args_baudrate = args["baudrate"]
    save_images_to_disk = args["saveimages"]
    simulate_warnings = args["simulate"]

    if args_debug:
        debug_level = logging.DEBUG

    logging_file_name = args["loggingFileName"]
    if logging_file_name != "":
        logging.basicConfig(filename=logging_file_name, level=debug_level, format='%(asctime)s: %(message)s')
    else:
        logging.basicConfig(level=debug_level, format='%(asctime)s: %(message)s')

    logging.info("************************************************")
    logging.info("************************************************")
    logging.info("******  STARTED Human Detection  ***************")
    logging.info("************************************************")
    logging.info("Application Arguments: {}".format(args))

    if args_show:
        cv2.namedWindow("detect")

    if args_image == 'c':
        thread_names = [THREAD_CAMERA, THREAD_DNN, THREAD_VISION, THREAD_COMMUNICATION, THREAD_FILES_SAVER]
        start_threads(args_show, args_port, args_baudrate, thread_names, save_images_to_disk, simulate_warnings)
    else:
        filelist = glob.glob(os.path.join(args_image, '*.png'))
        filelist.extend(glob.glob(os.path.join(args_image, '*.jpg')))
        filelist.extend(glob.glob(os.path.join(args_image, '*.bmp')))
        list_of_images = []
        for file in filelist:
            logging.info('********** ' + str(file) + ' ************')
            img = cv2.imread(file)
            list_of_images.append(img)
        _img_queue = queue.Queue()
        debug_queue = queue.Queue()
        target_fps = 0
        num_of_frames_to_rotate = 9
        logging.info("Creating HD Thread")
        hd_thread = HumanDetection(THREAD_DNN, logging, _img_queue, target_fps, True, num_of_frames_to_rotate,
                                   SW_VERSION,
                                   FW_VERSION, debug_queue)
        create_dummy_warning(hd_thread)
        hd_thread.start()
        while True:
            for i in range(len(list_of_images)):
                logging.info("Prepare to fetch an image")
                _img_queue.put(list_of_images.__getitem__(i))
                image = debug_queue.get()
                logging.info("Got an image")
                if args_show:
                    cv2.imshow('detect', image)
                    k = cv2.waitKey(1)
                    if k % 256 == 27:
                        # ESC pressed
                        logging.debug("Escape hit, closing...")
                        cv2.destroyAllWindows()
                #time.sleep(1.0)
        hd_thread.join(1)
        print("Exiting Main Thread...")


main()
