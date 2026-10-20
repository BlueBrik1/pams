#!/bin/bash
# Lightweight RTL smoke test (2,000 coefficients each, nice 10) of every generated competitor, run while Phase XII
# still occupies the CPUs; the full acceptance runs (6,000 RTL + 5 x 1,500 gate-level) are part of cbench.py.
cd ~/lwe_agent_handoff/phase2/masked_verification/competitors/models
for d in "$@"; do
  nice -n 10 python3 -I -c "import sys; sys.path.insert(0, '.'); import cbench; sys.exit(0 if cbench.sim.run('$d', 2000, 3) else 1)" 2>&1 | tail -2
done
