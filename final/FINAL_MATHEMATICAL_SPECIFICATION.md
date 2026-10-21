# Final mathematical specification of the publication circuit (`pams_jqr`)

This document describes the mathematics implemented by `final/rtl/pams_jqr.v`, a byte-identical copy of `competitors/rtl/pams_jqr.v`; hashes are in PUBLICATION_MANIFEST.md.

The decision mathematics is that of the frozen `rtl/pams.v` (Phase XI, MATHEMATICS.md §4). `pams_jqr` differs only in register placement:
- just-in-time operand delays (j);
- a two-stage share-wise constant multiplier (q);
- the public window logic split across existing stages (r).

None of these changes any value, any width, or the decision rule. Equivalence is checked below (§6).

## 1. Notation and parameters
| symbol | meaning |
|---|---|
| q = 3329 | ML-KEM modulus |
| d ∈ {4, 5, 10, 11} | compression width, selected per coefficient (`mode` = 0, 1, 2, 3). ML-KEM-512 / 768: d_u = 10, d_v = 4; ML-KEM-1024: d_u = 11, d_v = 5 |
| n = 3 | number of arithmetic shares (second-order masking) |
| x_0, x_1, x_2 ∈ [0, q) | canonical shares, x = x_0 + x_1 + x_2 mod q |
| c ∈ [0, 2^d) | public received ciphertext coefficient |
| K = 14 | width of the switched representation |
| F(v) = ⌊v · 2^K / q⌋ | share-wise modulus switch |
| Compress_d(x) = ⌈2^d x / q⌋ mod 2^d | FIPS 203 |

## 2. Function
- **Per coefficient:** b = [Compress_d(x) = c].
- **Per ciphertext:** D = ∧_{coefficients} b, output as a 3-share Boolean sharing (dec[2:0]).
- **Domain:** every c ∈ [0, 2^d) is legal; invalid ciphertexts give D = 0.

**Interval form** (q odd, so there are no ties):
- Compress_d(x) = c ⇔ x ∈ [a_c, a_{c+1}) cyclically in Z_q, with a_c = ⌈(2c − 1) q / 2^{d+1}⌉ mod q;
- the interval is cyclic for c = 0 (it wraps through q − 1 → 0);
- widths: {208, 209} (d = 4), {104, 105} (5), {3, 4} (10), {1, 2} (11).

## 3. Construction
```
Low_c  = F(a_c)                                   (public, mod 2^14)
Θ_c    = F(a_{c+1}) − F(a_c) − 1                  (public, mod 2^14)
y_i    = F(x_i)                                   (share-wise, each y_i is a 14-bit value held by share domain i)
Z      = (y_0 + y_1 + y_2 + 2 − Low_c)  mod 2^14  (the + 2 − Low_c is applied to share 0 only, share-locally)
b      = [Z < Θ_c]
```

**Hardware closed forms** for the public constants (RTL stage 1–2), with e = 13 − d and r_c = ((1 − 2c) q) mod 2^{d+1}:
- Low_c = (2c − 1)·2^e + qq(r_c) (mod 2^14), where qq(r) = ⌊r 2^e / q⌋ ∈ [0, 4] is computed with four constant comparisons;
- r_{c+1} = (r_c − 2q) mod 2^{d+1};
- Θ_c = 2^{e+1} − 1 + qq(r_{c+1}) − qq(r_c);
- 3 ≤ Θ_c ≤ 1027 < 2^11 for every (c, d) (Phase XII `math/audit.py`, check C, all 3,120 pairs).

**Share-wise switch:** F(x_i) = (x_i · 10321339) ≫ 21, exact for every x_i ∈ [0, q).
- In pams_jqr the product is computed as (x_i[11:6] · M) ≪ 6 + x_i[5:0] · M, with both partial products registered. This is an identical integer value.

## 4. Exactness argument
1. **Integer-error lemma** (Coron, Gérard, Trannoy, Zeitoun, TCHES 2023(4), Lemma 2; MATHEMATICS.md §2). For canonical shares, Σ F(x_i) ≡ F(x) − j (mod 2^14) with j ∈ {0, 1, 2}.
   - The proof is three lines (MATHEMATICS.md §2).
   - Phase XII also checked it exhaustively over all 3329³ = 36,892,780,289 canonical triples, with 0 violations (`validation/math/lemma.c`).
