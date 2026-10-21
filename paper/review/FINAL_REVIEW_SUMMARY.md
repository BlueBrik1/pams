# Final review summary and publication freeze (2026-10-21)

**What this is.** A final technical and editorial review of the PAMS manuscript, carried out by the AI system that produced the research and the paper (Claude Code, Claude Opus 5.5).

It is an **internal** review. It is **not**:
- independent academic validation;
- peer-reviewed acceptance;
- formal certification;
- confirmation of global novelty;
- evidence of physical side-channel resistance.

That no problem was found where none is reported does not show that none exists.

**Scope.** Hardware, RTL and frozen research results were not modified. Only files in `paper/` were edited.

| audit | file | verdict |
|---|---|---|
| Mathematics | `MATHEMATICS_AUDIT.md` | **Qualified pass**: no error in the construction or proofs within scope. Scope wording and one multiplier statement corrected. |
| Security | `SECURITY_AUDIT.md` | **Conditional claim, justified as stated.** No fundamental problem found. Claim made explicitly conditional. Transition limitation and PROLEAD scope sharpened. |
| Novelty | `NOVELTY_AUDIT.md` | **Classification B unchanged**, "to our knowledge". No identical architecture found in one bounded check. Two full texts still inaccessible. |
| Results | `RESULTS_AUDIT.md` | **All headline values confirmed** from frozen data. Six labelling and interpretation corrections. |
| Figures and RTL | `FIGURE_AND_RTL_AUDIT.md` | **RTL references correct.** One semantic figure error fixed (Figure 5). Arrow-heavy diagrams (2, 3, 5, 14, 15) redrawn without overlaps. |
| Bibliography | `BIBLIOGRAPHY_AUDIT.md` | 36 entries, all cited. Three entries completed from external metadata, two uncited removed, header overclaim fixed. Some fields still unverified. |

## Resolved findings (identified and corrected)

**Mathematics**
1. The multiplier at non-canonical inputs. The paper said it was "wrong for x_i ∈ [3329, 4005]"; it is wrong only at 3329 and 4005. The paper also implied that Lemma 1 needs canonical shares, which it does not (Section 3.1 F, Section 7).
2. "Independent machine proof" / "alone is a complete proof" became "a computational proof for the stated contract, assuming the script is correct" (Section 3.1 F, Appendix A.7).

**Security**

3. The Section 4.1 claim is now explicitly conditional on (i) ideal randomness, (ii) uniform canonical input sharings independent across coefficients, and (iii) the correctness of the project's structural checker. The paper states that no tool verified the whole lane. The same conditional wording is used in the abstract, the conclusion and Section 7.
4. The composition step now names the composability lemma [CS21, Lemma 1], its preconditions, why glitches between gadgets are covered, and the DAG argument for the unrolled lane. It says the checker is unreviewed project code.
5. The PROLEAD confirmation range was given as 0.4–1.8; the correct range is 0.2–1.8.
6. The PROLEAD scope now states four further limits:
   - the `pams_jqr` campaign covers mapping 0 only;
   - its size relative to the frozen campaign;
   - it has one negative control;
   - there was no lane test of `base_jq`, and no second-order sets near `dvalid`.
7. The transition limitation now gives the exact conditions of [CS21] Theorem 2, Corollary 2 and Proposition 4, and which of them fail.
8. The gadget-level PROLEAD bullet now says "four back-to-back executions" (previously "executed every cycle"), and that SILVER covers a single execution.

**Novelty**

9. Abstract: "a new protected datapath" became "to our knowledge, has not been described before".
10. D'Anvers et al. 2022 is now credited as prior art for share-wise switching to a power-of-two modulus inside a masked comparison.
11. The limitations record this review's retrieval attempt and its result.

**Results**

