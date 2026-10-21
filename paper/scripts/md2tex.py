#!/usr/bin/env python3
"""One-off source fix: convert Markdown-style lists ('- item', '  - nested') and '**bold**' that slipped into the
LaTeX sources into itemize environments and \\textbf{}. Lines inside \\caption{...} blocks are turned into inline
text instead (itemize is not allowed in captions). usage: python3 -I md2tex.py file.tex ..."""
import re, sys

BOLD = re.compile(r'\*\*(.+?)\*\*')


def convert(lines):
    out, stack, in_caption = [], [], 0
    for line in lines:
        m = re.match(r'^(\s*)- (.*)$', line)
        if in_caption or ('\\caption{' in line and not line.rstrip().endswith('}')):
            # inside a multi-line caption: inline the items
            if m: line = m.group(1) + m.group(2)
            in_caption += line.count('{') - line.count('}')
            if '\\caption{' in line and in_caption == 0: in_caption = 0
            out.append(BOLD.sub(r'\\textbf{\1}', line)); continue
        if m:
            depth = len(m.group(1)) // 2
            while len(stack) > depth + 1: out.append('  ' * (len(stack) - 1) + '\\end{itemize}'); stack.pop()
            if len(stack) < depth + 1:
                out.append('  ' * len(stack) + '\\begin{itemize}'); stack.append(depth)
            out.append('  ' * (depth + 1) + '\\item ' + BOLD.sub(r'\\textbf{\1}', m.group(2)))
            continue
        if stack and line.strip() and re.match(r'^\s{2,}\S', line) and not line.lstrip().startswith('\\'):
            out.append(BOLD.sub(r'\\textbf{\1}', line)); continue       # continuation of an item
        if stack and (line.strip() == '' or not line.startswith(' ')):
            while stack: out.append('  ' * (len(stack) - 1) + '\\end{itemize}'); stack.pop()
        out.append(BOLD.sub(r'\\textbf{\1}', line))
    while stack: out.append('\\end{itemize}'); stack.pop()
    return out


for f in sys.argv[1:]:
    src = open(f, encoding='utf-8').read().split('\n')
    new = convert(src)
    open(f, 'w', encoding='utf-8', newline='').write('\n'.join(new))
    print(f, sum(1 for l in new if '\\item ' in l) - sum(1 for l in src if '\\item ' in l), 'items added')
