# PAMS novelty and prior-art review (Phase XII)

**Classification: B, an apparently novel hardware application and architecture. It is not a new mathematical mechanism.**
- **Prior art for the components:** every mathematical component of PAMS is in the primary literature. The closest equivalents are:
  - the integer-error modulus-switching lemma, with the identical n − 1 offset: Coron, Gérard, Trannoy, Zeitoun, TCHES 2023(4), Lemma 2;
  - the same precision rule α = ⌈log2(q·n)⌉: Coron et al., TCHES 2023(1), HOCompress;
  - integer interval anchoring with a public-threshold comparison: Bos et al. 2021, Alg. 2; Azouaoui et al. 2023, Alg. 4–5.
- **What no reviewed source contains:** the exact Compress_d equality test written as one d-independent modulus switch, followed by a comparison with a per-coefficient public threshold anchored at the integer interval start.
- **Limits of the claim:** a referee may judge this an incremental, possibly obvious, combination. Patent and implementation searches found nothing equivalent, but the searches were not exhaustive.

Search tools and sources:
- web search (Google Scholar-style queries, Google Patents);
- full texts fetched from TCHES, CiC, arXiv and the Phase XI local extracts (`refs/`). IACR ePrint and PeerJ PDFs were blocked by a Cloudflare challenge; see Uncertainty.
- Fetch scripts are in `novelty/`. Downloaded texts are in `~/lwe_agent_handoff/phase2/ext/priorart/` (not committed).

## 1. PAMS as a formal construction
**Setting:**
- q odd (3329), n shares (3), d ∈ {4, 5, 10, 11}, public c ∈ [0, 2^d);
- the arithmetic sharing satisfies x ≡ Σ x_i (mod q) with x_i ∈ [0, q).

**Definitions:**
- F_K(v) = ⌊v·2^K/q⌋;
- a_c = ⌈(2c − 1)q/2^{d+1}⌉ mod q, so that Compress_d(x) = c ⇔ x ∈ [a_c, a_{c+1}) cyclically (FIPS 203 rounding; q odd, so there are no ties).

**Construction (rtl/pams.v, MATHEMATICS §4):**
```
Low_c = F_K(a_c)            Θ_c = F_K(a_{c+1}) − F_K(a_c) − 1   (mod 2^K)      [public, from c and d]
Z     = ( Σ_i F_K(x_i)  + (n − 1)  − Low_c )  mod 2^K                          [share-wise, then one masked adder]
D_c   = [ Z < Θ_c ]                                                            [masked comparator, public Θ_c]
```
- **Exactness:** D_c = [Compress_d(x) = c] for all x, all c and all d whenever ⌊2^K/q⌋ ≥ n, i.e. K ≥ ⌈log2(nq)⌉.
- **For q = 3329, n = 3:** K = 14, independent of d.
- **K = 13 fails** in the share-wise-floor model for every d (§5).

**Why it works:**
- Σ F_K(x_i) + (n − 1) = F_K(x) + e with 0 ≤ e ≤ n − 1 (§2, N1).
- Because ⌊2^K/q⌋ ≥ n, the images of x = a_{c+1} − 1 and x = a_{c+1} stay apart despite e. So does the cyclic wrap at a_c − 1 / a_c.

**Hardware:**
- The (n − 1) offset and −Low_c are applied to share 0.
- Since Θ_c < 2^11 (checked), the comparator splits into a carry-free zero test of Z[13:11] and an 11-bit ripple comparison.

