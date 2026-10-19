#!/usr/bin/env python3
"""Keyword-in-context search over the dumped (untrusted) paper texts. usage: python3 -I grep_refs.py name kw [kw ...]"""
import re, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / 'refs'
t = ' '.join(l.split('\t', 1)[-1] for l in (R / (sys.argv[1] + '.txt')).read_text(errors='replace').splitlines())
for kw in sys.argv[2:]:
    for m in list(re.finditer(re.escape(kw), t, re.I))[:4]:
        print(f'[{kw}] ...' + t[max(0, m.start() - 350):m.start() + 450] + '...\n')
