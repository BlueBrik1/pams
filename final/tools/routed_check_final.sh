#!/bin/bash
# validation/structure/compcheck.py (read-only) on every finished Phase XIV routed netlist: D/R/P/O + G (each routed
# gadget equals the verified gadget cell by cell). Output: final/runs/routed_check_final.jsonl
cd ~/lwe_agent_handoff/phase2/masked_verification
for m in final/runs/pnr_*_T*_s*/metrics.txt; do
  r=$(dirname $m); grep -q '^done 1' $m || continue; n=$(basename $r); d=$(echo $n | sed -E 's/^pnr_(.*)_T.*/\1/')
  res=$(python3 -I validation/structure/compcheck.py $r/final.v ${d}_lane --ref competitors/runs/pnrsyn_$d/mapped.v)
  echo "{\"run\": \"$n\", \"result\": $res}"
done > final/runs/routed_check_final.jsonl
python3 -I -c "
import json; rs=[json.loads(l) for l in open('final/runs/routed_check_final.jsonl')]
print(len(rs), 'routed netlists checked; PASS:', sum(r['result']['PASS'] for r in rs), '; G mismatches total:', sum(r['result']['G_gadget_mismatches'][0] for r in rs))"
