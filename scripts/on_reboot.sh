#!/bin/bash

echo "Run Human Detection!"

if pgrep -f "python dnnr.py" &>/dev/null; then
    echo "it is already running"
    exit
fi
source /home/pi/.profile
workon cv
cd /home/pi/vision
python dnnr.py -p "/dev/ttyAMA0" -b "115200" -m -r -z

# Optional Arguments:
#*********************
# "-i", "--image", required=False, help="path to an input image. if arg==c then the camera will be used instead of an image"
# "-s", "--show", required=False, default=False, help="show the processed image via X Server"
# "-d", "--debug", required=False, default=False, help="change the log level to DEBUG. default level is INFO"
# "-l", "--loggingFileName", required=False, default="", help="log to a file. Must add the log file path as an argument!"
# "-p", "--port", required=False, help="serial port"
# "-b", "--baudrate", required=False, help="serial baudrate"
# "-v", "--saveimages", required=False, default=False, help="save images to disk"
# "-m", "--simulate", required=False, default=False, help="simulate warnings on startup")
# "-r", "--draw", required=False, default=False, help="draw the detections and the warning's polygons on the images"
# "-z", "--buzzer", required=False, default=False, help="Activate buzzer"
# "-a", "--angle", required=False, default="90", help="rotating angle"
