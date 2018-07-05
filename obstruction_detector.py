#!/usr/bin/python
'''
Created on Jul 4, 2018

@author: ziv
'''

LOW_INTENSITY_THRESHOLD = 10
HIGH_INTENSITY_THRESHOLD = 250


class ObstructionDetector(object):
    """
    ObstructionDetector - this class detects if a set of images are being obstructed by an object
    An example for obstruction - when the camera is being covered by an object such as a hand preventing the camera's view
    This will cause the measured intensity value to be low
    This class divides the image to a matrix of tiles and measures the value of the tile's center points
    It keeps the result of the last frames - the number of frames is defined by the user in the constructor
    """

    def __init__(self, width=300, height=300, rows=3, columns=3, num_of_frames=5):
        self.width = width
        self.height = height
        self.rows = rows
        self.columns = columns
        # define constants
        self.pixels_in_a_tile_row = self.height / self.rows
        self.pixels_in_a_tile_col = self.width / self.columns
        self.num_of_frames = num_of_frames
        self.last_frames_obstructed = [False] * num_of_frames  # type:[bool]
        self.index = 0

    def is_last_frames_obstructed(self, image):
        """
        :param image:
        :return: True if all last frames are obstructed
        """
        self.__add_new_frame_result_to_list(image)
        # check if the last frames are obstructed - only if all of them are True then image is obstructed
        return self.last_frames_obstructed.count(True) == self.num_of_frames

    def __add_new_frame_result_to_list(self, image):
        result = self.__is_image_obstructed(image)
        self.last_frames_obstructed.insert(self.index, result)
        self.index = (self.index + 1) % self.num_of_frames

    def __is_image_obstructed(self, image):
        # divide the image into a matrix of [rows,columns] and check if the center is obstructed
        for row in range(self.rows):
            for col in range(self.columns):
                x, y = self.__get_center_coordinate_of_tile(row, col)
                if self.__is_pixel_obstructed(image, x, y):
                    return True
        return False

    def __get_center_coordinate_of_tile(self, row, col):
        return int(self.pixels_in_a_tile_row * (0.5 + row)), int(self.pixels_in_a_tile_col * (0.5 + col))

    @staticmethod
    def __is_pixel_obstructed(image, x, y):
        intensity = image[x, y] # type:[]
        print "intensity={} of x,y={},{}".format(intensity, x, y)
        if all(rgb < LOW_INTENSITY_THRESHOLD for rgb in intensity):  # todo also add the sun --> if intensity > HIGH_INTENSITY_THRESHOLD:
            return True
        return False

# def main():
#     obs_detector = ObstructionDetector()
    # get image from camera
    # is image obstructed in all center areas of tiles
