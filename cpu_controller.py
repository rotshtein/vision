"""
Created on Aug 14, 2018

@author: ziv
"""
import os
import time

from utils.hd_threading import HDThread

WAITING_TIME_MIN = 10 * 60
SAVE_CPU_TIME_MIN = 1 * 60


class CPUController(HDThread):
    def __init__(self, thread_name, logging, target_fps):
        super().__init__(thread_name, logging, target_fps)
        self.thread_name = thread_name
        self.num_of_cores = os.popen("grep - c ^ processor / proc / cpuinfo").readline()
        self.logging.info("{} - Starting with full CPU usage. Cores#={}".format(thread_name, self.num_of_cores))
        self.temperature_cpu_list = []

        # SET CPU START TIME
        self.increase_cpu_start_time = time.time()

        # SAVE TEMP_CPU TIMER
        self.save_temp_cpu_time = time.time()

        # todo remove next 2 lines - only for experimenting
        self.normalized_cpu = 50
        self.set_cpu_level_normalized(self.normalized_cpu)

    def _run(self) -> None:
        self.print_cpu_and_temp()
        self._limit_cpu_upon_temperature()

        if time.time() - self.save_temp_cpu_time > SAVE_CPU_TIME_MIN:
            self.logging.info(
                "{} - save temp_cpu to list".format(self.thread_name))
            self.temperature_cpu_list.append((self._get_temperature(), self.normalized_cpu))
            # reset timer
            self.save_temp_cpu_time = time.time()

    def _limit_cpu_upon_temperature(self) -> None:
        temperature = self._get_temperature()
        last_normalized_cpu = self.normalized_cpu

        if temperature > 80:
            self.normalized_cpu = 50
        else:
            if time.time() - self.increase_cpu_start_time > WAITING_TIME_MIN:
                self.normalized_cpu += 5

        if self.normalized_cpu != last_normalized_cpu:
            self.increase_cpu_start_time = time.time()
            self.set_cpu_level_normalized(self.normalized_cpu)

    def set_cpu_level_normalized(self, cpu_percent):
        cpu_usage_percent = self.num_of_cores * cpu_percent
        self._limit_cpu(cpu_usage_percent)

    def print_cpu_and_temp(self) -> None:
        self.logging.info("{} - CPU%={}, Temp={}'C".format(self.thread_name, self._get_cpu(), self._get_temperature()))

    def _get_cpu(self) -> float:
        f = 0.0
        try:
            f = float(
                os.popen("ps -p {} -o %cpu".format(self._get_python_pid())).read().replace("%CPU\n", "").replace("\n",
                                                                                                                 ""))
        except:
            pass
        return f

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
        import csv
        with open('temp_cpu.csv', mode='w', newline='') as file:
            fieldnames = ['Temp', 'CPU']
            writer = csv.writer(file, delimiter=',')
            writer.writerow([fieldnames[0], fieldnames[1]])
            for res in self.temperature_cpu_list:
                writer.writerow([res[0], res[1]])


if __name__ == '__main__':
    import logging

    cpu_controller = CPUController("thread_name", logging, 0)
    cpu_controller.temperature_cpu_list = [(12, 12), (212, 12)]
    cpu_controller.write_to_csv()
