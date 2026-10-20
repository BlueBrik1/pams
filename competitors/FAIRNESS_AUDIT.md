# Fairness audit

## 1. Hardware equivalence
| item | requirement | status for every design in BENCHMARKS.md |
|---|---|---|
| function | exact Compress_d(x) = c for d ∈ {4, 5, 10, 11}, per-coefficient d; AND over a ciphertext | **met**: exhaustive rule checks (cgen.py `check_offsets`, `check_bos_windows`) plus RTL and gate-level simulation of all 5 mappings with 0 mismatches |
| input / output | identical port list; 3 arithmetic shares mod q in; 3 Boolean output shares | **met**: one wrapper (`cgen.emit`), copied from the frozen gen.py; the frozen designs are re-emitted byte-identically |
| throughput | 1 coefficient per cycle | **met**: II = 1 everywhere, a fully pipelined stream with no stall logic |
| latency | reported, not credited | 17 (base_bk) to 35 (hoc_jq) cycles + 4. Not part of the ranking, as stated in the contract. The extra stages of p / q / r cost area, and that is counted. |
| accumulator | the same 2-gadget interleaved accumulator | **met**: identical text |
| public constants | computed in-lane from (c, d); no ROM | **met**. PAMS has the most public logic (Low_c, Θ_c), and it is counted: it is PAMS's critical path in several variants. |
| randomness | bits per cycle at the lane port; same generator assumption | **met**: 3 bits per gadget; no generator in any area figure. The comparison of the RNG cost would scale with the same 120 : 171 ratio as Phase XI. |
| flow / library / STA / mappings | identical | **met**: `bench.synth_D` and `bfbench.sta` called unchanged; the same 5 mappings |
| P&R | identical flow | **met**: `tools/run_pnr_mv.sh` (Phase XI batch 2) called unchanged, with the same 2.0 ns target, density and utilizations |
| memory / output-consumption model | none / registered outputs | identical |

**Not matched, and stated:**
1. **P&R only for finalists:** the dominated designs (bos, base_bk, hoc, base_q, hoc_jq, pams_j, pams_p, pams_q, pams_jq) were not routed.
2. **Loose P&R target:** the 2.0 ns P&R target is loose for every design (achieved 1.15–1.83 ns), the same as in Phase XI. Timing-driven optimization at a tight target could change the routed margins in either direction, and was not run.
3. **Pipelining depth:** depths beyond +2 were not built for either family.

## 2. Functional verification (every design)
| check | scope | result |
|---|---|---|
| exactness of each decision rule | all x ∈ [0, q), all c, all d; Simple / HOCompress also for floor error e ∈ {0, 1, 2} | pass (t = 13 / A = 1; t = 14 / A = 0; Bos windows) |
| RTL simulation | 6,001 coefficients (boundaries ± 2, wrap at 0 / q − 1, all d mixed), 1,079 ciphertexts | 0 mismatches, all designs |
| gate-level simulation | 1,500 coefficients × 5 mappings | 0 mismatches, all designs |
| regression of the generator | cgen.py reproduces rtl/base.v and rtl/pams.v (byte-identical up to the module name) | pass |

## 3. Security equivalence
**Same model for all designs in the ranking:**
- 3 shares;
- HPC2 gadgets byte-identical to the SILVER-verified frozen `hpc2` module;
- all other logic share-local or public;
- glitch-robust 2-PINI by trivial composition.

**Checked for every design and mapping:**
- `models/domaincheck.py` (Phase XI);
- `validation/structure/compcheck.py` (Phase XII), with checks D, R, P and O;
- for every routed netlist, also check G: each gadget equals the verified gadget cell by cell. All pass (`runs/routed_check{1,2,3}.txt`).

**What each generic change does to the security argument:**

| change | what moves | security effect |
|---|---|---|
| j (JIT CSA) | registers holding single-domain bits y_i[k] instead of 3-share S_k / T_k | share-local registers only; composition unchanged; same gadgets, same random-bit allocation |
| p / q | share-local registers inside the per-share constant multiplier and offset | share-local; no gadget changes |
| r (PAMS only) | registers in the public window logic | public data only |
| bk | a different gadget network (prefix tree) | the same composition theorem applies; checked by compcheck |
| bos | share-local mod-q subtraction on share 0; 5 comparator chains | share-local plus gadgets; checked by compcheck |

