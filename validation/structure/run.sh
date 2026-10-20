cd ~/lwe_agent_handoff/phase2/masked_verification
for d in pams base; do
  for k in 0 1 2 3 4; do echo "syn_${d}_p$k $(python3 -I validation/structure/compcheck.py runs/syn_${d}_p$k/mapped.json ${d}_lane)"; done
  echo "pnrsyn_$d $(python3 -I validation/structure/compcheck.py runs/pnrsyn_$d/mapped.json ${d}_lane)"
  for u in 45 50 55; do echo "pnr2_${d}_u$u $(python3 -I validation/structure/compcheck.py runs/pnr2_${d}_u$u/final.v ${d}_lane --ref runs/pnrsyn_$d/mapped.v)"; done
done
