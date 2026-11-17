# One adder, four libraries

Reproduces the worked example from "Logic Synthesis from the Ground Up", article 2, by Dheepak Jayaraman.

The same RTL (a half adder and an 8-bit adder) is mapped with Yosys and ABC against four versions of the
open Nangate 45 nm typical Liberty library. Delay comes from sta.py, a small table-based calculator.

## Open in Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dheepakjay/adder-four-libraries/blob/main/adder-four-libraries.ipynb)

## Run

    pip install yowasp-yosys==0.71.0.0.post1285
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
- The Yosys version matters. The numbers in the article come from Yosys 0.71, which bundles its own ABC.
  Yosys 0.70 gave different 8-bit results (for example 257 ps instead of 280 ps for the full library at the tight target),
  while the half adder stayed the same. Keep the pinned version to get the same numbers.
