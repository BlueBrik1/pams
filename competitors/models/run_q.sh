# variant q (two extra front-end stages) for the strongest families; same matched benchmark
cd ~/lwe_agent_handoff/phase2/masked_verification/competitors/models
python3 -I cgen.py base_q base_jq hoc_jq pams_q pams_jq | grep -v "^{" ; python3 -I cgen.py base_q base_jq hoc_jq pams_q pams_jq | grep "^{"
for d in base_q base_jq hoc_jq pams_q pams_jq; do python3 -I cbench.py $d 2>&1 | grep -v -E "^\S+ \{'k'" | tail -2; done
