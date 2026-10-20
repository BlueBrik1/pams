# PROLEAD campaign (sequential; each run writes lane/<tag>/ or gadget/<run>/ plus result.json)
cd ~/lwe_agent_handoff/phase2/masked_verification/validation/prolead
L() { echo "== $(date +%T) $*"; python3 -I run_lane.py "$@" 2>&1 | grep -v '^Warning'; }
# 1. gadget level, 2nd order multivariate, glitches + transitions (function-changing NCs without output check)
python3 -I run_gadget.py 4194304 2>&1 | tail -6
# 2. lane negative controls (detection power of the lane harness)
NO_OUTPUT_CHECK=1 L pams NC_exposed_decision 1 31-36 65536 36
NO_OUTPUT_CHECK=1 L pams NC_partial_recombination 2 34 65536 36
L pams NC_mask_reuse 2 34 262144 36
# 3. lane first order, every cycle of a 36-coefficient ciphertext, both lanes
L pams frozen 1 1-70 4194304 36
L base frozen 1 1-72 4194304 36
# 4. lane second order, univariate, one steady-state cycle (pipeline full, accumulator running), both lanes
L pams frozen 2 34 1048576 36
L base frozen 2 36 1048576 36
echo "== $(date +%T) done"
