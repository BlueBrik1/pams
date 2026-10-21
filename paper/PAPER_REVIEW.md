# Adversarial self-review of the manuscript

> **Superseded in part by the final review (2026-10-21).** The final technical review and publication freeze are recorded in `review/`. Start with `review/FINAL_REVIEW_SUMMARY.md`; it lists the resolved findings, unresolved issues, publication limitations and frozen claims. Where this file and `review/` differ, `review/` is authoritative. In particular, the bibliography status below is superseded by `review/BIBLIOGRAPHY_AUDIT.md`: the HOPE-MLKEM pages and DOI and the Hermelink pages are now filled in, and the two uncited entries were removed. This file records the earlier self-review of the first complete draft.

The manuscript was reviewed against the frozen evidence (`final/`, tag `pams-publication-freeze-v1`) and against the constraints of the manuscript directive. The review was done by the same AI system that wrote the paper (see `AI_USAGE_DISCLOSURE.md`), so it is **not** an independent review. A human reader should repeat at least the checks marked ★.

## 1. Checks performed

### Numbers

- ★ Every headline number in the abstract, introduction, Table 6 and the conclusion was compared with `final/runs/pnr_stats.json`, `competitors/runs/cbench.json`, `final/data/gadget_breakdown.csv` and `final/FINAL_RESEARCH_VERDICT.md`. These include the gadgets, the random bits, the synthesized, routed and die areas, the periods, the p-values, the flip-flop and buffer counts, the latency and the area-delay product.
- The area decomposition (Tables 7 and 19, `CROSS_LAYER_TRACEABILITY.md`) is generated from the mapped netlists by `scripts/resources.py`, and the groups add up to the synthesized total exactly.
- The P&R table (Table 21) and the competitor table (Table 23) are generated from the JSON files by `scripts/tables.py`. They were not typed by hand.
- The critical-path text (Section 6, Appendix C.5) was compared with `timing.rpt` through `data/critpath.json`: cell count, launch and capture registers, clock latency, data delay and slack.

### Mathematics

- ★ The proof of Proposition 1 was re-derived. Its bounds (member Z ≤ Θ − 1, non-member Z ≥ Θ + 1) were re-checked numerically for every (c, d). Both bounds are attained, so the margin is tight in both directions.
- The K = 13 counterexample (Remark 1, Appendix A.9) was recomputed. It collides only in the share-wise floor model, and the text says so.
- The closed forms for Low_c and Θ_c were asserted against the definitions:
  - for all 48 rows of Table 10 (`scripts/appendix_data.py`);
  - for all 3,120 (c, d) pairs in the frozen `check_pams`.

### Examples and RTL listings

- ★ The worked examples E1–E4 (Tables 2 and 9) were computed by the reference model and by simulating the frozen RTL. `scripts/examples.py` asserts that every register value agrees. The cycle trace of E1 (Table 16) is asserted register by register in `scripts/appendix_data.py`. In that trace the filler coefficients decide 0, so the decision of 1 at stage 31 can only be E1's.
- The Verilog listings are pulled from the frozen files with `\lstinputlisting` and their real line numbers. Every line range cited in the text was checked against the file.

### Claim discipline (directive constraints)

| constraint | where enforced |
|---|---|
| The area result applies to the verification lane only, not to an ML-KEM accelerator | abstract, introduction, Section 7 "Effect on scope", conclusion |
| No statistically established speed advantage is claimed | abstract ("no general speed advantage is demonstrated"), Section 6.3; the 1.2 ns p = 0.0006 is explicitly limited to the layout distributions of one netlist per design |
| A single valid baseline run at 1.1 ns is not presented as a distribution | Table 6 marks it "(1/7 valid)" and "single run"; Section 6.3 |
| Simulated leakage tests are not presented as physical security | Section 4.3 "What this does and does not show"; Section 4.4; Section 7 |
| No one-to-one gate mapping is invented | Section 3.3 and Appendix C.1: "the mapping is many-to-one"; `CROSS_LAYER_TRACEABILITY.md` "Where the layers do not line up" |
| Conceptual diagrams are not labelled as circuits | the captions of Figures 2, 5 and 14 say "conceptual"; Figures 3 and 15 are the extracted netlists |
| No venue, acceptance or affiliation | the title page placeholder; "manuscript draft"; the comment in `main.tex` |
| No copyrighted full texts | `refs/*.txt` (extracted paper texts) are gitignored in the research repository and not used in `paper/` |

### Layout

- Every page of the PDF was rendered with `pdftoppm` and inspected, before and after the corrections below.
- The final log has 0 undefined references and 0 undefined citations.
- The overfull boxes that remain are each under 5 pt, apart from one 23.7 pt box in the title block, which is invisible in the rendered page.

## 2. Corrections made during the review

### Factual corrections

