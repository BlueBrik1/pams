#!/bin/bash
# Phase XIV bounded-runtime rule: a P&R run that exceeds 90 min wall clock is stopped (by PID) and recorded as
# TIMEOUT (detailed routing did not converge within the budget). Applied identically to every run of the campaign.
LIMIT=5400
while pgrep -f pnr_campaign.sh > /dev/null; do
  ps -eo pid,etimes,args | grep openroad | grep -v grep | while read pid et rest; do
    out=$(tr '\0' '\n' < /proc/$pid/environ 2>/dev/null | grep '^OUT=' | cut -d= -f2)
    if [ -n "$out" ] && [ "$et" -gt $LIMIT ]; then
      echo "$(date '+%F %T') TIMEOUT after ${et}s (limit ${LIMIT}s): openroad PID $pid, run $out; last router line: $(grep -E 'Completing|violations' $out/openroad.log | tail -1)" | tee -a $out/TIMEOUT.txt
      kill $pid
    fi
  done
  sleep 30
done
