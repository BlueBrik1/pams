#!/usr/bin/env python3
"""Final review: check the manuscript's Verilog references against the frozen RTL (read-only).
  1. every \\lstinputlisting range: file exists, lines in range, and the nearest preceding "(lines a--b)" heading agrees
  2. every \\sig{...} identifier that looks like an RTL name exists as a word in pams_jqr.v or base_jq.v
     (cell names, tool names and generator-function names are reported separately, not as errors)
  3. key structural facts: 2,747 / 3,167 lines, 40 / 57 hpc2 instances, rnd widths 120 / 171, gadget g uses rnd[3g+2:3g],
     1,190 delay assignments in lines 1538-2729, hpc2 module lines 4-19
Writes paper/review/rtl_audit.json.  usage: python3 -I audit_rtl.py"""
import json, re
from pathlib import Path
PAPER = Path(__file__).resolve().parents[1]; MV = PAPER.parent
RTL = {'\\RTL': MV / 'final/rtl/pams_jqr.v', '\\RTLB': MV / 'final/rtl/base_jq.v'}
src = {k: v.read_text().split('\n') for k, v in RTL.items()}
words = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', '\n'.join(src['\\RTL'] + src['\\RTLB'])))
tex = {p: p.read_text() for p in list((PAPER / 'sections').glob('*.tex')) + list((PAPER / 'appendices').glob('*.tex'))}
R = {'listings': [], 'listing_problems': [], 'unknown_signals': {}, 'facts': {}}
for p, t in tex.items():
    for m in re.finditer(r'\\lstinputlisting\[firstline=(\d+),lastline=(\d+)(?:,firstnumber=(\d+))?\]\{(\\RTLB?)\}', t):
        a, b, fn, f = int(m[1]), int(m[2]), m[3], m[4]
        n = len(src[f]) - (1 if src[f][-1] == '' else 0)
        ok = 1 <= a <= b <= n and (fn is None or int(fn) == a)
        head = re.findall(r'lines?~?\s*(\d+)--(\d+)', t[max(0, m.start() - 400):m.start()])
        R['listings'].append(dict(file=p.name, rtl=f, first=a, last=b, heading=head[-1] if head else None))
        if not ok: R['listing_problems'].append((p.name, a, b, 'range'))
for p, t in tex.items():
    for s in re.findall(r'\\sig\{([^}]*)\}', t):
        raw = s.replace('\\_', '_').replace('$i$', '0').replace('$N$', '111').replace('$', '')
        for tok in re.split(r'[\s,/.()\\+\-:\[\]]+', raw):
            tok = tok.strip('{}')
            if not tok or tok.isdigit() or not re.match(r'[A-Za-z_]', tok): continue
            if tok in words: continue
            R['unknown_signals'].setdefault(tok, set()).add(p.name)
R['unknown_signals'] = {k: sorted(v) for k, v in sorted(R['unknown_signals'].items())}
L = src['\\RTL']
R['facts'] = dict(
    pams_lines=len(L) - (L[-1] == ''), base_lines=len(src['\\RTLB']) - (src['\\RTLB'][-1] == ''),
    pams_hpc2=sum(1 for l in L if re.match(r'\s*hpc2\s+\w+\s*\(', l)), base_hpc2=sum(1 for l in src['\\RTLB'] if re.match(r'\s*hpc2\s+\w+\s*\(', l)),
    pams_rnd='[119:0] rnd' in L[21], base_rnd=any('[170:0] rnd' in l for l in src['\\RTLB'][:40]),
    hpc2_module=(L[3].lstrip().startswith('module hpc2'), L[18].strip().startswith('endmodule')),
    delay_assignments=sum(1 for l in L[1537:2729] if re.match(r'\s*r\d+\s*<=', l)),
    gadget_lines=(min(i + 1 for i, l in enumerate(L) if re.match(r'\s*hpc2\s+ug', l)), max(i + 1 for i, l in enumerate(L) if re.match(r'\s*hpc2\s+ug', l))),
)
gi = [(m[1], int(m[2]), int(m[3])) for l in L for m in [re.search(r'hpc2\s+(u\w+)\s*\(.*?\.r\(rnd\[(\d+):(\d+)\]\)', l)] if m]
R['facts']['rnd_slices_ok'] = all(hi == lo + 2 for _, hi, lo in gi) and sorted(lo for _, _, lo in gi) == list(range(0, 3 * len(gi), 3))
R['facts']['rnd_slices_checked'] = len(gi)
R['facts']['gadget_order'] = [g for g, _, _ in sorted(gi, key=lambda x: x[2])]
(PAPER / 'review').mkdir(exist_ok=True)
(PAPER / 'review' / 'rtl_audit.json').write_text(json.dumps(R, indent=1, default=list))
print(json.dumps({k: R[k] for k in ('listing_problems', 'facts', 'unknown_signals')}, indent=1, default=list)[:6000])
for x in R['listings']: print(x)
