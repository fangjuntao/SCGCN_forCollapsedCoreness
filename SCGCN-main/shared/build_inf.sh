#!/bin/bash
c++ -O3 -Wall -shared -std=c++11 -fPIC -fopenmp `python2 -m pybind11 --includes` infSpread.cpp -o infSpread`python-config --extension-suffix`
