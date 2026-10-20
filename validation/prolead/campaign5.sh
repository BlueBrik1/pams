# PROLEAD 3.1.0 never seeds rand() in hardware mode (src/Util/Util.cpp GenerateThreadRng; srand only in the software
# path), so a rerun with the same simulation count replays the same random inputs and is not an independent test.
# Confirmation of the base order-1 flag (ug476 u[4] @65) with 16,777,216 simulations: the first 4,194,304 equal the
# screening data, the remaining 12,582,912 are new. A real leak grows ~linearly in -log10 p (to ~20); an artefact decays.
cd ~/lwe_agent_handoff/phase2/masked_verification/validation/prolead
echo "== $(date +%T) confirm16M base_frozen_o1_1-72_4194304 (ug476 u[4] @65)"
PROBES='.*lane\.ug476\.pd_n0_u_5_0__4' python3 -I run_lane.py base frozen 1 65 16777216 36 2>&1 | grep -v -E '^Warning'
mv lane/base_frozen_o1_65_16777216 lane/confirm16M_base_frozen_o1_1-72_4194304 2>/dev/null
echo "== $(date +%T) done"
