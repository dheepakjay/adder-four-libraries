# One adder, four libraries

Reproduces the worked example from "Logic Synthesis from the Ground Up", article 2, by Dheepak Jayaraman.

The same RTL (a half adder and an 8-bit adder) is mapped with Yosys and ABC against four versions of the
open Nangate 45 nm typical Liberty library. Delay comes from sta.py, a small table-based calculator.

## Run

    pip install yowasp-yosys     # or install Yosys itself
    ./run.sh

Run it from inside this folder: the pip build of Yosys can only see the current directory.

## Files

- add.v        the two designs
- c.constr     ABC constraints: input driven by BUF_X1, 3 fF on every output
- cut_lib.py   writes the four reduced libraries from the Nangate file
- sta.py       NLDM delay calculator (Liberty tables, bilinear interpolation, worst of rise and fall)
- run_all.py   maps every design against every library at a tight (100 ps) and a relaxed (600 ps) target
- run.sh       downloads the library and runs everything

## What the numbers mean

- Area is in library units. Delay uses a 20 ps input slew, 3 fF output load and no wires.
- sta.py is not sign-off timing. I checked its table interpolation by hand and nothing more.
  Compare rows with each other, do not quote the absolute delays.
- One mapper (ABC), one run per cell of the table. Commercial tools will choose differently.
- The Nangate library has half-adder and full-adder cells. ABC maps to single-output cells only, so it never uses them.
- run_all.py ends with a check against the unmodified library, which keeps HA_X1 and FA_X1. They are not used.
- Small differences in your Yosys version can move individual numbers a little.