2. **Reduction to a finite check.** Hence Z = F(x) − j + 2 − Low_c (mod 2^14) depends on the shares only through (x, j). The decision is exact for all share triples iff it is exact for all (x, j, c, d) with j ∈ {0, 1, 2}.
3. **Exhaustive check.** For all 3329 · 3 · 3104 cases, b = [Compress_d(x) = c]; 0 mismatches. This covers both the plain and the split comparator (Phase XII `math/audit.py`, check D). The lemma plus this enumeration is a complete proof for the stated input contract.
4. **Why it works:** ⌊2^14 / q⌋ = 4 ≥ n = 3. The images of x = a_{c+1} − 1 and x = a_{c+1} remain separated despite the error j, and so do the images at the cyclic wrap (a_c − 1 versus a_c).

## 5. Precision requirement and its scope
- **Sufficient:** K = ⌈log2(n q)⌉ = 14, independent of d, because ⌊2^K/q⌋ ≥ n.
- **Insufficient in this model:** K = 13 fails in the **share-wise-floor model** (y_i = ⌊x_i 2^K/q⌋, decision any function of Σ y_i + public offset mod 2^K). For every d, a member and a non-member collide on reachable share triples. Example for d = 11: x = 0 as (0, 0, 0) and x = 1 as (3326, 2, 2) give the same switched sum (`validation/math/audit_results.json`, check F).
- **Scope:** this is **not** a universal hardware lower bound. Other share maps (rounding with offsets, prime-modulus A2B, more shares, different error handling) are outside the model.

## 6. Hardware interpretation and equivalence of the final RTL
**Masked kernel** (identical to frozen PAMS; MATHEMATICS.md §5):
- the CSA of the three share-domain operands (13 majority gadgets);
- a ripple carry fused with a ripple comparator against the public Θ_c (10 + 10 gadgets);
- the carry-free zero test of Z[13:11] (valid since Θ_c < 2^11): 2 OR gadgets for bits 12–13, 1 OR-tree gadget, and 1 AND with the late bit 11;
- 1 final AND of the zero test and the comparator.

That is 38 kernel HPC2 gadgets, plus 2 accumulator gadgets.

**Accumulation.** b is AND-accumulated over the ciphertext by one HPC2 with 2-cycle feedback (two interleaved chains) plus one final HPC2. dec is valid 4 cycles after the last coefficient's decision.

**What the optimizations change:**
- **j:** the operand bits y_i[k] are delayed in single-domain registers until the ripple stage that consumes bit k, instead of delaying the 3-share S_k, T_k. The values are unchanged.
- **q:** a pipelined multiplier, giving the same F(x_i).
- **r:** the registered intermediates qc, qn, e, c are carried one stage, and Low_c / Θ_c are completed in the next stage. The values are unchanged.

**Equivalence evidence:**
- **Generator regression:** the same generator with all options off reproduces `rtl/pams.v` byte-identically (Phase XIII).
- **Simulation of the final RTL, mapping-0 gate-level, and the P&R input netlist** (`final/runs/fsim_*.log`), on:
  - every interval boundary of every (c, d): a_c − 1, a_c, a_{c+1} − 1, a_{c+1}, 12,416 coefficients;
  - every x ∈ [0, q) for every d, against c = Compress_d(x) and against c + 1, 26,632 coefficients;
  - share patterns including zeros and q − 1 values;
  - ciphertexts of 2–9 coefficients.

  Results in FINAL_BENCHMARKS.md §6 and below.

## 7. Input requirement (interface contract)
- Shares must be canonical: 0 ≤ x_i < 3329.
  - F is computed by a constant multiplier that is exact only on [0, q).
  - The frozen and the final PAMS multiplier give wrong values for x_i ∈ [3329, 4005]. The Simple baseline's multiplier is wrong at x_i = 3329 (Phase XII audit, check B).
- Neither design checks this. It is an **upstream interface requirement** for both, and no validator is added to either.

## 8. Supported ML-KEM parameters
All three parameter sets: ML-KEM-512, -768 and -1024, i.e. d ∈ {4, 5, 10, 11}, selectable per coefficient, at one coefficient per cycle.
