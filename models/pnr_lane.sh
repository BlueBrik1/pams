#!/bin/bash
# Matched P&R of a generated lane with the project flow (pnr/run_pnr.sh + pnr.tcl, OpenROAD ORFS 26Q3, Nangate45):
# flow-C synthesis (don't-use-pruned library, ABC -D 500) -> tie cells -> floorplan/place/CTS/route/RCX.
# usage: pnr_lane.sh DESIGN UTIL [PERIOD=2.0]     output: masked_verification/runs/pnr_<design>_u<util>/
set -u
D=$1; U=$2; PER=${3:-2.0}
MV=~/lwe_agent_handoff/phase2/masked_verification; P2=~/lwe_agent_handoff/phase2
SYN=$MV/runs/pnrsyn_$D
if [ ! -f $SYN/mapped.v ]; then
  mkdir -p $SYN
  python3 -I - <<PY || exit 1
import sys; from pathlib import Path
sys.path.insert(0, '$P2'); import bfbench as B; B.FLOW = 'C'
m, v, gl = B.synth([Path('$MV/rtl/$D.v')], Path('$SYN'), top='${D}_lane'); print('flow C synth', m)
PY
fi
TOP=${D}_lane bash $MV/tools/run_pnr_mv.sh $SYN/mapped.v $MV/runs/pnr2_${D}_u$U $PER $U 0.6 4 | tail -25
