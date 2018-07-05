#!/usr/bin/python
'''
Created on Jul 4, 2018

@author: ziv
'''

import cv2

LOW_INTENSITY_THRESHOLD = 20
HIGH_INTENSITY_THRESHOLD = 80

class ObstructionDetector:
    def __init__(self, width=300, height=300, rows=3, columns=3):
        self.width = width
        self.height = height
        self.rows = rows
        self.columns = columns
    
    def is_obstructed(image):
        # divide the image into a matrix of [rows,columns] and check if the center is above threshold
        for row in range(rows):
            for col in range(columns):
                x,y = get_center_of_tile(row, col)
                is_pixel_obstructed(image, x, y)

    def get_center_of_tile(row, col):
        pixels_in_a_row = self.height/self.rows
        pixels_in_a_col = self.width/self.columns
        return (pixels_in_a_row*(0.5+row), pixels_in_a_col*(0.5+col))        
    
    
    def is_pixel_obstructed(image, x, y):
        intensity = calcualte_intensity(image, x, y)
        # todo - add compare to last ? 
        if intensity<LOW_INTENSITY_THRESHOLD and intensity>HIGH_INTENSITY_THRESHOLD
            return True
        return False

     



def main():
    ObstructionDetector obs_detector = new ObstructionDetector()
    # get image from camera
    # is image obstructed in all center areas of tiles
    