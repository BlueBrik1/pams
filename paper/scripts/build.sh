#!/bin/bash
# Build PAMS_paper.pdf: regenerate data-derived figures (optional, -f), then pdflatex + bibtex + 2x pdflatex.
# Requires TinyTeX (user-local, ~/.TinyTeX) or any TeX Live with the packages listed in README.md.
set -e
cd "$(dirname "$0")/.."
export PATH=$(ls -d ~/.TinyTeX/bin/* 2>/dev/null | head -1):$PATH
if [ "$1" = "-f" ]; then
  python3 -I scripts/examples.py && python3 -I scripts/resources.py && python3 -I scripts/appendix_data.py && python3 -I scripts/tables.py && python3 -I scripts/generate_figures.py results physical gates math
fi
pdflatex -interaction=nonstopmode -halt-on-error main.tex > build.log 2>&1 || { tail -40 build.log; exit 1; }
bibtex main >> build.log 2>&1 || { tail -20 build.log; exit 1; }
pdflatex -interaction=nonstopmode -halt-on-error main.tex >> build.log 2>&1
pdflatex -interaction=nonstopmode -halt-on-error main.tex >> build.log 2>&1
cp main.pdf PAMS_paper.pdf
grep -E "Warning.*(undefined|Citation|Reference)|multiply defined" build.log | sort -u | head -20 || true
echo "pages: $(grep -o 'Output written on main.pdf ([0-9]* pages' build.log | tail -1)"
