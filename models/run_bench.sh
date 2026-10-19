cd ~/lwe_agent_handoff/phase2/masked_verification/models && date +%H:%M && rm -f ../runs/bench.json && timeout 7000 python3 -I bench.py base pams pams_r 2>&1 | tail -4 && date +%H:%M
