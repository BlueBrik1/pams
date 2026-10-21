# Final novelty statement

**Classification (Phase XII, unchanged): B, an apparently novel hardware architecture and application. It is not a new mathematical mechanism.**

## Contribution claimed
> An exact masked ML-KEM ciphertext-verification datapath. It combines share-wise modulus switching into one fixed 14-bit representation for all compression widths with public interval anchoring and a per-coefficient public threshold comparison, which reduces the protected (masked nonlinear) hardware needed to support all ML-KEM compression widths.

**Check against the final RTL (`final/rtl/pams_jqr.v`):**

| element of the claim | where in the RTL |
|---|---|
| fixed 14-bit switch for d ∈ {4, 5, 10, 11} | `s_i = ((x_i[11:6]·M) ≪ 6 + x_i[5:0]·M) ≫ 21` with M = 10321339 (= ⌊x_i 2^14/q⌋); 14-bit lane `y0..y2` for every mode |
| public interval anchoring | `lowr` = Low_c = ⌊a_c 2^14/q⌋ from (c, d), subtracted share-locally on share 0: `y0 <= s0p - lowp + 14'd2` |
| per-coefficient public threshold | `thr` = Θ_c from (c, d), compared bit-serially in the masked ripple comparator (`th2[k]`) |
| reduced protected hardware | 40 HPC2 gadgets and 120 random bits per cycle, against 57 / 171 for the strongest conventional (Simple) lane, `base_jq` |

## What is not claimed (established prior art that the construction uses)
| component | source to cite |
|---|---|
| share-wise floor modulus switching with an integer error 0 ≤ e ≤ n − 1 (and the n − 1 offset) | J.-S. Coron, F. Gérard, M. Trannoy, R. Zeitoun, "Improved Gadgets for the High-Order Masking of Dilithium", IACR TCHES 2023(4), pp. 110–145, Alg. 4 *ModSwitch*, Lemma 2; restated in Coron, Gérard, Lepoint, Trannoy, Zeitoun, TCHES 2024(4), pp. 335–354 |
| precision rule α = ⌈log2(q·n)⌉ (14 bits for n = 3) in masked ML-KEM compression | J.-S. Coron, F. Gérard, S. Montoya, R. Zeitoun, "High-order Polynomial Comparison and Masking Lattice-based Encryption", IACR TCHES 2023(1), pp. 153–192, §5.1, Alg. 2 *HOCompress*, Thm. 6 |
| masked comparison by anchoring at the integer interval start S(c) / E(c) of Compress^{-1}(c) | J. W. Bos, M. Gourjon, J. Renes, T. Schneider, C. van Vredendaal, "Masking Kyber: First- and Higher-Order Implementations", IACR TCHES 2021(4), pp. 173–214, §3.2, Alg. 2 |
| protected comparison with a public threshold (carry-only, sign bit) | M. Azouaoui, O. Bronchain, G. Cassiers, C. Hoffmann, Y. Kuzovkova, J. Renes, T. Schneider, M. Schönauer, F.-X. Standaert, C. van Vredendaal, "Protecting Dilithium against Leakage: Revisited Sensitivity Analysis and Improved Implementations", IACR TCHES 2023(4), pp. 58–79, Alg. 4 *SecLeq*, Alg. 5 *SecBoundCheck* |
| exact conventional masked comparison (the baseline algorithm, Simple / MaskedCompress) | T. Fritzmann, M. Van Beirendonck, D. B. Roy, P. Karl, T. Schamberger, I. Verbauwhede, G. Sigl, "Masked Accelerators and Instruction Set Extensions for Post-Quantum Cryptography", IACR TCHES 2022(1), pp. 414–460 (Alg. 13; §2.2.3); J.-P. D'Anvers, M. Van Beirendonck, I. Verbauwhede, "Revisiting Higher-Order Masked Comparison for Lattice-Based Cryptography: Algorithms and Bit-Sliced Implementations", IEEE Trans. Computers 72(2), 2023, pp. 321–332, §3.2 |
| masking gadget and composition | G. Cassiers, B. Grégoire, I. Levi, F.-X. Standaert, "Hardware Private Circuits: From Trivial Composition to Full Verification", IEEE Trans. Computers 70(10), 2021 (HPC2); G. Cassiers, F.-X. Standaert, "Trivially and Efficiently Composing Masked Gadgets with Probe Isolating Non-Interference", IEEE TIFS 15, 2020 (PINI) |
| verification tools used | SILVER (Knichel, Sasdrich, Moradi, ASIACRYPT 2020); PROLEAD (Müller, Moradi, TCHES 2022(4)) |

Authors, venues and pages of the CGTZ23, CGMZ23, Bos 2021, Azouaoui 2023, Fritzmann 2022 and D'Anvers 2023 entries were checked against the locally held full texts (title pages; D'Anvers pp. 321–332 from the running page numbers). The HPC, PINI, SILVER and PROLEAD entries are given from the Phase XII reports and must be checked against the publisher versions when the bibliography is written.

## Closest prior art and the difference
| nearest construction | difference from PAMS |
|---|---|
| Simple (Fritzmann 2022; D'Anvers 2023) | anchors at the half-integer of the compressed grid and tests a fixed power-of-two block; needs d + 13 bits (24 for d = 11; the published code uses d + 14); no per-c threshold. Fritzmann et al. §2.2.3 explicitly consider interval comparison and reject it for d ≥ 2. |
| HOCompress (CGMZ23) | same width rule α, but on top of the d integer bits (d + 14 bits), then compresses and compares with c |
| Bos 2021 / Azouaoui 2023 | same predicate family (integer interval, public bound); uses exact prime-modulus A2B per range check instead of a d-independent modulus switch |
| CGTZ23 ModSwitch | the switching lemma itself; no ML-KEM comparator |

**What remains:** none of the reviewed sources (`validation/NOVELTY_REVIEW.md`) contains the combination of one d-independent ⌈log2(nq)⌉-bit switch, integer-interval anchoring and a per-coefficient threshold comparison for exact ML-KEM ciphertext verification. Neither do two patents (US 11528124 B2, US 12273454 B2) or three implementations (D'Anvers 2023 code, HOPE-MLKEM, mkm4).

## Limits of the claim
- **Search scope:** the search was targeted, not exhaustive. Phase XIV made one final retrieval attempt (2026-10-20):
  - **Buschkowski et al., ePrint 2026/1265** (mixed-domain masking DSE, arbitrary-order ML-KEM decapsulation core): the abstract was read; it does not describe the comparison method. The PDF was refused (HTTP 403). Still unresolved.
  - **Dobiáš et al., PeerJ CS 2026** (first-order, FPGA): not found by search. Still unresolved; first order in any case.
  - **Hermelink et al., CCS 2024 / ePrint 2024/060:** the abstract was read. It attacks the D'Anvers et al. higher-order comparison and proposes no new comparator. It is relevant to the limitations (physical security), not to novelty.
- **Obviousness:** the exactness follows in a few lines from CGTZ23 Lemma 2 plus the interval form. A referee may judge the combination obvious; the contribution must be argued through its hardware consequence.
- **Wording:** "to our knowledge", never "first".
