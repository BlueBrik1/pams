#!/bin/bash
# Matched P&R of a competitor lane: models/pnr_lane.sh (Phase XI batch 2) with input/output redirected to competitors/.
# flow-C synthesis (don't-use-pruned library, ABC -D 500) -> tools/run_pnr_mv.sh (frozen, used read-only:
# pnr_mv.tcl = project flow + repair_timing -hold -max_buffer_percent 60), period target 2.0 ns, density 0.6.
# usage: pnr_c.sh DESIGN UTIL [PERIOD=2.0]     output: competitors/runs/pnr2_<design>_u<util>/
set -u
D=$1; U=$2; PER=${3:-2.0}
MV=~/lwe_agent_handoff/phase2/masked_verification; P2=~/lwe_agent_handoff/phase2; CR=$MV/competitors/runs
SYN=$CR/pnrsyn_$D
if [ ! -f $SYN/mapped.v ]; then
  mkdir -p $SYN
  python3 -I - <<PY || exit 1
import sys; from pathlib import Path
sys.path.insert(0, '$P2'); import bfbench as B; B.FLOW = 'C'
m, v, gl = B.synth([Path('$MV/competitors/rtl/$D.v')], Path('$SYN'), top='${D}_lane'); print('flow C synth', m)
PY
fi
[ "$U" = synth-only ] && exit 0
TOP=${D}_lane bash $MV/tools/run_pnr_mv.sh $SYN/mapped.v $CR/pnr2_${D}_u$U $PER $U 0.6 4 | tail -25
