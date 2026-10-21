# Novelty and related-work audit (final manuscript review, 2026-10-21)

**Reviewer:** the AI system that produced the research. This is an internal review, and **not a confirmation of global novelty**.

**Sources:**
- `final/FINAL_NOVELTY_STATEMENT.md` and `validation/NOVELTY_REVIEW.md`;
- the locally held full texts: `refs/` (Bos 2021, Coron 2023, D'Anvers 2022/2023, Heinz 2022, X2X and others) and `phase2/ext/priorart/papers/`;
- one bounded web check (below).

**Classification: B, unchanged.** An apparently new hardware architecture and application, built entirely from published mathematical components. "To our knowledge" wording is required and is used throughout.

## 1. The claim audited

> An exact second-order masked ML-KEM ciphertext-verification architecture combining share-wise modulus switching into a common 14-bit representation, public interval anchoring, and a protected comparison against a per-coefficient public threshold.

The manuscript claims no new lemma, precision rule, interval method or threshold gadget. This was checked in the abstract, Section 1 (contributions), Section 2.3 ("What PAMS takes and adds"), Section 7 ("Architectural, not mathematical, novelty") and the conclusion.

## 2. Related work, element by element

| work | what it introduced | what PAMS borrows | what PAMS combines differently | kind of difference | wording justified? |
|---|---|---|---|---|---|
| Coron, Gérard, Trannoy, Zeitoun, TCHES 2023(4) (ModSwitch, Lemma 2) | Share-wise floor switching q → 2^K with integer error 0 ≤ e ≤ n − 1, and the n − 1 offset | The lemma and the offset, identically | Uses the switched sum for an interval test, not inside Dilithium | Application | Yes: credited as "Coron et al. [14], Lemma 2" |
| Coron, Gérard, Montoya, Zeitoun, TCHES 2023(1) (HOCompress) | Precision α = ⌈log₂(qn)⌉ on top of d integer bits, then compress and compare with c | The width rule (K = α = 14) | Removes the d integer bits through integer anchoring; replaces "= c" by "< Θ_c" | Architectural (predicate formulation), not mathematical | Yes |
| Bos, Gourjon, Renes, Schneider, van Vredendaal, TCHES 2021(4) | Masked comparison anchored at the integer interval start/end of Compress⁻¹(c), via exact mod-q A2B | Integer interval anchoring | Anchors in the switched 2^K domain after a d-independent switch; one threshold instead of two exact mod-q A2B range checks | Architectural (substitution of known parts) | Yes |
| Azouaoui et al., TCHES 2023(4) (SecLeq, SecBoundCheck) | Masked comparison with a public bound computing only carries / the sign | Public-threshold comparison by a carry-only chain | Per-coefficient threshold Θ_c(c, d) in a 14-bit switched domain | Implementation and application | Yes |
| Fritzmann et al., TCHES 2022(1) (Simple, Alg. 13; §2.2.3) | Exact masked compression via a power-of-two switch with fractional bits; d-dependent block test; interval comparison considered and set aside for d ≥ 2 | The power-of-two switch with an error-absorbing precision (as background) | A per-c threshold removes the obstacle they cite; the width becomes independent of d | Architectural | Yes; their §2.2.3 statement is quoted accurately |
| D'Anvers et al., TCHES 2022(2) | Higher-order ciphertext comparison: random-sum method with a modulus switch to a large (possibly power-of-two) modulus, keeping fractional bits; probabilistic (collision 2^−s) | — (background) | PAMS is exact, and per coefficient | Different method | **Corrected in this review.** Section 2.3 did not say that this paper already scales shares to a power-of-two modulus inside a masked comparison. It now does, and calls it prior art. |
| D'Anvers, Van Beirendonck, Verbauwhede, IEEE TC 72(2) 2023 | Framework, exact Simple method, and the hybrid / GF methods (collision-prone) | Simple as the baseline algorithm | — | — | Yes |
| Cassiers et al. (HPC 2021, PINI 2020, transitions 2021, Trivium 2024) | Gadget, composition theorems, RNG | All used as published | — | — | Yes |
| Norga et al. X2X; Shahmirzadi & Hutter 2024; Bronchain & Cassiers 2022 | Conversion hardware | Brent–Kung / X2X style is a competitor in Appendix D.7 | — | — | Yes |
| Kamucheka 2022; HOPE-MLKEM (Camacho-Ruiz et al. 2026); Ranney et al. 2026 | Masked ML-KEM hardware | — | HOPE-MLKEM has no ciphertext comparator in its RTL (Phase XII code review); Ranney et al. use a D'Anvers-style comparison on FPGA | — | Yes |
| Patents US 11528124 B2, US 12273454 B2 (Phase XII) | Bos-style comparison; masked compression via an error term | — | No switch to a power of two, no threshold | — | Yes |

## 3. Bounded prior-art check of this review (one attempt, 2026-10-21)

| target | result |
|---|---|
| Buschkowski et al., ePrint 2026/1265 | The ePrint abstract page was readable. It describes mixed-domain masking DSE (a HADES extension), an arbitrary-order ML-KEM decapsulation core and TVLA; it does **not** mention the comparison method. The PDF was refused (HTTP 403). **Still unresolved.** |
| 2026 *PeerJ Computer Science* article cs-4003 ("Two birds, one mask", first-order unified ML-DSA/ML-KEM hardware) | Located by search; the page was refused (HTTP 403). **Still unresolved.** It is first order in any case. |
| CHES 2025 poster 4 (found by search) | Masked FrodoKEM (Gérard, Guerreau). The comparison is a masked zero test with a power-of-two q. Not relevant. |
| Web searches: masked ML-KEM ciphertext comparison with modulus switching / interval / threshold, 2025–2026 | Returned D'Anvers 2022/2023, Bos 2021, Ranney 2026, Berthet 2025 (CiC, code-based masking), and Hermelink 2024. **No source with the PAMS combination was found.** |

No essentially identical architecture was discovered, so no fundamental novelty problem was found. An unsuccessful search does not establish novelty, and the paper says so.

## 4. Corrections applied

1. **Abstract.** "into a new protected datapath" became "into a protected datapath that, to our knowledge, has not been described before".
2. **Section 2.3.** D'Anvers et al. 2022 is now described accurately as prior art for share-wise switching to a power-of-two modulus inside a masked comparison, with fractional bits and a probabilistic check.
3. **Section 7, "Incomplete access to recent prior art".** It now records this review's retrieval attempt and its outcome (two full texts still refused), and states that the search was targeted and that an unsuccessful search does not establish novelty. A duplicated sentence was removed.

## 5. Remaining novelty limitations

- Two 2026 full texts remain inaccessible (above).
- MPC, FHE and LWE-decoder literature (local truncation, threshold tests on switched shares) was not searched systematically.
- The patent search was keyword-based. No CPC-class or EPO/WIPO full-text search was made.
- **Obviousness:** exactness follows in a few lines from published results, and a referee may judge the combination incremental. The paper argues the contribution through its measured hardware consequence (Section 7).
- External expert confirmation of novelty is required before any claim beyond "to our knowledge".
