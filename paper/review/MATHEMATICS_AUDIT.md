# Mathematics audit (final manuscript review, 2026-10-21)

**Reviewer:** the AI system that produced the research and the manuscript (Claude Code, Claude Opus 5.5). This is an internal review, not an independent one.

**Scope:**
- every lemma, proposition, remark and nontrivial equation in Section 3.1 and Appendix A;
- the worked examples;
- the correspondence with `final/FINAL_MATHEMATICAL_SPECIFICATION.md` and with the final RTL.

**Result: QUALIFIED PASS.** No mathematical error was found in the construction, the lemma or the exactness proof, within the scope below. Two statements about the scope of the evidence were overstated. One factual statement about the multiplier at non-canonical inputs was wrong. All three are corrected. The analysis of non-canonical inputs remains incomplete and is recorded as unresolved.

## How the checks were made

**By hand:** every algebraic step of the following was followed.
- Lemma 1, the integer-error modulus switch (Section 3.1 C; Appendix A.3).
- Proposition 1, exactness (Section 3.1 F; Appendix A.7).
- The closed forms for Low_c and Θ_c (Equations 7, 8, 20–22).
- The interval form of Compress_d (Equations 2, 15).
- The split comparator (Equation 24).
- The K = 13 remark (Appendix A.9).

**By script:** `paper/scripts/audit_math.py` is a new, lightweight script that runs in about 1 s. Its output is in `review/math_audit_results.json`. It re-checks:
- the interval form for all (x, c, d);
- the widths, the 3,120 (c, d) pairs, and the Θ range 3–1027;
- the closed forms;
- Proposition 1 with its tight bounds, over all 31,159,440 (x, j, c, d) cases;
- the exact reachability of j (with constructive witnesses for every x);
- the gap of F₁₄ and F₁₃, and the K = 13 witness;
- the multiplier over all 12-bit inputs.

The 3329³ lemma enumeration of Phase XII was **not** repeated, because no discrepancy required it.

**By simulation:** `paper/scripts/examples.py` and `paper/scripts/appendix_data.py` simulate `final/rtl/pams_jqr.v` with Icarus Verilog. They assert that the registers hold the reference values for E1–E4 (Tables 2 and 9) and for the cycle trace of E1 (Table 16). The trace covers the shares, all six partial products, F₁₄(x_i), the anchored operand, qq(r_c), qq(r_{c+1}), e, Low_c, Θ_c, the first CSA majority, and the decision.

## Findings

| # | location | original claim | problem | evidence | correction | status |
|---|---|---|---|---|---|---|
| M1 | Section 3.1 F, "Canonical shares"; Section 7 "Canonical input shares" | "the constant multiplier is wrong for x_i ∈ [3329, 4005]"; "Lemma 1 and the multiplier constant both assume x_i < q"; non-canonical inputs "would break correctness" | The multiplier differs from F₁₄ (mod 2¹⁴) at **only two** 12-bit inputs: 3329 (16383 vs 0) and 4005 (3326 vs 3327). The proof of Lemma 1 never uses x_i < q, so the lemma holds for any non-negative shares. The "would break" claim was not demonstrated. | `audit_math.py` item 7. A direct evaluation over [0, 4096) found exactly 2 mismatches. Random sampling (200,000 cases containing a bad share, and 200,000 other non-canonical cases) and a targeted search at interval starts with j = 2 found **no** wrong decision. | Text now states the two exact values, that the lemma does not need canonicity, and that non-canonical inputs were sampled but not analysed completely and "could" affect correctness. Canonical shares remain the stated interface contract. | **Resolved** (statement corrected). A complete analysis of non-canonical inputs is **unresolved** and recorded as a limitation. |
| M2 | Section 3.1 F, after the proof | "that enumeration is an independent machine proof" | Overstated. It is a computational proof for the stated contract, conditional on the correctness of the enumeration script. "Independent" also suggests a different party. | — | Changed to "a second, computational proof for the stated input contract, assuming the enumeration script is correct". The text also states what this review re-ran and what it did not. | Resolved |
| M3 | Appendix A.7, "Machine check" | "this enumeration alone is a complete proof" | Same over-statement. It also relies on Lemma 1 to reduce share triples to (x, j). | — | "together with the lemma, a complete computational proof for the stated input contract, provided the script is correct", plus a note on the review re-run. | Resolved |
| M4 | `final/FINAL_MATHEMATICAL_SPECIFICATION.md` §4 (frozen) | "For all 3329 · 3 · 3104 cases" | Typo in the frozen document. The number of (c, d) pairs is 3,120 (16 + 32 + 1024 + 2048), giving 31,159,440 cases. | `audit_math.py`: pairs = 3120, cases = 31,159,440 | Not edited, because the document is frozen. The manuscript uses the correct count. | Recorded |
| M5 | same document §7 (frozen) | "wrong values for x_i ∈ [3329, 4005]" | The interval reading is wrong (see M1). `validation/SECURITY_VERIFICATION.md` §1.3 states it correctly ("at x_i = 3329 (and at 4005 for PAMS)"). | M1 | Not edited (frozen). The manuscript is corrected. | Recorded |
| M6 | `validation/SECURITY_VERIFICATION.md` §2 (Phase XII) vs `final/FINAL_MATHEMATICAL_SPECIFICATION.md` §6 | "3 top-region gadgets … 2 final-combination gadgets" vs "4 top-region, 1 final AND" | Different classification of the AND gadget `ug1535`. The total is 40 in both, and the RTL has 40 instances. | `audit_rtl.py`: 40 `hpc2` instances in lines 1500–1537. `final/data/gadget_breakdown.csv` gives 4 + 1. | None needed. The manuscript follows the final specification (4 + 1). | Recorded |

