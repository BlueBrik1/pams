#!/usr/bin/env python3
"""Cost of the randomness source in the same flow: Trivium-64 (flow B, Yosys/ABC Nangate45, OpenSTA).
A lane needing R fresh bits per cycle needs ceil(R / 64) instances (seeding / reseeding logic not included).
usage: python3 -I rng_cost.py   -> runs/rng_cost.json"""
import json, math, sys
from pathlib import Path
H = Path(__file__).resolve().parent; P2 = H.parents[1]; sys.path.insert(0, str(P2))
import bfbench as B
B.FLOW = 'B'
w = H.parents[0] / 'runs' / 'syn_trivium64'; w.mkdir(parents=True, exist_ok=True)
m, mapped, gl = B.synth([H.parents[0] / 'rtl' / 'trivium64.v'], w, top='trivium64'); m.update(B.sta(mapped, w, top='trivium64'))
bench = json.loads((H.parents[0] / 'runs' / 'bench.json').read_text())
R = {'base': 171, 'pams': 120, 'pams_r': 120}
res = dict(trivium64=dict(area=m['area'], tclk=m['tclk'], ff=m['ff']))
for d, r in R.items():
    n = math.ceil(r / 64); res[d] = dict(rand_bits=r, instances=n, rng_area=n * m['area'], lane_area=bench[d]['area_med'],
                                          total=bench[d]['area_med'] + n * m['area'])
(H.parents[0] / 'runs' / 'rng_cost.json').write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