12. The Table 6 caption said "7 valid seeds at each target", which is false at 1.1 ns. It now gives the actual counts.
13. Area at 1.1 ns: 19.6 %, with its basis stated. The p-value is restricted to 2.0 and 1.2 ns and scoped to the layout distributions of one netlist per design in one flow.
14. The area-delay product is now given per target (22.5 / 20.3 %), with the 1.1 ns value (19.4 %) labelled as a single observation.
15. Router runtime and convergence are explicitly not circuit speed.

**Figures**

16. Figure 5: the public arrow pointed into domain 2. It now enters domain 0.
17. Figure 2: share 0 is drawn next to the public lane, so the Low_c arrow crosses no lane.
18. Figure 3: edge labels were replaced by line styles, with wider spacing; no edge crosses a node.
19. Figure 14 was redrawn: no overlapping boxes, labels or arrowheads, one bridged crossing, and an exact footnote on random-bit use.
20. Figure 15: wider spacing; no edge crosses a cell.

**Bibliography**

21. Added:
    - HOPE-MLKEM pages and DOI;
    - D'Anvers 2023 DOI;
    - Hermelink et al. pages.
22. Removed the two uncited entries.
23. Corrected the bib header's verification claim.

**Records**

24. New appendix tables (previous session) and new review scripts (`audit_math.py`, `audit_results.py`, `audit_rtl.py`) make the checks repeatable.

## Unresolved issues (need external review, experiments, sources or author confirmation)

- **Authorship.** Names, affiliations and the human contribution are placeholders (`AI_USAGE_DISCLOSURE.md` checklist). Author confirmation is required.
- **Independent expert review of the security argument.** An expert should confirm that the HPC/PINI glitch-robust composition theorem applies as stated: Boolean sharings with constant-zero shares, public-dependent share-0 logic, and pipelined reuse. This review relied on [CS21]'s restatement, not the HPC paper text.
- **Structural checker.** `compcheck.py` is unreviewed project code. Independent review, or re-checking with an established tool (maskVerif or coco-alma were not available or not attempted), is recommended.
- **Transitions.** Transition and glitch+transition robustness are unproven. Whether [CS21] Proposition 4 could cover the datapath gadgets is open, and the accumulator would remain uncovered in any case.
- **Physical security.** There was no TVLA on hardware, no coupling model, and nothing on FO-comparison attacks.
- **Mathematics.**
  - A complete analysis of non-canonical inputs is missing.
  - An independent human check of the proofs is recommended.
  - The 3329³ enumeration was not re-run in this review.
- **Prior art.**
  - Buschkowski et al. (ePrint 2026/1265) and PeerJ CS article cs-4003: full texts refused (HTTP 403).
  - MPC, FHE and LWE-decoder literature was not searched systematically.
  - The patent search was keyword-based.
- **Bibliography.**
  - Not confirmed: SILVER pages and DOI, OpenROAD DOI, and the DOM and ABC pages.
  - 18 entries are at verification level C (frozen documents, not re-verified).
- **Reproducibility.** The T1.2 s1 DEF and netlist (Figures 4, 12, 16) are gitignored and not in the publication manifest. Their hashes are in `FIGURE_PROVENANCE.md`.
- **Frozen-document inaccuracies.** These were not repaired, by design:
  - the "3104" typo and the "[3329, 4005]" phrasing in `final/FINAL_MATHEMATICAL_SPECIFICATION.md`;
  - the RTL header comments (generator name, HPC2 venue, "stage 2" label), already listed in `PAPER_REVIEW.md`.

## Publication limitations (claims that are conditional and must not be overstated)

