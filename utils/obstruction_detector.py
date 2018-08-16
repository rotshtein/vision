#!/usr/bin/python
'''
Created on Jul 4, 2018

@author: ziv
'''
import argparse
import logging

import cv2
import glob

import numpy as np

DEFAULT_INTENSITY_VARIANCE_THRESHOLD = 1000


class ObstructionDetector(object):
    """
    ObstructionDetector - this class detects if a set of images are being obstructed by an object
    An example for obstruction - when the camera is being covered by an object such as a hand preventing the camera's view
    This will cause the measured intensity value to be low
    This class divides the image to a matrix of tiles and measures the value of the tile's center points
    It keeps the result of the last frames - the number of frames is defined by the user in the constructor
    """

    def __init__(self, logging, rows=3, columns=3, max_hits=5):
        self.logging = logging
        self.rows = rows
        self.columns = columns

        # [Tile1[False, False, False, False, False], Tile2[False...], ...]
        self.init_last_tiles_matrix(max_hits, rows, columns)
        self.index = 0
        self.variance_threshold = DEFAULT_INTENSITY_VARIANCE_THRESHOLD
        self.min_obstruction_hits = 5
        self.max_obstruction_hits = max_hits
        self.no_visibility_threshold = 1000
        self.medium_visibility_threshold = 2500
        self.full_visibility_threshold = 4000

    def init_last_tiles_matrix(self, max_hits, rows=3, columns=3):
        self.last_tiles_obstructed_matrix = [[False for i in range(max_hits)] for j in
                                             range(rows * columns)]

    def set_visibility_thresholds(self, no_visibility_threshold, medium_visibility_threshold,
                                  full_visibility_threshold):
        self.no_visibility_threshold = no_visibility_threshold
        self.medium_visibility_threshold = medium_visibility_threshold
        self.full_visibility_threshold = full_visibility_threshold

    def set_obstruction_threshold(self, variance_threshold):
        self.variance_threshold = variance_threshold

    def set_obstruction_min_max_hits(self, min_hits, max_hits):
        self.min_obstruction_hits = min_hits
        self.max_obstruction_hits = max_hits
        self.init_last_tiles_matrix(max_hits)

    def is_last_frames_obstructed(self, image, tiles_to_ignore):
        """
        :param tiles_to_ignore:
        :param image:
        :return: True if all last frames are obstructed
        """
        self.tiles_to_ignore = [] if tiles_to_ignore is None else tiles_to_ignore
        self.height = image.shape[0]
        self.width = image.shape[1]
        # define constants
        self.pixels_in_a_tile_row = self.height / self.rows
        self.pixels_in_a_tile_col = self.width / self.columns

        self.tile_relative_coordinates = self.__get_coordinates_of_tile()

        # handle current frame - do validation
        # self.logging.info("Vision - Started Obstruction detection. Tiles to ignore:{}".format(tiles_to_ignore))
        self.__validate_frame_and_add_result_to_list(image)

        # check if any tile is consecutively obstructed in the last n frames
        obstructed_tiles_not_ignored = []
        debug_all_obstructed_result = []
        _tile_index = 0
        # tile holds the last n results
        for tile in self.last_tiles_obstructed_matrix:
            if tile.count(True) >= self.min_obstruction_hits:
                debug_all_obstructed_result.append(_tile_index)
                if _tile_index not in self.tiles_to_ignore:
                    obstructed_tiles_not_ignored.append(_tile_index)
            _tile_index += 1

        self.index = (self.index + 1) % self.max_obstruction_hits
        self.logging.info(
            "Obstruction - Result: Obstructed Tiles Not to ignore:{}. All Obstructed Tiles including ignored:{}.".format(
                obstructed_tiles_not_ignored, debug_all_obstructed_result))
        return obstructed_tiles_not_ignored

    def __validate_frame_and_add_result_to_list(self, image):
        tile_index = 0
        for main_row in range(self.rows):
            for main_col in range(self.columns):
                result = self.__is_tile_obstructed(image, main_row, main_col, tile_index)
                self.last_tiles_obstructed_matrix[tile_index][self.index] = result
                # self.logging.debug(self.last_tiles_obstructed_matrix)
                tile_index += 1

    def __is_tile_obstructed(self, image, row, col, tile_index):
        # self.logging.debug("Tile [{}][{}]".format(row, col) + " (Index={}".format(tile_index) + ")")
        variance_temp_list = []
        for x, y in self.tile_relative_coordinates:
            abs_tile_y = self.height / self.rows * row
            abs_tile_x = self.width / self.columns * col

            abs_x = int(x + abs_tile_x)
            abs_y = int(y + abs_tile_y)

            # note - intensity from image is backwards img[y,x] !!!
            intensity = image[abs_y, abs_x]  # type:[]
            # self.logging.debug("intensity={} of point=[{},{}]".format(intensity, abs_x, abs_y))
            variance_temp_list.append(intensity)
        is_tile_below_variance_threshold = self.__is_all_points_intensity_below_variance_threshold(variance_temp_list)
        return is_tile_below_variance_threshold

    def __get_coordinates_of_tile(self):
        coordinates = []
        tile_height = self.height / self.rows
        tile_width = self.width / self.columns

        sub_tile_height = tile_height / self.rows
        sub_tile_width = tile_width / self.columns

        for tile_row in range(self.rows):
            for tile_col in range(self.columns):
                coordinates.append((int(sub_tile_width * (0.5 + tile_col)), int(sub_tile_height * (0.5 + tile_row))))
        return coordinates

    def __is_all_points_intensity_below_variance_threshold(self, variance_temp_list):
        # next line is commented out - was relevant to rgb image - now it's gray
        # var = np.var(variance_temp_list, axis=0)  # axis=0 for calculating the arrays vertically [r, g, b]
        var = np.var(variance_temp_list)
        self.logging.debug("variance=" + str(var))
        return var < self.variance_threshold

    def __is_all_points_intensity_below_threshold(self, intensity_below_threshold_temp_list):
        return intensity_below_threshold_temp_list.count(False) == 0

    def __get_center_coordinate_of_tile(self, row, col):
        return int(self.pixels_in_a_tile_row * (0.5 + row)), int(self.pixels_in_a_tile_col * (0.5 + col))


if __name__ == '__main__':
    debug_level = logging.INFO

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True, help="path to input image")
    ap.add_argument("-d", "--debug", required=False, default=False, help="change log level to DEBUG")
    args = vars(ap.parse_args())

    if args["debug"] == 'True':
        debug_level = logging.DEBUG

    logging.basicConfig(level=debug_level, format='%(asctime)s: %(message)s')

    filelist = glob.glob(args["image"])
    obstruction_detector = ObstructionDetector(logging)

    # Testing for image C:\Projects\vision\data\matrix_0_5.png ==> All Tiles except 0 and 5 are obstructed
    for img_file in filelist:
        logging.info('********** ' + str(img_file) + ' ************')
        img = cv2.imread(img_file)
        res = []
        obstruction_detector.set_obstruction_min_max_hits(3, 7)
        # Test 1 - do not ignore cells
        for i in range(5):
            res = obstruction_detector.is_last_frames_obstructed(img, None)
        # expected result --> all except tiles 0 and 7
        assert (res == [1, 2, 3, 4, 5, 6, 8])

        # Test 2 - ignore cells 0-5
        for i in range(5):
            res = obstruction_detector.is_last_frames_obstructed(img, [0, 1, 2, 3, 4, 5])
        # expected result --> all except tiles 0 and 7.
        assert (res == [6, 8])
