#!/usr/bin/env python3
"""Attribute Overfull hbox warnings in main.log to source files (tracks the '(./file.tex' nesting). Review helper."""
import re, sys
log = open(sys.argv[1] if len(sys.argv) > 1 else 'main.log', errors='replace').read()
pat = re.compile(r'\((\./[^\s()]+\.tex)|\)|Overfull \\hbox \(([\d.]+)pt too wide\) (?:in paragraph at lines (\d+)--\d+|detected at line (\d+))')
stack, out = [], []
for tok in pat.finditer(log):
    if tok.group(1):
        stack.append(tok.group(1))
    elif tok.group(0) == ')':
        if stack: stack.pop()
    else:
        out.append((float(tok.group(2)), stack[-1] if stack else '?', tok.group(3) or tok.group(4)))
for w, f, l in sorted(out, reverse=True):
    print(f'{w:7.1f}pt  {f}:{l}')