**Not done per competitor:**
- no SILVER run (the gadget is identical);
- no lane-level PROLEAD campaign (the brief says not to rerun it);
- no transition analysis.

The Phase XII transition caveat (HPC2 is not O-PINI; executions are adjacent) applies to every design here identically, because all use the same gadget in the same pipelined way. The competitors' full security therefore rests on the same composition argument as frozen PAMS, minus the lane-level PROLEAD evidence that only the frozen designs have. They are marked as **"composition-checked, not lane-PROLEAD-tested"**.

**Excluded because they change the security model** (X2X / Shahmirzadi–Hutter):
- DOM-indep AND gadgets with explicit SNI refresh (t-NI composition);
- DOM without refresh (t-probing, TVLA-validated only);
- half-cycle register paths;
- lower-order first adder layers.

These are not trivially composable glitch-robust PINI; X2X itself notes the higher verification cost. Each one applies to PAMS's identical CSA / ripple / gadget structure as much as to Simple's, so excluding them from both sides does not bias the comparison toward PAMS.

## 4. Optimization fairness
**Effort per family:**

| family | variants built | measured |
|---|---|---|
| Simple (base) | 8: base, base_j, base_p, base_jp, base_bk, base_bkp, base_q, base_jq (base_bkj dropped as identical) | synthesis; 4 routed |
| HOCompress | 3 | synthesis; 1 routed |
| Bos | 2 | synthesis |
| PAMS | 8 (frozen + 7 counterparts) | synthesis; 3 routed + frozen |

Optimization effort was not skewed toward PAMS: the competitor families received at least as many variants.

**Generic improvements applied to both:**
- j, p and q were applied to base (and to hoc) and to PAMS alike.
- The frozen-versus-frozen comparison is reported separately (BENCHMARKS.md §3, rows `pams` versus `base`). This separates the effect of the improvements from the comparison: the improvements reduce the frozen-versus-frozen area gap from 21.3 % to 19.3 % (pams_jqr versus base_jq).

**The PAMS-specific retiming (r):**
- *Bias concern:* PAMS received one optimization (r) that the baseline did not.
  - *Justification:* r pipelines public logic, which only PAMS has in a critical amount.
  - The baseline's public logic (offset (2c − 1)·2^12 − 1, region mask) never appeared on a critical path, so an r for the baseline would change nothing measurable.
- Without r, PAMS at depth +2 (pams_jq, 1.242 ns) is **slower** than base_jq (1.057 ns). The comparison table reports both.

**Mapping noise:**
- The PAMS j / p variants show larger ABC delay variation (up to 8 %) than the base variants (≤ 2 %).
- Medians are used throughout, and the min / max are reported.
- For the claims in FINAL_COMPETITOR_REPORT.md, the worst-case pair (PAMS max versus competitor min) is checked as well.

**Consistency of the frozen results:**
- Phase XI numbers were reproduced exactly by re-synthesis.
- The frozen routed rows come from Phase XI, the same flow version and scripts.
- No Phase XI or Phase XII artifact was modified (`git diff` of rtl/, models/, runs/ and the top-level documents is empty).
- The only stray side effects were 3 Python bytecode cache files written into `models/__pycache__/` by importing the frozen scripts. They were deleted, and the scripts now set `sys.dont_write_bytecode`.

## 5. Known limits of the comparison
- **Published circuits:** no published second-order exact ASIC verifier exists, so every competitor is this project's implementation of a published algorithm or technique. A better RTL engineer could improve any of them, but the same is true of PAMS.
- **Delay depends on pipelining:** the delay ranking depends on how much share-wise pipelining one allows. Both families remain front-end limited at the depths built.
- **Physical evidence:** no silicon, no power or energy figures beyond Phase XI's vectorless estimate, and no tight-target timing closure.
