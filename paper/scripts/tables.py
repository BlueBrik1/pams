#!/usr/bin/env python3
"""LaTeX tables generated from the frozen result files (no hand-typed numbers):
  paper/data/tab_pnr_runs.tex     every seeded P&R run (final/runs/pnr_stats.json)
  paper/data/tab_competitors.tex  Phase XIII synthesis of every competitor and PAMS variant (competitors/runs/cbench.json)
usage: python3 -I tables.py"""
import json, sys
from pathlib import Path
sys.dont_write_bytecode = True
PAPER = Path(__file__).resolve().parents[1]; MV = PAPER.parent
st = json.loads((MV / 'final/runs/pnr_stats.json').read_text()); cb = json.loads((MV / 'competitors/runs/cbench.json').read_text())
tt = lambda s: s.replace('_', r'\_')

L = [r'\begin{tabular}{@{}llrlrrrrrrl@{}}', r'\toprule',
     r'design & target & seed & status & period (ns) & setup WNS & hold WNS & cell (\si{\micro\meter\squared}) & buffers & wire (\si{\micro\meter}) & critical path (launch$\to$capture) \\', r'\midrule']
import re


def qnames(run, insts):
    """Q-net (RTL register) names of the launch / capture flip-flops, from the run's routed netlist final.v"""
    f = MV / 'final/runs' / run / 'final.v'
    if not f.exists() or not all(insts): return [None for _ in insts]
    v = f.read_text(); out = []
    for i in insts:
        m = re.search(rf'DFF_X\d\s+{re.escape(i)}\s*\((.*?)\);', v, re.S)
        q = re.search(r'\.Q\(([^)]+)\)', m.group(1)) if m else None
        out.append(q.group(1).strip().lstrip('\\') if q else i)
    return out


for k in sorted(st['runs'], key=lambda k: (-st['runs'][k]['target'], st['runs'][k]['design'] != 'pams_jqr', st['runs'][k]['seed'])):
    r = dict(st['runs'][k])
    r['crit_start'], r['crit_end'] = qnames(k, [r['crit_start'], r['crit_end']])
    status = 'valid' if r['valid'] else (f"DRC {int(r['drc'])}" if r['done'] else 'TIMEOUT')
    f = lambda v, fmt: (fmt % v) if v is not None else '--'
    L.append(f"{tt(r['design'])} & {r['target']:.1f} & {r['seed']} & {status} & {f(r['period'], '%.3f')} & {f(r['setup_wns'], '%+.3f')} & "
             f"{f(r['hold'], '%+.4f')} & {f(r['cell'], '%.0f')} & {f(r['buffers'], '%.0f')} & {f(r['wirelength'], '%.0f')} & "
             f"{tt(str(r['crit_start'] or '--'))}$\\to${tt(str(r['crit_end'] or '--'))} \\\\")
L += [r'\bottomrule', r'\end{tabular}']
(PAPER / 'data' / 'tab_pnr_runs.tex').write_text('\n'.join(L) + '\n')

order = ['base', 'pams', 'base_j', 'base_p', 'base_jp', 'base_bk', 'base_bkp', 'hoc', 'hoc_jp', 'bos', 'bos_j', 'base_q', 'base_jq', 'hoc_jq',
         'pams_j', 'pams_p', 'pams_jp', 'pams_jpr', 'pams_q', 'pams_jq', 'pams_jqr']
L = [r'\begin{tabular}{@{}lrrrrrrl@{}}', r'\toprule',
     r'design & area (\si{\micro\meter\squared}) & delay (ns) & FFs (top) & HPC2 & rnd bits & latency & checks (gate / domain / composition) \\', r'\midrule']
for d in order:
    r = cb[d]
    ok = '/'.join('pass' if r[k] else 'FAIL' for k in ('all_gate_pass', 'all_domain_pass', 'all_compcheck_pass'))
    L.append(f"{tt(d)} & {r['area_med']:,.0f} & {r['tclk_med']:.3f} & {r['ff_med']:,.0f} & {r['gadgets']} & {r['rnd_bits']} & {r['decision_latency']}+4 & {ok} \\\\")
L += [r'\bottomrule', r'\end{tabular}']
(PAPER / 'data' / 'tab_competitors.tex').write_text('\n'.join(L).replace(',', '{,}') + '\n')
print('wrote tab_pnr_runs.tex, tab_competitors.tex')
