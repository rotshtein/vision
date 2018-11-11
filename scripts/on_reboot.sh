#!/bin/bash

echo "Run Human Detection!"

if pgrep -f "python dnnr.py" &>/dev/null; then
    echo "it is already running"
    exit
fi
source /home/pi/.profile
workon cv
cd ~pi/vision
python dnnr.py -i c -p "/dev/ttyAMA0" -b "115200" -m

# Optional Arguments:
#*********************
# -v - optional argument - If added images will be saved to the Debug folder
# -l "hd_log.log" - Write to a log file - need to add the file name. without this argument info will be written to the console
# -d - Debug mode - Log level - debug. default is info.