- **Area table.** The resource-table values were corrected to the generated ones. An earlier hand-typed version had wrong group areas.
- **Critical path.** The cell count is 21, not 22.
- **Constant M.** The binary expansion of M was corrected to `100111010111110110111011`.
- **Partial products.** Each has at most 30 significant bits, not 45.
- **Baseline listing.** It ends at line 46.
- **Cost of the modulus switch.** It was corrected to 3,528 µm².
- **Routed simulation.** It is labelled "2.0 ns, seed 1".
- **Seed-difference statement.** Corrected (seeds 1–2 and 2–3, 84 %) and changed to "about 70× the seed range".
- **XNOR description.** The ABC XNOR realization was described accurately.
- **E3 commentary in Appendix A.11.** An incorrect statement about which j attains the member bound was replaced: for E3, Z = 12 − j.
- **Traceability area roll-up.** It is now summed from `data/resources.json`. A hand-typed draft had wrong baseline values.
- **The 1.2 ns timing sentence.** It was rephrased from "faster in every seed" to "lower period in every seed", with the scope of the statistic stated.

### Layout corrections

The following were fixed:

- overflowing equations (2), (5) and (8);
- the predicate block;
- the notation table, Table 2 and Table 3, which were too wide;
- clipped or overfull tables: the headline, resource, PROLEAD, region, stage, provenance and traceability tables;
- overlapping labels in Figures 1, 2 and 5;
- Figure 3, which was too small;
- the axis-label overlap in Figure 12;
- listing frames that ran into run-in headings;
- a missing provenance table.

## 3. Unresolved issues and residual uncertainty

### Bibliography

- All 38 BibTeX entries (36 cited) correspond to real works that were looked up during the research phases. Fields that could not be confirmed were left out. Specifically, the following are not given:
  - page numbers for SILVER (Knichel et al., ASIACRYPT 2020);
  - a DOI for OpenROAD (Ajayi et al., DAC 2019);
  - a DOI for Hermelink et al. (CCS 2024), where the ePrint number is given instead;
  - page numbers for the 2026 HOPE-MLKEM article (Camacho-Ruiz et al., TCHES 2026(2)).
- ★ These entries should be completed from the publishers' pages before submission.
- Two entries are not cited and therefore do not appear in the PDF: `berthet2025` and `coron2024rej`.
- Prior-art coverage is incomplete, as Section 7 states. Only the abstract of Buschkowski et al. (2026) was accessible, and one 2026 first-order FPGA work could not be retrieved.

### Inaccurate comments in the frozen RTL

These comments are not repaired, because the frozen artifacts must not change. The manuscript describes the actual behaviour.

- `final/rtl/pams_jqr.v` line 1 says the file was "generated by masked_verification/models/gen.py". It was generated by `competitors/models/cgen.py`, which imports the building blocks of `gen.py`. The comment is inherited from the frozen template. Section 3.2 and Appendix B.1 state the actual generator.
- Line 2 cites the HPC2 gadget as "Cassiers et al. TCHES 2021". HPC2 was introduced in *Hardware Private Circuits* (IEEE Transactions on Computers 70(10), 2021); the TCHES 2021 paper by the same authors is the transition-robustness work. The paper cites the IEEE TC article for HPC2.
- Line 46 labels the modulus switch "stage 2". In the final variant (q) the multiplier is split across stages 3 and 4. The manuscript uses the actual register stages, verified by simulation (Table 16).

### Earlier phase reports

- The Phase XIII reports describe PAMS's critical path as the public window logic (`c0 → low`). That holds in **synthesis** STA, where `lowrq` is the worst register group at 1.033 ns. After routing at 1.2 ns, however, the worst path in both designs is a share-wise multiplier stage (`x1r[5] → ml1[23]`). At 2.0 ns and 1.1 ns it is PAMS's public logic again. The paper reports all three (Section 6.3 and Appendix C.5). The statements are compatible, but a reader of the Phase XIII report alone could miss the target dependence. Following the directive, the Phase XIV results take precedence.

### Reproducibility

- The T1.2 s1 run's `final.def` and `final.v`, used by Figures 4, 12 and 16, are gitignored and are not hashed in `final/PUBLICATION_MANIFEST.md`, which hashes the T2.0 s1 outputs. Their hashes are recorded in `FIGURE_PROVENANCE.md` instead.
- PROLEAD 3.1.0 is unseeded in hardware mode. A rerun gives different (statistically equivalent) maxima.

### Limits of the evidence (restated from Section 7)

- one library, one flow, one utilization;
- no silicon;
- no power measurement;
- no transition robustness;
- randomness generation is excluded from the area;
- canonical input shares are assumed, not checked.

### Authors

- The authorship, affiliations and the human contributions are open. See the checklist in `AI_USAGE_DISCLOSURE.md`.

## 4. Questions a skeptical reviewer is likely to ask, with where the paper answers them

- **"Is the baseline a straw man?"** Section 2.3 "Choice of baseline", Section 5.1, and the competitor study (Appendix D.7, Table 23). Each of the 21 designs was synthesized under the same flow, and the strongest conventional one was selected.
- **"Is the area saving just pipelining?"** Table 7 and Appendix C.7. Most of the saving is gadgets (−3,066 µm²), and PAMS pays +873 µm² for public logic.
- **"Do seeds give independent samples?"** No. Section 5.3 says so, and the statistics are read in that sense.
- **"Does PROLEAD prove security?"** No. Section 4.3 and Section 7.
- **"Is the construction new mathematics?"** No. Section 7 "Architectural, not mathematical, novelty".
