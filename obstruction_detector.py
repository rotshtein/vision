#!/usr/bin/python
'''
Created on Jul 4, 2018

@author: ziv
'''
import numpy as np

LOW_INTENSITY_THRESHOLD = 110
HIGH_INTENSITY_THRESHOLD = 250
INTENSITY_VARIANCE_THRESHOLD = 1500


class ObstructionDetector(object):
    """
    ObstructionDetector - this class detects if a set of images are being obstructed by an object
    An example for obstruction - when the camera is being covered by an object such as a hand preventing the camera's view
    This will cause the measured intensity value to be low
    This class divides the image to a matrix of tiles and measures the value of the tile's center points
    It keeps the result of the last frames - the number of frames is defined by the user in the constructor
    """

    def __init__(self, rows=3, columns=3, num_of_frames_to_validate=5):
        self.rows = rows
        self.columns = columns
        self.num_of_frames_to_validate = num_of_frames_to_validate
        self.last_frames_obstructed = [False] * num_of_frames_to_validate  # type:[bool]
        self.index = 0

    def is_last_frames_obstructed(self, image):
        """
        :param image:
        :return: True if all last frames are obstructed
        """
        self.height = image.shape[0]
        self.width = image.shape[1]
        # define constants
        self.pixels_in_a_tile_row = self.height / self.rows
        self.pixels_in_a_tile_col = self.width / self.columns

        self.__validate_frame_and_add_result_to_list(image)
        # check if the last frames are obstructed - only if all of them are True then image is obstructed
        return self.last_frames_obstructed.count(True) == self.num_of_frames_to_validate

    def __validate_frame_and_add_result_to_list(self, image):
        result = self.__is_image_obstructed(image)
        self.last_frames_obstructed[self.index] = result
        self.index = (self.index + 1) % self.num_of_frames_to_validate

    def __is_image_obstructed(self, image):
        """
        :param image:
        :return: True if all tile's intensity is below the threshold or inside the variance
        """
        # divide the image into a matrix of [rows,columns] and check if the center is obstructed
        intensity_below_threshold_temp_list = []
        variance_temp_list = []
        for row in range(self.rows):
            for col in range(self.columns):
                center_row, center_col = self.__get_center_coordinate_of_tile(row, col)
                intensity = image[center_row, center_col]  # type:[]
                # print "intensity={} of point=[{},{}]".format(intensity, center_col, center_row)
                variance_temp_list.append(intensity)
                intensity_below_threshold_temp_list.append(self.__is_pixel_intensity_below_threshold(intensity))

        is_below_threshold = self.__is_all_points_intensity_below_threshold(intensity_below_threshold_temp_list)
        # if intensity is below variance --> this means image is similar in all detected points ==> image is blocked
        is_below_variance_threshold = self.__is_all_points_intensity_below_variance_threshold(variance_temp_list)
        is_obstructed = is_below_threshold or is_below_variance_threshold
        return is_obstructed

    def __is_all_points_intensity_below_variance_threshold(self, variance_temp_list):
        var = np.var(variance_temp_list, axis=0)  # axis=0 for calculating the arrays vertically [r, g, b]
        print "variance=" + str(var)
        return all(var_color < INTENSITY_VARIANCE_THRESHOLD for var_color in var)

    def __is_all_points_intensity_below_threshold(self, intensity_below_threshold_temp_list):
        return intensity_below_threshold_temp_list.count(False) == 0

    def __get_center_coordinate_of_tile(self, row, col):
        return int(self.pixels_in_a_tile_row * (0.5 + row)), int(self.pixels_in_a_tile_col * (0.5 + col))

    def __is_pixel_intensity_below_threshold(self, intensity):
        """
        below threshold ==> image is dark ==> image is blocked
        :param intensity:
        :return:
        """
        if all(rgb < LOW_INTENSITY_THRESHOLD for rgb in
               intensity):  # todo also add the sun --> if intensity > HIGH_INTENSITY_THRESHOLD:
            return True
        return False

# def main():
#     obs_detector = ObstructionDetector()
# get image from camera
# is image obstructed in all center areas of tiles
