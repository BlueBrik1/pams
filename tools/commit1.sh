cd ~/lwe_agent_handoff
git add phase2/masked_verification
git status --short phase2/masked_verification | head -30
git commit -q -F - <<'MSG'
Masked verification: PAMS lane vs optimized Simple baseline (synthesis milestone)

- models/pams.py: exhaustive exactness (all x, c, d, share-error j) of baseline (t=13, W=24) and PAMS (K=14)
- models/impossible.py: K=13 impossible for any decision rule; baseline top-bits rule needs t=13
- models/gen.py: both lanes from identical HPC2 gadgets + aligner; sim.py RTL/gate checks
- models/hpc2check.py: exhaustive glitch-extended 2-probe + PINI check of the gadget (+ negative control)
- models/domaincheck.py: structural share-domain check of mapped netlists (+ negative control)
- runs/bench.json: flow B, 5 mappings: base 21598 um2 / 1.649 ns, pams 16998 um2 / 1.487 ns

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_019E7WSFHBAvBtzeYyj73qE3
MSG
git log --oneline -1
