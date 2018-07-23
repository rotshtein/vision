#!/usr/bin/python
'''
Created on Jun 8, 2018

@author: uri
'''
import queue
import threading

import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import sys
import os
import argparse
import glob
from datetime import datetime
import time
import serial
import logging

from hd_thread import HDThread
from obstruction_detector import ObstructionDetector

HEIGHT_THR = 150

# SERIAL CONSTANTS
BAUD_RATE = 19200
ROBOT_STOP_MESSAGE_HEX = "\xAA\x09\x1E\x15\x0F\xAA\x00\xFF\x61"
ROBOT_STATUS_MESSAGE_HEX = "\xAA\x09\x1E\x16\x0F\xA7\x00\x04\x5E"

start_time = datetime.now()


class FindHuman:
    def __init__(self):
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                        "sofa", "train", "tvmonitor"]
        self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))
        # load our serialized model from disk
        logging.info("loading model...")
        self.net = cv2.dnn.readNetFromCaffe('MobileNetSSD_deploy.prototxt.txt', 'MobileNetSSD_deploy.caffemodel')

        self.ser = serial.Serial(  # ttyUSB0 for USB port / ttyS0 for IO
            port='/dev/ttyS0',
            baudrate=BAUD_RATE,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0.1
        )

    def dnn(self, show, set_confidence, debug, image):
        logging.info("DNN - Start ")
        process_start = temp_time = datetime.now()
        (h, w) = image.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
        logging.debug("DNN - blobFromImage Resize. Duration= " + str(datetime.now() - temp_time))

        # pass the blob through the network and obtain the detections and
        # predictions
        logging.debug("DNN - Computing object detections...")
        temp_time = datetime.now()
        self.net.setInput(blob)
        detections = self.net.forward()
        logging.info("DNN - setInput() + forward(). Duration=" + str(datetime.now() - temp_time))

        if show:
            cv2.imshow('detect', image)

        # loop over the detections
        for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
            # print '********** ' + str(file) + ' ************'
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by ensuring the `confidence` is
            # greater than the minimum confidence
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
                    # time.sleep(0.1)
                    # if debug == True:
                    #     try:
                    #         ret_value = self.ser.readline()
                    #         # TODO - add ACK handling ?
                    #         logging.info("DNN - Received Ack Message from Robot: " + ret_value.encode("hex"))
                    #     except Exception as e:
                    #         logging.info("DNN - Received Exception: " + str(e))
                else:
                    pass
                    # self.ser.write(ROBOT_STATUS_MESSAGE_HEX)

                if show:
                    show_start = datetime.now()
                    cv2.rectangle(image, (startX, startY), (endX, endY),
                                  self.COLORS[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)
                    k = cv2.waitKey(1)
                    if k % 256 == 27:
                        # ESC pressed
                        logging.info("FromCamera - Escape hit, closing...")
                        return
                    logging.info("DNN - Show Window Duration= " + str(datetime.now() - show_start))
                    logging.info("DNN - getWindowProperty={}".format(cv2.getWindowProperty('detect', 0) < 0))

        logging.info("DNN - End. Duration=" + str(datetime.now() - process_start))

    def vision(self, obs_detector, img):
        gray_image = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        tiles_to_ignore = [0, 1, 2, 6, 7, 8]
        obstructed_tiles = obs_detector.is_last_frames_obstructed(gray_image, tiles_to_ignore)
        if obstructed_tiles.__len__() != 0:
            logging.info("Vision - WARNING! Camera is being Obstructed by Tiles:{}.".format(obstructed_tiles))

    def fromCamera(self, show, camera, rawCapture):
        # while True:
        temp_time = start_time = datetime.now()
        logging.info("FromCamera - Start.")

        camera.capture(rawCapture, format="bgr", use_video_port=True)
        logging.info("FromCamera - Capturing image. Duration= " + str(datetime.now() - temp_time))
        img = rawCapture.array

        # img = self.Process(img, True, confidence, debug)

        # temp_time = datetime.now()
        # logging.info("Obstruction Detection Duration= {}".format(str(datetime.now() - temp_time)))

        temp_time = datetime.now()
        rawCapture.truncate(0)
        logging.info("FromCamera - Capturing truncate Duration= " + str(datetime.now() - temp_time))

        logging.info("FromCamera - End. Total Duration=" + str(datetime.now() - start_time))
        return img
    # cam.release()


def is_point_in_polygon(point, polygon):
    polygonLength = polygon.size, i = 0
    inside = False
    pointX = point.X, pointY = point.Y
    endPoint = polygon[polygonLength - 1]
    endX = endPoint.X
    endY = endPoint.Y
    while i < polygonLength:
        startX = endX
        startY = endY
        endPoint = polygon[i]
        i += 1
        endX = endPoint.X
        endY = endPoint.Y
        pointY_inside_segment = (endY > pointY ^ startY > pointY)  # ? pointY inside[startY; endY] segment ?
        under_segment = ((pointX - endX) < (pointY - endY) * (startX - endX) / (startY - endY))  # is under the segment?
        _inside = pointY_inside_segment and under_segment
        inside ^= _inside
    return inside


def start_threads(fu, show, debug):
    thread_names = ["Thread_FromCamera", "Thread_DNN", "Thread_Vision"]
    # max size = 3 - due to
    img_queue = queue.Queue(2)
    threads = []
    thread_id = 1
    confidence = 0.2
    for tName in thread_names:
        if thread_id == 1:
            # "Thread Capture" - PUT IN QUEUE
            is_get_from_queue = False
            thread_sleep_sec = 0.2
            camera = PiCamera()
            # camera.resolution = (300, 300)
            rawCapture = PiRGBArray(camera)
            args = [show, camera, rawCapture]
            thread = HDThread(logging, thread_id, tName, img_queue, thread_sleep_sec, is_get_from_queue, fu, "fromCamera", args)

        elif thread_id == 2:
            # "Thread DNN" - GET FROM QUEUE
            is_get_from_queue = True
            thread_sleep_sec = 0.01
            args = [show, confidence, debug]
            thread = HDThread(logging, thread_id, tName, img_queue, thread_sleep_sec, is_get_from_queue, fu, "dnn", args)

        elif thread_id == 3:
            # "Thread Vision" - GET FROM QUEUE
            is_get_from_queue = True
            thread_sleep_sec = 0.3
            obs_detector = ObstructionDetector(logging)
            logging.info("Starting Obstruction Detector . Variance Threshold={}.".format(obs_detector.variance))
            args = [obs_detector]
            thread = HDThread(logging, thread_id, tName, img_queue, thread_sleep_sec, is_get_from_queue, fu, "vision", args)

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
