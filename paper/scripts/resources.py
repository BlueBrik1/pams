#!/usr/bin/env python3
"""Area accounting of the mapped finalists (competitors/runs/syn_<d>_p0/mapped.json, Yosys flow B mapping 0) by
functional block. Cell areas from the Nangate45 liberty used for synthesis.
  * HPC2 gadgets: every cell inside the hpc2 instances (keep_hierarchy, so the boundary is exact).
  * Flip-flops outside gadgets: classified by the name of the net on their Q pin (RTL register names survive
    synthesis): input registers, share-wise front-end registers, public-constant registers, aligned operands,
    alignment (delay-chain) registers r<N>, control pipeline, accumulator glue.
  * Combinational cells outside gadgets: attributed to the register group(s) or gadget pins reached by their
    fan-out cone (forward to the first register / gadget input / output port). A cell whose cone reaches more than
    one group is counted as 'shared'. This attribution is approximate where ABC merged logic across stages.
Writes paper/data/resources.json and prints a table. usage: python3 -I resources.py"""
import json, re, sys
from collections import defaultdict
from pathlib import Path
sys.dont_write_bytecode = True
PAPER = Path(__file__).resolve().parents[1]; MV = PAPER.parent
LIB = Path.home() / 'lwe_agent_handoff/current/lib/NangateOpenCellLibrary_typical.lib'
AREA = {m.group(1): float(m.group(2)) for m in re.finditer(r'cell\s*\(\s*"?(\w+)"?\s*\)\s*\{\s*(?:/\*.*?\*/\s*)?.*?area\s*:\s*([\d.]+)', LIB.read_text(), re.S)}
OUTP = {'Z', 'ZN', 'Q', 'QN'}


def ffgroup(q):
    rules = [(r'^x\dq', 'input registers (shares)'), (r'^(c0|d0)$', 'input registers (public c, d)'),
             (r'^x\dr', 'share-wise front end: register x_r'), (r'^(mh|ml)\d', 'share-wise front end: partial products'),
             (r'^(s\dp|fq\d)$', 'share-wise front end: switched value'), (r'^y\d$', 'aligned operands y_i'),
             (r'^(qcr|qnr|e0r|c0r|lowr|thr|lowrq|thrq|lowp|thp|th2|offr|enr|shr|offrq|enrq|shrq|offp|enp|shp|en2)$', 'public constant registers'),
             (r'^r\d+$', 'alignment registers (delay chains)'), (r'^(vp|fp|lp|f2p|lastp|fprev|cvalid|dvalid)$', 'control pipeline'),
             (r'^e0$', 'public constant registers'), (r'^m\d$', 'share-wise front end: partial products'),
             (r'^\$auto\$alumacc', 'front-end registers with Yosys-internal net names'),
             (r'^acc_last$', 'accumulator')]
    base = re.sub(r'\[\d+\]$', '', q)
    for pat, g in rules:
        if re.match(pat, base): return g
    return 'other registers'


def account(d):
    J = json.loads((MV / f'competitors/runs/syn_{d}_p0/mapped.json').read_text()); top = J['modules'][f'{d}_lane']
    gad_area = sum(AREA[c['type']] for c in J['modules']['hpc2']['cells'].values()); gad_ff = sum(c['type'].startswith('DFF') for c in J['modules']['hpc2']['cells'].values())
    names = {}
    for n, v in top['netnames'].items():
        for i, b in enumerate(v['bits']):
            if isinstance(b, int) and (b not in names or names[b].startswith('$')): names[b] = n if len(v['bits']) == 1 else f'{n}[{i}]'
    sinks = defaultdict(list)
    for cn, c in top['cells'].items():
        for p, bs in c['connections'].items():
            if c['type'] == 'hpc2':
                if p in ('a', 'b', 'r'):
                    for b in bs: sinks[b].append(('gadget-in', cn))
                continue
            if p not in OUTP and p != 'CK':
                for b in bs: sinks[b].append((cn, p))
    for p, v in top['ports'].items():
        if v['direction'] == 'output':
            for b in v['bits']: sinks[b].append(('port', p))
    groups = defaultdict(lambda: [0, 0.0]); ngad = 0
    target = {}
    for cn, c in top['cells'].items():
        if c['type'] == 'hpc2': ngad += 1; continue
        if c['type'].startswith('DFF'):
            q = names.get(c['connections']['Q'][0], '?') if 'Q' in c['connections'] else '?'
            g = ffgroup(q); target[cn] = g; groups['FF: ' + g][0] += 1; groups['FF: ' + g][1] += AREA[c['type']]
    memo = {}

    def reach(cn, seen=()):
        if cn in memo: return memo[cn]
        c = top['cells'][cn]; out = set()
        for p, bs in c['connections'].items():
            if p not in OUTP: continue
            for b in bs:
                for s, sp in sinks.get(b, []):
                    if s == 'gadget-in': out.add('masked kernel: gadget input XOR network')
                    elif s == 'port': out.add('output ports')
                    elif s in target: out.add(target[s])
                    elif s not in seen: out |= reach(s, seen + (cn,))
        memo[cn] = out; return out
    for cn, c in top['cells'].items():
        if c['type'] == 'hpc2' or c['type'].startswith('DFF'): continue
        r = reach(cn); g = ('logic -> ' + next(iter(r))) if len(r) == 1 else ('logic -> shared' if r else 'logic -> (dead)')
        groups[g][0] += 1; groups[g][1] += AREA[c['type']]
    total = sum(v[1] for v in groups.values()) + ngad * gad_area
    return dict(hpc2_instances=ngad, hpc2_area_each=gad_area, hpc2_ff_each=gad_ff, hpc2_area=ngad * gad_area, total=total,
                groups={k: dict(cells=v[0], area=round(v[1], 3)) for k, v in sorted(groups.items())})


if __name__ == '__main__':
    out = {d: account(d) for d in ('pams_jqr', 'base_jq')}
    (PAPER / 'data' / 'resources.json').write_text(json.dumps(out, indent=1))
    for d, r in out.items():
        print(f"== {d}: total {r['total']:.1f} um2 (cbench area {json.loads((MV / 'competitors/runs/cbench.json').read_text())[d]['maps'][0]['area']}); "
              f"HPC2 {r['hpc2_instances']} x {r['hpc2_area_each']:.3f} = {r['hpc2_area']:.1f}")
        for k, v in r['groups'].items(): print(f"   {k:60} {v['cells']:5} cells {v['area']:9.1f} um2")
