#!/usr/bin/env python3
"""One-off layout fix: wrap given tabular environments (by 1-based line numbers of \\begin{tabular} / \\end{tabular})
in \\resizebox{<width>}{!}{...}. usage: wrap_tables.py file.tex begin end width [begin end width ...]"""
import sys
f = sys.argv[1]; L = open(f, encoding='utf-8').read().split('\n')
spec = sys.argv[2:]
jobs = [(int(spec[i]), int(spec[i + 1]), spec[i + 2]) for i in range(0, len(spec), 3)]
for b, e, w in sorted(jobs, reverse=True):
    assert L[b - 1].lstrip().startswith('\\begin{tabular'), L[b - 1]
    assert L[e - 1].lstrip().startswith('\\end{tabular'), L[e - 1]
    L[e - 1] = L[e - 1] + '}'
    L[b - 1] = '\\resizebox{' + w + '}{!}{%\n' + L[b - 1]
open(f, 'w', encoding='utf-8', newline='').write('\n'.join(L)); print('wrapped', len(jobs), 'in', f)
