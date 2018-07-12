#!/bin/bash

echo "Run Human Detection!"
source ~/.profile
workon cv
python dnnr.py -i c
