#!/bin/bash
# 6 matched P&R runs (2 lanes x UTIL 45/50/55, period target 2.0 ns), at most 3 concurrent
cd ~/lwe_agent_handoff/phase2/masked_verification/models
date +%H:%M
bash pnr_lane.sh base 50 > ../runs/pnr2log_base_u50.txt 2>&1 &
bash pnr_lane.sh pams 50 > ../runs/pnr2log_pams_u50.txt 2>&1 &
wait
bash pnr_lane.sh base 45 > ../runs/pnr2log_base_u45.txt 2>&1 &
bash pnr_lane.sh pams 45 > ../runs/pnr2log_pams_u45.txt 2>&1 &
bash pnr_lane.sh base 55 > ../runs/pnr2log_base_u55.txt 2>&1 &
wait
bash pnr_lane.sh pams 55 > ../runs/pnr2log_pams_u55.txt 2>&1
date +%H:%M
for f in ../runs/pnr2_*_u*/metrics.txt; do echo "== $f"; grep -E "period_achieved|cell_area|die_area|drc_violations|hold_wns|parasitics|wirelength|done" $f | tr '\n' ' '; echo; done
