for t in pdflatex lualatex xelatex latexmk bibtex biber kpsewhich tlmgr dot netlistsvg inkscape rsvg-convert pdftoppm pdfinfo convert magick; do printf "%-12s %s\n" $t "$(command -v $t || echo -)"; done
python3 -c "import matplotlib; print('matplotlib', matplotlib.__version__)" 2>&1 | tail -1
python3 -c "import numpy; print('numpy', numpy.__version__)" 2>&1 | tail -1
ls ~/lwe_agent_handoff/dashboard/.node/bin 2>/dev/null
ls ~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot/usr/bin | grep -E "pdftotext|pdftoppm|pdfinfo" 
df -h ~ | tail -1
