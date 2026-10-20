#!/usr/bin/env python3
"""Markdown tables for BENCHMARKS.md from competitors/runs/cbench.json and the P&R metrics (competitors/runs/pnr2_*;
frozen base / pams routed results from the Phase XI runs/pnr2_*, same flow). improvement = (comp - pams) / comp x 100.
usage: python3 -I tables.py > ../runs/tables.md"""
import json, statistics, sys
from pathlib import Path
sys.dont_write_bytecode = True
C = Path(__file__).resolve().parents[1]; MV = C.parent
S = json.loads((C / 'runs' / 'cbench.json').read_text())
SFX = lambda d: d.split('_', 1)[1].replace('bk', '') if '_' in d else ''
DEPTH = lambda d: 2 if 'q' in SFX(d) else 1 if 'p' in SFX(d) else 0


def routed(d):
    root = MV / 'runs' if d in ('base', 'pams') else C / 'runs'
    rows = []
    for u in (45, 50, 55):
        f = root / f'pnr2_{d}_u{u}' / 'metrics.txt'
        if not f.exists(): return None
        m = dict(l.split(None, 1) for l in f.read_text().splitlines() if ' ' in l)
        if m.get('done', '').strip() != '1': return None
        rows.append(dict(u=u, per=float(m['period_achieved']), cell=float(m['cell_area']), die=float(m['die_area_um2']),
                         drc=int(m['drc_violations']), hold=float(m['hold_wns'])))
    md = lambda k: statistics.median(r[k] for r in rows)
    return dict(per=md('per'), cell=md('cell'), die=md('die'), per_rng=(min(r['per'] for r in rows), max(r['per'] for r in rows)),
                drc=sum(r['drc'] for r in rows), hold_min=min(r['hold'] for r in rows), rows=rows)


imp = lambda c, p: (c - p) / c * 100
print('| design | depth | area µm² median [min, max] | delay ns median [min, max] | FFs | comb. cells | HPC2 | rnd bits/cycle | latency | II | gate / domain / compcheck |')
print('|---|---|---|---|---|---|---|---|---|---|---|')
for d, r in S.items():
    print(f"| {d} | +{DEPTH(d)} | {r['area_med']:,.0f} [{r['area_min']:,.0f}, {r['area_max']:,.0f}] | {r['tclk_med']:.3f} [{r['tclk_min']:.3f}, {r['tclk_max']:.3f}] | "
          f"{r['ff_med']:,.0f} | {r['comb_cells_med']:,.0f} | {r['gadgets']} | {r['rnd_bits']} | {r['decision_latency']} + 4 | 1 | "
          f"{'/'.join('PASS' if r[k] else 'FAIL' for k in ('all_gate_pass', 'all_domain_pass', 'all_compcheck_pass'))} |")
print()
print('| design | routed period ns median [min, max] | routed cell area µm² | die area µm² | DRC | min hold WNS ns |')
print('|---|---|---|---|---|---|')
R = {}
for d in ['base', 'pams'] + [k for k in S if k not in ('base', 'pams')]:
    r = routed(d)
    if r: R[d] = r; print(f"| {d} | {r['per']:.3f} [{r['per_rng'][0]:.3f}, {r['per_rng'][1]:.3f}] | {r['cell']:,.0f} | {r['die']:,.0f} | {r['drc']} | {r['hold_min']:+.3f} |")
print()
pairs = [('pams', d) for d in S if not d.startswith('pams')] + [('pams_jpr', d) for d in ('base_p', 'base_jp', 'hoc_jp', 'base_bkp', 'base_jq')] + \
        [('pams_jqr', d) for d in ('base_jq', 'hoc_jq', 'base_q')]
print('| PAMS design | competitor | synth area impr. % | synth delay impr. % | routed cell impr. % | routed period impr. % | routed die impr. % | rnd impr. % |')
print('|---|---|---|---|---|---|---|---|')
for p, c in pairs:
    if p not in S or c not in S: continue
    a, b = S[c], S[p]
    rr = (f"{imp(R[c]['cell'], R[p]['cell']):+.1f} | {imp(R[c]['per'], R[p]['per']):+.1f} | {imp(R[c]['die'], R[p]['die']):+.1f}"
          if c in R and p in R else '— | — | —')
    print(f"| {p} | {c} | {imp(a['area_med'], b['area_med']):+.1f} | {imp(a['tclk_med'], b['tclk_med']):+.1f} | {rr} | {imp(a['rnd_bits'], b['rnd_bits']):+.1f} |")
