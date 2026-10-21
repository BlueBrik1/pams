#!/bin/bash
# Phase XIV focused lane PROLEAD on the publication candidate pams_jqr (after the P&R campaign, so no CPU contention):
# output-check self-test, first order over all cycles, second order at the steady-state cycle (latency + 5 = 36),
# and one function-changing negative control at the same cycle.
cd ~/lwe_agent_handoff/phase2/masked_verification/final/prolead
while pgrep -f 'pnr_campaign.sh|campaign1.sh' > /dev/null; do sleep 30; done
run() { echo "== $(date +%T) $*"; python3 -I run_lane_final.py "$@" 2>&1 | grep -v -E '^Warning|SyntaxWarning|probe_placement'; }
BADC=7 run pams_jqr frozen 1 36 4096 36          # self-test: one mismatching coefficient must fail PROLEAD's output check
mv lane/pams_jqr_frozen_o1_36_4096 lane/selftest_BADC7_pams_jqr_frozen_o1_36_4096 2>/dev/null
run pams_jqr frozen 1 1-72 1048576 36
NO_OUTPUT_CHECK=1 run pams_jqr NC_partial_recombination 2 36 65536 36
run pams_jqr frozen 2 36 262144 36
echo "== $(date +%T) done"
