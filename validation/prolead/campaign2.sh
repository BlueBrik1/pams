# Follow-up runs after campaign.sh (re-runs of FLINT-aborted runs, with the retry wrapper)
cd ~/lwe_agent_handoff/phase2/masked_verification/validation/prolead
while pgrep -f campaign.sh > /dev/null; do sleep 60; done
L() { echo "== $(date +%T) $*"; python3 -I run_lane.py "$@" 2>&1 | grep -v -E '^Warning|SyntaxWarning|probe_placement'; }
python3 -I run_gadget.py 4194304 2>&1 | tail -6
NO_OUTPUT_CHECK=1 L pams NC_exposed_decision 1 31-36 65536 36
L pams NC_mask_reuse 2 34 262144 36
NO_OUTPUT_CHECK=1 L base NC_partial_recombination 2 36 65536 36
echo "== $(date +%T) done"
