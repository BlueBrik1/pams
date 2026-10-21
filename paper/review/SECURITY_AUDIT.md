# Security audit (final manuscript review, 2026-10-21)

**Reviewer:** the AI system that produced the research and the manuscript. This is an internal review, not an external peer review.

**Sources:**
- `final/FINAL_SECURITY_STATUS.md` and `validation/SECURITY_VERIFICATION.md`;
- the PROLEAD and SILVER result files;
- the locally held full text of Cassiers and Standaert, *Provably Secure Hardware Masking in the Transition- and Glitch-Robust Probing Model*, TCHES 2021(2), cited as [CS21] below.

The HPC paper [CGLS20] itself was not available locally. Its composition result was checked through [CS21]'s restatement (Lemma 1, §5.2) and its §2 summary.

**Result: no fundamental problem found.** The whole-circuit claim is now stated as a conditional claim, with every dependency named. No security result had to be withdrawn. Two statements were sharpened: the transition limitation now cites the exact theorem conditions, and the PROLEAD scope now lists all its restrictions.

## 1. Proof-dependency chain

```
[F1] SILVER (formal, BDD): mapped HPC2 variants v0, v1 are glitch-robust 2-PINI (single execution, glitches, no transitions)
        |
        +-- [C1] identity: every gadget instance in the 24 final synthesis / P&R-input netlists is byte-identical to v0 or v1
        |         (final/models/gadget_identity.py; hash comparison: mechanical, low risk)
        +-- [C2] G-check: every routed gadget equals the verified gadget cell by cell after collapsing P&R buffers / resizing
        |         (compcheck.py, project code, on 40 routed netlists)
        v
[T1] published theorem: trivial PINI composition [CS20], extended to glitches [CGLS20]; restated as the
     glitch-robust composability lemma [CS21, Lemma 1, Section 5.2]
     preconditions:
       (P1) every gadget execution is glitch-robust t-PINI                      <- F1 + C1 + C2
       (P2) logic between gadgets is share-isolating (+ public data)            <- compcheck D (project code)
       (P3) connections respect share indices                                   <- compcheck P, O (project code)
       (P4) the gadget executions form a DAG                                    <- argued: only feedback is the accumulator,
                                                                                  through registers; acyclic when unrolled
       (P5) each gadget uses fresh, independent, uniform randomness           <- compcheck R (wiring, project code)
                                                                                  + ASSUMPTION A2 (ideal source)
        v
[R1] lane is glitch-robust 2-PINI  ==>  2-probing secure in the glitch-robust model
        provided  A1: input sharing uniform, canonical, independent across coefficients (ASSUMED, not checked)
                  A2: rnd ideal i.i.d. uniform every cycle (ASSUMED; rnd is a primary input)
                  A3: outputs cdec/dec go only to PINI-compatible consumers (ASSUMED)
                  A4: silicon matches the verified netlist (checked up to the routed netlist, logically only)
        +
[S1] PROLEAD (statistical): no leakage surviving confirmation on frozen pams/base (extensive) and on
     pams_jqr mapping 0 (focused), robust glitches + transitions; negative controls detected
        -- corroborates R1 empirically; it is not part of the proof
```

The step from [T1] to [R1] is a standard application of a published theorem. The step from the theorem's preconditions to "they hold for these netlists" rests on project code (`compcheck.py`), which has negative controls but has not been independently reviewed. That dependency is now stated in the paper (Section 4.1 claim, item iii; Section 4.2; Section 7).

## 2. Points examined

