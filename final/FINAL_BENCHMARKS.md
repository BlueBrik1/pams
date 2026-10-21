# Final benchmarks: pams_jqr against base_jq (Phase XIV)

**Status:** all values are EDA-tool estimates (Yosys/ABC, OpenSTA, OpenROAD with RCX), not silicon measurements.

## 0. Settings (identical for every run of both designs)
| item | setting |
|---|---|
| library | Nangate45 typical: synthesis `current/lib/NangateOpenCellLibrary_typical.lib`; P&R the ORFS `nangate45` platform (LEF, liberty, `rcx_patterns.rules`) |
| synthesis | Yosys 0.33 + ABC flow B (BUF_X1 drive, 5 fF load, -D 500); HPC2 `keep_hierarchy`; 5 mappings (pad 0/3/6, -D 400, -D 650) |
| P&R input | flow C (same flow, liberty without the ORFS DONT_USE cells), `competitors/runs/pnrsyn_<d>/mapped.v` |
| P&R flow | `final/tools/pnr_final.tcl` = Phase XI/XIII `tools/pnr_mv.tcl` with one change: `SEED` drives `place_pins -random_seed` and both `global_placement … -random_seed`. Everything else is unchanged: utilization 50 %, density 0.6, CTS, setup repair, hold repair (60 % buffer cap), global route (50 congestion iterations), detailed route (64 iterations), RCX |
| constraints | one clock `clk` at the target period; input / output delay 0 (I/O at the clock edge); input transition 0.05 ns; output load 5 fF; no clock uncertainty (the same in all phases) |
| run validity | flow finished, 0 DRC, RCX parasitics, hold WNS ≥ 0 |
| run-time bound | 90 min wall clock per run (watchdog; such runs are recorded as TIMEOUT) |
| concurrency | 3 runs, 4 OpenROAD threads each |

**Seed independence (verified, not assumed):**
- Seed 1 at 2.0 ns reproduces the Phase XIII u50 run bit-identically (same `final.def` sha256 7aaa0d45…).
- Seeds 2 and 3 move 84 % of the common instances (mean displacement 11 µm) and 171 of 181 I/O pins (`final/models/placediff.py`). They are physically different implementations of the same netlist.
- These runs sample implementation (placement / routing) variation only. They are not independent samples of any physical process, and the statistics below are read in that sense.

## 1. Synthesis (5 mappings; median [min, max]; Phase XIII `competitors/runs/cbench.json`)
| design | cell area µm² | worst-path delay ns | FFs (top) | comb. cells | HPC2 | rnd bits/cycle | latency |
|---|---|---|---|---|---|---|---|
| **pams_jqr** | 17,022 [17,001, 17,022] | 1.033 [1.033, 1.041] | 1,294 | 3,366 | 40 | 120 | 31 + 4 |
| **base_jq** | 21,097 [21,097, 21,097] | 1.057 [1.057, 1.057] | 1,500 | 3,175 | 57 | 171 | 33 + 4 |
| pams_jpr | 16,237 [16,237, 16,250] | 1.163 [1.159, 1.163] | 1,107 | 3,362 | 40 | 120 | 30 + 4 |
| base_jp | 20,048 [20,048, 20,052] | 1.457 [1.457, 1.457] | 1,271 | 3,304 | 57 | 171 | 32 + 4 |
| pams (frozen, Phase XI) | 16,998 [16,998, 17,046] | 1.487 [1.487, 1.487] | 1,309 | 3,294 | 40 | 120 | 29 + 4 |
| base (frozen, Phase XI) | 21,598 [21,597, 21,598] | 1.649 [1.649, 1.650] | 1,565 | 3,434 | 57 | 171 | 31 + 4 |

**pams_jqr against base_jq (synthesis):**
- area −19.3 %;
- delay −2.3 %;
- gadgets and random bits −29.8 %;
- latency −2 cycles.

## 2. Post-route: seeded campaign, utilization 50 %, 7 seeds per design and target (`final/runs/pnr_stats.json`)
| design | target ns | runs valid / total | meet target | achieved period median [min, max] (std) ns | cell area median [min, max] (std) µm² | die µm² | buffers | registers | ADP µm²·ns |
|---|---|---|---|---|---|---|---|---|---|
| pams_jqr | 2.00 | 7 / 7 | 7 | 1.156 [1.146, 1.165] (0.007) | 18,734 [18,706, 18,771] (22) | 35,596 | 1,543 | 2,494 | 21,629 |
| base_jq | 2.00 | 7 / 7 | 7 | 1.198 [1.142, 1.255] (0.041) | 23,285 [23,266, 23,309] (14) | 43,694 | 2,048 | 3,210 | 27,901 |
| pams_jqr | 1.20 | 7 / 7 | 7 | 1.094 [1.091, 1.097] (0.002) | 18,750 [18,710, 18,778] (23) | 35,596 | 1,558 | 2,494 | 20,532 |
| base_jq | 1.20 | 7 / 7 | 7 | 1.105 [1.102, 1.111] (0.003) | 23,304 [23,278, 23,338] (24) | 43,694 | 2,081 | 3,210 | 25,761 |
| pams_jqr | 1.10 | **7 / 7** | 7 | 1.068 [1.062, 1.070] (0.002) | 18,786 [18,777, 18,828] (17) | 35,596 | 1,604 | 2,494 | 20,067 |
| base_jq | 1.10 | **1 / 7** | 1 | 1.066 (single valid run) | 23,367 (single) | 43,694 | 2,136 | 3,210 | 24,904 |

- **Registers** counts all flip-flops, including the 30 per gadget. **Die area** is fixed by the floorplan at 50 % utilization of the synthesized area.
- **Achieved period** = target − worst setup slack over the in2reg / reg2reg / reg2out / in2out groups, on RCX parasitics.

