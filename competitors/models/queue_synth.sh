#!/bin/bash
# Phase XIII synthesis queue. Waits until the Phase XII PROLEAD campaign (campaign.sh .. campaign4.sh and any
# PROLEAD process) has finished, so it never competes with it; then runs the matched synthesis benchmark
# sequentially (one job at a time). Log: competitors/runs/queue_synth.log
cd ~/lwe_agent_handoff/phase2/masked_verification/competitors/models
while pgrep -f 'campaign[234]?\.sh' > /dev/null || pgrep -x PROLEAD > /dev/null; do sleep 60; done
echo "== $(date '+%F %T') Phase XII idle; resources:"; nproc; free -g | head -2; uptime
python3 -I cgen.py base pams base_x pams_x base_j base_p base_jp base_bk base_bkp hoc hoc_jp bos bos_j pams_j pams_p pams_jp
for d in base pams base_j base_p base_jp base_bk base_bkp hoc hoc_jp bos bos_j pams_j pams_p pams_jp; do
  echo "== $(date +%T) $d"; nice -n 10 python3 -I cbench.py $d 2>&1 | grep -v -E "^\S+ \{'k'" | tail -3
done
echo "== $(date +%T) mul12 (Coron lower-bound block)"
nice -n 10 python3 -I - <<'PY'
import json, sys; from pathlib import Path
C = Path('..').resolve(); sys.path.insert(0, str(C.parent / 'models')); import bench
w = C / 'runs' / 'syn_mul12'; w.mkdir(parents=True, exist_ok=True)
m, mapped, gl = bench.synth_D([C / 'rtl' / 'mul12.v'], w, 'mul12_lane', 500); m.update(bench.B.sta(mapped, w, top='mul12_lane'))
(w / 'result.json').write_text(json.dumps(m, indent=1)); print('mul12', m['area'], m['ff'], m['tclk'])
PY
echo "== $(date '+%F %T') done"
