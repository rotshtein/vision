"""
Created on Aug 14, 2018

@author: ziv
"""
import argparse
import glob
import logging
import os
import queue

import cv2

from camera import Camera
from communication import Communication
from cpu_controller import CPUController
from file_saver import FilesSaver
from human_detection import HumanDetection
from messages_receiver_handler import MessagesReceiverHandler
from protocol.requests.hd_set_warning_msg import HDSetWarningMessage
from protocol.requests.hd_setup_msg import HDSetupMessage
from utils.point_in_polygon import Point
from visibility import Visibility
from warning import ObjectClassHolder

SW_VERSION = "0.6"
FW_VERSION = "0.4"

THREAD_COMMUNICATION = "Thread_Communication"
THREAD_VISIBILITY = "Thread_Visibility"
THREAD_DNN = "Thread_DNN"
THREAD_CAMERA = "Thread_Camera"
THREAD_FILES_SAVER = "Thread_Files_Saver"
THREAD_CPU_CONTROLLER = "Thread_CPU_Controller"


def start_threads(show, port, baudrate, thread_names, save_images_to_disk, simulate_warnings, draw_polygons_on_image,
                  activate_buzzer, rotating_angle):
    # max size = 1 - we don't want old images!
    detection_queue = queue.Queue(1)
    visibility_queue = queue.Queue(1)
    debug_queue = queue.Queue(1)
    debug_save_img_queue = queue.Queue()
    threads = []
    messages_receiver_handler = MessagesReceiverHandler(activate_buzzer)
    thread = None
    for tName in thread_names:
        if tName == THREAD_CAMERA:
            target_fps = 6
            thread = Camera(tName, logging, detection_queue, visibility_queue, target_fps)
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_DNN:
            num_of_frames_to_rotate = 3
            target_fps = 0
            thread = HumanDetection(tName, logging, detection_queue, target_fps, show, num_of_frames_to_rotate,
                                    SW_VERSION,
                                    FW_VERSION, debug_queue, save_images_to_disk, debug_save_img_queue,
                                    draw_polygons_on_image, rotating_angle)
            if simulate_warnings:  # only for debugging purpose - init app with a warning
                create_dummy_warning(thread)
            thread.load_configuration_from_fs()
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_VISIBILITY:
            target_fps = 2
            thread = Visibility(tName, logging, visibility_queue, target_fps)
            thread.load_configuration_from_fs()
            messages_receiver_handler.add_rx_listeners(thread)

        elif tName == THREAD_COMMUNICATION:
            # no fps since serial is a blocking method
            thread = Communication(tName, logging, messages_receiver_handler, port, baudrate)

        elif tName == THREAD_FILES_SAVER:
            # no fps since queue.get is a blocking method
            thread = FilesSaver(tName, logging, debug_save_img_queue)

        elif tName == THREAD_CPU_CONTROLLER:
            target_fps = 1
            thread = CPUController(tName, logging, target_fps)

        thread.start()
        threads.append(thread)

    is_exit = False
    # if show:
    while not is_exit:
        cv2.imshow('detect', debug_queue.get())
        k = cv2.waitKey(1)
        if k % 256 == 27:
            # ESC pressed
            logging.debug("Escape hit, closing...")
            is_exit = True
            cv2.destroyAllWindows()

    # Wait for all threads to complete
    for t in threads:
        # t.exit_thread()
        t.join()

    print("Exiting Main Thread")


def create_dummy_warning(hd_thread):
    hd_thread.num_of_frames_to_rotate = 3
    polygon_arr = [Point(0, 0), Point(0, 300), Point(300, 300), Point(300, 0)]
    object_class_holder = ObjectClassHolder([False, False, False, False, False, False, False, True])
    warning_message = HDSetWarningMessage(2, polygon_arr, object_class_holder, 0, 300, 20, 1, 1, True, False)
    hd_thread.on_set_warning_msg(warning_message)
    warning_message = HDSetWarningMessage(3, polygon_arr, object_class_holder, 0, 300, 20, 1, 1, True, True)
    hd_thread.on_set_warning_msg(warning_message)

    setup_message = HDSetupMessage(5, 1000, 63, 128, 190, 2, 3, False, False, False, True, True, 90)
    hd_thread.on_setup_message(setup_message)


