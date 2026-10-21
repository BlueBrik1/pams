#!/usr/bin/env python3
"""Figure-ready CSV data for the paper (final/data/): every seeded P&R run, synthesis results of all Phase XIII/XIV
designs, the gadget breakdown, and the historical comparison series. Sources: final/runs/pnr_stats.json,
competitors/runs/cbench.json, competitors/runs/pnr2_*/metrics.txt, runs/pnr2_*/metrics.txt (frozen designs)."""
import csv, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
F = Path(__file__).resolve().parents[1]; MV = F.parent; D = F / 'data'; D.mkdir(exist_ok=True)
st = json.loads((F / 'runs' / 'pnr_stats.json').read_text())
cols = ['design', 'target', 'seed', 'valid', 'meets_target', 'done', 'drc', 'period', 'setup_wns', 'hold', 'cell', 'die', 'buffers',
        'registers', 'instances', 'wirelength', 'adp', 'crit_start', 'crit_end', 'error']
with open(D / 'pnr_seeded_runs.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, cols, extrasaction='ignore'); w.writeheader()
    for k in sorted(st['runs']): w.writerow(st['runs'][k])
cb = json.loads((MV / 'competitors' / 'runs' / 'cbench.json').read_text())
with open(D / 'synthesis_all_designs.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['design', 'area_med_um2', 'area_min', 'area_max', 'delay_med_ns', 'delay_min', 'delay_max', 'ffs', 'comb_cells', 'hpc2', 'rnd_bits', 'latency_decision'])
    for d, r in cb.items():
        w.writerow([d, r['area_med'], r['area_min'], r['area_max'], r['tclk_med'], r['tclk_min'], r['tclk_max'], r['ff_med'], r['comb_cells_med'], r['gadgets'], r['rnd_bits'], r['decision_latency']])
with open(D / 'gadget_breakdown.csv', 'w', newline='') as f:     # MATHEMATICS.md §6, unchanged by j / q / r
    w = csv.writer(f); w.writerow(['part', 'pams', 'simple_baseline'])
    for row in (['CSA majorities', 13, 23], ['ripple carries', 10, 12], ['comparator', 10, 0], ['top region (OR / tree / AND)', 4, 20],
                ['final combination', 1, 0], ['accumulator', 2, 2], ['total', 40, 57], ['random bits per cycle', 120, 171]):
        w.writerow(row)
with open(D / 'utilization_sweep_routed.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['design', 'util', 'period_ns', 'cell_um2', 'die_um2', 'drc', 'hold_wns'])
    for d in ('base', 'pams', 'base_jp', 'pams_jpr', 'base_jq', 'pams_jqr', 'base_j', 'base_p', 'hoc_jp', 'pams_jp'):
        for u in (45, 50, 55):
            p = (MV / 'runs' if d in ('base', 'pams') else MV / 'competitors' / 'runs') / f'pnr2_{d}_u{u}' / 'metrics.txt'
            if not p.exists(): continue
            m = dict(l.split(None, 1) for l in p.read_text().splitlines() if ' ' in l)
            w.writerow([d, u, m['period_achieved'].strip(), m['cell_area'].strip(), m['die_area_um2'].strip(), m['drc_violations'].strip(), m['hold_wns'].strip()])
print(sorted(p.name for p in D.iterdir()))
