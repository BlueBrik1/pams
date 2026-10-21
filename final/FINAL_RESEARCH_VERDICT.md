# Final research verdict (read this first)

**Assessment: PAMS is reliably smaller, but not demonstrably faster.**
- Against the strongest conventional exact second-order lane we could build, PAMS reduces:
  - masked gadgets and fresh randomness by 29.8 %;
  - routed cell area by 19.5 % (die 18.5 %), consistently across every seed and every timing target.
- Clock periods are comparable: PAMS is faster by 1.0–3.6 % in medians where both designs route, which is inconclusive at the loose target and of no practical size when pushed.
- At a 1.1 ns target, PAMS routes DRC-clean in 7 / 7 runs and the baseline in 1 / 7.

## 1. Final PAMS circuit selected for publication
- **Circuit:** `final/rtl/pams_jqr.v` (module `pams_jqr_lane`), SHA-256 `804fd73a…3760ba0e7f` (full hash in PUBLICATION_MANIFEST.md).
- **What it is:** the frozen PAMS algorithm (`rtl/pams.v`, Phase XI) with three generic implementation changes:
  - j: just-in-time operand delays;
  - q: two-stage share-wise multiplier;
  - r: public window logic retimed into the existing stages.
- **Unchanged:** decision mathematics, gadget count and randomness.

