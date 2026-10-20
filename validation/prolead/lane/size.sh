cd ~/lwe_agent_handoff/phase2/masked_verification/validation/prolead
/usr/bin/time -f "wall %e s, maxrss %M kB" timeout 3000 python3 -I run_lane.py pams frozen 2 34 65536 36 2>&1 | grep -v "^Warning"
grep -E "probing sets|Standard Probes|OKAY|LEAK" -A2 lane/pams_frozen_o2_34_65536/prolead.log | grep -v "^--$" | cut -c1-160 | tail -8
