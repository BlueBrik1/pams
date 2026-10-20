# Order-1 confirmation of the base lane's flagged set (5.46 at 4,194,304 sims, 95,976 sets; null max ~5.1).
cd ~/lwe_agent_handoff/phase2/masked_verification/validation/prolead
while pgrep -f 'campaign[23]?.sh' > /dev/null; do sleep 60; done
echo "== $(date +%T) confirm base_frozen_o1_1-72_4194304 (ug476 u[4] @65)"
PROBES='.*lane\.ug476\.pd_n0_u_5_0__4' python3 -I run_lane.py base frozen 1 65 4194304 36 2>&1 | grep -v -E '^Warning'
mv lane/base_frozen_o1_65_4194304 lane/confirm_base_frozen_o1_1-72_4194304 2>/dev/null
echo "== $(date +%T) done"
