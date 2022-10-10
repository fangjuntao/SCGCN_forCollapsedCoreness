#!/bin/bash
c++ -O3 -Wall -shared -std=c++11 -fPIC -fopenmp `python3 -m pybind11 --includes` kcore.cpp -o kcore`python-config --extension-suffix`
