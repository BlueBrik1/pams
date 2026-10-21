#!/bin/bash
# Gate-level simulation of ROUTED netlists (OpenROAD final.v -> liberty functions inlined, as bfbench does for
# synthesis netlists), with the systematic stimulus (fsim.py) and the frozen random accept-heavy stimulus (sim.py).
cd ~/lwe_agent_handoff/phase2/masked_verification
LIB=~/lwe_agent_handoff/current/lib/NangateOpenCellLibrary_typical.lib
for r in "$@"; do
  d=$(echo $r | sed -E 's/^pnr_(.*)_T.*/\1/'); w=final/runs/$r
  yosys -q -p "read_liberty -ignore_miss_func $LIB; read_verilog $w/final.v; hierarchy -top ${d}_lane; flatten; opt_clean; write_verilog -noattr $w/gate_routed.v" > $w/gate_export.log 2>&1
  python3 -I final/models/fsim.py $d $w/gate_routed.v > $w/fsim_routed.log 2>&1; echo "$r systematic rc=$? $(tail -1 $w/fsim_routed.log)"
  python3 -I -c "import sys; sys.dont_write_bytecode=True; sys.path.insert(0,'models'); import sim; from pathlib import Path; sim.H=Path('competitors/models').resolve(); sys.exit(0 if sim.run('$d', 6000, 11, '$w/gate_routed.v') else 1)" > $w/sim_routed.log 2>&1; echo "$r random rc=$? $(tail -1 $w/sim_routed.log)"
done