### Comparison (positive = PAMS better; exact two-sided rank-sum p over all C(14, 7) label assignments)
| target ns | period improvement (medians) | p (period) | PAMS faster per seed index (descriptive) | period ranges overlap | cell area improvement | p (cell) | die improvement | ADP improvement |
|---|---|---|---|---|---|---|---|---|
| 2.00 | +3.6 % | 0.073 | 5 / 7 | **yes** | +19.5 % | 0.0006 | +18.5 % | +22.5 % |
| 1.20 | +1.0 % | 0.0006 | 7 / 7 | no (1.091–1.097 vs 1.102–1.111) | +19.5 % | 0.0006 | +18.5 % | +20.3 % |
| 1.10 | not comparable as a distribution (1 valid baseline run): 1.068 vs 1.066, **−0.2 %**. Including the 5 finished but DRC-failing baseline runs (1.066–1.073, median 1.072): +0.3 % | — | — | yes | +19.6 % (vs the valid run) | — | +18.5 % | +19.4 % |

p = 0.0006 is the smallest value attainable with 7 + 7 runs, reached when the two groups are completely separated.

## 3. The 1.1 ns target: routability
| | pams_jqr | base_jq |
|---|---|---|
| runs that finished with 0 DRC | **7 / 7** | 1 / 7 (seed 5) |
| finished with residual DRC violations | 0 | 4 (seeds 2, 3, 4, 7: 3, 1, 6, 3 violations) |
| stopped at the 90-min limit (TIMEOUT) | 0 | 2 (seed 1 after 126 min: 40 % of the last detailed-route iteration, 13 violations; seed 6 after 90 min) |
| wall-clock time per run | 1 min 13 s – 1 min 22 s | 1 min 27 s (seed 5); 31–126 min otherwise |
| routed wirelength | 58,067–58,506 µm | 72,529–73,494 µm |

**Interpretation:**
- At 1.1 ns both designs close timing on the placed netlist (achieved ≈ 1.06–1.07 ns).
- The baseline's larger, more heavily buffered netlist (≈ 2,140 buffers, 25 % more wirelength) usually fails to route DRC-clean within the flow's 64 detailed-route iterations. PAMS routes cleanly every time.
- This is a flow-specific routability observation at one utilization (50 %). A lower utilization would likely let the baseline route, at a larger die.

## 4. Earlier post-route results (Phase XIII utilization sweep; same flow at seed 1, 2.0 ns target)
| design | routed period median [min, max] over UTIL 45/50/55 | cell area | die |
|---|---|---|---|
| base_jq | 1.222 [1.150, 1.241] | 23,290 | 43,694 |
| pams_jqr | 1.162 [1.153, 1.162] | 18,706 | 35,596 |
| base_jp | 1.579 [1.573, 1.584] | 22,232 | 41,728 |
| pams_jpr | 1.248 [1.243, 1.261] | 17,903 | 34,025 |
| base (frozen) | 1.801 [1.795, 1.810] | 23,770 | 44,811 |
| pams (frozen) | 1.613 [1.607, 1.614] | 18,704 | 35,525 |

## 5. Timing conclusion
- **At the loose 2.0 ns target:** PAMS's median period is 3.6 % lower, but the distributions overlap. The baseline's seed spread is 1.142–1.255 ns; PAMS's is 1.146–1.165 ns. Inconclusive, p = 0.07.
- **At the 1.2 ns target:** timing-driven repair brings both designs close to their limits. PAMS is faster in every seed, but by only 1.0 % (11 ps).
- **At the 1.1 ns target:** the only valid baseline run is 2 ps faster than PAMS's median.
- **Reading:** the two architectures have **comparable clock periods** (≈ 1.06–1.10 ns when pushed). There is no timing advantage of practical size. The repeatable effects are PAMS's much smaller seed variability and its clean routability at 1.1 ns.

## 6. Functional verification of the benchmarked netlists
| netlist | stimulus | coefficients | ciphertexts (accepting) | mismatches |
|---|---|---|---|---|
| RTL pams_jqr / base_jq / pams / base | systematic (all interval boundaries of every (c, d) + every x for every d against c and c + 1) | 39,112 each | 7,096 (76) each | 0 |
| gate level: synthesis mapping 0 and flow-C P&R input, both finalists | systematic | 39,112 each | 7,096 (76) each | 0 |
| **routed** (T 2.0 s1, final.v with liberty functions inlined), both finalists | systematic + frozen random (`models/sim.py`) | 39,112 + 6,001 | 7,096 (76) + 1,086 (573) | 0 |
| all 5 synthesis mappings, both finalists (Phase XIII) | random | 6,001 RTL + 5 × 1,500 gate level | 1,079 (558) RTL | 0 |

## 7. Failures and exclusions (none hidden)
- **base_jq at 1.1 ns:**
  - 4 runs finished with DRC violations, so they are invalid; their periods are reported in §3;
  - 2 runs were stopped at the 90-min limit (`TIMEOUT.txt` in the run directory).
- **PAMS-side failures:** none.
- **Harness slips, corrected and not counted:** one launch attempt of the campaign through `wsl.exe bash -c` lost its `$` variables and ran nothing. It was relaunched from a script file (`final/tools/campaign1.sh`).
- **Not run (bounded experiment):** targets below 1.1 ns, other utilizations, and clock uncertainty or OCV derating. At 1.1 ns the baseline already fails routing in 6 of 7 runs, and both designs achieve ≈ 1.06–1.07 ns, so lower targets would not change the conclusion.

## 8. Reproduction
See FINAL_REPRODUCIBILITY.md §6–§8.
