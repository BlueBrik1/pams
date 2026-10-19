#!/bin/bash
# negative controls for the two home-made security checkers (expected: both FAIL)
cd ~/lwe_agent_handoff/phase2/masked_verification/models
timeout 3000 python3 -I hpc2check.py --broken > ../runs/negctl_hpc2.txt 2>&1; tail -2 ../runs/negctl_hpc2.txt
cp ../rtl/pams.v ../rtl/pams.v.keep
python3 -I gen.py pams --leak > /dev/null && mv ../rtl/pams.v ../rtl/pams_leak.v && mv ../rtl/pams.v.keep ../rtl/pams.v
sed -i 's/module pams_lane/module pams_leak_lane/' ../rtl/pams_leak.v
python3 -I - <<'PY'
import sys; from pathlib import Path
P2 = Path.cwd().parents[1]; sys.path.insert(0, str(P2)); import bfbench as B; B.FLOW = 'B'
w = Path.cwd().parent / 'runs' / 'negctl_leak'; w.mkdir(parents=True, exist_ok=True)
B.synth([Path.cwd().parent / 'rtl' / 'pams_leak.v'], w, top='pams_leak_lane')
PY
python3 -I domaincheck.py ../runs/negctl_leak/mapped.json pams_leak_lane | head -3
