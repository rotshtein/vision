#!/usr/bin/python
'''
Created on Jun 8, 2018

@author: uri
'''
import numpy as np
import cv2
import argparse
import glob
from datetime import datetime
from matplotlib import pyplot as plt


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
        (h, w) = image.shape[:2]
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        gray_image = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2RGB)
        
       
        blob = cv2.dnn.blobFromImage(cv2.resize(gray_image, (300, 300)), 0.007843, (300, 300), 127.5)
        
        histr = []
        color = ('b','g','r')
        for i,col in enumerate(color):
            histr = cv2.calcHist([gray_image],[i],None,[16],[0,256])
            plt.plot(histr,color = col)
            plt.xlim([0,16])
            
        plt.show(False)
        plt.pause(0.05)
        plt.clf()
        print np.std(histr, axis=0)
        
        '''
        hist = cv2.calcHist([image],[0],None,[16],[0,256])
        
        high_sum = 0;
        low_sum = 0;
        for i in range(6,15):
            high_sum += hist[i]
        
        for i in range(0,5):
            low_sum += hist[i]
        
        if (low_sum > high_sum):
            print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'

       
        print hist[0], hist[1], hist[2], hist[3], hist[4], hist[5], hist[6], hist[7] 
        
        if (hist[7] < 1000):
            print '>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
        '''
        # pass the blob through the network and obtain the detections and
        # predictions
        if (not show):
            print("[INFO] computing object detections...")
        self.net.setInput(blob)
        detections = self.net.forward()

        # loop over the detections
        for i in np.arange(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with the
            # prediction
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
                label = "{}: {:.2f}%".format(self.CLASSES[idx], confidence * 100)

                if show == True:
                    cv2.rectangle(gray_image, (startX, startY), (endX, endY),
                    self.COLORS[idx], 2)
                    y = startY - 15 if startY - 15 > 15 else startY + 15
                    cv2.putText(gray_image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.COLORS[idx], 2)
                else:
                    print("[INFO] {}".format(label))                
        return gray_image
    
    def FromCamera(self, video_device, confidence):
        cam = cv2.VideoCapture(video_device)
        width = cam.get(cv2.CAP_PROP_FRAME_WIDTH )   # float
        height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT ) # float
        print 'Camera picture size {}x{}'.format(width,height)
        
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
        for img_file in filelist:
            print '********** ' + str(img_file) + ' ************'
            start = datetime.now()
            img = cv2.imread(img_file)
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
