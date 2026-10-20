# Phase XIII experiment log

All paths are relative to `masked_verification/` unless stated. All commands run inside WSL Ubuntu as user `slee5`.

## 0. Resources and the Phase XII campaign (2026-10-20, 15:19)
- **Machine:** 16 logical CPUs, 31 GB RAM (26 GB free), 8 GB swap.
- **Phase XII PROLEAD** (`validation/prolead/campaign.sh` → `campaign4.sh`):
  - running: PROLEAD PID 12031 (parent run_lane.py PID 12028), `base frozen 2 36 1048576`, at 1,593% CPU and 1.5 GB RSS;
  - queued: campaign2.sh PID 29309, campaign3.sh PID 30380, campaign4.sh PID 16083;
  - load average 16.7.
- **Other processes:** the dashboard Vite server and a codex daemon, both idle.
- **Policy, following the brief's priority order:**
  - Phase XII processes and files are not touched;
  - while PROLEAD runs, only light work runs, at `nice -n 10` or `nice -n 19`: code generation, mathematical checks, RTL smoke simulations;
  - measured at 15:35: a nice-19 job gets ≈ 1.5 % of one core while PROLEAD runs, so PROLEAD loses < 0.1 %;
  - synthesis and P&R are queued behind the campaign (`models/queue_synth.sh` waits until no `campaign*.sh` and no PROLEAD process exist), then run one job at a time.

## 1. Generator and regression checks
```
cd competitors/models && nice -n 10 python3 -u -I cgen.py base pams base_x pams_x base_j base_p base_jp base_bk base_bkp hoc hoc_jp bos bos_j pams_j pams_p pams_jp
```
(`gen_all.sh`; the run printed nothing on failure because of stdout buffering, so it now uses `python3 -u`.)
- **check_offsets():** passed for every x ∈ [0, q), d ∈ {4, 5, 10, 11} and floor error e ∈ {0, 1, 2}:
  - Simple at t = 13 with A = 1;
  - HOCompress precision at t = 14 with A = 0 (A ∈ {0, 1, 2} all exact; t = 12 has no exact offset).
- **check_bos_windows():** [Compress_d(x) = c] = [(x − a_c) mod q < W_c] holds for every d, c and x, using the RTL's a_c / W_c formulas.
- **Frozen re-emission:** `base`, `pams`: the frozen gen.py with output redirected to competitors/rtl is **byte-identical** to rtl/base.v and rtl/pams.v.
- **Regression of the new generator:** `base_x`, `pams_x` are identical to rtl/base.v / rtl/pams.v up to the module name.
  - The first attempt **failed**: the top-region gadgets of Simple were created in a different order (same circuit, different wire numbering). The creation order was fixed, then the check passed.
- **Bugs found and fixed before any measurement:**
  1. A local variable shadowed the helper `early` (UnboundLocalError).
  2. The just-in-time variants first recomputed T_t at the boundary bit, giving one extra gadget and 3 extra random bits. That bit now reuses the early T_t, so the gadget counts equal the frozen designs.
  3. In the `p` variants, the register `f2p` collided with the control pipeline's `f2p`; it was renamed `fq2`.

Generated facts (gadgets incl. the 2 accumulator gadgets / random bits per cycle / per-coefficient decision latency):

| design | gadgets | rnd bits/cycle | latency |
|---|---|---|---|
| base, base_j | 57 | 171 | 31 |
| base_p, base_jp | 57 | 171 | 32 |
| base_bk | 75 | 225 | 17 |
| base_bkp | 75 | 225 | 18 |
| hoc | 59 | 177 | 33 |
| hoc_jp | 59 | 177 | 34 |
| bos, bos_j | 91 | 273 | 31 |
| pams, pams_j | 40 | 120 | 29 |
| pams_p, pams_jp | 40 | 120 | 30 |

`base_bkj` was identical in structure to `base_bk` (BK has no ripple left for JIT to act on), so it was dropped.

## 2. RTL smoke test (Phase XII still running; nice 10)
```
bash competitors/models/rtl_smoke.sh base_x base_j base_jp base_bk base_bkp hoc hoc_jp bos bos_j pams_x pams_j pams_p pams_jp base_p
```
- Each design: models/sim.py stimulus, seed 3; 2,003 coefficients (1,442 matching); 363 ciphertexts (175 accept).
- **All 14 designs: 0 coefficient mismatches and 0 ciphertext mismatches.**
- The first run of base_p / base_jp / base_bkp / hoc_jp did not compile (the f2p clash above). They pass after the fix.