## 2. Strongest conventional competitor
- **Circuit:** `final/rtl/base_jq.v` (module `base_jq_lane`).
- **Algorithm:** the Simple method (Fritzmann et al. 2022; D'Anvers et al. 2023) with the exhaustively optimized t = 13 / A = 1 offset, carry-free zero test, the same generic j / q optimizations, and the same gadget, accumulator and flow.
- **Families evaluated and dominated** (Phase XIII):
  - Bos-style interval checking;
  - HOCompress precision;
  - Brent–Kung (X2X-style) carries;
  - Coron's arithmetic route (lower bound).
- **Equivalent of PAMS's r:** none needed. The baseline's public logic needs ≤ 0.595 ns, while its critical stages are its share-wise multiplier stages at ≈ 1.02 ns (`final/runs/pubpaths_base_jq.txt`).

## 3. Final area improvement (positive = PAMS smaller)
| measure | improvement | basis |
|---|---|---|
| routed cell area | **19.5 %** (all targets; 18,734–18,786 vs 23,285–23,367 µm² medians) | 7 seeds × 3 targets; every PAMS run smaller than every baseline run (rank-sum p = 0.0006, the minimum attainable) |
| die area (same 50 % utilization) | **18.5 %** | — |
| synthesized cell area | 19.3 % (17,022 vs 21,097 µm²) | 5 mappings each |
| area-delay product (routed) | 19.4 – 22.5 % | — |

## 4. Final timing result and confidence
| target | PAMS median period | baseline median period | difference | confidence |
|---|---|---|---|---|
| 2.0 ns (loose) | 1.156 ns | 1.198 ns | −3.6 % | **inconclusive**: ranges overlap (1.146–1.165 vs 1.142–1.255), p = 0.07 |
| 1.2 ns | 1.094 ns | 1.105 ns | −1.0 % (11 ps) | separated in all 7 seeds (p = 0.0006), but practically negligible |
| 1.1 ns | 1.068 ns (7 / 7 valid) | 1.066 ns (1 / 7 valid) | +0.2 % (PAMS 2 ps slower) | equal; the baseline fails DRC-clean routing in 6 / 7 runs |
| synthesis | 1.033 ns | 1.057 ns | −2.3 % | 5 mappings |

**Statement for the paper:** "the clock periods are comparable (within 1–4 %); PAMS's advantage is area, protected logic and randomness, not speed."

## 5. Randomness and gadget savings
- **Gadgets:** 40 vs 57 HPC2 (−29.8 %): CSA 13 vs 23; decision logic 25 vs 32; accumulator 2 each.
- **Fresh random bits per cycle:** 120 vs 171 (−29.8 %).
- **Generator cost:** with dedicated Trivium-64 generators this is 2 vs 3 instances (Phase XI model). The generator is not part of the area figures.

## 6. Security status (FINAL_SECURITY_STATUS.md)
**Glitch-robust second-order probing security with ideal randomness:**
- the gadget is SILVER-proven;
- every final gadget instance is byte-identical to a proven variant;
- the composition preconditions are checked on every synthesized and routed netlist;
- the PINI composition theorem applies.

**PROLEAD evidence:** the extensive Phase XII campaign covers frozen pams.v. pams_jqr received a focused campaign (§3 of the security status): first order over all 72 cycles (1 M simulations) and second order at the steady-state cycle (262 k), with no leakage surviving confirmation (the flagged maxima 5.53 / 5.21 decay to 0.78 / 0.44 at 4.2 M simulations), and a negative control detected at 41.4. That is smaller than the frozen-design campaign.

**Unresolved:**
- transition (and glitch + transition) robustness: no applicable theorem, statistical evidence only;
- the randomness source;
- physical leakage;
- integration.

The same contract and the same checks apply to base_jq (no lane PROLEAD for base_jq in this phase).

## 7. Mathematical correctness status
**Exact for all valid inputs:** q = 3329; d ∈ {4, 5, 10, 11}; every c; canonical 3-share inputs. Evidence:
- the integer-error lemma (CGTZ23 Lemma 2), plus an exhaustive check over all 3329³ triples;
- exhaustive (x, j, c, d) enumeration;
- public constants verified for all (c, d).

**The final RTL, gate-level and routed netlists** match the reference on:
- every interval boundary of every (c, d);
- every x for every d;

with 0 mismatches.

**Precision:** 14 bits are sufficient for every d. 13 bits are insufficient **in the share-wise floor model** (not a universal bound).

**Interface:** canonical shares (0 ≤ x_i < 3329) are an upstream requirement of both designs; neither validates them.

## 8. Novelty classification
**B:** an apparently new hardware architecture and application, not a new mathematical mechanism (FINAL_NOVELTY_STATEMENT.md).

## 9. Practical limitations
- **Scope of the estimates:**
  - tool estimates in one technology (Nangate45) and one open flow (Yosys / ABC, OpenROAD);
  - one utilization for the seeded study;
  - no clock uncertainty or OCV;
  - no silicon, no power or energy measurement beyond a vectorless estimate.
- **Subsystem only:** a ciphertext-verification lane. The decapsulation-level saving is diluted by the rest of masked ML-KEM.
- **Randomness:** generator excluded from the area figures; must be independently seeded.
- **Transitions:** robustness unproven for both designs (HPC2 is not O-PINI; executions are adjacent).
- **Physical attacks:** attacks on the FO comparison itself (Hermelink et al. CCS 2024) apply to any masked comparator.
- **Baseline status:** the baseline is our implementation of a published algorithm. No published second-order exact ASIC verifier exists for direct comparison.
- **Latency:** PAMS is 2 cycles shorter (35 vs 37 to the ciphertext decision). Both have 1 coefficient per cycle throughput. For a streaming verifier this changes only the decision delay after the last coefficient, by 2 cycles.

## 10. Contributions defensible in an academic paper
1. **The PAMS datapath:** an exact masked ML-KEM ciphertext-verification datapath that combines share-wise modulus switching to one fixed 14-bit representation for all ML-KEM compression widths with integer interval anchoring and a per-coefficient public threshold comparison. It is built from published components (CGTZ23, CGMZ23, Bos 2021, Azouaoui 2023), whose combination we did not find in the literature.
2. **A complete second-order (3-share, HPC2) RTL implementation** at one coefficient per cycle, supporting ML-KEM-512/768/1024 with per-coefficient d.
3. **Measured reductions** against the strongest conventional exact lane we could build under the same gadget, flow and optimizations:
   - −29.8 % gadgets and randomness;
   - −19.5 % routed cell area;
   - −18.5 % die;
   - comparable clock period.
4. **A matched competitor study** (Bos-style, HOCompress, Brent–Kung / X2X-style, Coron-arithmetic lower bound, optimized Simple), with fairness analysis.
5. **Security evidence** in the glitch-robust probing model:
   - SILVER on the gadget;
   - mechanical composition-precondition checks on all netlists including routed ones;
   - PROLEAD on complete lanes, with negative controls.

## 11. Claims we must NOT make
- That PAMS is **faster** (generally, or by 9.8 % / 10.4 %). Those figures are against the unpipelined original baseline (`rtl/base.v`) only, and do not hold against `base_jq`.
- The **21.3 % area** figure as the final result. It is a historical, original-baseline comparison and must be labelled as such.
- That PAMS introduces a new mathematical identity, or that we discovered modulus switching with integer error, the ⌈log2(nq)⌉ precision rule, interval anchoring or public-threshold comparison.
- "First" or "world's first": only "to our knowledge, not previously described".
- That 14 bits is a universal lower bound. It is minimal only in the share-wise floor model.
- Transition-robust or physically secure masking; security with a PRNG beyond a computational assumption.
- That pams_jqr received the same whole-lane PROLEAD campaign as frozen pams.v.
- Silicon, power or energy results; results for other technologies or flows.
- That PAMS beats all published implementations. No comparable published second-order ASIC verifier exists.
- That the 1.1 ns routability difference is general. It was observed at 50 % utilization in one flow.
