#!/bin/bash
# final functional verification: RTL + gate-level (synthesis mapping 0 and the flow-C P&R input) of both finalists,
# plus the frozen designs as a reference. Logs: final/runs/fsim_*.log
cd ~/lwe_agent_handoff/phase2/masked_verification
for d in pams_jqr base_jq pams base; do
  python3 -I final/models/fsim.py $d > final/runs/fsim_${d}_rtl.log 2>&1; echo "$d RTL rc=$? $(tail -1 final/runs/fsim_${d}_rtl.log)"
done
for d in pams_jqr base_jq; do
  for n in syn_${d}_p0 pnrsyn_${d}; do
    python3 -I final/models/fsim.py $d competitors/runs/$n/gate.v > final/runs/fsim_${n}_gate.log 2>&1; echo "$n gate rc=$? $(tail -1 final/runs/fsim_${n}_gate.log)"
  done
done