**Note on the Phase XII brief:**
- The brief describes "pre-alignment in Z_3329 before modulus switching". The frozen RTL instead aligns **after** switching, by subtracting Low_c in the 2^14 domain.
- The Z_q-pre-aligned variant (x_0' = x_0 − a_c mod q, then threshold F_K(w_c − 1) + 3, which depends only on the interval width) is also exact (`math/audit_results.json`, check G).
- This review treats both forms as the same mechanism.

## 2. Claimed new elements and the closest prior art
| # | element | status | closest primary source (exact location) |
|---|---|---|---|
| N1 | share-wise floor switching with an integer error 0 ≤ e ≤ n − 1 (Phase XI "integer-error lemma") | **known; identical statement and offset** | Coron, Gérard, Trannoy, Zeitoun, *Improved Gadgets for the High-Order Masking of Dilithium*, TCHES 2023(4) 110–145, §4.1, Algorithm 4 *ModSwitch* ("y1 ← y1 + (n − 1)"), Lemma 2 (0 ≤ e ≤ n − 1, any p1 → p2). Restated as Lemma 1 in Coron, Gérard, Lepoint, Trannoy, Zeitoun, TCHES 2024(4) 335–354. CGTZ23 says the technique "was already used in [CGMZ23] to mask the Compress function of Kyber". |
| N2 | anchoring at the integer interval start a_c = S(c) of Compress^{-1}(c) | **known** | Bos, Gourjon, Renes, Schneider, van Vredendaal, *Masking Kyber*, TCHES 2021(4) 173–214, §3.2, Algorithm 2 (PolyCompare: w0 += 2^{k−1} − S(c), x0 −= E(c) mod q). Azouaoui et al., *Protecting Dilithium against Leakage*, TCHES 2023(4) 58–79, Alg. 5 SecBoundCheck (x0 += λ0 mod q, so that the interval becomes [0, λ0 + λ1]). D'Anvers, Van Beirendonck, Verbauwhede, IEEE TC 72(2) 2023, streamlined hybrid (code: `Bp[i][0] = (Bp[i][0] − uncL + Q) % Q`). Coron et al. TCHES 2023(1) §5.2 (public candidate list = interval of Z_q). |
| N3 | a power-of-two target whose resolution absorbs the n-bounded error; width ⌈log2(nq)⌉ | **known as a precision rule** | Coron, Gérard, Montoya, Zeitoun, *High-order Polynomial Comparison and Masking Lattice-based Encryption*, TCHES 2023(1) 153–192, §5.1 Alg. 2 HOCompress: switch to 2^{d+α} with **α = ⌈log2(q·n)⌉, condition 2^α > q·n** (Thm. 6). That is 14 bits for n = 3, on top of the d integer bits. CGTZ23/CGLTZ24 choose p2 = 2^α·q with 2^α ≥ n so that the error is removable. Fritzmann et al., TCHES 2022(1) 414–460, Alg. 13 (f fractional bits, f ≥ 13 at first order). |
| N4 | comparison with a public threshold by a carry-only chain | **known** | Azouaoui et al. 2023, Alg. 4 SecLeq (add the (k+1)-bit two's complement of −(ψ + 1); "only the sign bit (and so all the intermediate carries) must be explicitly computed"; optimizations depend on the constant). A standard masked-adder technique. |
| N5 | **the combination:** an exact Compress_d(x) = c test as [(ModSwitch_{q→2^K}(x) − F_K(a_c)) mod 2^K < Θ_c], one K = ⌈log2(nq)⌉ for all d, a per-coefficient public Θ_c, no prime-modulus A2B, no d-dependent width | **not found** in any reviewed source (§3) | Nearest equivalents (§3): CGMZ23 HOCompress (d + α bits, then compress and compare); D'Anvers 2023 / Fritzmann 2022 Simple (d + t bits, aligned block); Bos 2021 / Azouaoui 2023 (exact mod-q A2B, then threshold or MSB). |
| N6 | split comparator (top 3 bits zero test, since Θ_c < 2^11) | hardware optimization of N4 | (generic) |
| N7 | second-order HPC2 ASIC lane with matched synthesis and P&R comparison against Simple | new measured result (local) | no matched published second-order ASIC verifier found |

## 3. Side-by-side comparison with the nearest constructions
Notation: x̄ = the masked value, a = public anchor, W = Boolean width processed by the masked adder.

| construction | per-share map | anchor | decision | W for d = 11, n = 3 | exact? |
|---|---|---|---|---|---|
| **PAMS** | F_14(x_i), + (n − 1) on share 0 | integer a_c, subtracted as F_14(a_c) | Z < Θ_c (public, per c) | **14** | yes (§5) |
| Simple: Fritzmann 2022 Alg. 13; D'Anvers 2023 Alg. 7; code `KYBER_FRAC_BITS = 14` for 3 shares | ⌊x_i 2^{d+f}/q⌋ | half-integer (c − ½) of the compressed grid | top d bits = 0 (aligned block) | d + f = 25 (published f = 14); 24 with Phase XI's optimized offset (t = 13, A = 1) | yes |
| HOCompress, CGMZ23 §5.1 | ⌊(x_i 2^{d+α+1} + q)/2q⌋, + 2^α − 1 | none (compresses, then compares to c) | the compressed value equals c | d + α = 25 (α = 14) | yes |
| Bos 2021 Alg. 2 / NXP US11528124 | x_i themselves (mod q) | S(c) and E(c) in Z_q | MSB of two exact mod-q A2B (k = 12) | 2 × 12-bit A2B **mod q** | yes |
| Azouaoui 2023 SecBoundCheck (Dilithium) | x_i (mod q) | λ0 in Z_q | SecLeq (public bound) after exact SecA2BModp | ⌈log2 q⌉ + 1, **mod-q** conversion | yes |
| D'Anvers 2023 streamlined hybrid | (x − uncL − j) products mod q, random linear combination, switch to 2^{13+14} | integer uncL | top 13 bits zero (zero test of a Z_q element) | 27 | no (collision probability q^{−LB}) |
| CGLTZ24 §4.2 (Dilithium rejection) | ModSwitch to 2^ρ q, ShiftMod | public bound a | ⌊(x − a)/2^ρ⌋ = 0 (mod q) zero test | mod-q arithmetic | yes |

**Does a change of variables reduce PAMS to any of these?**
- **Simple:**
  - Simple tests membership in a fixed, power-of-two-aligned block [0, 2^t) after anchoring on the compressed grid.
  - No choice of t, offset or scaling turns the non-aligned integer interval into such a block at width below d + 13: Phase XI exhaustive search, re-audited in §5, finds no exact offset at t = 12 or 11.
  - PAMS needs a per-c threshold, which is precisely the element Simple lacks. Fritzmann et al. (§2.2.3, p. 426) state: "When dealing with 2 intervals of width q/2, it is possible to position their boundary exactly at a power of two… However, already for d = 2 … this technique is no longer applicable", and abandon interval comparison for d ≥ 2. PAMS removes that obstacle with the public threshold, so the two are not the same construction.
- **CGMZ23:** PAMS's K equals CGMZ23's α exactly. PAMS is HOCompress with the d integer bits removed by integer anchoring and the "= c" test replaced by "< Θ_c". The width rule is the same; the predicate is not.
- **Bos 2021 / Azouaoui 2023:** these are the same predicate family (an interval with integer endpoints, a public offset, a threshold or sign test). PAMS replaces the exact mod-q A2B with the CGTZ23 ModSwitch and absorbs the error in the threshold. That is a substitution of known parts. I found no source that makes it.

**Differences that survive:** only N5 (with N6/N7 as engineering). It needs no new identity: given CGTZ23 Lemma 2 and the interval form, exactness follows in a few lines (§1). The novelty is the formulation and its hardware consequence (14 instead of 24/25 bits, with fewer gadgets), not new mathematics.

## 4. Patents and accessible implementations
**Patents:**
- **US 11528124 B2** (NXP; Gourjon, Bos, Renes, Schneider, van Vredendaal; priority 2021-04-07). Claims 1 and 11 cover two masked shifts anchored at the interval start and end, A2B, MSB extraction and masked AND (the Bos 2021 method). No switch to a power-of-two modulus; no threshold comparison. **Not PAMS.**
- **US 12273454 B2** (Infineon; Pessl; priority 2021-03-19). A masked compression computed through the division-free error term (x·2^d + q/2) mod q, then A2B and a masked equality test. No threshold, no interval anchoring, no modulus switch. **Not PAMS.**
- **Not examined:**
  - US 12166879 ("Rejection of masked polynomials") and US 12578927 (Boolean-to-arithmetic transition): the USPTO PDFs are image-only, so their claims were not read. The titles indicate other topics.
  - Google Patents queries for modulus switching plus threshold comparison returned no further candidates.
  - The patent search was keyword-based and not exhaustive (no CPC-class review, no EPO/WIPO full-text search).

**Implementations (cloned read-only; commit given):**
- **KULeuven-COSIC/Revisiting-Masked-Comparison @ a22ce2a (D'Anvers 2023):**
  - Simple with `KYBER_FRAC_BITS 14` for 3 shares, so the Phase XI baseline (13 bits with an optimized offset) is stronger than the published code;
  - the hybrid method anchors at `uncL` but uses mod-q products plus a 27-bit switch;
  - no threshold method.
- **HWSec-CSIC/hope-mlkem @ 72a90d8 (Camacho-Ruiz et al., TCHES 2026(2) 272–295):**
  - no ciphertext comparator in the RTL;
  - the `ENCODER_COMPRESS_MASKED_*` modules add the two shares with `mod_add` before an unmasked `COMPRESS` (`rtl/encoder_masked.v`, lines ~37–48).
- **masked-kyber-m4/mkm4 @ f2b6290 (Heinz et al. 2022):** first-order; comparison as in the earlier literature.
- **Not obtained:** `fragerar/HO_Kyber` (empty repository); Adams Bridge was not re-reviewed here (Phase X).
- **Other primary texts read:**
  - Ranney et al., arXiv 2606.31681 (2026): higher-order masked comparison (D'Anvers GF method) on FPGA, which leaks through parallelism;
  - Berthet et al., CiC 2(3) 2025: Reed–Solomon code-based masking with a Lagrange-interpolated comparison (CGMZ23);
  - Bronchain & Cassiers, TCHES 2022(4): compression via mod-p A2B;
  - Wang et al., arXiv 2602.19604 (MPC, dealer-assisted bitwise comparison).
  None contains N5.

## 5. Mathematical audit summary (details: `math/`, FINAL_VALIDATION_REPORT §3)
- **N1 (exhaustive):**
  - over all 3329³ = 36,892,780,289 canonical triples, j ∈ {0, 1, 2} at K = 14, 13 and 24, with 0 violations (`math/lemma.c`);
  - j = 2 is reachable for 3,327 of the 3,329 values of x.
- **N5 exactness:**
  - all (x, j, c, d): 0 mismatches for d = 4, 5, 10, 11, including the split-comparator form;
  - the RTL public-constant logic matches F_14(a_c) and Θ_c for all 3,120 (c, d) pairs, with max Θ_c = 1,027 < 2^11.
- **K = 13 impossibility (on reachable pairs only):** member and non-member collide for every d. Witnesses with concrete share triples:
  - d = 11: x = 0 as (0, 0, 0) versus x = 1 as (3326, 2, 2), both giving switched sum 0;
  - d = 4: x = 728 versus x = 729.
- **Scope of the bound:** it is a lower bound **in the share-wise floor model only**. Other share maps (rounding with offsets, prime-modulus A2B) are not covered.

## 6. Uncertainty
- **Inaccessible full texts** (Cloudflare challenge):
  - Dobiáš et al., *Two birds, one mask*, PeerJ CS 2026 (first-order unified ML-DSA/ML-KEM FPGA hardware);
  - Buschkowski et al., ePrint 2026/1265 (mixed-domain masking DSE, ML-KEM decapsulation core);
  - Hermelink et al., CCS 2024 / ePrint 2024/060 (abstract only);
  - Norga et al. X2X 2025: the Phase XI extract was used; the 2025 final version was not re-checked.

  Any of the first two could contain a masked ciphertext comparison. Their abstracts do not mention one.
- **Not read directly:** Oder et al., TCHES 2018(1) (TransformPower2, d = 1 decoding), known here only through Fritzmann 2022 §2.2.2.
- **Possible equivalents outside the PQC masking literature were not systematically searched:** threshold tests on modulus-switched shares in MPC (local truncation), FHE, or LWE decoders.
- An unsuccessful search does not establish global novelty.
- **Obviousness:** N5 is a short corollary of CGTZ23 Lemma 2 and the interval form, combined with known threshold comparators. The defensible claim is the architecture and its measured benefit, not a new identity.

## 7. Verdict
- **Not A:** the core identity is CGTZ23 Lemma 2; the width rule is CGMZ23's α; the anchoring and the threshold comparison are in Bos 2021 and Azouaoui 2023.
- **Not C or D:**
  - no reviewed source discloses the combined predicate N5 for ML-KEM ciphertext verification;
  - the closest line of work (Fritzmann 2022) explicitly considers interval comparison and rejects it for d ≥ 2;
  - the hardware consequence (a d-independent 14-bit lane instead of d + 13/14 bits) is new and measured.
- **B:** the mathematics exists; this realization and its demonstrated benefit do not appear in the reviewed work. Publishable framing: "an exact, d-independent masked ML-KEM ciphertext check obtained by combining ModSwitch [CGTZ23] with integer-interval anchoring and a public-threshold comparator". It must cite CGTZ23, CGMZ23, Bos 2021 and Azouaoui 2023 as the sources of every component.
