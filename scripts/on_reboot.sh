#!/bin/bash

echo "Run Human Detection!"

if pgrep -f "python dnnr.py" &>/dev/null; then
    echo "it is already running"
    exit
fi
source /home/pi/.profile
workon cv
cd /home/pi/vision
python dnnr.py -i c -p "/dev/ttyAMA0" -b "115200" -m -l hd_log.log
