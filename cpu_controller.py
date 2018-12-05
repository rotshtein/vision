"""
Created on Aug 14, 2018

@author: ziv
"""
import os
import time

from utils.hd_threading import HDThread

WAITING_TIME_MIN = 10 * 60


class CPUController(HDThread):
    def __init__(self, thread_name, logging, target_fps):
        super().__init__(thread_name, logging, target_fps)
        self.thread_name = thread_name
        self.num_of_cores = os.popen("grep - c ^ processor / proc / cpuinfo").readline()
        self.logging.info("{} - Starting with full CPU usage. Cores#={}".format(thread_name, self.num_of_cores))
        self.start_time = time.time()

    def _run(self) -> None:
        self._print_cpu_and_temp()
        self._limit_cpu_upon_temperature()

    def _print_cpu_and_temp(self) -> None:
        self.logging.info("{} - CPU%={}, Temp={}'C".format(self.thread_name, self._get_cpu(), self._get_temperature()))

    def _limit_cpu_upon_temperature(self) -> None:
        temperature = self._get_temperature()
        last_normalized_cpu = self.normalized_cpu
        if temperature > 80:
            self.normalized_cpu = 50
        else:
            if time.time() - self.start_time > WAITING_TIME_MIN:
                self.normalized_cpu += 5

        if self.normalized_cpu != last_normalized_cpu:
            self.logging.info(
                "{} - setting target CPU%={}".format(self.thread_name, self._get_cpu()))
            self.timer = time.time()
            self._set_cpu_level_normalized(self.normalized_cpu)

    def _get_cpu(self) -> float:
        return float(
            os.popen("ps -p {} -o %cpu".format(self._get_python_pid())).read().replace("%CPU\n", "").replace("\n", ""))

    def _get_temperature(self) -> float:
        temp_str = os.popen("vcgencmd measure_temp").readline()
        return float(temp_str.replace("temp=", "").rstrip("\n\r").replace("'C", ""))

    def _get_python_pid(self) -> int:
        return int(os.popen("pgrep -f python").readline())

    def _set_cpu_level_normalized(self, cpu_percent):
        cpu_usage_percent = self.num_of_cores * cpu_percent
        self._limit_cpu(cpu_usage_percent)

    def _limit_cpu(self, cpu_usage_percent):
        self.logging.info("Setting CPU")
        os.popen("sudo killall cpulimit")
        os.popen("sudo cpulimit -l {} -p {}".format(cpu_usage_percent, self._get_python_pid()))
