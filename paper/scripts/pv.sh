#!/bin/bash
# preview PDFs (first page) as PNGs in paper/_preview/ (not part of the deliverable). usage: pv.sh DPI file.pdf ...
cd ~/lwe_agent_handoff/phase2/masked_verification/paper; mkdir -p _preview; rm -f figures/math-1.png
dpi=$1; shift
for f in "$@"; do b=$(basename $f .pdf); bash scripts/preview.sh $f _preview/$b 1 1 $dpi; done
ls _preview
