cd ~/lwe_agent_handoff/phase2/masked_verification/validation/prolead
for o in 3 4 5 6; do echo "offset $o: $(END_OFFSET=$o timeout 900 python3 -I run_lane.py pams frozen 1 31 64 2>&1 | grep -o '"returncode": [-0-9]*'; grep -h 'what()' lane/pams_frozen_o1_31_64/prolead.log)"; done
echo "self-test (coefficient 7 mismatching, offset 4): $(BADC=7 END_OFFSET=4 timeout 900 python3 -I run_lane.py pams frozen 1 31 64 2>&1 | grep -o '"returncode": [-0-9]*'; grep -h 'what()' lane/pams_frozen_o1_31_64/prolead.log)"
for o in 5 6; do echo "base offset $o: $(END_OFFSET=$o timeout 900 python3 -I run_lane.py base frozen 1 33 64 2>&1 | grep -o '"returncode": [-0-9]*'; grep -h 'what()' lane/base_frozen_o1_33_64/prolead.log)"; done
