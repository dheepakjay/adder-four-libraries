#!/bin/sh
# Reproduce the adder experiment from scratch. Needs python3, curl and yosys (or yowasp-yosys).
set -e
LIB_URL=https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib
[ -f NangateOpenCellLibrary_typical.lib ] || curl -sSL -o NangateOpenCellLibrary_typical.lib "$LIB_URL"
python3 cut_lib.py NangateOpenCellLibrary_typical.lib
python3 run_all.py
