#!/usr/bin/env python3
"""Summarise P&R metrics of runs/pnr1_* (default project flow) and runs/pnr2_* (hold-buffer cap 60%, both lanes).
usage: python3 -I pnr_summary.py   -> runs/pnr_summary.json"""
import json, statistics
from pathlib import Path
R = Path(__file__).resolve().parents[1] / 'runs'
K = ('period_achieved', 'hold_wns', 'cell_area', 'die_area_um2', 'core_area_um2', 'drc_violations', 'done', 'wirelength_um', 'vias',
     'buffers', 'instances', 'power_total_w', 'parasitics', 'slack_reg2reg', 'slack_in2reg', 'synth_cell_area')
out = {}
for d in sorted(R.glob('pnr[12]_*_u*')):
    f = d / 'metrics.txt'; m = {}
    if f.exists():
        for l in f.read_text().splitlines():
            p = l.split(None, 1)
            if len(p) == 2 and p[0] in K: m[p[0]] = p[1]
    log = (d / 'openroad.log').read_text(errors='replace') if (d / 'openroad.log').exists() else ''
    m['error'] = next((l.strip() for l in log.splitlines() if '[ERROR' in l), '')
    out[d.name] = m
    print(f"{d.name:16s} period {m.get('period_achieved', 'FAIL')[:6]:>6s} hold {m.get('hold_wns', '-')[:7]:>7s} cell {m.get('cell_area', '-'):>10s} "
          f"die {m.get('die_area_um2', '-')[:9]:>9s} DRC {m.get('drc_violations', '-'):>3s} wire {m.get('wirelength_um', '-'):>6s} "
          f"buf {m.get('buffers', '-'):>5s} P {m.get('power_total_w', '-'):>8s} {m['error'][:60]}")
for flow in ('pnr2',):
    for d in ('base', 'pams'):
        rs = [out[k] for k in out if k.startswith(f'{flow}_{d}_') and 'period_achieved' in out[k]]
        if rs:
            med = lambda key: statistics.median(float(r[key]) for r in rs)
            print(f'{flow} {d}: n={len(rs)} median period {med("period_achieved"):.3f} ns, cell area {med("cell_area"):.0f}, die {med("die_area_um2"):.0f} um2')
(R / 'pnr_summary.json').write_text(json.dumps(out, indent=1))
