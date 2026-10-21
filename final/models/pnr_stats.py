#!/usr/bin/env python3
"""Statistics of the Phase XIV seeded P&R campaign (final/runs/pnr_<design>_T<target>_s<seed>/).
Run validity: flow finished (done 1), 0 DRC, RCX-extracted parasitics, hold WNS >= 0. 'Meets target' (setup slack
>= 0) is reported separately. Per (design, target): n valid / failed, median / min / max / sample std of the achieved
period, cell area, die area, buffers, registers, area-delay product (cell area x achieved period).
Comparison per target: medians, the exact two-sided Mann-Whitney / Wilcoxon rank-sum p-value over all C(n1+n2, n1)
label assignments, and the count of seed-wise wins. Seeds are independent per design (seed k of PAMS and seed k of
the baseline place different netlists), so pairing by seed number is reported only as a descriptive count.
Writes final/runs/pnr_stats.json and prints markdown tables. usage: python3 -I pnr_stats.py"""
import itertools, json, re, statistics as st, sys
from pathlib import Path
sys.dont_write_bytecode = True
F = Path(__file__).resolve().parents[1]
runs = {}
for d in sorted((F / 'runs').glob('pnr_*_T*_s*')):
    if not d.is_dir(): continue
    m = re.match(r'pnr_(.+)_T([\d.]+)_s(\d+)$', d.name); des, T, s = m.group(1), float(m.group(2)), int(m.group(3))
    f = d / 'metrics.txt'
    kv = dict(l.split(None, 1) for l in f.read_text().splitlines() if ' ' in l) if f.exists() else {}
    tr = (d / 'timing.rpt').read_text() if (d / 'timing.rpt').exists() else ''
    sp = re.search(r'Startpoint: (\S+)', tr); ep = re.search(r'Endpoint: (\S+)', tr)
    num = lambda k: float(kv[k]) if k in kv and kv[k].strip() not in ('NA', '') else None
    r = dict(design=des, target=T, seed=s, done=kv.get('done', '').strip() == '1', drc=num('drc_violations'),
             rcx=kv.get('parasitics', '').strip() == 'rcx_extracted', period=num('period_achieved'), setup_wns=num('slack_setup_wns'),
             hold=num('hold_wns'), cell=num('cell_area'), die=num('die_area_um2'), buffers=num('buffers'), registers=num('registers'),
             instances=num('instances'), wirelength=num('wirelength_um'), crit_start=sp.group(1) if sp else None, crit_end=ep.group(1) if ep else None)
    if not r['done']:
        log = (d / 'openroad.log').read_text(errors='replace') if (d / 'openroad.log').exists() else ''
        err = re.findall(r'\[ERROR [^\]]+\].*', log); r['error'] = err[-1][:200] if err else 'did not finish'
    r['valid'] = bool(r['done'] and r['drc'] == 0 and r['rcx'] and r['hold'] is not None and r['hold'] >= 0)
    r['meets_target'] = bool(r['valid'] and r['setup_wns'] is not None and r['setup_wns'] >= 0)
    r['adp'] = r['cell'] * r['period'] if r['valid'] else None
    runs[d.name] = r


def summary(rs, k):
    v = [r[k] for r in rs]
    return dict(median=st.median(v), min=min(v), max=max(v), std=st.stdev(v) if len(v) > 1 else 0.0)


def ranksum_p(a, b):
    """exact two-sided p of the rank-sum statistic (ties get midranks; enumerates all label assignments)"""
    allv = a + b; n = len(allv); order = sorted(range(n), key=lambda i: allv[i]); ranks = [0.0] * n; i = 0
    while i < n:
        j = i
        while j + 1 < n and allv[order[j + 1]] == allv[order[i]]: j += 1
        for k in range(i, j + 1): ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    obs = sum(ranks[:len(a)]); mean = len(a) * (n + 1) / 2
    combos = list(itertools.combinations(range(n), len(a)))
    return sum(abs(sum(ranks[i] for i in c) - mean) >= abs(obs - mean) - 1e-9 for c in combos) / len(combos)


