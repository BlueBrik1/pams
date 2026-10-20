# Phase XII final validation report: PAMS security and mathematical novelty

**Overall: CONDITIONALLY VALIDATED.**
- **Security verdict:** PARTIALLY VERIFIED (`SECURITY_VERIFICATION.md`).
- **Novelty classification:** B (`NOVELTY_REVIEW.md`).
- **Why not VALIDATED:**
  - Neither principal question is fully resolved in the strong sense the brief requires.
  - Security is established in the glitch-robust probing model with ideal randomness, but not for transitions, the randomness source or physical leakage.
  - Novelty holds only as a new combination, an architecture with a measured benefit. It is not a new mechanism, and the prior-art search is not exhaustive.
- **Why not INVALIDATED or UNRESOLVED:** no flaw was found in the frozen design, and the result survives its two principal tests within clearly stated conditions.

Frozen artifacts (`rtl/pams.v`, `rtl/base.v`, benchmark settings and Phase XI measurements) were not modified. All Phase XII outputs are in `validation/`.

## 1. Security: verdict and evidence (details: SECURITY_VERIFICATION.md)
**Established:** glitch-robust 2-probing security of both frozen lanes with ideal randomness. This covers all 15 synthesis netlists, both P&R input netlists and all 6 routed netlists. Evidence:

1. **Gadget, formal (SILVER, established tool):**
   - both distinct mapped HPC2 variants (covering all mappings) are probing-, NI-, PINI- and uniformity-secure at order 2, in both the standard and the glitch-robust model;
   - robust SNI holds at order 1 only, which is consistent with HPC2 being PINI and not SNI;
   - three broken variants (unregistered refresh, mask reuse, recombination) fail as expected.
2. **Gadget, statistical (PROLEAD v3.1.0, established tool):**
   - setup: order 2, glitches and transitions, multivariate, four back-to-back invocations, 4,194,304 simulations;
   - both variants: max −log10 p 4.2–4.6 over 6,984 sets, no leakage;
   - all three broken variants: ∞.
3. **Composition:** the trivial PINI composition theorem (Cassiers & Standaert TIFS 2020; HPC, IEEE TC 2021). Its preconditions were checked mechanically on all 18 netlists with the home-made `compcheck.py`, which comes with negative controls:
   - no cross-domain mixing outside gadgets;
   - one gadget per random bit;
   - gadget port and output domains correct;
   - routed gadgets identical to the verified gadget.
4. **Whole lane, statistical (PROLEAD, established tool):**
   - first order at every cycle, and second order at the steady-state cycle;
   - up to 16.8 M simulations;
   - all six flagged maxima were multiple-testing artefacts. Each confirmation with more data decays: 6.08 → 0.24, 5.96 → 1.81, 6.79 → 1.20, 5.46 → 1.59;
   - every injected flaw in the full lane is detected: exposed decision ∞, partial recombination 48.9 / 22.5, mask reuse ∞.
   - Caveat found here: PROLEAD 3.1.0 does not seed its RNG in hardware mode, so only confirmations with larger simulation counts were treated as evidence.
5. **Timing:** the latency is fixed. cvalid/dvalid depend only on public control in all 12 synthesis netlists checked.

**Not established:**
- **Transitions:** robustness against transitions combined with glitches. No published theorem applies: HPC2 is not O-PINI, every gadget executes every cycle, and the accumulator chain makes execution k feed execution k+2. There is statistical evidence only.
- **Randomness:** generation is not implemented. With the modelled Trivium-64, the guarantee becomes computational, and the PRNG's own leakage is outside the analysis.
- **Physical leakage:** not assessed. Published attacks on the FO comparison function itself apply equally to any masked comparator.
- **Integration:** the upstream sharing (A1) and the downstream consumer (A3) are assumptions.
- **Tools not used:** maskVerif (needs OCaml/opam, absent without root) and Coco (CPU co-verification, not applicable).

## 2. Novelty and closest prior art (details: NOVELTY_REVIEW.md)
**Classification B:** an apparently novel hardware application and architecture, not a new mathematical mechanism.

**Closest prior art:**
- Coron–Gérard–Trannoy–Zeitoun, TCHES 2023(4), Alg. 4 / Lemma 2: the integer-error ModSwitch with the identical n − 1 offset;
- Coron–Gérard–Montoya–Zeitoun, TCHES 2023(1), HOCompress: the same width rule α = ⌈log2(qn)⌉ = 14;
- Bos et al. 2021 Alg. 2, and Azouaoui et al. 2023 SecLeq / SecBoundCheck: integer interval anchoring and public-threshold comparison.

**What is new:** none of these sources contains the combination, namely one d-independent 14-bit modulus switch followed by a comparison with a per-coefficient public threshold anchored at the integer interval start. Fritzmann et al. 2022 explicitly reject interval comparison for d ≥ 2.

**Patents:**
- US 11528124 B2 (NXP) and US 12273454 B2 (Infineon) do not disclose it.
- Two image-only patents were not read.

**Implementations:** D'Anvers 2023 code, HOPE-MLKEM and mkm4 do not contain it.

