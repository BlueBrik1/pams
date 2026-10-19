# Phase XI final report: exact second-order masked ML-KEM ciphertext verification

## Verdict: **PROMISING**
- **Hardware:** a correct design beats the strongest matched baseline we could build on both mapped area and worst-path delay, in synthesis and after place-and-route, by margins far outside the measured variation.
- **Not SUCCESS:**
  - the second-order security evidence is a compositional argument plus home-made exhaustive and structural checks, with no established leakage-verification tool and no physical evaluation;
  - originality rests on negative searches (E4) over the accessible literature.

## The mechanism: pre-aligned modulus switching (PAMS)
- **Prior exact methods, and what they cost:**
  - The best exact method (Fritzmann et al. 2022 / D'Anvers et al. 2023, "Simple") switches each arithmetic share to a 2^{d+13} modulus. It subtracts the half-integer compressed value and tests "top d bits are zero". It is exact only with t = 13 fractional bits, so the lane is 24 bits wide for ML-KEM-1024.
  - Bos et al. 2021 anchor on the integer interval [S(c), E(c)) of Z_q, but use two prime-modulus A2B conversions.
- **PAMS combines the integer anchor with modulus switching and measures what that buys:**
  1. y_i = ⌊x_i 2^14/q⌋ per share, and Low_c = ⌊a_c 2^14/q⌋, the image of the integer interval start.
  2. **Integer-error lemma:** Σ y_i ≡ ⌊x 2^14/q⌋ − j with j ∈ {0, 1, 2}.
     - The switched domain only has to separate neighbouring integers of Z_q, so 2^K ≥ 3q, i.e. **K = 14 for every d**, instead of d + 13.
     - Proven exact (lemma + exhaustive (x, j, c, d)).
     - K = 13 is impossible for any decision rule (collision proof).
  3. The price is a per-coefficient public threshold Θ_c (closed form from c and d). Its comparison is folded into the existing carry ripple at one gadget per bit.
     - Θ_c < 2^11 lets the top 3 bits use the carry-free zero test.
     - The public logic is one constant multiply by q plus small comparators.
- **Gadget accounting:**
  - The baseline's cheaper decision structure (carry-free top-bit test) still costs more than PAMS's comparator: 55 vs 38 kernel gadgets.
  - Randomness: 171 vs 120 fresh bits per cycle.
  - The per-share exact scaling constant shrinks from 34 to 24 bits, with a 14-bit instead of a 24-bit result.

## Evidence
| claim | evidence | strength |
|---|---|---|
| exact FIPS 203 equality, all parameter sets, all c (incl. invalid ciphertexts), boundaries | lemma proof + exhaustive enumeration; RTL simulation (≥ 8,000 boundary-focused coefficients, 1,429 ciphertexts); gate-level simulation of all 15 mappings | strong |
| smaller and faster than the strongest baseline (synthesis) | 16,998 vs 21,598 µm² (−21.3%), 1.487 vs 1.649 ns (−9.8%); 5 mappings each, spread < 0.3% | strong (tool estimates) |
| smaller and faster after P&R | 18,704 vs 23,770 µm² cell (−21.3%), 1.613 vs 1.801 ns (−10.4%), die −20.7%; 3 utilizations each, 0 DRC, hold met, RCX | strong (tool estimates); the baseline needed a raised hold-buffer cap (default flow failed for the baseline only) |
| including randomness generation | 24,281 vs 32,522 µm² (−25.3%) with Trivium-64 sources | model (generator measured; seeding excluded) |
| second-order glitch-robust security | HPC2 everywhere + PINI composition; exhaustive gadget check (0 failures; negative control 108 failures); structural domain check of every netlist (0 violations; negative control 79) | **argued + home-made checks only** |
| novelty | no prior work found that anchors at the integer interval start and switches to a d-independent minimal width with a threshold comparator (Bos 2021, Heinz 2022, Fritzmann 2022 via D'Anvers 2023, D'Anvers 2022, Coron 2023, X2X 2025, Shahmirzadi–Hutter 2024 read) | **E4 (negative search)**: not proof |

## Fairness
- **Same building blocks:** both lanes use the same gadget, linear operations, aligner, accumulator, technology, flows and constraints.
- **The baseline received every optimization that applies to it:**
  - exhaustively optimal offset (the naive offset is inexact);
  - minimal t for its rule;
  - minimal exact multiplier;
  - mode shifter;
  - carry-free top-region test with an early OR tree.
- **The baseline is our implementation of the published algorithm,** not a published circuit; no matched second-order ASIC verifier was available.
- **Improvements that would apply to both lanes:** X2X-style conversion optimizations or other gadget families would change absolute numbers. PAMS's advantage comes from the width (14 vs 24) and gadget count, which such changes do not remove; this was not measured.
- **Scope:** subsystem only. No complete-decapsulation or complete-accelerator improvement is claimed.

## Remaining work for SUCCESS
1. **Established-tool verification** (e.g. PROLEAD or Coco on the netlist) of both lanes at second order, glitch-robust.
2. **A literature and patent check for interval-anchored modulus switching** in masked lattice decoders (including Saber/Kyber decryption-side Compress), with full-text access to recent hardware works (Dobiáš 2026, Ranney 2026).
3. **Optionally,** a TVLA campaign on an FPGA prototype. No hardware is available here.

## Artifacts
- **Documents:** `BASELINE.md`, `MATHEMATICS.md`, `CANDIDATES.md`, `SECURITY.md`, `BENCHMARKS.md`, `EXPERIMENT_LOG.md`.
- **Code:** `models/*.py|sh`, `rtl/{base,pams,pams_r,trivium64}.v`.
- **Results:** `runs/bench.json`, `runs/pnr_summary.json`, `runs/rng_cost.json`, `runs/negctl_hpc2.txt`.
