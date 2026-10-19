#!/bin/bash
# Copy of the project P&R flow with ONE change for both lanes: hold repair may insert up to 60% buffers
# (default 20% made the baseline fail with RSZ-0060). Originals in phase2/pnr/ are not modified.
P2=~/lwe_agent_handoff/phase2; T=$P2/masked_verification/tools
sed 's/^repair_timing -hold$/repair_timing -hold -max_buffer_percent 60/' $P2/pnr/pnr.tcl > $T/pnr_mv.tcl
grep -n "repair_timing -hold" $T/pnr_mv.tcl
sed "s#\"\$H/pnr.tcl\"#\"$T/pnr_mv.tcl\"#; s#^H=.*#H=$P2/pnr; P2=$P2#" $P2/pnr/run_pnr.sh > $T/run_pnr_mv.sh
grep -n "pnr_mv.tcl\|^H=" $T/run_pnr_mv.sh
