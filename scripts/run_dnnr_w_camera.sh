#!/bin/bash

echo "Run Human Detection!"
source ~/.profile
workon cv
python dnnr.py -i c -s -p "/dev/ttyUSB0" -b "38400"
