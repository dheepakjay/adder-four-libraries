"""run_all.py: map each design against each library variant and time the result.
usage: python3 run_all.py
Needs yosys (or yowasp-yosys) on the PATH, the four lib_*.lib files from cut_lib.py,
add.v, c.constr and sta.py in the current directory."""
import os, re, shutil, subprocess, sys
from collections import Counter
import sta

YOSYS = shutil.which('yosys') or shutil.which('yowasp-yosys')
if not YOSYS: sys.exit('yosys not found on PATH')
LIBS = [('Full library', 'lib_full'), ('No XOR or XNOR cells', 'lib_noxor'),
        ('NAND2, NOR2, INV and BUF only', 'lib_nand'), ('Full library, X1 drive only', 'lib_x1')]
TARGETS = [('tight', 100), ('relaxed', 600)]      # ABC delay target in ps
IN_SLEW, OUT_LOAD = 0.02, 3.0                      # ns, fF

def map_design(top, lib, target):
    out = f'nl_{top}_{lib}_{target}.v'
    if os.path.exists(out): os.remove(out)
    cmd = (f'read_verilog add.v; synth -noabc -top {top} -flatten; '
           f'abc -liberty {lib}.lib -D {target} -constr c.constr; '
           f'opt_clean -purge; write_verilog -noattr {out}')
    # run from this directory with relative names: the sandboxed yowasp build only sees the cwd
    subprocess.run([YOSYS, '-p', cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out if os.path.exists(out) else None

for top in ('ha', 'add8'):
    print(f'\n== {top} ==')
    print(f'{"library":32s} {"target":8s} {"cells":>5s} {"area":>7s} {"delay ps":>9s}  cells used')
    for label, lib in LIBS:
        for tname, tps in TARGETS:
            nl = map_design(top, lib, tps)
            if not nl:
                print(f'{label:32s} {tname:8s} mapping failed'); continue
            delay, area, ncells, _ = sta.run(lib + '.lib', nl, IN_SLEW, OUT_LOAD)
            used = Counter(re.findall(r'^\s*([A-Z][A-Z0-9]*_X\d+)\s', open(nl).read(), re.M))
            print(f'{label:32s} {tname:8s} {ncells:5d} {area:7.2f} {delay:9.1f}  ' +
                  ' '.join(f'{k}:{v}' for k, v in sorted(used.items())))

# Extra check: the unmodified library also holds half-adder and full-adder cells. Are they used?
orig = 'NangateOpenCellLibrary_typical'
if os.path.exists(orig + '.lib'):
    print('\n== unmodified Nangate library (includes HA_X1 and FA_X1) ==')
    for top in ('ha', 'add8'):
        nl = map_design(top, orig, 100)
        if not nl: print(top, 'mapping failed'); continue
        text = open(nl).read()
        print(f'{top}: HA_X1 used {len(re.findall(r"^\s*HA_X1", text, re.M))} times, '
              f'FA_X1 used {len(re.findall(r"^\s*FA_X1", text, re.M))} times')
