#!/bin/bash
# render pages FIRST..LAST of PAMS_paper.pdf to paper/_preview/p-NN.png at DPI (visual inspection)
cd ~/lwe_agent_handoff/phase2/masked_verification/paper; mkdir -p _preview; rm -f _preview/p-*.png
bash scripts/preview.sh main.pdf _preview/p $1 $2 ${3:-70}
ls _preview | grep '^p-' | tr '\n' ' '
