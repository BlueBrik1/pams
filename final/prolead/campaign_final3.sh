#!/bin/bash
# Confirmation of the order-2 maximum of pams_jqr_frozen_o2_36_262144 (5.21; ug1331 v[2] & ug1470 rbr[2]) with
# 4,194,304 simulations (first 262,144 = screening data; 3,932,160 new).
cd ~/lwe_agent_handoff/phase2/masked_verification/final/prolead
while pgrep -f 'campaign_final2.sh' > /dev/null; do sleep 20; done
echo "== $(date +%T) confirm pams_jqr_frozen_o2_36_262144"
PROBES='.*lane\.ug1331\.pd_n0_v_5_0__2|.*lane\.ug1470\.pd_n0_rbr_5_0__2' python3 -I run_lane_final.py pams_jqr frozen 2 36 4194304 36 2>&1 | grep -v -E '^Warning'
mv lane/pams_jqr_frozen_o2_36_4194304 lane/confirm_pams_jqr_frozen_o2_36_262144 2>/dev/null
echo "== $(date +%T) done"
