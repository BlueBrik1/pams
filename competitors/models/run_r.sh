cd ~/lwe_agent_handoff/phase2/masked_verification/competitors/models
python3 -I cgen.py pams pams_x pams_jpr pams_jqr | grep -v "^{"; python3 -I cgen.py pams_jpr pams_jqr | grep "^{"
for d in pams_jpr pams_jqr; do python3 -I cbench.py $d 2>&1 | grep -v -E "^\S+ \{'k'" | tail -2; done
