#!/usr/bin/python
'''
Created on Jun 8, 2018

@author: uri
'''
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

from obstruction_detector import ObstructionDetector

BAUD_RATE = 19200
MAX_HEIGHT = 480
HEIGHT_THR = 150
#ROBOT_STOP_MESSAGE_HEX_STR = 'AA091E150FAA00FF61'
ROBOT_STOP_MESSAGE_HEX = "\xAA\x09\x1E\x15\x0F\xAA\x00\xFF\x61"
ROBOT_STATUS_MESSAGE_HEX = "\xAA\x09\x1E\x16\x0F\xA7\x00\x04\x5E"
#ROBOT_STATUS_MESSAGE_HEX_STR = 'AA091E160FA700045E'

start_time = datetime.now()


class FindHuman:
    def __init__(self):
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	        "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	        "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	       "sofa", "train", "tvmonitor"]
        self.COLORS = np.random.uniform(0, 255, size=(len(self.CLASSES), 3))
        # load our serialized model from disk
        print("[INFO] loading model...")
        self.net = cv2.dnn.readNetFromCaffe('MobileNetSSD_deploy.prototxt.txt', 'MobileNetSSD_deploy.caffemodel')                
        self.ser = serial.Serial( #ttyUSB0
               port='/dev/ttyS0',
               baudrate = BAUD_RATE,
               parity=serial.PARITY_NONE,
               stopbits=serial.STOPBITS_ONE,
               bytesize=serial.EIGHTBITS,
               timeout=0.1
            )
    
    def Process(self, image, show, set_confidence, debug):
        global start_time
        (h, w) = image.shape[:2]
        print_info("Process - Start ")
        process_start = temp_time = datetime.now()
        blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843, (300, 300), 127.5)
        print_info("Process - blobFromImage Resize. Duration= " + str(datetime.now() - temp_time))

        # pass the blob through the network and obtain the detections and
        # predictions
        print_info("Process - Computing object detections...")
        temp_time = datetime.now()
        self.net.setInput(blob)
        detections = self.net.forward()
        print_info("Process - setInput() + forward(). Duration=" + str(datetime.now() - temp_time))

        # loop over the detections
        for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
            #print '********** ' + str(file) + ' ************'
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
                print_info("{}".format(label))
                # todo - uri - take thresholds (height) from configuration file
                if self.CLASSES[idx]=="person" and (MAX_HEIGHT - endY) < HEIGHT_THR:
                    print_info("Send Stop Message to Robot")
                    # stop robot
                    #self.ser.write(ROBOT_STOP_MESSAGE_HEX_STR.decode("hex"))
                    self.ser.write(ROBOT_STOP_MESSAGE_HEX)
                    #time.sleep(0.1)
                    if debug == True:
                        try:
                            ret_value = self.ser.readline()
                            # TODO - add ACK handling ?
                            print(str(datetime.now()) + " - [INFO] Received Ack Message from Robot: " + ret_value.encode("hex"))
                        except Exception, e:
                            print(str(datetime.now()) + " - [INFO] Received Exception: " + str(e))
                else:
                    self.ser.write(ROBOT_STATUS_MESSAGE_HEX)
                    
                if show == True:
                    cv2.rectangle(image, (startX, startY), (endX, endY),
                    self.COLORS[idx], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)
        print_info("Process End. Duration=" + str(datetime.now() - process_start))
        return image
    
    def FromCamera(self, video_device, confidence, show, debug):
        global start_time
        camera = PiCamera()
        rawCapture = PiRGBArray(camera)
        
        time.sleep(0.1)
        #cam = cv2.VideoCapture(video_device)

        obs_detector = ObstructionDetector()

        while True:
            #ret, img = cam.read()
            temp_time = start_time = datetime.now()
            print_info("************ FromCamera - Start.")
            camera.capture(rawCapture, format="bgr")
            print_info("Capturing image. Duration= " + str(datetime.now() - temp_time))
            img=rawCapture.array
            img = self.Process(img, True, confidence, debug)

            temp_time = datetime.now()
            if obs_detector.is_last_frames_obstructed(img):
                print_info("WARNING! Camera is being Obstructed")
            print_info("Obstruction Detection Duration= " + str(datetime.now() - temp_time))

            if show:
                show_start = datetime.now()
                cv2.imshow('detect',img)
                print_info("Show Window Duration= " + str(datetime.now() - show_start))

            temp_time = datetime.now()
            rawCapture.truncate(0)
            print_info("Capturing truncate Duration= " + str(datetime.now() - temp_time))
            k = cv2.waitKey(1)
    
            if k%256 == 27:
                # ESC pressed
                print("Escape hit, closing...")
                break
            print_info("************ FromCamera - End. Total Duration=" + str(datetime.now() - start_time))

            #if (show) & (cv2.getWindowProperty('detect', 0) < 0):
            #    break
        #cam.release()
            
def print_info(message):
    print(str(datetime.now()) + " - [INFO] " + message)

        
def main ():
	# construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True,help="path to input image")
    ap.add_argument("-s", "--show", required=False, default=False, action='store_true',help="Whether to show the processed image")
    ap.add_argument("-c", "--confidence", type=float, default=0.2, help="minimum probability to filter weak detections")
    ap.add_argument("-d", "--debug", required=False, default=False, action='store_true',help="Whether to debug")
    args = vars(ap.parse_args())
	
    if args["show"] == True:
        cv2.namedWindow("detect")
    print "Debug_Mode=" + str(args["debug"])
    
    fu=FindHuman()
    
    if (args["image"] == 'c'):
        fu.FromCamera(0, 0.2, args["show"], args["debug"])
    else:
        filelist = glob.glob(args["image"]) 
        for file in filelist:
            print '********** ' + str(file) + ' ************'
            start_time = datetime.now()
            img = cv2.imread(file)
            img = fu.Process(img, args["show"], args["confidence"], args["debug"])
            if args["show"] == True:
                cv2.imshow('detect',img)
                try:
                    while cv2.getWindowProperty('detect', 0) >= 0:
                        k = cv2.waitKey(50)
                        if k > 0:
                            break;
                except:
                    pass
            print datetime.now()- start_time
    cv2.destroyAllWindows()
    
main()