| # | question (task §4A) | finding |
|---|---|---|
| 1 | Exact property SILVER proves | Probing, NI and PINI secure at order 2 in the standard and robust (glitch) models; uniformity holds; robust SNI only at order 1. This is for a **single invocation** without transitions (`SECURITY_VERIFICATION.md` §3.1). The paper states this, and now says explicitly that SILVER covers a single execution without transitions. |
| 2 | Does the theorem apply to the gadget interfaces used? | Yes. HPC2 is used as a 3-share AND with Boolean input sharings. Some first-layer inputs have a constant-zero share, e.g. a = (y₀, y₁, 0). PINI is a simulation property over share indices and does not require uniform input sharings ([CS21] footnote 3: generic composition cannot assume independent input sharings). Constant shares are tie cells inside the gadget hierarchy and were part of the verified netlists. |
| 3 | Do the share domains satisfy the assumptions? | compcheck D, P and O report 0 violations on every final netlist. The arithmetic shares x_i form domain i. A2B is "free": y_i is share i of a Boolean sharing whose other shares are zero, a standard construction. Under A1, any 2 of the 3 arithmetic shares are uniform and independent of x, which is what turns 2-PINI into probing security. |
| 4 | Public vs secret classification | Public signals are c, d, Low_c, Θ_c, their bits and delayed copies, and the control. They depend only on (c, d) and vin/first/last. compcheck treats them as public, and the constant-time cone check (12 netlists) shows the control depends on no share and no random bit. |
| 5 | Registers, fan-out and reconvergence | In the glitch-robust model a probe extends through combinational logic back to registers and inputs. Extensions *between* gadgets, for example from an HPC2 output XOR into a downstream share-local XOR network, stay in one circuit share. [CS21 §2] states that "the propagation of glitches outside of gadgets causes no security issue thanks to the circuit shares principle", and Lemma 1 formalises this. Reconvergent fan-out inside one domain is share-isolating. Fan-out of one register to several gadgets is permitted by PINI composition: probes are simulated per share index, not per wire. |
| 6 | Fresh randomness | compcheck R: each `rnd` bit reaches exactly one gadget's r-port; there are 3 distinct bits per gadget, and nothing else mixes randomness. `audit_rtl.py` confirms that gadget g uses rnd[3g+2:3g] for all 40 gadgets. Independence and uniformity of the bits are **assumed** (A2). |
| 7 | Accumulator | uacc and ufin are HPC2 instances fed through a public mux. Its constant sharing (1, 0, 0) is share-isolating. The feedback runs through registers, so the unrolled execution graph is a DAG (P4). It is covered by the same argument in the glitch model, but is the reason the transition argument fails (Section 5). |
| 8 | Does composition apply to the complete design? | Yes, conditionally on P2, P3 and P5 as established by compcheck, and on A1–A4. |
| 9 | Differences between `pams_jqr` and the circuit of the original whole-lane tests | The changes j, q and r move registers within one domain or within public logic. Gadget network, gadget inputs (same values, same cycle), gadget count and random-bit allocation are unchanged (`FINAL_SECURITY_STATUS.md` §4). The composition argument therefore carries over, and its preconditions were re-checked on the final netlists. The **statistical** evidence differs: the final circuit had a smaller focused campaign. The paper says so, and now lists the specific differences. |
| 10 | Do synthesis and routing preserve the structure? | `keep_hierarchy` preserves gadget boundaries; C1 covers the 24 synthesis / P&R-input netlists; C2 covers the 40 routed netlists. The checks are logical, not electrical: couplings are out of scope. |

## 3. Evidence by category, as the paper now states it

| category | statement | where in the paper |
|---|---|---|
| Formally verified (established tool) | Mapped HPC2 variants v0 and v1 are glitch-robust 2-PINI (SILVER, single execution, no transitions). | Table 4; Section 4.2 Step 1 |
| Conditional circuit-wide result | Under A1–A3 and the correctness of the structural checker, the lane is glitch-robust 2-PINI, hence second-order probing secure in the glitch-robust model, by the published composition theorem. | Section 4.1 (claim, now conditional), Section 4.2 Step 2, abstract, conclusion, Section 7 |
| Machine-checked preconditions (project code) | D, R, P, O and G checks: 0 violations on 5 mappings, the P&R inputs and 40 routed netlists; negative controls detected; constant-time control (12 netlists). | Table 4; Section 4.2; Appendix D.2 |
| Statistical observations | PROLEAD: no leakage surviving confirmation; flagged maxima decay to 0.2–1.8; negative controls detected (margin up to 35 above the null on `pams_jqr`). | Section 4.3; Tables 5 and 20 |
| Assumptions | A1 (uniform canonical sharing, independent across coefficients), A2 (ideal fresh randomness), A3 (PINI consumers), A4 (silicon = netlist). | Section 4.1; Section 4.4; Section 7 |
| Unproven | Transition and glitch+transition robustness; physical side-channel resistance; security of any RNG; integration. | Section 4.4; Section 7 |

## 4. PROLEAD reporting (task §4C)

Checked against `FINAL_SECURITY_STATUS.md` §3 and `SECURITY_VERIFICATION.md` §4.3:
- simulation counts (2²⁰, 2¹⁸, 2¹⁶ for `pams_jqr`; 2²², 2¹⁶ and 2²⁰ for the frozen designs);
- probing-set counts (71,568; 493,055; 494,047; 67,130; 910; 459,212; 95,976; 887,642);
- maxima, null maxima, confirmations and negative controls.

