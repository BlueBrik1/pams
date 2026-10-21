#!/usr/bin/env python3
"""validation/structure/control.py applied to the final netlists: cvalid and dvalid (the only timing outputs) must
depend on no share domain and no random bit. Same propagation code, other netlist paths.
Writes final/runs/control_final.json."""
import json, sys
from pathlib import Path
sys.dont_write_bytecode = True
MV = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MV / 'validation' / 'structure'))
import compcheck as C  # noqa: E402

out = {}
for d in ('pams_jqr', 'base_jq'):
    for run in [f'syn_{d}_p{k}' for k in range(5)] + [f'pnrsyn_{d}']:
        cells, ports, gports = C.load_json(str(MV / 'competitors' / 'runs' / run / 'mapped.json'), f'{d}_lane')
        N = C.Net(cells)

        def get(n, seen):
            if n in seen: return frozenset()
            seen.add(n)
            for p, (dr, nets) in ports.items():
                if dr == 'input' and n in nets:
                    return frozenset({p}) if p in ('x0', 'x1', 'x2', 'rnd') else frozenset()
            if any(n in g['c'] for g in gports.values()): return frozenset({'gadget'})
            dv = N.drv.get(n)
            if dv is None: return frozenset()
            t, pm = cells[dv[0]]
            ins = [pm['D']] if t.startswith('DFF') else [m for q, m in pm.items() if q not in C.OUT_PINS and q != 'CK']
            return frozenset().union(*[get(m, seen) for m in ins])
        out[run] = {p: sorted(get(ports[p][1][0], set())) for p in ('cvalid', 'dvalid')}
(MV / 'final' / 'runs' / 'control_final.json').write_text(json.dumps(out, indent=1))
print(json.dumps(out)); print('timing outputs data-independent in all netlists:', all(not v for r in out.values() for v in r.values()))
