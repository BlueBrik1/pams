#!/bin/bash
# Phase XIV bounded P&R campaign 1: both finalists, seeds 1-7, targets 2.0 / 1.2 / 1.1 ns (UTIL 50, DENS 0.6)
for T in 2.0 1.2 1.1; do
  bash ~/lwe_agent_handoff/phase2/masked_verification/final/tools/pnr_campaign.sh $T "1 2 3 4 5 6 7" pams_jqr base_jq
  echo "$(date +%T) done T=$T"
done
