#! /bin/bash

# for when Makefile.in changes - with assertions:
./configure --enable-debug

# for when every time the source code changes:
make clean && make -j
