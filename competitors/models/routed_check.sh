# Phase XII composition-precondition check (validation/structure/compcheck.py, used read-only) on routed competitor netlists
cd ~/lwe_agent_handoff/phase2/masked_verification
for d in "$@"; do
  echo "pnrsyn_$d $(python3 -I validation/structure/compcheck.py competitors/runs/pnrsyn_$d/mapped.json ${d}_lane | head -c 400)"
  for u in 45 50 55; do echo "pnr2_${d}_u$u $(python3 -I validation/structure/compcheck.py competitors/runs/pnr2_${d}_u$u/final.v ${d}_lane --ref competitors/runs/pnrsyn_$d/mapped.v | head -c 400)"; done
done
