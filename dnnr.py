"""
Created on Aug 14, 2018

@author: ziv
"""
import os
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


def start_threads(show, port, baudrate):
    thread_names = [THREAD_CAMERA, THREAD_DNN, THREAD_VISION, THREAD_COMMUNICATION]
    # thread_names = [THREAD_COMMUNICATION]
    # max size = 2 - we don't want old images!
    img_queue = queue.Queue(2)
    debug_queue = queue.Queue(1)
    threads = []
    messages_receiver_handler = MessagesReceiverHandler()
    thread = None
    for tName in thread_names:
        if tName == THREAD_CAMERA:
            target_fps = 4
            thread = Camera(tName, logging, img_queue, target_fps)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_DNN:
            num_of_frames_to_rotate = 9
            target_fps = 0
            thread = HumanDetection(tName, logging, img_queue, target_fps, show, num_of_frames_to_rotate, SW_VERSION,
                                    FW_VERSION, debug_queue)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_VISION:
            target_fps = 2
            thread = Vision(tName, logging, img_queue, target_fps)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_COMMUNICATION:
            # no fps since it's blocking
            thread = Communication(tName, logging, messages_receiver_handler, port, baudrate)

        thread.start()
        threads.append(thread)

    is_exit = False
    if show:
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


def main():
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="path to input image")
    ap.add_argument("-s", "--show", required=False, default=False, action='store_true',
                    help="Whether to show the processed image")
    ap.add_argument("-c", "--confidence", type=float, default=0.2, help="minimum probability to filter weak detections")
    ap.add_argument("-d", "--debug", required=False, default=False, action='store_true',
                    help="change log level to DEBUG")
    ap.add_argument("-l", "--loggingFileName", required=False, default="", help="log to a file")
    ap.add_argument("-p", "--port", required=False, help="serial port")
    ap.add_argument("-b", "--baudrate", required=False, help="serial baudrate")
    args = vars(ap.parse_args())

    debug_level = logging.INFO
    args_debug = args["debug"]
    args_show = args["show"]
    args_image = args["image"]
    args_confidence = args["confidence"]
    args_port = args["port"]
    args_baudrate = args["baudrate"]

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
        start_threads(args_show, args_port, args_baudrate)
    else:
        filelist = glob.glob(os.path.join(args_image, '*.png'))
        _img_queue = queue.Queue()
        for file in filelist:
            logging.info('********** ' + str(file) + ' ************')
            img = cv2.imread(file)
            _img_queue.put(img)
        initial_queue_size = _img_queue.qsize()
        debug_queue = queue.Queue()
        target_fps = 0
        num_of_frames_to_rotate = 9
        thread = HumanDetection(THREAD_DNN, logging, _img_queue, target_fps, True, num_of_frames_to_rotate, SW_VERSION,
                                FW_VERSION, debug_queue)
        thread.start()
        index = 0
        if args_show:
            while initial_queue_size > 0:
                cv2.imshow('detect{}'.format(index), debug_queue.get())
                index += 1
                print("index={}".format(index))
                initial_queue_size -= 1
            k = cv2.waitKey()
            if k % 256 == 27:
                # ESC pressed
                logging.debug("Escape hit, closing...")
                cv2.destroyAllWindows()
        thread.join(1)
        print("Exiting Main Thread...")


main()
