"""cut_lib.py: write four reduced copies of the Nangate45 Liberty file.
usage: python3 cut_lib.py NangateOpenCellLibrary_typical.lib
Writes lib_full.lib, lib_noxor.lib, lib_nand.lib, lib_x1.lib in the current directory."""
import re, sys
src = open(sys.argv[1]).read()

def cell_blocks(s):
    out = []
    for m in re.finditer(r'\n\s*cell\s*\(\s*"?([A-Za-z0-9_]+)"?\s*\)\s*\{', s):
        start = m.start() + 1
        depth, j = 0, m.end() - 1
        while True:
            if s[j] == '{': depth += 1
            elif s[j] == '}':
                depth -= 1
                if depth == 0: break
            j += 1
        out.append((m.group(1), start, j + 1))
    return out

blocks = cell_blocks(src)
# cells the tools cannot use for plain combinational mapping, or that this study does not use
skip = re.compile(r'^(FILL|TAP|ANTENNA|LOGIC|CLKGATE|DFF|DLH|DLL|SDFF|TBUF|TINV|HA_|FA_)')

def make(name, keep):
    s = src
    for n, a, b in sorted(blocks, key=lambda x: -x[1]):
        if not keep(n):
            s = s[:a] + s[b:]
    open(name, 'w').write(s)
    print(name, sum(1 for n, _, _ in blocks if keep(n)), 'cells')

usable = lambda n: not skip.match(n)
make('lib_full.lib',  lambda n: usable(n))
make('lib_noxor.lib', lambda n: usable(n) and not n.startswith(('XOR', 'XNOR')))
make('lib_nand.lib',  lambda n: n in ('NAND2_X1', 'NOR2_X1', 'INV_X1', 'BUF_X1'))
make('lib_x1.lib',    lambda n: usable(n) and n.endswith('_X1'))
