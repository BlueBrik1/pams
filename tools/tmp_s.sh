cd ~/lwe_agent_handoff/phase2/masked_verification
for d in runs/pnr_*_u*; do mv $d ${d/pnr_/pnr1_}; done
for f in runs/pnrlog_*.txt; do mv $f ${f/pnrlog_/pnr1log_}; done
sed -i 's#bash $P2/pnr/run_pnr.sh $SYN/mapped.v $MV/runs/pnr_${D}_u$U#bash $MV/tools/run_pnr_mv.sh $SYN/mapped.v $MV/runs/pnr2_${D}_u$U#' models/pnr_lane.sh
sed -i 's#\.\./runs/pnrlog_#../runs/pnr2log_#g; s#\.\./runs/pnr_\*_u\*/metrics.txt#../runs/pnr2_*_u*/metrics.txt#' models/pnr_all.sh
grep -n "run_pnr" models/pnr_lane.sh; grep -c pnr2 models/pnr_all.sh; ls runs | grep pnr
