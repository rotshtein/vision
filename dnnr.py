#!/usr/bin/python
'''
Created on Jun 8, 2018

@author: uri
'''
import math
import queue
import threading

import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import argparse
import glob
from datetime import datetime
import serial
import logging

from protocol.bytes_converter import calc_checksum
from utils.hd_thread import HDThread
from utils.image_rotator import ImageRotator
from utils.obstruction_detector import ObstructionDetector

# SERIAL CONSTANTS
PREAMBLE_PREFIX = b'xAA'

OPCODE_SETUP_MSG = b'xB1'
OPCODE_SET_WARNING_MSG = b'0xB2'
OPCODE_CLEAR_ALL_WARNINGS_MSG = b'xB3'
OPCODE_SET_POWER_MSG = b'xB4'
OPCODE_GET_WARNING_MSG = b'xB5'

OPCODE_GET_WARNING_RESPONSE = b'xC1'
OPCODE_ACK_RESPONSE = b'xD1'
OPCODE_NACK_RESPONSE = b'xD2'

BAUD_RATE = 19200
# ROBOT_STOP_MESSAGE_HEX = "\xAA\x09\x1E\x15\x0F\xAA\x00\xFF\x61"
# ROBOT_STATUS_MESSAGE_HEX = "\xAA\x09\x1E\x16\x0F\xA7\x00\x04\x5E"

FROM_CAMERA_TH_SLEEP_SEC = 0.12
DNN_TH_SLEEP_SEC = 0.01
VISION_TH_SLEEP_SEC = 0.12
COMM_TH_SLEEP_SEC = 0.12

start_time = datetime.now()


def handle_setup_msg(message):
    pass


def handle_set_power_msg(message):
    pass


def handle_set_warning_msg(message):
    pass


def handle_set_warning_msg(message):
    pass


def handle_get_warning_msg():
    pass


def handle_clear_all_warning_msg(msg):
    pass


def convert_data_to_bytes(data):
    pass


def build_response_message(opcode, data=None):
    data_bytes = bytearray([0])
    if data is not None:
        # convert data to bytes
        convert_data_to_bytes(data)

    msg_length = bytes(data_bytes.__len__() + 4)
    res_message_bytes_array = bytearray([PREAMBLE_PREFIX, msg_length, opcode]) + data_bytes
    checksum = calc_checksum(res_message_bytes_array)
    res_message_bytes_array = res_message_bytes_array + bytearray([checksum])
    return res_message