out = dict(runs=runs, groups={}, comparisons={})
targets = sorted({r['target'] for r in runs.values()}, reverse=True)
print('| design | target ns | runs valid / total | meet target | period median [min, max] (std) ns | cell area median [min, max] (std) µm² | die µm² | buffers | registers | ADP µm²·ns |')
print('|---|---|---|---|---|---|---|---|---|---|')
for T in targets:
    for des in ('pams_jqr', 'base_jq'):
        rs = [r for r in runs.values() if r['design'] == des and r['target'] == T]
        ok = [r for r in rs if r['valid']]
        if not rs: continue
        g = dict(n=len(rs), valid=len(ok), meets=sum(r['meets_target'] for r in ok), failed=[(r['seed'], r.get('error')) for r in rs if not r['valid']])
        if ok:
            for k in ('period', 'cell', 'die', 'buffers', 'registers', 'adp', 'setup_wns', 'hold'): g[k] = summary(ok, k)
            g['crit'] = sorted({(r['crit_start'], r['crit_end']) for r in ok})
            p, c = g['period'], g['cell']
            print(f"| {des} | {T:.2f} | {len(ok)} / {len(rs)} | {g['meets']} | {p['median']:.3f} [{p['min']:.3f}, {p['max']:.3f}] ({p['std']:.3f}) | "
                  f"{c['median']:,.0f} [{c['min']:,.0f}, {c['max']:,.0f}] ({c['std']:,.0f}) | {g['die']['median']:,.0f} | {g['buffers']['median']:,.0f} | "
                  f"{g['registers']['median']:,.0f} | {g['adp']['median']:,.0f} |")
        out['groups'][f'{des}@{T}'] = g
print()
print('| target ns | PAMS period impr. (medians) | p (rank-sum, period) | PAMS faster in seed k (descriptive) | cell area impr. | p (cell) | die impr. | ADP impr. | period ranges overlap? |')
print('|---|---|---|---|---|---|---|---|---|')
imp = lambda b, p: (b - p) / b * 100
for T in targets:
    a = [r for r in runs.values() if r['design'] == 'pams_jqr' and r['target'] == T and r['valid']]
    b = [r for r in runs.values() if r['design'] == 'base_jq' and r['target'] == T and r['valid']]
    if len(a) < 2 or len(b) < 2: continue
    ga, gb = out['groups'][f'pams_jqr@{T}'], out['groups'][f'base_jq@{T}']
    pp = ranksum_p([r['period'] for r in a], [r['period'] for r in b]); pc = ranksum_p([r['cell'] for r in a], [r['cell'] for r in b])
    sa = {r['seed']: r for r in a}; sb = {r['seed']: r for r in b}; common = sorted(set(sa) & set(sb))
    wins = sum(sa[s]['period'] < sb[s]['period'] for s in common)
    overlap = not (ga['period']['max'] < gb['period']['min'] or gb['period']['max'] < ga['period']['min'])
    c = dict(period_impr=imp(gb['period']['median'], ga['period']['median']), p_period=pp, seed_wins=f'{wins}/{len(common)}',
             cell_impr=imp(gb['cell']['median'], ga['cell']['median']), p_cell=pc, die_impr=imp(gb['die']['median'], ga['die']['median']),
             adp_impr=imp(gb['adp']['median'], ga['adp']['median']), period_overlap=overlap)
    out['comparisons'][str(T)] = c
    print(f"| {T:.2f} | {c['period_impr']:+.1f} % | {pp:.4f} | {c['seed_wins']} | {c['cell_impr']:+.1f} % | {pc:.4f} | {c['die_impr']:+.1f} % | {c['adp_impr']:+.1f} % | {'yes' if overlap else 'no'} |")
(F / 'runs' / 'pnr_stats.json').write_text(json.dumps(out, indent=1, default=str))
