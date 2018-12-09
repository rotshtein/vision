"""
Created on Aug 14, 2018

@author: ziv
"""
import os
import time
from datetime import datetime
from statistics import mean

import psutil

from utils.hd_threading import HDThread

FILE_NAME_CSV = 'temp_cpu.csv'

WAITING_TIME_MIN = 10 * 60
SAVE_CPU_TIME_MIN = 1 * 60


class CPUController(HDThread):
    def __init__(self, thread_name, logging, target_fps):
        super().__init__(thread_name, logging, target_fps)
        self.thread_name = thread_name
        self.num_of_cores = 0
        try:
            self.num_of_cores = int(os.popen("nproc").readline().replace("\n", ""))
        except:
            pass
        self.logging.info("{} - Starting with full CPU usage. Cores#={}".format(thread_name, self.num_of_cores))
        self.temperature_cpu_list = []
        self.cpu_average_list = []

        # SET CPU START TIME
        self.cpu_change_start_timer = time.time()

        # SAVE TEMP_CPU TIMER
        self.save_temp_cpu_time = time.time()

        # todo remove next 2 lines - only for experimenting
        self.normalized_cpu = 50
        self.set_cpu_level_normalized(self.normalized_cpu)
        self.end_test_timer = None
        self.cool_down_timer = None

        self.stop_test_state = False
        self.test_ended_state = False
        self.increase_cpu_state = True
        self.cool_down_state = False
        self.cpu_get_stuck_value = 0

    def _run(self) -> None:
        start_time = datetime.now()
        self.print_cpu_and_temp()
        self._limit_cpu_upon_temperature()

        self.cpu_average_list.append(self._get_cpu())

        # save result to list every 1 min.
        if time.time() - self.save_temp_cpu_time > SAVE_CPU_TIME_MIN and (not self.test_ended_state or not self.stop_test_state):
            self.save_temp_avg_cpu_to_list()
            # reset timer
            self.save_temp_cpu_time = time.time()

        iteration_time = datetime.now() - start_time
        self.iteration_time_sec = iteration_time.microseconds / 1000000

    def _limit_cpu_upon_temperature(self) -> None:
        temperature = self._get_temperature()
        last_normalized_cpu = self.normalized_cpu

        if self.stop_test_state:
            return

        if self.test_ended_state:
            # wait 1 min.
            self.logging.info(
                "{} - Entered Test Ended state".format(self.thread_name))
            if self.end_test_timer is None:
                self.end_test_timer = time.time()
            if time.time() - self.end_test_timer > WAITING_TIME_MIN:
                self.save_temp_avg_cpu_to_list()
                self.write_to_csv()
                self.stop_test_state = True
        else:
            if temperature > 80:
                self.logging.info(
                    "{} - Temp exceeded 80 deg. Decreasing CPU to 50%".format(self.thread_name))
                self.cpu_get_stuck_value = self.normalized_cpu
                self.normalized_cpu = 50
                self.cool_down_state = True

            if self.cool_down_state:
                self.logging.info(
                    "{} - Entered Cool Down (from 80deg) state".format(self.thread_name))
                # wait 1 min
                if self.cool_down_timer is None:
                    self.cool_down_timer = time.time()
                if time.time() - self.cool_down_timer > WAITING_TIME_MIN:
                    self.logging.info(
                        "{} - Ended cool down state".format(self.thread_name))
                    self.cool_down_state = False
                    if self.increase_cpu_state:
                        self.increase_cpu_state = False
                        self.normalized_cpu = self.cpu_get_stuck_value - 5
                    else:
                        self.test_ended_state = True

            if self.increase_cpu_state:
                # stop condition
                if self.normalized_cpu == 100:
                    self.increase_cpu_state = False
                else:
                    if time.time() - self.cpu_change_start_timer > WAITING_TIME_MIN:
                        self.normalized_cpu += 5
            else:
                # stop condition
                if self.normalized_cpu == 50:
                    self.test_ended_state = True
                else:
                    if time.time() - self.cpu_change_start_timer > WAITING_TIME_MIN:
                        self.normalized_cpu -= 5

        if self.normalized_cpu != last_normalized_cpu:
            self.cpu_change_start_timer = time.time()
            self.set_cpu_level_normalized(self.normalized_cpu)

    def save_temp_avg_cpu_to_list(self):
        global dnn_fps
        average_cpu = mean(self.cpu_average_list)
        self.cpu_average_list.clear()
        self.logging.info(
            "{} - save to list: temp={}, target_cpu={}, avg_cpu={}, DNN_fps={}".format(self.thread_name, self._get_temperature(), self.normalized_cpu, average_cpu/self.num_of_cores, dnn_fps))
        self.temperature_cpu_list.append((self._get_temperature(), self.normalized_cpu, average_cpu, dnn_fps))

    def set_cpu_level_normalized(self, cpu_percent):
        cpu_usage_percent = self.num_of_cores * cpu_percent
        self._limit_cpu(cpu_usage_percent)

    def print_cpu_and_temp(self) -> None:
        self.logging.info("{} - CPU%={}, Temp={}'C".format(self.thread_name, self._get_cpu(), self._get_temperature()))

    def _get_cpu(self) -> float:
        return psutil.cpu_percent()

    def _get_temperature(self) -> float:
        f = 0.0
        try:
            temp_str = os.popen("vcgencmd measure_temp").readline()
            f = float(temp_str.replace("temp=", "").rstrip("\n\r").replace("'C", ""))
        except:
            pass
        return f

    def _get_python_pid(self) -> int:
        i = 0
        try:
            i = int(os.popen("pgrep -f python").readline())
        except:
            pass
        return i

    def _limit_cpu(self, cpu_usage_percent):
        self.logging.info(
            "{} - setting target CPU%={}".format(self.thread_name, cpu_usage_percent))
        os.popen("sudo killall cpulimit")
        os.popen("sudo cpulimit -l {} -p {}".format(cpu_usage_percent, self._get_python_pid()))

    def write_to_csv(self):
        self.logging.info("{} - writing to {}".format(self.thread_name, FILE_NAME_CSV))
        import csv
        with open(FILE_NAME_CSV, mode='w', newline='') as file:
            fieldnames = ['Temp [Deg]', 'Target CPU [%]', 'Average CPU [%]', 'DNN Fps [1/sec]']
            writer = csv.writer(file, delimiter=',')
            # write header
            writer.writerow([fieldnames[0], fieldnames[1], fieldnames[2], fieldnames[3]])
            # write data
            for res in self.temperature_cpu_list:
                writer.writerow([res[0], res[1], res[2], res[3]])


if __name__ == '__main__':
    import logging

    cpu_controller = CPUController("thread_name", logging, 0)
    cpu_controller.temperature_cpu_list = [(12, 12), (212, 12)]
    cpu_controller.write_to_csv()