class FindHuman:
    def __init__(self):
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]
        self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))
        # load our serialized protocol from disk
        logging.info("loading protocol...")
        self.net = cv2.dnn.readNetFromCaffe('data/caffemodels/MobileNetSSD_deploy.prototxt.txt', 'data/caffemodels/MobileNetSSD_deploy.caffemodel')

        self.rotate_counter = 0

        self.ser = serial.Serial(  # ttyUSB0 for USB port / ttyS0 for IO
            port='/dev/ttyS0',
            baudrate=BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
        )

    def communication(self):
        logging.info("Communication - Start ")
        process_start = temp_time = datetime.now()
        # read from socket
        # read first 3 bytes - msg[0]=preamble; msg[1]=length; msg[2]=opcode
        while True:
            logging.info("Communication - read(3) ")
            msg = self.ser.read(3)
            msg_in_hex = hex(int.from_bytes(msg, byteorder='little'))

            # TODO - handle set messages
            logging.info("Communication - handling 3 bytes: {}".format(msg_in_hex))

            # read preamble
            if msg_in_hex[0] != PREAMBLE_PREFIX:
                logging.error("Communication error reading Preamble. Expected=0xAA. Received={}".format(msg[0]))
                return

            # read length
            length = int.from_bytes(msg[1], byteorder='little')

            # read opcode
            opcode = msg_in_hex[2]

            # continue reading message - minus 3 preamble + length + opcode
            msg = self.ser.read(length-3)
            # handle message
            try:
                if opcode == OPCODE_SETUP_MSG:
                    handle_setup_msg(msg)
                    response = build_response_message(OPCODE_ACK_RESPONSE)
                elif opcode == OPCODE_SET_WARNING_MSG:
                    handle_set_warning_msg(msg)
                    response = build_response_message(OPCODE_ACK_RESPONSE)
                elif opcode == OPCODE_CLEAR_ALL_WARNINGS_MSG:
                    handle_clear_all_warning_msg(msg)
                    response = build_response_message(OPCODE_ACK_RESPONSE)
                elif opcode == OPCODE_SET_POWER_MSG:
                    handle_set_power_msg(msg)
                    response = build_response_message(OPCODE_ACK_RESPONSE)
                elif opcode == OPCODE_GET_WARNING_MSG:
                    get_warning_data = handle_get_warning_msg()
                    response = build_response_message(OPCODE_GET_WARNING_RESPONSE, get_warning_data)
            except:
                response = build_response_message(OPCODE_NACK_RESPONSE)

            # todo - send message
            msg = self.ser.write(response)

            msg_encoded = msg.encode("hex")
            logging.info("DNN - Received Ack Message from Robot: " + msg_encoded)
            logging.info("Communication - End. Duration=" + str(datetime.now() - process_start))


    # Warning!! do not change order of 'image' argument - it must be last!
    def dnn(self, show, set_confidence, debug, num_of_frames_to_rotate, image):
        logging.info("DNN - Start ")
        process_start = temp_time = datetime.now()
        (h, w) = image.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
        logging.debug("DNN - blobFromImage Resize. Duration= " + str(datetime.now() - temp_time))

        if self.rotate_counter >= num_of_frames_to_rotate:
            logging.info("DNN - Rotating image by 90 deg...")
            temp_time = datetime.now()
            image_rotator = ImageRotator()
            image_rotated = image_rotator.rotate_image(image, 90)
            image = image_rotator.crop_around_center(image_rotated,
                                                     *image_rotator.largest_rotated_rect(w, h, math.radians(90)))
            self.rotate_counter = 0
            logging.info("DNN - Rotating image Duration=" + str(datetime.now() - temp_time))

        # pass the blob through the network and obtain the detections and predictions
        logging.debug("DNN - Computing object detections...")
        temp_time = datetime.now()
        self.net.setInput(blob)
        detections = self.net.forward()
        logging.info("DNN - setInput() + forward(). Duration=" + str(datetime.now() - temp_time))

        # loop over the detections
        for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the prediction
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by ensuring the `confidence` is greater than the minimum confidence
            if confidence > set_confidence:
                # extract the index of the class label from the `detections`,
                # then compute the (x, y)-coordinates of the bounding box for
                # the object
                idx = int(detections[0, 0, i, 1])
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                # display the prediction
                label = "{}: {:.2f}% {} {}".format(self.CLASSES[idx], confidence * 100, startX, startY)
                logging.info("DNN - {}".format(label))

                # TODO - add result to protocol to ROBOT
                if self.CLASSES[idx] == "person" and (h - endY) < HEIGHT_THR:
                    logging.info("DNN - Send Stop Message to Robot")
                    # stop robot
                    # self.ser.write(ROBOT_STOP_MESSAGE_HEX_STR.decode("hex"))
                    # self.ser.write(ROBOT_STOP_MESSAGE_HEX)
                    # if debug == True:
                    #     try:
                    #         time.sleep(0.1)
                    #         ret_value = self.ser.readline()
                    #         # TODO - add ACK handling ?
                    #         logging.info("DNN - Received Ack Message from Robot: " + ret_value.encode("hex"))
                    #     except Exception as e:
                    #         logging.info("DNN - Received Exception: " + str(e))
                else:
                    pass
                    # self.ser.write(ROBOT_STATUS_MESSAGE_HEX)

                if show:
                    cv2.rectangle(image, (startX, startY), (endX, endY),
                                  self.COLORS[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)

        if show:
            cv2.imshow('detect', image)
            k = cv2.waitKey(1)
            if k % 256 == 27:
                # ESC pressed
                logging.info("FromCamera - Escape hit, closing...")
                return

        logging.info("DNN - End. Duration=" + str(datetime.now() - process_start))
        self.rotate_counter += 1

    def vision(self, obs_detector, img):
        gray_image = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        tiles_to_ignore = [0, 1, 2, 6, 7, 8]
        obstructed_tiles = obs_detector.is_last_frames_obstructed(gray_image, tiles_to_ignore)
        if obstructed_tiles.__len__() != 0:
            logging.info("Vision - WARNING! Camera is being Obstructed by Tiles:{}.".format(obstructed_tiles))

    def fromCamera(self, camera, rawCapture):
        temp_time = start_time = datetime.now()
        logging.info("FromCamera - Start.")
        camera.capture(rawCapture, format="bgr", use_video_port=True)
        logging.info("FromCamera - Capturing image. Duration= " + str(datetime.now() - temp_time))
        img = rawCapture.array

        temp_time = datetime.now()
        rawCapture.truncate(0)
        logging.info("FromCamera - Capturing truncate Duration= " + str(datetime.now() - temp_time))

        logging.info("FromCamera - End. Total Duration=" + str(datetime.now() - start_time))
        return img


def start_threads(fu, show, debug):
    thread_names = ["Thread_FromCamera", "Thread_DNN", "Thread_Vision"]
                    # , "Thread_Comm"]
    # max size = 2 - we don't want old images!
    img_queue = queue.Queue(2)
    queue_lock = threading.Lock()
    threads = []
    thread_id = 1
    confidence = 0.2
    thread = None
    for tName in thread_names:
        if thread_id == 1:
            # "Thread Capture" - PUT IN QUEUE
            is_get_from_queue = False
            camera = PiCamera()
            # camera.resolution = (300, 300)
            rawCapture = PiRGBArray(camera)
            # set fromCamera args
            args = [camera, rawCapture]
            thread = HDThread(logging, thread_id, tName, img_queue, queue_lock, FROM_CAMERA_TH_SLEEP_SEC,
                              is_get_from_queue, fu,
                              "fromCamera", args)

        elif thread_id == 2:
            # "Thread DNN" - GET FROM QUEUE
            is_get_from_queue = True
            num_of_frames_to_rotate = 9
            # set dnn args
            args = [show, confidence, debug, num_of_frames_to_rotate]
            thread = HDThread(logging, thread_id, tName, img_queue, queue_lock, DNN_TH_SLEEP_SEC, is_get_from_queue, fu,
                              "dnn", args)

        elif thread_id == 3:
            # "Thread Vision" - GET FROM QUEUE
            is_get_from_queue = True
            obs_detector = ObstructionDetector(logging)
            logging.info("Starting Obstruction Detector . Variance Threshold={}.".format(obs_detector.variance))
            # set vision args
            args = [obs_detector]
            thread = HDThread(logging, thread_id, tName, img_queue, queue_lock, VISION_TH_SLEEP_SEC, is_get_from_queue,
                              fu,
                              "vision", args)

        elif thread_id == 4:
            args = []
            thread = HDThread(logging, thread_id, tName, img_queue, queue_lock, COMM_TH_SLEEP_SEC, is_get_from_queue,
                              fu,
                              "communication", args)
        thread.start()
        threads.append(thread)
        thread_id += 1

    # Wait for queue to empty
    # while not img_queue.empty():
    #     pass

    # Notify threads it's time to exit
    # exitFlag = 1

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
    logging.info(
        "Threads sleep [sec]: FromCamera={}, DNN={}, VISION={}".format(FROM_CAMERA_TH_SLEEP_SEC, DNN_TH_SLEEP_SEC,
                                                                       VISION_TH_SLEEP_SEC))

    if args_show:
        cv2.namedWindow("detect")

    fu = FindHuman()

    if args_image == 'c':
        start_threads(fu, args_show, args_debug)
        # fu.FromCamera(0, 0.2, args["show"], args["debug"])
    else:
        filelist = glob.glob(args_image)
        for file in filelist:
            logging.info('********** ' + str(file) + ' ************')
            start_time = datetime.now()
            img = cv2.imread(file)
            img = fu.dnn(args_show, args_confidence, args_debug, img)
            if args_show == True:
                cv2.imshow('detect', img)
                try:
                    while cv2.getWindowProperty('detect', 0) >= 0:
                        k = cv2.waitKey(50)
                        if k > 0:
                            break;
                except:
                    pass
            logging.info(datetime.now() - start_time)
    cv2.destroyAllWindows()


main()
