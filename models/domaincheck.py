#!/usr/bin/env python3
"""Structural share-domain separation check of a mapped lane (Yosys JSON written by bfbench.synth; hpc2 kept as a
hierarchical module). Home-made structural check, not a leakage verifier.

Labels: input bits of x0 / x1 / x2 -> domain {0} / {1} / {2}; c, mode, vin, first, last -> public; rnd -> fresh
randomness R; hpc2 instance output c[i] -> {i}.
Propagation: every cell of the top module (combinational and flip-flops) outputs the union of its input labels.
Fails if, outside hpc2 instances:
- any net carries two share domains;
- randomness reaches anything other than an hpc2 'r' port.
Also requires every output share port cdec[i] / dec[i] to be domain {i} only.
usage: python3 -I domaincheck.py mapped.json top"""
import json, sys
J = json.load(open(sys.argv[1])); top = sys.argv[2]; M = J['modules'][top]
lab = {}
for name, p in M['ports'].items():
    for i, b in enumerate(p['bits']):
        if p['direction'] != 'input' or not isinstance(b, int): continue
        lab[b] = {f'D{name[1]}'} if name in ('x0', 'x1', 'x2') else ({'R'} if name == 'rnd' else set())
cells = M['cells']; changed = True; viol = []
import re
from pathlib import Path
LIB = Path(__file__).resolve().parents[2] / 'ext/tools/orfs_rootfs/OpenROAD-flow-scripts/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib'
DIRS = {}                                                   # liberty cells carry no directions in the JSON: read the .lib
for cm in re.finditer(r'(?m)^\s*cell\s*\(\s*"?(\w+)"?\s*\)\s*\{(.*?)(?=^\s*cell\s*\(|\Z)', LIB.read_text(), re.S):
    DIRS[cm.group(1)] = {pm.group(1): pm.group(2) for pm in re.finditer(r'(?<![_A-Za-z0-9])pin\s*\(\s*"?(\w+)"?\s*\)\s*\{[^{}]*?direction\s*:\s*"?(\w+)', cm.group(2), re.S)}
for c in cells.values():
    if 'port_directions' not in c:
        if c['type'] in J['modules']:
            c['port_directions'] = {pn: J['modules'][c['type']]['ports'][pn]['direction'] for pn in c['connections']}
        else:
            c['port_directions'] = {pn: DIRS[c['type']][pn] for pn in c['connections']}
outs = lambda c: [b for pn, bs in c['connections'].items() if c['port_directions'].get(pn) == 'output' for b in bs if isinstance(b, int)]
ins = lambda c: [(pn, b) for pn, bs in c['connections'].items() if c['port_directions'].get(pn) == 'input' for b in bs]
for c in cells.values():                                  # hpc2 outputs: share i -> domain i
    if c['type'] == 'hpc2':
        for i, b in enumerate(c['connections']['c']): lab[b] = {f'D{i}'}
while changed:
    changed = False
    for c in cells.values():
        if c['type'] == 'hpc2': continue
        u = set().union(*[lab.get(b, set()) if isinstance(b, int) else set() for _, b in ins(c)])
        for b in outs(c):
            if not u <= lab.get(b, set()): lab[b] = lab.get(b, set()) | u; changed = True
for n, c in cells.items():
    if c['type'] == 'hpc2':
        for pn, b in ins(c):
            L = lab.get(b, set()) if isinstance(b, int) else set()
            if pn in ('a', 'b') and len(L - {'R'}) > 1: pass  # an input wire of a gadget is one share: checked below by bit
            if pn in ('a', 'b') and 'R' in L: viol.append(f'{n}.{pn}: randomness on a data input')
            if pn == 'r' and L - {'R'}: viol.append(f'{n}.r: non-random data on the randomness port')
        for pn in ('a', 'b'):
            for i, b in enumerate(c['connections'][pn]):
                L = (lab.get(b, set()) if isinstance(b, int) else set()) - {'R'}
                if L - {f'D{i}'}: viol.append(f'{n}.{pn}[{i}]: domains {sorted(L)} on share {i}')
    else:
        for b in outs(c):
            L = lab.get(b, set())
            if len(L - {'R'}) > 1: viol.append(f'{n} ({c["type"]}): mixes {sorted(L)}')
            if 'R' in L: viol.append(f'{n} ({c["type"]}): randomness outside a gadget')
for pname in ('cdec', 'dec'):
    for i, b in enumerate(M['ports'][pname]['bits']):
        L = lab.get(b, set()) if isinstance(b, int) else set()
        if L - {f'D{i}'}: viol.append(f'output {pname}[{i}] carries {sorted(L)}')
print(f'{top}: {len(cells)} cells ({sum(c["type"] == "hpc2" for c in cells.values())} hpc2), violations {len(viol)}')
for v in viol[:10]: print('  ', v)
sys.exit(1 if viol else 0)
