# Figure and RTL audit (final manuscript review, 2026-10-21)

## 1. Verilog references

**Method:** `paper/scripts/audit_rtl.py` (new; output in `review/rtl_audit.json`) checks the manuscript sources against the frozen `final/rtl/pams_jqr.v` and `final/rtl/base_jq.v`.

| check | result |
|---|---|
| Listings are verbatim | All 17 listings are `\lstinputlisting` of the frozen files with their real line numbers, so they cannot drift from the source. Every range lies inside its file, and every `firstnumber` equals `firstline`. |
| Cited line ranges vs headings | All agree. The HPC2 listing shows lines 1–19, where lines 1–3 are comments and line 4 is the `(* keep_hierarchy *)` attribute; the heading "lines 4–19" refers to the module. |
| File sizes | `pams_jqr.v` 2,747 lines; `base_jq.v` 3,167 lines (as stated). |
| Named signals | Every `\sig{}` identifier exists in the RTL. The only exceptions are cell names (DFF_X1 …), netlist instance names (`_8799_`, `_8676_`), tool and script function names, design names, and naming-convention placeholders (xN, rN). The critical-path names `mh` and `fq` refer to the RTL groups `mh0..2` and `fq0..2`. |
| Gadget count and placement | 40 `hpc2` instances in lines 1500–1537 (`pams_jqr`); 57 in `base_jq`. |
| Randomness slices | For all 40 gadgets, gadget g uses `rnd[3g+2:3g]`, contiguously and without overlap. The instance order matches Appendix B.7. |
| Delay registers | 1,190 assignments in lines 1538–2729, as stated. 782 distinct flip-flops after synthesis (frozen Phase XIV evidence, not re-derived). |
| Widths | 12-bit shares; 11-bit c; 14-bit y_i, Low_c and Θ_c; 48-bit partial-product registers with ≤ 30 significant bits; `rnd` 120 / 171 bits. All consistent with the RTL. |
| Stage numbering and latency | Confirmed by the new RTL trace (Table 16): x_q at stage 1, x_r at 2, partial products and Low_c at 3, s_p at 4, y_i and Θ_c at 5, first gadget output at 7, `cdec` with `cvalid` at 31 (and at no other stage), `dvalid` at 35. Initiation interval 1. |
| Critical paths | The text in Section 6.3 and Appendix C.5 agrees with `timing.rpt` (via `data/critpath.json`) and with Table 21 (Q-net names resolved from `final.v`): 1.2 ns PAMS `x1r[5]→ml1[23]`, 21 cells; baseline `x0r[9]→mh0[31]`. |
| One-to-one mapping claims | Section 3.3, Appendix C.1 and `CROSS_LAYER_TRACEABILITY.md` state that the RTL-to-gate mapping is many-to-one for combinational logic. Only register names, gadget boundaries and domain connectivity are traced. No prose claims a one-to-one correspondence where synthesis restructured logic. |

**Cross-layer chain** (equation → RTL → gates → placement → cost): checked in `CROSS_LAYER_TRACEABILITY.md` (area roll-up summed from `data/resources.json`) and in Table 24. No inconsistency was found.

## 2. Figure accuracy

| figure | provenance | accuracy check |
|---|---|---|
| 1 | reference model | Plotted values come from `models/pams.py`; the boundaries are consistent with Proposition 1. |
| 2 (datapath, conceptual) | hand TikZ | Signal names, widths and stages match the RTL and the Table 16 trace. Labelled conceptual. |
| 3 (bit-1 slice) | Graphviz from `mapped.json` | Regenerated. The pins match the text in Appendix C.3 (ug111 a = (y0, y1, 0), b = (y0, 0, y2); ug134 a = r106/r108/r110, b = ug111 shares 1–2 + x114). |
| 4 (placement) | DEF of T1.2 s1 | Unchanged; classification and areas from `data/placement_classes.json`. |
| 5 (domains, conceptual) | hand TikZ | **Semantic error found and fixed:** the "public → share 0" arrow pointed into domain 2's F₁₄(x₂) box. It now enters domain 0. |
| 6–11, 13 | matplotlib from frozen JSON/CSV | Values cross-checked in RESULTS_AUDIT. Figure 6's caption states n = 1 for the baseline at 1.1 ns. |
| 12 (critical paths) | `timing.rpt` | Matches the text. |
| 14 (HPC2, conceptual) | hand TikZ | Redrawn. The wiring was re-derived from RTL lines 10–14 for share 0. The footnote on random-bit use was ambiguous and is now exact. |
| 15 (mapped HPC2) | Graphviz from `mapped.json` | 63 cells (30 DFF_X1, 15 AND2_X1, 6 XOR2_X1, 12 XNOR2_X1); regenerated, identical cell list. |
| 16 (layouts) | OpenROAD `save_image`, T1.2 s1 | Unchanged; same scale. |

## 3. Legibility and overlaps (including the author's request: "ensure no overlapping elements" in the arrow-heavy diagrams)

All pages were rendered at 60 dpi on contact sheets, and the diagram pages at 150–170 dpi, then inspected. Changes:

- **Figure 2.** Share 0 is now drawn as the bottom share lane, directly above the public lane. The Low_c arrow is a short segment that crosses no other lane; previously it ran diagonally through the share-1 row.
- **Figure 3.** The pin letters on edges piled up where several edges converge. They were replaced by an edge style (solid = port a / input A, dashed = port b / input B), which the caption explains. Spacing was raised (`nodesep` 0.1 → 0.35, `ranksep` 0.3 → 0.7) with spline routing, and no edge crosses a node. Orthogonal routing was tried and rejected, because it merged edges into shared corridors.
- **Figure 5.** The public box and arrow were moved (see the semantic fix above), which removes the overlap of the "to share 0" label with the domain-2 column.
- **Figure 14.** It was redrawn on an orthogonal grid. Previously the `ra[0]` and `rb[0]` boxes overlapped, the ⊕ node sat under the `rbr` box, several arrows cut through the middle AND, and two column headers collided. The new drawing has:
  - no overlapping boxes, labels or arrowheads;
  - separated XOR inputs.

  Because `ra[0]` feeds all three ANDs, one crossing is topologically unavoidable. It is drawn as a bridge.
- **Figure 15.** Spacing was raised (`nodesep` 0.12 → 0.35, `ranksep` 0.35 → 0.7), and no edge passes through a cell. The remaining edge crossings are the gadget's real cross-share wiring (b_j and r_ij reach other shares' refreshes), not layout artefacts.

## 4. Remaining (unresolved) figure and provenance items

- **Figure 3:** one dashed edge (ug111 → x116) passes close to, but not through, the r110 node.
- **Figure 15:** edge crossings remain, because they are inherent to the circuit.
- **Table 21 (all 42 P&R runs):** scaled to text width, about 7 pt. It is legible at print size, but dense.
- **Figures 4, 12, 16:** they use the T1.2 s1 run, whose `final.def` and `final.v` are gitignored and not hashed in `final/PUBLICATION_MANIFEST.md`. Their SHA-256 values are recorded in `FIGURE_PROVENANCE.md`.
- **Conceptual figures (2, 5, 14):** they are hand drawings from reading the RTL. They are labelled conceptual and have been checked by this review only.