**Limits of the claim:**
- several full texts were inaccessible: Dobiáš 2026, Buschkowski 2026, and Hermelink CCS 2024 (abstract only);
- the search was not exhaustive;
- a referee may judge the combination obvious.

## 3. Mathematical audit (`math/`)
**Integer-error lemma.** Σ F_K(x_i) = F_K(x) − j with j ∈ {0, 1, 2}, checked exhaustively over all 3329³ = 36,892,780,289 canonical share triples at K = 14, 13 and 24 (`lemma.c`). There are 0 violations, and j = 2 is reachable for 3,327 of the 3,329 values of x.

**Decision exactness** (`audit.py`):

| check | what it covers | result |
|---|---|---|
| A | interval starts and closed form | correct; widths {208, 209}, {104, 105}, {3, 4}, {1, 2} |
| D | PAMS decision for all x, j, c and d ∈ {4, 5, 10, 11} | 0 mismatches; also 0 for the split-comparator form |
| E | baseline (Simple, t = 13, A = 1) | 0 mismatches |
| C | RTL public constants against F_14(a_c) and Θ_c, all 3,120 (c, d) pairs | match; Θ_max = 1,027 < 2^11 |
| G | the Z_q-pre-aligned variant | exact |

**K = 13 is impossible** in the share-wise floor model for every d. The collisions use reachable share triples, e.g. for d = 11: x = 0 as (0, 0, 0) versus x = 1 as (3326, 2, 2). This is a lower bound for this share map only.

**Interface caveat, found here.** The constant multipliers are exact only for canonical shares, x_i < 3329. They are wrong at x_i = 3329 (both designs) and at x_i ∈ [3329, 4005] (PAMS), and the RTL does not check the input. This is an interface assumption (A1), identical in kind for both designs, and it should be stated in any publication.

## 4. Do the Phase XI performance numbers remain valid?
**Yes, for the frozen designs.** No design was changed and no flaw requiring a repair was found. Phase XIII re-synthesized both frozen designs bit-identically under the same flow and reproduced 21,598 µm² / 1.649 ns (base) and 16,998 µm² / 1.487 ns (PAMS). The Phase XI P&R results stand.

**Two qualifications:**
1. **Randomness generator excluded.** The numbers are lane-only. Phase XI's RNG-inclusive figure (−25.3 %) rests on the Trivium-64 cost model, whose security role is the computational assumption of §1.
2. **Strength of the baseline is a separate question.** Whether `base.v` is the strongest conventional competitor is being tested in Phase XIII (`competitors/`). Phase XIII's first results show, for example, that one extra pipeline stage makes the baseline faster than frozen PAMS. The Phase XI percentages are valid against `base.v` only; their validity against a stronger competitor is answered in `competitors/FINAL_COMPETITOR_REPORT.md`.

## 5. Flaws found
- **In the frozen design:** none demonstrated, in security or in functionality.
- **Gaps** (not flaws):
  - transition robustness is unproven;
  - randomness generation is unimplemented;
  - canonical-input checking is absent;
  - integration is unverified.
- **In the Phase XI documentation:**
  - The novelty framing overstated the mathematics: the "integer-error lemma" is CGTZ23 Lemma 2.
  - The Phase XII brief's description ("pre-alignment in Z_3329") does not match the frozen RTL, which aligns after switching in the 2^14 domain. Both forms are exact (check G).
- **In my own process:** a frozen Phase XI file (`tools/tmp.sh`) was accidentally overwritten early in this phase. It was restored byte-exactly from the export snapshot, and no other frozen file differs.

## 6. What blocks publication
1. **Transitions:** either a transition-robust argument (e.g. an O-PINI accumulator, or an idle cycle so that Theorem 2 of Cassiers–Standaert 2021 applies), or an explicit restriction of the claim to the glitch-robust model.
2. **Novelty framing:** the paper must cite CGTZ23, CGMZ23, Bos 2021 and Azouaoui 2023 for each component and claim only the combination and its hardware consequence. The inaccessible 2026 works (Dobiáš, Buschkowski) should be checked before submission.
3. **Baseline strength:** the improvement figures must be stated against the strongest fairly matched conventional competitor (Phase XIII), not only against `base.v`.
4. **Randomness:** state the RNG model, and either implement and verify one or exclude it explicitly.
5. **Physical evidence:** there is no silicon or FPGA TVLA. This is common for an architecture paper, but it must be stated.
6. **Interface:** state the canonical-share assumption, or add a check.

## 7. Overall assessment
**CONDITIONALLY VALIDATED.** The PAMS lane is an exact, second-order, glitch-robust-probing-secure masked ML-KEM ciphertext verifier, under ideal randomness and canonical shares. This was verified with established tools at the gadget level, by a published composition theorem with mechanically checked preconditions, and by whole-lane statistical testing with effective negative controls. Its mathematics is exhaustively checked.

**Conditions:**
- the transition-robustness gap;
- the randomness model;
- a publication framing as a novel *combination* of known components (class B);
- improvement figures re-stated against the strongest competitor (Phase XIII).
