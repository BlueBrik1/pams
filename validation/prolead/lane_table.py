#!/usr/bin/env python3
"""Summary table of every lane PROLEAD run: probing-set count (from prolead.log), simulations, max -log10 p, the
multiple-testing null expectation of the max (median of the max of N independent uniform p-values:
-log10(1 - 2^(-1/N)) ~ log10(N / ln 2)), and the top set. Writes lane_table.json."""
import json, math, os, re
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lane'); out = []
for tag in sorted(os.listdir(H)):
    r, l = os.path.join(H, tag, 'result.json'), os.path.join(H, tag, 'prolead.log')
    if not os.path.exists(r): continue
    j = json.load(open(r)); log = open(l).read() if os.path.exists(l) else ''
    rows = re.findall(r'^\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*[\d.]+\s*\|\s*$', log, re.M)
    m = rows[-1] if rows else None                      # | #Standard | #Extended | #Probing Sets | min | max | avg |
    n = int(m[2]) if m else None
    null = -math.log10(1 - 2 ** (-1 / n)) if n else None
    out.append(dict(tag=tag, variant=j.get('variant'), order=j.get('order'), cycles=j.get('cycles'), sims=j.get('simulations_done'),
                    sets=n, max=j.get('max_minus_log10_p'), null_median_max=round(null, 2) if null else None,
                    leak=j.get('leakage_detected'), top=j.get('top_probing_set'), rc=j.get('returncode'), attempts=j.get('attempts')))
json.dump(out, open(os.path.join(os.path.dirname(H), 'lane_table.json'), 'w'), indent=1)
for o in out: print(o)
