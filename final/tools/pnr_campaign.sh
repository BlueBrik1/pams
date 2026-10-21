#!/bin/bash
# Phase XIV seeded P&R campaign. Inputs are the Phase XIII flow-C netlists (competitors/runs/pnrsyn_<d>/mapped.v,
# read-only); utilization 50 %, density 0.6, 4 OpenROAD threads per run, at most 3 concurrent runs.
# usage: pnr_campaign.sh PERIOD "SEEDS" DESIGN [DESIGN ...]     output: final/runs/pnr_<d>_T<period>_s<seed>/
set -u
MV=~/lwe_agent_handoff/phase2/masked_verification; PER=$1; SEEDS=$2; shift 2
for s in $SEEDS; do
  for d in "$@"; do
    while [ $(jobs -r | wc -l) -ge 3 ]; do sleep 5; done
    o=$MV/final/runs/pnr_${d}_T${PER}_s$s
    [ -f $o/metrics.txt ] && grep -q "^done 1" $o/metrics.txt && continue        # resumable; finished runs are kept
    SEED=$s TOP=${d}_lane bash $MV/final/tools/run_pnr_final.sh $MV/competitors/runs/pnrsyn_$d/mapped.v $o $PER 50 0.6 4 > $o.log 2>&1 &
  done
done
wait