Tables 5 and 20 agree with the sources.

**Corrections:**
- "Every flagged maximum decays to 0.4–1.8" was wrong. The smallest confirmation is 0.24 (frozen pams, order 2, 2¹⁶ screening). The text now reads 0.2–1.8 and points to Table 20.
- The limitations list of Section 4.3 now adds four points:
  - the final campaign covers only the mapping-0 netlist (gadget variant v0);
  - its exact size relative to the frozen campaign;
  - it has only one negative control;
  - no lane-level PROLEAD test was run on `base_jq`, and probing sets near `dvalid` were not tested at second order.
- Multiple-comparison effects were already explained (median null maximum ≈ log₁₀(N/ln 2)) and are correct.

The paper does not claim that `pams_jqr` received the frozen design's campaign, and it does not present non-detection as proof.

## 5. Transition issue (task §4D)

Checked against [CS21] §5.3, which gives the exact conditions:
- Theorem 2 / Corollary 2 require iterated transition-robust O-PINI gadgets, or transition-robust PINI gadgets **with no adjacent executions**;
- Proposition 4 relaxes adjacency for a structural gadget **all** of whose executions are parallel, if that gadget is iterated transition-robust PINI;
- HPC2 is shown not to be O-PINI (p. 149).

For PAMS:
- every gadget executes every cycle, so its executions are adjacent;
- the datapath gadgets' executions for different coefficients are parallel, with no path between them, but iterated transition robustness of the mapped HPC2 was not established, because SILVER covers glitches only;
- the accumulator's executions are serial (k → k + 2).

No published theorem is shown to apply. The paper previously summarised this in three bullets and now states the exact conditions. The status remains **unproven, with statistical evidence only**. No claim of transition robustness is made or implied.

Whether Proposition 4 could cover the datapath gadgets is a question for an expert reviewer. This review did not attempt a new proof. Even if it did, the accumulator would remain uncovered.

## 6. Corrections applied to the manuscript

1. **Section 4.1 claim.** It is now explicitly conditional, with conditions (i)–(iii), including the correctness of the project's structural checker. A sentence adds that no tool verified the whole lane and that whole-lane evidence is statistical.
2. **Section 4.2 Step 1, PROLEAD bullet.** It now reads "four back-to-back executions, statistical; SILVER covers a single execution without transitions" (previously: "when the gadget is executed every cycle").
3. **Section 4.2 Step 2.** It cites the composability lemma [CS21, Lemma 1], lists preconditions P1–P4, explains why glitches between gadgets are covered, argues P4 for the unrolled lane, and states that the checker is unreviewed project code.
4. **Section 4.3.** The confirmation range is corrected to 0.2–1.8, and the four scope limitations are added.
5. **Section 4.4, Transitions.** The exact conditions of Theorem 2, Corollary 2 and Proposition 4 are given, with which ones fail and why.
6. **Abstract, conclusion, Section 7.** The security sentence is now conditional, the checker is named as project code, and PROLEAD is called statistical evidence.

## 7. Recommended final wording (as now used in the abstract)

> We argue glitch-robust second-order probing security conditionally, under ideal randomness and canonical uniform input sharings: the argument combines SILVER-verified gadgets, the published PINI composition theorem and netlist-level precondition checks performed by our own structural checker. In focused PROLEAD simulations no leakage survives confirmation; this is statistical evidence, not a proof.

## 8. Remaining unproven properties and recommended external checks

- **Transitions:** transition and glitch+transition robustness are unproven, for both designs.
- **Randomness:** the RNG is excluded. With a PRNG the guarantee becomes computational, and the PRNG's own leakage is outside the analysis.
- **Physical security:** there was no TVLA, no coupling model, and nothing on the attacks on the FO comparison function itself (Hermelink et al. CCS 2024; Ranney et al. 2026).
- **Integration:** A1 and A3 are assumed.
- **Independent review of the composition argument:** an expert should confirm that the HPC composition theorem applies as stated here. The specific points are:
  - Boolean sharings with constant-zero shares;
  - public-dependent logic on share 0;
  - pipelined reuse in the glitch model.

  This review relied on [CS21]'s restatement, not on the HPC paper's own text.
- **Independent review or replacement of `compcheck.py`:** for example by an established tool. maskVerif was unavailable, and coco-alma was not attempted.
