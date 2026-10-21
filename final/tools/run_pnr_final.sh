#!/usr/bin/env bash
# Phase XIV copy of tools/run_pnr_mv.sh (only change: final/tools/pnr_final.tcl, SEED from env, default 1)
# usage: SEED=n run_pnr_final.sh NETLIST OUTDIR [PERIOD=2.5] [UTIL=50] [DENS=0.6] [THREADS=4]
# One matched OpenROAD place-and-route run (pnr.tcl). Same knobs for every design unless overridden explicitly.
set -u
H=/home/slee5/lwe_agent_handoff/phase2/pnr; P2=/home/slee5/lwe_agent_handoff/phase2
export SEED=${SEED:-1} OUT=$(realpath -m "$2") TOP=${TOP:-ntt_mlkem} PERIOD=${3:-2.5} UTIL=${4:-50} DENS=${5:-0.6} THREADS=${6:-4}
mkdir -p "$OUT"
bash "$H/prep_netlist.sh" "$1" "$OUT/pnr_in.v" "$TOP" > "$OUT/prep.log" 2>&1 || { echo "prep failed"; cat "$OUT/prep.log"; exit 1; }
export NETLIST=$OUT/pnr_in.v
( time bash "$P2/orfs_run.sh" openroad -no_init -exit "/home/slee5/lwe_agent_handoff/phase2/masked_verification/final/tools/pnr_final.tcl" ) > "$OUT/openroad.log" 2>&1
# metrics from tool summaries: TritonRoute totals (last occurrence) and the vectorless power report (Total row, watts)
wl=$(grep -E "Total wire length = " "$OUT/openroad.log" | tail -1 | grep -oE "[0-9.]+ um" | grep -oE "[0-9.]+")
nv=$(grep -E "Total number of vias = " "$OUT/openroad.log" | tail -1 | grep -oE "[0-9]+" | tail -1)
pw=$([ -f "$OUT/power.rpt" ] && awk '$1 == "Total" {print $5}' "$OUT/power.rpt" | head -1)
for kv in "wirelength_um ${wl:-NA}" "vias ${nv:-NA}" "power_total_w ${pw:-NA}"; do echo "$kv" >> "$OUT/metrics.txt"; echo "METRIC $kv" >> "$OUT/openroad.log"; done
grep -E "^METRIC|^real" "$OUT/openroad.log" | tail -30