## Items checked with no error found

| item | what was verified |
|---|---|
| Compress_d (Eq. 1, 14) | FIPS 203 rounding (half up). There is no tie, since q is odd. The reference `compress` agrees with the vectorised formula for all x. |
| Interval form (Eq. 2, 15) | Both cases of the derivation. a_c = ⌈(2c−1)q/2^{d+1}⌉ mod q matches `models/pams.py` `starts` for all four d. Membership equals Compress_d(x) = c for every (x, c, d). Widths are {208, 209}, {104, 105}, {3, 4} and {1, 2}. I₀ wraps for d ∈ {4, 5, 10} and not for d = 11 (a₀ = 0). |
| Lemma 1 (Eq. 5, 17, 18) | Steps 1–4. The bound 0 ≤ j ≤ n − 1 follows from 0 ≤ Σr_i ≤ n(q−1) and r ≥ 0. Reduction mod 2^K is valid because the 2^K·k term vanishes. Sampling of 40,000 random triples agrees. |
| Reachability of j | Derived by hand and confirmed for every x: j = 0 and j = 1 are always reachable, and j = 2 iff ρ(x) ≤ q − 3, i.e. for 3,327 of the 3,329 values. Both manuscript statements ("j = 2 occurs for 3,327 values"; "all three values of j occur for 3,327 values") are therefore correct. |
| Gap (Eq. 13) | Steps of F₁₄ are 4 or 5, and the wrap step is 2¹⁴ − F₁₄(q−1) = 5. F₁₃ steps are 2 or 3. |
| Closed forms (Eq. 7, 8, 20–22) | Derived by hand, including the negative A₀ for c = 0, the wrap at c = 2^d − 1 (r_{2^d} = r₀), qq ∈ [0, 4] because 2¹⁴ < 5q, and Θ ∈ [2^{e+1} − 5, 2^{e+1} + 3]. They are asserted equal to the definitions for all 3,120 pairs and for all 48 rows of Table 10. |
| Proposition 1 | Setup: 0 < D_c < 2^K for d ≥ 1, and the representatives in [a_c, a_c + q). Member bound: Δ + 2 − j ≤ D_c − g + 2 = Θ_c + 3 − g. Non-member bound: Δ + 2 − j ≤ 2^K − g + 2. Neither wraps. The tight bounds −1 and +1 were re-computed over all cases. The decision mismatch count is 0. |
| Split comparator (Eq. 24) | Valid because Θ_c ≤ 1027 < 2¹¹. |
| K = 13 remark | The necessity argument (g ≥ 3, given reachability) is correct. The witnesses (0, 0, 0) vs (3326, 2, 2) at d = 11 and the d = 4, 5, 10 rows of the table were recomputed. The scope limitation ("share-wise floor model only") is stated. |
| Simple baseline (A.10) | Nested floors of non-negative values are exact. The exactness reduction to (x, j, c, d) holds for any K. The offset search is frozen Phase XI/XII evidence and was not re-run. |
| Worked examples E1–E4 | Every number was recomputed by hand in Appendix A.11 and asserted against the RTL in simulation. |
| Notation | Consistent across Sections 2–3 and Appendix A: F_K, Low_c, Θ_c, ŷ₀, Z and j. |

## Correspondence with the RTL

The equations map to `pams_jqr.v` as follows:
- Equation 7 is line 44 (`lowr`);
- Equation 8 is line 45 (`thr`);
- r_c and r_{c+1} are line 39 (`rc`, `rn`, with 2q mod 2¹² = 2562);
- qq is lines 31–35;
- Equation 9 is lines 48–51, with M = 10321339 and the split multiplier;
- Equation 10 is line 56.

The simulated register values agree with the reference model (see "How the checks were made").

## Not covered by this audit
- A complete analysis of non-canonical inputs (M1).
- A re-run of the 3329³ lemma enumeration.
- A formal (proof-assistant) verification of any statement. The proofs are hand proofs plus exhaustive computation.
- An independent human check of the proofs. It is recommended before submission.
