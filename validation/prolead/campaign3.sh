# Confirmation runs: re-test the strongest second-order probing set of a screening run with many more simulations,
# probing only its nets. A true leak grows with the number of simulations; a multiple-testing artefact does not.
cd ~/lwe_agent_handoff/phase2/masked_verification/validation/prolead
while pgrep -f 'campaign2?.sh' > /dev/null; do sleep 60; done
confirm() {   # design cycle screening-tag
  top=$(python3 -I -c "import json,re,sys; r=json.load(open('lane/$3/result.json')); print('|'.join('.*'+re.escape(re.sub(r'\(\d+\)$','',s.strip().lstrip('\\\\'))) for s in r['top_probing_set'].strip('[]').split(',')))")
  echo "== $(date +%T) confirm $3 -> PROBES=$top"
  PROBES="$top" python3 -I run_lane.py $1 frozen 2 $2 4194304 36 2>&1 | grep -v -E '^Warning'
  mv lane/$1_frozen_o2_$2_4194304 lane/confirm_$3 2>/dev/null
}
confirm pams 34 pams_frozen_o2_34_65536
[ -d lane/pams_frozen_o2_34_1048576 ] && confirm pams 34 pams_frozen_o2_34_1048576
[ -d lane/base_frozen_o2_36_1048576 ] && confirm base 36 base_frozen_o2_36_1048576
echo "== $(date +%T) done"
