"""
Created on Aug 14, 2018

@author: ziv
"""
import queue
import cv2
import argparse
import glob
from datetime import datetime
import logging

from camera import Camera
from communication import Communication
from messages_receiver_handler import MessagesReceiverHandler
from human_detection import HumanDetection
from protocol.bytes_converter import calc_checksum
from vision import Vision

SW_VERSION = "0.1"
FW_VERSION = "0.1"

THREAD_COMMUNICATION = "Thread_Communication"
THREAD_VISION = "Thread_Vision"
THREAD_DNN = "Thread_DNN"
THREAD_CAMERA = "Thread_Camera"


def start_threads(show, debug):
    thread_names = [THREAD_CAMERA, THREAD_DNN, THREAD_VISION, THREAD_COMMUNICATION]
    # max size = 2 - we don't want old images!
    img_queue = queue.Queue(2)
    threads = []
    messages_receiver_handler = MessagesReceiverHandler()
    thread = None
    for tName in thread_names:
        if tName == THREAD_CAMERA:
            fps = 4
            thread = Camera(tName, logging, img_queue, fps)

        elif tName == THREAD_DNN:
            num_of_frames_to_rotate = 9
            confidence = 0.2
            fps = 0
            thread = HumanDetection(tName, logging, img_queue, fps, confidence, show, num_of_frames_to_rotate, debug,
                                    SW_VERSION, FW_VERSION)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_VISION:
            fps = 3
            thread = Vision(tName, logging, img_queue, fps)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_COMMUNICATION:
            # no fps since it's blocking
            thread = Communication(tName, logging, messages_receiver_handler)

        thread.start()
        threads.append(thread)

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print("Exiting Main Thread")


def main():
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="path to input image")
    ap.add_argument("-s", "--show", required=False, default=False, action='store_true',
                    help="Whether to show the processed image")
    ap.add_argument("-c", "--confidence", type=float, default=0.2, help="minimum probability to filter weak detections")
    ap.add_argument("-d", "--debug", required=False, default=False, action='store_true',
                    help="change log level to DEBUG")
    ap.add_argument("-l", "--loggingFileName", required=False, default="", help="change log level to DEBUG")
    args = vars(ap.parse_args())

    debug_level = logging.INFO
    args_debug = args["debug"]
    args_show = args["show"]
    args_image = args["image"]
    args_confidence = args["confidence"]

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
        start_threads(args_show, args_debug)
    else:
        filelist = glob.glob(args_image)
        for file in filelist:
            logging.info('********** ' + str(file) + ' ************')
            start_time = datetime.now()
            img = cv2.imread(file)
            num_of_frames_to_rotate = 9
            confidence = 0.2
            fps = 0
            _img_queue = queue.Queue(2)
            _img_queue.put(img)
            thread = HumanDetection(THREAD_DNN, logging, _img_queue, fps, confidence, True, num_of_frames_to_rotate, False,
                                    SW_VERSION, FW_VERSION)
            thread.run()
            if args_show:
                cv2.imshow('detect', img)
                try:
                    while cv2.getWindowProperty('detect', 0) >= 0:
                        k = cv2.waitKey(50)
                        if k > 0:
                            break
                except:
                    pass
            logging.info(datetime.now() - start_time)
    cv2.destroyAllWindows()


main()