- **Security.** It is a conditional, composition-based claim in the glitch-robust probing model only. It assumes ideal randomness, uniform canonical input sharings and PINI consumers, and relies on project-code precondition checks. PROLEAD evidence is statistical and, for the final circuit, comes from a focused campaign on one netlist.
- **Scope of the area result.** The area result concerns a ciphertext-verification lane, not a complete ML-KEM accelerator or decapsulation core.
- **Speed.** Clock periods are comparable; there is no general speed advantage. The 1.2 ns separation (p = 0.0006) is about 11 ps and is limited to layouts of one netlist in this flow.
- **1.1 ns.** The routability difference (7/7 vs 1/7) is a bounded physical-design observation at 50 % utilization in one flow. The baseline timing there is a single run.
- **Evaluation.** Everything uses one technology (Nangate45) and one open flow. These are EDA estimates only: no silicon and no power measurement.
- **Novelty.** "To our knowledge", within a targeted search, as an architectural combination of published components, not a new mathematical mechanism.
- **K = 13.** The 14-bit requirement is a lower bound only in the share-wise floor model.

## Frozen claims (what the final PDF supports)

1. **Mathematical.**
   - For q = 3329, d ∈ {4, 5, 10, 11}, every c and canonical 3-share inputs, the decision [Z < Θ_c] equals [Compress_d(x) = c].
   - The proof rests on CGTZ23 Lemma 2 plus the gap argument (g = 4). It is confirmed by exhaustive (x, j, c, d) enumeration, with tight margins −1 and +1.
   - The public constants Low_c and Θ_c have the stated closed forms for all 3,120 (c, d).
2. **Architectural.**
   - One d-independent 14-bit share-wise switch with public interval anchoring and a per-coefficient public-threshold comparison.
   - Implemented as a three-share HPC2 lane at one coefficient per cycle for all ML-KEM parameter sets.
   - 40 HPC2 gadgets and 120 fresh random bits per cycle, against 57 and 171 for the strongest conventional (Simple) lane built under the same gadget, flow and optimizations.
3. **Security.**
   - The mapped HPC2 gadget is glitch-robust 2-PINI (SILVER).
   - Under the stated assumptions and checker correctness, the lane is glitch-robust 2-PINI by published composition, hence second-order probing secure in the glitch-robust model.
   - No PROLEAD leakage survived confirmation at the stated simulation counts.
   - Transition robustness and physical security are not claimed.
4. **Performance** (Nangate45, matched open flow, 7 placement seeds per target, 50 % utilization):
   - routed standard-cell area −19.5 % (2.0 and 1.2 ns; −19.6 % at 1.1 ns);
   - estimated die area −18.5 %;
   - synthesized area −19.3 %;
   - comparable clock periods;
   - every PAMS run smaller than every baseline run;
   - at 1.1 ns, PAMS routed DRC-clean in 7/7 runs, the baseline in 1/7.

## Assessment

**Ready for external expert review: yes.** The manuscript is complete, internally consistent with the frozen evidence, and explicit about every conditional claim and open issue.

**Not yet ready for submission to a selected venue.** The reasons are not a technical defect found in this review. They are:
- authorship and the human-contribution statement are unconfirmed placeholders;
- the security argument's reliance on project-code precondition checks, and its application of the published composition theorem, should be confirmed by an independent expert;
- some bibliographic fields need completion;
- the target venue's AI-use policy must be checked.

No substantive problem was found that would require changing the frozen hardware.

## Freeze record

| item | value |
|---|---|
| Final PDF | `paper/PAMS_paper.pdf` |
| Pages | 48: main text 1–20, references 20–22, Appendix A 23–28, B 29–37, C 37–42, D 42–48 |
| Content | 25 numbered equations, 25 tables, 16 figures, 36 references (0 undefined) |
| SHA-256 (PAMS_paper.pdf) | `a411539f2649c366b1555d5d4f66d2d7073c6d1ed82f8152349e89e5c54fba0e` |
| Compilation | `bash paper/scripts/build.sh` (pdflatex + bibtex + 2× pdflatex, TinyTeX / TeX Live 2026); `-f` first regenerates data-derived tables and figures |
| Git | paper-only commit tagged `pams-paper-freeze-v1` (annotated) in the research repository; not pushed |
| Research snapshot (unchanged) | tag `pams-publication-freeze-v1`, commit `d033f76` |
