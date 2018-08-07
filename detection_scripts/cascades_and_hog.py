'''
Created on Jun 8, 2018

@author: uri
'''
import cv2
import sys
import os
import argparse
import glob
from datetime import datetime

class FindHuman:
    def __init__(self):
        lowerbody = os.path.join('data','haarcascades', 'haarcascade_lowerbody.xml')
        upperbody = os.path.join('data','haarcascades', 'haarcascade_upperbody.xml')
        self.lower_body_cascade = cv2.CascadeClassifier(lowerbody)
        self.upper_body_cascade = cv2.CascadeClassifier(upperbody)
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    
    
    def Process(self, img, show, confidence):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
        lower = self.lower_body_cascade.detectMultiScale(gray, 1.1, 3)
        faces = self.upper_body_cascade.detectMultiScale(gray, 1.1, 3)
        (hrect, weights) = self.hog.detectMultiScale(img, winStride=(4, 4), padding=(8, 8), scale=1.05)
        
        print len(faces), len(lower) , len(hrect), str(weights)
        
        for (x,y,w,h) in faces:
            print '(' + str(x) + ',' + str(y) + ') , (' + str(x+w) + ',' + str(y+h) + ')'
    
        for (x,y,w,h) in lower:
            print '(' + str(x) + ',' + str(y) + ') , (' + str(x+w) + ',' + str(y+h) + ')'
        

        for (x,y,w,h) in hrect:
            print '(' + str(x) + ',' + str(y) + ') , (' + str(x+w) + ',' + str(y+h) + ')'
			
        if show == True:
            # Mark on the image with box        
            for (x,y,w,h) in faces:
                cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,255),2)
    
            for (x,y,w,h) in lower:
                cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
         
            i = 0   
            for (x,y,w,h) in hrect:
                if (weights[i] > confidence):
                    cv2.rectangle(img,(x,y),(x+w,y+h),(255,255,0),2)
                    cv2.putText(img, str(weights[i]), (x,y), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (0,0,0), 1);
                i += 1
   
            cv2.putText(img, "Upper body", (30,30), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (0,255,255), 1);
            cv2.putText(img, "Lower body", (30,45), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (0,255,0), 1);
            cv2.putText(img, "HOG-" + str(weights), (30,60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 0.8, (255,255,0), 1);
    
        return img
    
    def FromCamera(self, video_device):
        cam = cv2.VideoCapture(video_device)
        while True:
            ret, img = cam.read()
            img = self.Process(img)
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
        fu.FromCamera(0)
    else:
        filelist = glob.glob(args["image"]) 
        for file in filelist:
            print '********** ' + str(file) + ' ************'
            print datetime.now().time()
            img = cv2.imread(file)
            img = fu.Process(img, args["show"], args["confidence"])
            if args["show"] == True:
                cv2.imshow('detect',img)
                try:
                    while cv2.getWindowProperty('detect', 0) >= 0:
                        cv2.waitKey(50)
                except:
                    pass
            print datetime.now().time()
    cv2.destroyAllWindows()
    
main()
