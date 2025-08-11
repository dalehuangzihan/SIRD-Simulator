#! /bin/bash

# for when Makefile.in changes - with assertions:
./configure --enable-debug

# for when every time the source code changes:
# make clean && make -j
make clean && make -j CXXFLAGS="-g -O0 -fsanitize=address,undefined -fno-omit-frame-pointer"

