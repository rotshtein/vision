from datetime import datetime
import queue
import threading
import time

import numpy

exitFlag = 0


class HDThread(threading.Thread):
    def __init__(self, logging, thread_id, thread_name, working_queue, sleep_time, is_fetch_data, target_object,
                 target_method_name, method_args):
        threading.Thread.__init__(self)
        self.logging = logging
        self.threadID = thread_id
        self.thread_name = thread_name
        self.working_queue = working_queue  # type: queue.Queue
        self.sleep_time = sleep_time
        self.is_get_from_queue = is_fetch_data
        self.target_object = target_object
        self.target_method_name = target_method_name
        self.method_args = method_args
        self.exit_flag = exitFlag
        self.queue_lock = threading.Lock()
        self.last_working_time = datetime.now()

        self.fps_statistics = []

    def run(self):
        self.logging.info("Starting {} with args:{}".format(self.thread_name, self.method_args))
        while not self.exit_flag:
            if self.is_get_from_queue:
                self.get_data()
            else:
                self.put_data()
        self.logging.info("Exiting " + self.thread_name)

    def put_data(self):
        """
        Put data in queue only if queue is not full. if full skip
        :return:
        """
        # get image from camera
        temp_time = datetime.now()
        self.queue_lock.acquire()
        if not self.working_queue.full():
            self.logging.info("%s - started " % self.thread_name)
            image = getattr(self.target_object, self.target_method_name)(*self.method_args)
            # put image in queue
            self.working_queue.put(image)
            self.queue_lock.release()
            now = datetime.now()
            fps = 1.0 / (now - self.last_working_time).microseconds * 1000000
            self.fps_statistics.append(fps)
            self.logging.info(
                "{} - processing took {} sec. fps={}. sleep={} sec".format(self.thread_name, now - temp_time, fps,
                                                                           self.sleep_time))
            self.last_working_time = now
        else:
            self.queue_lock.release()
            self.logging.info("%s - queue is full. going to sleep... %s" % (self.thread_name, self.sleep_time))
        if self.fps_statistics.__len__() > 100:
            # remove first value since it's not correct
            self.fps_statistics.pop(0)
            self.logging.info("FPS Summary of {} - avg={}. max={}. min={}. queue_size={}".format(self.thread_name, numpy.mean(self.fps_statistics),
                                                                            numpy.max(self.fps_statistics),
                                                                            numpy.min(self.fps_statistics),
                                                                            self.working_queue.qsize()))
            self.fps_statistics.clear()
        time.sleep(self.sleep_time)

    def get_data(self):
        temp_time = datetime.now()
        self.queue_lock.acquire()
        # if vision thread and last
        is_rule_for_vision_thread = self.thread_name is "Thread_Vision" and self.working_queue.qsize() > 1
        is_rule_for_other_threads = self.thread_name is not "Thread_Vision" and not self.working_queue.empty()
        if is_rule_for_vision_thread or is_rule_for_other_threads:
            # get image from queue
            self.logging.info("%s - started " % self.thread_name)
            data = self.working_queue.get()
            self.queue_lock.release()
            params_data = self.method_args + [data]
            getattr(self.target_object, self.target_method_name)(*params_data)
            now = datetime.now()
            fps = 1.0 / (now - self.last_working_time).microseconds * 1000000
            self.fps_statistics.append(fps)
            self.logging.info(
                "{} - processing took {} sec. fps={}. sleep={} sec".format(self.thread_name, now - temp_time, fps,
                                                                           self.sleep_time))
            self.last_working_time = now
        else:
            self.queue_lock.release()
            self.logging.info("{} - queue is empty. going to sleep... {}".format(self.thread_name, self.sleep_time))

        if self.fps_statistics.__len__() > 100:
            # remove first value since it's not correct
            self.fps_statistics.pop(0)
            self.logging.info("FPS Summary of {} - avg={}. max={}. min={}. queue_size={}".format(self.thread_name, numpy.mean(self.fps_statistics),
                                                                            numpy.max(self.fps_statistics),
                                                                            numpy.min(self.fps_statistics),
                                                                            self.working_queue.qsize()))
            self.fps_statistics.clear()
        time.sleep(self.sleep_time)


class Foo:
    # PUT IN QUEUE
    def capture_image(self, x, y):
        # every 0.01sec
        return time.asctime() + " - capture_image.".format(x, y)

    # GET FROM QUEUE
    def do_dnn_detection(self, x, y, image):
        # every 0.6sec
        pass

    def do_vision_detection(self, x, y, image):
        # every 0.01sec
        pass


if __name__ == '__main__':
    threadList = ["Thread Capture", "Thread DNN", "Thread Vision"]
    workQueue = queue.Queue(10)
    threads = []
    threadID = 1
    is_get_from_queue = True

    import logging

    debug_level = logging.INFO
    logging.basicConfig(level=debug_level, format='%(asctime)s: %(message)s')
    for tName in threadList:
        foo = Foo()
        if threadID == 1:
            # PUT IN QUEUE
            is_get_from_queue = False
            process_thread_sleep_sec = 1
            thread = HDThread(logging, threadID, tName, workQueue, process_thread_sleep_sec, is_get_from_queue, foo,
                              "capture_image",
                              ['1', '2'])
        elif threadID == 2:
            # GET FROM QUEUE
            is_get_from_queue = True
            process_thread_sleep_sec = 10
            thread = HDThread(logging, threadID, tName, workQueue, process_thread_sleep_sec, is_get_from_queue, foo,
                              "do_dnn_detection", ['1', '2'])
        elif threadID == 3:
            # GET FROM QUEUE
            is_get_from_queue = True
            process_thread_sleep_sec = 5
            thread = HDThread(logging, threadID, tName, workQueue, process_thread_sleep_sec, is_get_from_queue, foo,
                              "do_vision_detection", ['1', '2'])
        thread.start()
        threads.append(thread)
        threadID += 1

    # Wait for queue to empty
    while not workQueue.empty():
        pass

    # Notify threads it's time to exit
    # exitFlag = 1

    # Wait for all threads to complete
    for t in threads:
        t.join()
    print("Exiting Main Thread")
