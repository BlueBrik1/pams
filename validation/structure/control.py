#!/usr/bin/env python3
"""Timing / control independence: cvalid and dvalid (the only timing outputs) must depend on no share domain and no
random bit, i.e. only on vin/first/last/c/mode. Uses compcheck's domain propagation on every netlist."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import compcheck as C  # noqa: E402

out = {}
for d in ('pams', 'base'):
    for run in [f'syn_{d}_p{k}' for k in range(5)] + [f'pnrsyn_{d}']:
        cells, ports, gports = C.load_json(f'{RES}/runs/{run}/mapped.json', f'{d}_lane')
        N = C.Net(cells)
        # reuse check() for the domain map, then read the control outputs' domains
        res = C.check(cells, ports, gports)
        dom = {}
        def get(n, seen=None):
            seen = seen or set()
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
        out[run] = {p: sorted(get(ports[p][1][0])) for p in ('cvalid', 'dvalid')}
json.dump(out, open(os.path.join(HERE, 'control_results.json'), 'w'), indent=1)
print(json.dumps(out))
