# Paper evidence index

Paths are relative to `phase2/masked_verification/`. "Final" means the circuits `final/rtl/pams_jqr.v` and `final/rtl/base_jq.v` (hashes in PUBLICATION_MANIFEST.md).

## 1. Claims and their evidence
| potential paper claim | supporting artifact | evidence type | limitations |
|---|---|---|---|
| PAMS computes [Compress_d(x) = c] exactly for d ∈ {4, 5, 10, 11}, every c, every canonical sharing | MATHEMATICS.md §2–4; `validation/math/lemma.c` + `lemma_results.txt` (all 3329³ triples); `validation/math/audit.py` → `audit_results.json` (check D: all (x, j, c, d)) | proof (lemma) + exhaustive enumeration | canonical shares 0 ≤ x_i < q; share-wise floor model |
| the final RTL implements that function | `final/runs/fsim_*_rtl.log`, `fsim_*_gate.log`, `pnr_*_T2.0_s1/fsim_routed.log`, `sim_routed.log` | simulation of all interval boundaries of every (c, d) and every x for every d (39,112 coefficients); RTL, gate-level, routed | simulation is exhaustive over the functional cases listed, not over all share triples; the share independence follows from the lemma |
| the public constants Low_c, Θ_c are correct; Θ_c < 2^11 | `validation/math/audit_results.json` (check C, all 3,120 (c, d)) | exhaustive | — |
| 14 bits suffice for every d | MATHEMATICS.md §4; FINAL_MATHEMATICAL_SPECIFICATION.md §5 | proof | — |
| 13 bits do not suffice | `validation/math/audit_results.json` (check F, reachable collisions with witnesses) | exhaustive, constructive | **only in the share-wise floor model**; not a universal lower bound |
| PAMS needs 40 HPC2 gadgets and 120 random bits per cycle, against 57 / 171 | `competitors/runs/cbench.json` (gadget counts from the RTL); compcheck R check on every netlist | structural count | HPC2 gadget family, these ripple structures |
| PAMS reduces routed cell area by 19.5 % (die 18.5 %) against the strongest conventional lane we built | `final/runs/pnr_stats.json`, FINAL_BENCHMARKS.md §2 (7 seeds × 3 targets) | physical-design estimate; complete separation of all seeds (rank-sum p = 0.0006, the minimum attainable with 7 + 7) | Nangate45, OpenROAD flow, 50 % utilization; implementation variation only |
| synthesized area −19.3 % | `competitors/runs/cbench.json` (5 mappings each) | synthesis estimate | — |
| clock period: comparable (1.0 % / 3.6 % median advantage; inconclusive at 2.0 ns; equal at 1.1 ns) | FINAL_BENCHMARKS.md §2, §5 | physical-design estimate | small differences, inside or near the seed spread |
| PAMS routes DRC-clean at 1.1 ns in 7 / 7 seeds, the baseline in 1 / 7 | FINAL_BENCHMARKS.md §3; `final/runs/pnr_base_jq_T1.1_s*/` | physical-design observation | one utilization, one flow; may disappear at lower utilization |
| area-delay product −19.4 % to −22.5 % | `final/runs/pnr_stats.json` | derived | — |
| both designs sustain one coefficient per cycle; latency 35 vs 37 cycles | RTL (control pipeline), FINAL_DESIGN_SPECIFICATION.md §3 | design fact | — |
| PAMS is second-order secure against glitch-extended probes (ideal randomness) | SILVER on the gadget (`validation/silver/results.json`); gadget identity (`final/runs/gadget_identity.json`); composition preconditions (`final/runs/routed_check_final.jsonl`, compcheck on all synthesis / P&R-input netlists in `competitors/runs/cbench.json`); PINI composition theorem | formal (gadget) + published theorem + mechanical precondition check | glitch-robust probing model only; ideal randomness; home-made precondition checker (with negative controls) |
| no leakage detected in the whole lane | Phase XII `validation/SECURITY_VERIFICATION.md` §4.3 (frozen pams.v, up to 16.8 M simulations); `final/prolead/` (pams_jqr, focused) | statistical (PROLEAD fixed-vs-random) | not a proof; second order at one steady-state cycle; frozen-design campaign larger than the final-design campaign |
| constant time | `final/runs/control_final.json` | structural | — |
| the strongest conventional exact method is Simple; Bos-, HOCompress-, Brent–Kung- and Coron-arithmetic-style lanes are dominated | `competitors/BENCHMARKS.md`, `competitors/CANDIDATES.md` | synthesis estimates, plus a lower bound (Coron) | our implementations of published algorithms; no published second-order ASIC verifier to reproduce |
| the baseline received every applicable optimization (including an equivalent of PAMS's r) | `competitors/FAIRNESS_AUDIT.md`; `final/runs/pubpaths_base_jq.txt` (public logic ≤ 0.595 ns vs ≈ 1.02 ns critical) | timing analysis | — |
| novelty: the combination is apparently new | `validation/NOVELTY_REVIEW.md`, FINAL_NOVELTY_STATEMENT.md | literature / patent / code review | not exhaustive; 2 recent works not fully accessible |

## 2. Figure and table source data (`final/data/`)
| figure / table | file | columns |
|---|---|---|
| period-versus-area scatter of all seeded runs (by target; valid / invalid marked) | `pnr_seeded_runs.csv` | design, target, seed, valid, period, cell, die, buffers, wirelength, drc, crit_start/end |
| synthesis comparison of all designs (Pareto plot of the Phase XIII competitors) | `synthesis_all_designs.csv` | design, area median/min/max, delay median/min/max, FFs, cells, gadgets, rnd bits, latency |
| gadget breakdown bar chart | `gadget_breakdown.csv` | part, pams, simple baseline |
| historical utilization sweep (Phase XI / XIII) | `utilization_sweep_routed.csv` | design, util, period, cell, die, drc, hold |
| architecture diagram (pipeline) | FINAL_DESIGN_SPECIFICATION.md §3 | stage-by-stage contents of both lanes |
| mathematical construction figure | FINAL_MATHEMATICAL_SPECIFICATION.md §3 | Low_c, Θ_c, Z, decision |
| security-evidence table | FINAL_SECURITY_STATUS.md §1–3 | tool, scope, result |

## 3. Historical numbers (label clearly if used)
| comparison | area | delay | source |
|---|---|---|---|
| frozen pams.v vs frozen base.v (Phase XI) | −21.3 % (synthesis and routed cell) | −9.8 % synthesis / −10.4 % routed | BENCHMARKS.md; this is against the **original** baseline only |
