#!/usr/bin/env python3
"""Fairness check for the PAMS-only 'r' optimization: worst data arrival into each register group of a mapped
netlist (OpenSTA, the synthesis STA setup of bfbench.sta), to see whether the baseline's public logic is ever near
its critical path. Groups = registers whose Q net matches a name prefix. Writes final/runs/pubpaths_<design>.txt.
usage: pubpaths.py DESIGN GROUP [GROUP ...]   e.g. pubpaths.py base_jq offr enr shr offrq offp y0 fq0"""
import re, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
MV = Path(__file__).resolve().parents[2]
LIB = MV.parents[1] / 'current' / 'lib' / 'NangateOpenCellLibrary_typical.lib'
d, groups = sys.argv[1], sys.argv[2:]
v = MV / 'competitors' / 'runs' / f'syn_{d}_p0' / 'mapped.v'
text = v.read_text()
top = text[text.index(f'module {d}_lane('):]
regs = {g: [m.group(1) for m in re.finditer(r'DFF_X\d (\S+) \((?:(?!\);).)*?\.Q\(' + re.escape(g) + r'(?:\[\d+\])?\)', top, re.S)] for g in groups}
tcl = [f'read_liberty {{{LIB}}}', f'read_verilog {{{v}}}', f'link_design {d}_lane',
       'create_clock -name c -period 1000 [get_ports clk]',
       'set_input_delay 0 -clock c [delete_from_list [all_inputs] [get_ports clk]]', 'set_output_delay 0 -clock c [all_outputs]',
       'set_input_transition 0.05 [delete_from_list [all_inputs] [get_ports clk]]', 'set_load 0.005 [all_outputs]']
for g, cells in regs.items():
    if not cells: tcl.append(f'puts "GROUP {g} NONE"'); continue
    tcl.append(f'puts "GROUP {g} {len(cells)}"')
    tcl.append('report_checks -path_delay max -format end -digits 4 -to [get_pins {' + ' '.join(f'{c}/D' for c in cells) + '}]')
tf = MV / 'final' / 'runs' / f'pubpaths_{d}.tcl'; tf.write_text('\n'.join(tcl) + '\nexit\n')
out = subprocess.run([str(Path.home() / '.local/bin/sta'), '-no_init', '-no_splash', '-exit', str(tf)], capture_output=True, text=True).stdout
res = []
for blk in re.split(r'(?=GROUP )', out)[1:]:
    g = blk.split()[1]
    sl = re.findall(r'^\S+ \(\S+\)\s+([\d.]+)\s+([\d.]+)\s+(-?[\d.]+)\s+\(', blk, re.M)   # endpoint (cell), required, actual, slack
    worst = max((float(a_) + 1000 - float(r_) for r_, a_, _ in sl), default=None)         # arrival + setup = min period
    res.append(f'{g:8} registers {len(regs[g]):3}  min period for this group {worst:.3f} ns' if worst else f'{g:8} none')
(MV / 'final' / 'runs' / f'pubpaths_{d}.txt').write_text('\n'.join(res) + '\n\n' + out)
print('\n'.join(res))
