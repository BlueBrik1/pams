#!/bin/bash
# Confirmation of the order-1 flag of pams_jqr_frozen_o1_1-72_1048576 (ug767 u[1] @47, 5.53): the single set re-tested
# with 4,194,304 simulations (first 1,048,576 = screening data, PROLEAD is unseeded; 3,145,728 new). Real leak: grows
# ~linearly (to ~22); multiple-testing artefact: decays.
cd ~/lwe_agent_handoff/phase2/masked_verification/final/prolead
while pgrep -f campaign_final.sh > /dev/null; do sleep 30; done
echo "== $(date +%T) confirm pams_jqr_frozen_o1_1-72_1048576 (ug767 u[1] @47)"
PROBES='.*lane\.ug767\.pd_n0_u_5_0__1' python3 -I run_lane_final.py pams_jqr frozen 1 47 4194304 36 2>&1 | grep -v -E '^Warning'
mv lane/pams_jqr_frozen_o1_47_4194304 lane/confirm_pams_jqr_frozen_o1_1-72_1048576 2>/dev/null
echo "== $(date +%T) done"
