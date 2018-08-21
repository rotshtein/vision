#!/bin/bash

echo "Run Human Detection!"
source ~/.profile
workon cv
python dnnr.py -i c -p "/dev/ttyAMA0" -b "115200"
