#!/bin/bash

echo "Run Human Detection!"
source ~/.profile
workon cv
cd vision/
python dnnr.py -i c -s
