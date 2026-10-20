#!/bin/bash
# matched P&R of the given designs at UTIL 45/50/55 (2.0 ns target), at most 3 concurrent runs (4 threads each)
cd ~/lwe_agent_handoff/phase2/masked_verification/competitors/models
# flow-C synthesis once per design before the parallel runs (concurrent pnr_c.sh calls raced on runs/pnrsyn_<d>/:
# one run read a partially written mapped.json -- base_jq u45/u50, batch 2; those runs were discarded and redone)
for d in "$@"; do bash pnr_c.sh $d synth-only > ../runs/pnrsynlog_$d.txt 2>&1; done
for d in "$@"; do
  for u in 45 50 55; do
    while [ $(jobs -r | wc -l) -ge 3 ]; do sleep 5; done
    bash pnr_c.sh $d $u > ../runs/pnr2log_${d}_u$u.txt 2>&1 &
  done
done
wait
for d in "$@"; do for u in 45 50 55; do f=../runs/pnr2_${d}_u$u/metrics.txt; echo "== ${d}_u$u $(grep -E 'period_achieved|^cell_area|die_area|drc_violations|hold_wns|done|error' $f 2>/dev/null | tr '\n' ' ')"; done; done
