#!/usr/bin/env python3
"""Final review: recompute every headline number of the manuscript from the frozen evidence (read-only) and print them,
so that RESULTS_AUDIT.md can compare them with the text. Writes paper/review/results_audit.json.
usage: python3 -I audit_results.py"""
import json, statistics as st, csv
from itertools import combinations
from pathlib import Path
PAPER = Path(__file__).resolve().parents[1]; MV = PAPER.parent
P = json.loads((MV / 'final/runs/pnr_stats.json').read_text())
runs = list(P['runs'].values()) if isinstance(P['runs'], dict) else P['runs']
def sel(dz, T, valid=None, done=None):
    return [r for r in runs if r['design'] == dz and r['target'] == T and (valid is None or r['valid'] == valid) and (done is None or r['done'] == done)]
def ranksum_p(a, b):
    """exact two-sided rank-sum p over all label assignments (no ties expected)"""
    allv = sorted(a + b); n = len(a); rank = {v: i + 1 for i, v in enumerate(allv)}
    obs = sum(rank[v] for v in a); mu = n * (len(allv) + 1) / 2
    cnt = tot = 0
    for c in combinations(range(1, len(allv) + 1), n):
        tot += 1; cnt += abs(sum(c) - mu) >= abs(obs - mu) - 1e-9
    return cnt / tot
out = {}
for T in (2.0, 1.2, 1.1):
    row = {}
    for dz in ('pams_jqr', 'base_jq'):
        v = sel(dz, T, valid=True); f = sel(dz, T, done=True)
        row[dz] = dict(n_runs=len(sel(dz, T)), n_valid=len(v), n_finished=len(f),
                       period_median=st.median(r['period'] for r in v) if v else None,
                       period_range=[min(r['period'] for r in v), max(r['period'] for r in v)] if v else None,
                       cell_median_valid=st.median(r['cell'] for r in v) if v else None,
                       cell_median_finished=st.median(r['cell'] for r in f) if f else None,
                       cell_range_finished=[min(r['cell'] for r in f), max(r['cell'] for r in f)] if f else None,
                       die_median=st.median(r['die'] for r in f) if f else None,
                       buffers_median=st.median(r['buffers'] for r in f) if f else None,
                       wire_range=[min(r['wirelength'] for r in f), max(r['wirelength'] for r in f)] if f else None,
                       adp_median=st.median(r['adp'] for r in v) if v else None)
    a, b = row['pams_jqr'], row['base_jq']
    row['cell_improvement_finished'] = 1 - a['cell_median_finished'] / b['cell_median_finished']
    if b['cell_median_valid']: row['cell_improvement_valid'] = 1 - a['cell_median_valid'] / b['cell_median_valid']
    row['die_improvement'] = 1 - a['die_median'] / b['die_median']
    if b['n_valid'] >= 2:
        row['period_diff'] = 1 - a['period_median'] / b['period_median']
        row['period_p'] = ranksum_p([r['period'] for r in sel('pams_jqr', T, True)], [r['period'] for r in sel('base_jq', T, True)])
        row['adp_improvement'] = 1 - a['adp_median'] / b['adp_median']
    pa = [r['cell'] for r in sel('pams_jqr', T, done=True)]; pb = [r['cell'] for r in sel('base_jq', T, done=True)]
    row['cell_every_pams_below_every_base'] = max(pa) < min(pb)
    if len(pa) == 7 and len(pb) == 7: row['cell_p'] = ranksum_p(pa, pb)
    out[str(T)] = row
B = json.loads((MV / 'competitors/runs/cbench.json').read_text())
out['cbench_keys'] = list(B)[:40] if isinstance(B, dict) else len(B)
for k in ('pams_jqr', 'base_jq'):
    if isinstance(B, dict) and k in B: out['synth_' + k] = B[k] if not isinstance(B[k], list) else B[k][:2]
with open(MV / 'final/data/gadget_breakdown.csv') as fh: out['gadget_breakdown'] = list(csv.DictReader(fh))
(PAPER / 'review').mkdir(exist_ok=True)
(PAPER / 'review' / 'results_audit.json').write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=1, default=str)[:9000])
