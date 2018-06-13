#!/usr/bin/python
'''
Created on Jun 8, 2018

@author: uri
'''
from scipy.spatial import distance as dist
import numpy as np
import cv2
import sys
import os
import argparse
import glob
from datetime import datetime
import imutils
from imutils import perspective
from imutils import contours

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
    
    
    
    def Process(self, image, show, set_confidence):
        #image = cv2.GaussianBlur(image, (7, 7), 0)
        edged = cv2.Canny(image, 100, 200)

        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if imutils.is_cv2() else cnts[1]
        
        
        orig = image.copy()
        # loop over the contours individually
        for c in cnts:
            # if the contour is not sufficiently large, ignore it
            if cv2.contourArea(c) < 100:
                continue
         
            # compute the rotated bounding box of the contour
            orig = image.copy()
            box = cv2.minAreaRect(c)
            box = cv2.cv.BoxPoints(box) if imutils.is_cv2() else cv2.boxPoints(box)
            box = np.array(box, dtype="int")
         
            # order the points in the contour such that they appear
            # in top-left, top-right, bottom-right, and bottom-left
            # order, then draw the outline of the rotated bounding
            # box
            box = perspective.order_points(box)
            cv2.drawContours(orig, [box.astype("int")], -1, (0, 255, 0), 2)
         
            # loop over the original points and draw them
            for (x, y) in box:
                cv2.circle(orig, (int(x), int(y)), 5, (0, 0, 255), -1)
        return orig
        
    def FromCamera(self, video_device, confidence):
        cam = cv2.VideoCapture(video_device)
        while True:
            ret, img = cam.read()
            img = self.Process(img, True, confidence)
            cv2.imshow('detect',img)
            if not ret:
                break
            k = cv2.waitKey(1)
    
            if k%256 == 27:
                # ESC pressed
                print("Escape hit, closing...")
                break
        
            if (cv2.getWindowProperty('detect', 0) < 0):
                break
        cam.release()
        
def main ():
	# construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True,help="path to input image")
    ap.add_argument("-s", "--show", required=False, default=False, action='store_true',help="Whether to show the processed image")
    ap.add_argument("-c", "--confidence", type=float, default=0.2, help="minimum probability to filter weak detections")
    args = vars(ap.parse_args())
	
    if args["show"] == True:
        cv2.namedWindow("detect")
    
    fu=FindHuman()
    
    if (args["image"] == 'c'):
        fu.FromCamera(0, 0.2)
    else:
        filelist = glob.glob(args["image"]) 
        for file in filelist:
            print '********** ' + str(file) + ' ************'
            start = datetime.now()
            img = cv2.imread(file)
            img = fu.Process(img, args["show"], args["confidence"])
            if args["show"] == True:
                cv2.imshow('detect',img)
                try:
                    while cv2.getWindowProperty('detect', 0) >= 0:
                        k = cv2.waitKey(50)
                        if k > 0:
                            break;
                except:
                    pass
            print datetime.now()- start
    cv2.destroyAllWindows()
    
main()
