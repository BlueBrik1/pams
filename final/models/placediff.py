#!/usr/bin/env python3
"""Do two P&R runs differ physically? Compares cell placements in final.def: fraction of common instances whose
location differs, mean displacement (um), and the IO pin placement. usage: placediff.py RUN_A RUN_B"""
import re, sys
sys.dont_write_bytecode = True


def load(run):
    d = open(f'{run}/final.def').read()
    units = int(re.search(r'UNITS DISTANCE MICRONS (\d+)', d).group(1))
    comps = d[d.index('COMPONENTS'):d.index('END COMPONENTS')]
    cells = {m.group(1): (int(m.group(2)), int(m.group(3)))
             for m in re.finditer(r'-\s+(\S+)\s+\S+.*?\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)', comps)}
    pins = d[d.index('\nPINS'):d.index('END PINS')]
    io = {m.group(1): (int(m.group(2)), int(m.group(3)))
          for m in re.finditer(r'-\s+(\S+)\s+\+\s+NET.*?PLACED\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)', pins, re.S)}
    return cells, io, units


if __name__ == '__main__':
    (ca, ia, u), (cb, ib, _) = load(sys.argv[1]), load(sys.argv[2])
    common = set(ca) & set(cb)
    moved = [k for k in common if ca[k] != cb[k]]
    disp = sum(abs(ca[k][0] - cb[k][0]) + abs(ca[k][1] - cb[k][1]) for k in common) / max(len(common), 1) / u
    print(f'cells A {len(ca)} B {len(cb)} common {len(common)}; moved {len(moved)} ({100 * len(moved) / max(len(common), 1):.1f} %); '
          f'mean |dx|+|dy| {disp:.2f} um; IO pins moved {sum(ia[k] != ib.get(k) for k in ia)}/{len(ia)}')