## 3. Synthesis queue
```
bash competitors/models/queue_synth.sh > competitors/runs/queue_synth.log 2>&1      # background task b9ut2dswf
```
- **Started:** 17:46:08, when the queue found no campaign*.sh and no PROLEAD process.
- **Resources at start:** nproc 16; 30 GB available; load 6.5 and falling.
- **Overlap with Phase XII:** the Phase XII confirmation run `campaign5.sh` (PROLEAD, 16.8 M simulations) was started at 17:46 as well. It ran concurrently with the queue, whose cbench jobs ran at `nice -n 10` and used one core.
- **Finished:** 18:22 (14 designs × 5 mappings + mul12), ≈ 4 min per design.
- **Results:** `runs/cbench.json`, `runs/queue_synth.log`.
- **Reproduction:** base 21,598 µm² / 1.649 ns and pams 16,998 / 1.487, identical to Phase XI `runs/bench.json`.

## 4. Follow-up variants (after reading the critical paths)
```
bash competitors/models/run_q.sh   # base_q base_jq hoc_jq pams_q pams_jq   -> runs/run_q.log
bash competitors/models/run_r.sh   # pams_jpr pams_jqr (re-checks pams / pams_x identity first) -> runs/run_r.log
```
- **q (multiplier split into two registered halves):**
  - base_jq reached 1.057 ns, faster than every PAMS variant built up to that point;
  - pams_q / pams_jq gained almost nothing: their critical path had moved to the public window logic (c0 → low0, identified from the start and end register names in mapped.v).
- **r (public window logic split over the existing front-end stages):** pams_jpr 1.163 ns, pams_jqr 1.033 ns.
- **All new variants:** RTL and gate-level 0 mismatches; domain and compcheck PASS.

## 5. Place and route
```
bash competitors/models/pnr_batch.sh base_j base_p base_jp hoc_jp pams_jp   # runs/pnr_batch1.log
bash competitors/models/pnr_batch.sh base_jq pams_jqr pams_jpr              # runs/pnr_batch2.log
bash competitors/models/routed_check.sh <designs>                           # runs/routed_check{1,2,3}.txt
```
- **Scheduling and run time:** 3 runs concurrent, 4 OpenROAD threads each, about 1–2 min per run.
- **Run outcomes:** 24 runs, plus the 2 failed attempts that were redone (below). All 24 met setup at 2.0 ns, with positive hold and 0 DRC violations.
- **Failures and fixes:**
  1. **base_jq u45 / u50, batch 2:** the three concurrent runs raced on the shared flow-C synthesis directory, and one read a partially written mapped.json (JSONDecodeError). This was a harness fault.
     - Fix: `pnr_batch.sh` now synthesizes once per design before the parallel runs.
     - The base_jq pnrsyn and all three runs were deleted and redone. u55 reproduced bit-identically: period 1.240872, cell area 23,287.234.
  2. **The redo first failed immediately:** the Python edits to `pnr_batch.sh` / `pnr_c.sh` had written CRLF line endings (Python text mode on Windows), which broke bash.
     - Fix: stripped the CRs with `sed -i 's/\r$//'`. cgen.py and the Phase XII `lane_table.py` were also converted; Python itself was unaffected.
- **Routed composition checks:** all 32 netlists pass (8 P&R input netlists + 24 routed netlists), with G = 0 gadget mismatches on every routed one.

## 6. Tables
```
python3 -I competitors/models/tables.py > competitors/runs/tables.md
```
- **First run:** it mislabeled frozen `pams` as depth +1, because the suffix was parsed from the design name itself. Fixed and regenerated.
- **Use:** BENCHMARKS.md §1–3 are this file, inserted verbatim.

## 7. Clean-up
- **Bytecode files:** importing the frozen `models/bench.py`, `gen.py` and `sim.py` wrote 3 `.pyc` files into `models/__pycache__/`. Git showed them as untracked; they were deleted. cgen.py, cbench.py and tables.py now set `sys.dont_write_bytecode`.
- **Frozen files:** `git diff` over the frozen paths shows no change, apart from the pre-existing, Phase-XII-restored `tools/tmp.sh` working-copy state.

## 8. Tool versions
- Yosys 0.33 (git sha1 2584903a060); Icarus Verilog 12.0 (stable); OpenSTA 3.1.0 (`~/.local/bin/sta`); OpenROAD from ORFS 26Q3 (`phase2/orfs_run.sh`, as in Phase XI); Python 3.12.
- Printed 2026-10-20 with `yosys -V`, `iverilog -V`, `sta -version`.