def main():
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=False, default="c",
                    help="path to input image. if arg==c then the camera will be used instead of an image. "
                         "other wise need to specify the path to the images folder. e.g. data")
    ap.add_argument("-s", "--show", required=False, default=False, action='store_true',
                    help="show the processed image via X Server")
    ap.add_argument("-d", "--debug", required=False, default=False, action='store_true',
                    help="change the log level to DEBUG. default level is INFO")
    ap.add_argument("-l", "--loggingFileName", required=False, default="",
                    help="log to a file. Must add the log file path as an argument!")
    ap.add_argument("-p", "--port", required=False, help="serial port")
    ap.add_argument("-b", "--baudrate", required=False, help="serial baudrate")
    ap.add_argument("-v", "--saveimages", required=False, default=False, action='store_true',
                    help="save images to disk")
    ap.add_argument("-m", "--simulate", required=False, default=False, action='store_true',
                    help="simulate warnings on startup")
    ap.add_argument("-r", "--draw", required=False, default=False, action='store_true',
                    help="draw the detected polygons on the images")
    ap.add_argument("-z", "--buzzer", required=False, default=False, action='store_true', help="Activate buzzer")
    ap.add_argument("-a", "--angle", required=False, default="90", help="rotating angle")
    args = vars(ap.parse_args())

    debug_level = logging.INFO
    args_debug = args["debug"]
    args_show = args["show"]
    args_image = args["image"]
    args_port = args["port"]
    args_baudrate = args["baudrate"]
    save_images_to_disk = args["saveimages"]
    simulate_warnings = args["simulate"]
    draw_polygons_on_image = args["draw"]
    activate_buzzer = args["buzzer"]
    rotating_angle = args["angle"]

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
    arm_freq = os.popen("vcgencmd get_config arm_freq").readline()
    logging.info(arm_freq)

    if args_show:
        cv2.namedWindow("detect")

    if args_image == 'c':
        thread_names = [THREAD_CAMERA, THREAD_DNN, THREAD_VISIBILITY, THREAD_COMMUNICATION, THREAD_FILES_SAVER,
                        THREAD_CPU_CONTROLLER]
        start_threads(args_show, args_port, args_baudrate, thread_names, save_images_to_disk, simulate_warnings,
                      draw_polygons_on_image, activate_buzzer, rotating_angle)
    else:
        simulate_images(args_image, args_show)


def simulate_images(args_image, args_show):
    filelist = glob.glob(os.path.join(args_image, '*.png'))
    filelist.extend(glob.glob(os.path.join(args_image, '*.jpg')))
    filelist.extend(glob.glob(os.path.join(args_image, '*.bmp')))
    list_of_images = []
    for file in filelist:
        logging.info('********** ' + str(file) + ' ************')
        img = cv2.imread(file)
        list_of_images.append(img)
    _img_queue = queue.Queue()
    debug_queue = queue.Queue()
    target_fps = 0
    num_of_frames_to_rotate = 9
    logging.info("Creating HD Thread")

    hd_thread = HumanDetection(THREAD_DNN, logging, _img_queue, target_fps, True, num_of_frames_to_rotate,
                               SW_VERSION,
                               FW_VERSION, debug_queue)
    create_dummy_warning(hd_thread)
    hd_thread.start()
    while True:
        for i in range(len(list_of_images)):
            logging.info("Prepare to fetch an image")
            _img_queue.put(list_of_images.__getitem__(i))
            image = debug_queue.get()
            logging.info("Got an image")
            if args_show:
                cv2.imshow('detect', image)
                k = cv2.waitKey(1)
                if k % 256 == 27:
                    # ESC pressed
                    logging.debug("Escape hit, closing...")
                    cv2.destroyAllWindows()
            # time.sleep(1.0)
    hd_thread.join(1)
    print("Exiting Main Thread...")


if __name__ == '__main__':
    main()
