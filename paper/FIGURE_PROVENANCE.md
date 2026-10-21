# Figure provenance

Every figure in `PAMS_paper.pdf` is listed below with its source artifact, how it was made, and what kind of figure it is. Paths are relative to `phase2/masked_verification/`. This is the extended form of Table 25 (Appendix D.9).

## Figure types

- **Conceptual:** drawn by hand in TikZ from reading the RTL. It shows structure, not a synthesized circuit, and each caption says so.
- **Extracted gate level:** generated automatically from the Yosys/ABC mapped netlist. Every node is a real cell or a real port.
- **Physical (EDA data):** drawn from OpenROAD output: DEF placement, timing reports, or the OpenROAD renderer itself.
- **Graph from data:** a matplotlib plot of measured numbers.

No figure was produced with an AI image generator. No conceptual figure is labelled as a synthesized circuit.

## Figures

| # | label | content | source artifact(s) | method | design(s) | type |
|---|---|---|---|---|---|---|
| 1 | `fig:boundaries` | Z near the wrapped interval I₀ (d = 4) and interval a₁ = 105, for j = 0, 1, 2 | `models/pams.py` (compress, starts, low_formula) | `generate_figures.py math` (`fig_math`), matplotlib; points also in `paper/data/math_fig.json` | math | graph from data |
| 2 | `fig:datapath` | lane datapath: share lanes, public lane, kernel, accumulator | `final/rtl/pams_jqr.v` (read by hand) | TikZ, `figures/architecture/datapath.tex` | `pams_jqr` | conceptual |
| 3 | `fig:slice` | bit-1 gadgets ug111/ug128/ug134 and their 3-level fan-in | `competitors/runs/syn_pams_jqr_p0/mapped.json` | `generate_figures.py gates` (`dot_slice`): fan-in traversal of the Yosys JSON, Graphviz `dot`; source `figures/gates/slice_bit1.dot` | `pams_jqr` mapping 0 | extracted gate level |
| 4 | `fig:placement` | every placed cell, coloured by functional class; worst path | `final/runs/pnr_{pams_jqr,base_jq}_T1.2_s1/final.def`, `timing.rpt`; platform LEF cell sizes | `generate_figures.py physical` (`fig_placement`): DEF COMPONENTS parsing, classification by instance and master name (`paper/data/placement_classes.json`), matplotlib | both | physical (EDA data) |
| 5 | `fig:domains` | share-domain structure and composition argument | the security argument (Section 4) | TikZ in `sections/security.tex` | — | conceptual |
| 6 | `fig:area` | synthesized and routed standard-cell area | `competitors/runs/cbench.json` (synthesis, 5 mappings), `final/runs/pnr_stats.json` (routed, 7 seeds × 3 targets) | `generate_figures.py results`, matplotlib | both | graph from data |
| 7 | `fig:die` | estimated die footprints to scale | `final/runs/pnr_stats.json` (die area at 50 % utilization) | same | both | graph from data |
| 8 | `fig:gadgets` | HPC2 gadgets per lane by function | `final/data/gadget_breakdown.csv` | same | both | graph from data |
| 9 | `fig:random` | fresh random bits per cycle | `final/data/gadget_breakdown.csv` (3 bits × gadgets) | same | both | graph from data |
| 10 | `fig:timing` | achieved clock period of every P&R run | `final/runs/pnr_stats.json` | same | both | graph from data |
| 11 | `fig:adp` | area vs. achieved period, iso-ADP lines | `final/runs/pnr_stats.json`, `competitors/runs/cbench.json` | same | both | graph from data |
| 12 | `fig:critpath` | per-cell delay of the worst routed path | `final/runs/pnr_{pams_jqr,base_jq}_T1.2_s1/timing.rpt`; Q-net names from `final.v` | `generate_figures.py physical` (`fig_critpath`): report parsing (`paper/data/critpath.json`) | both | physical (timing data) |
| 13 | `fig:routing` | routing outcome by seed and target | `final/runs/pnr_stats.json` | `generate_figures.py results` | both | graph from data |
| 14 | `fig:hpc2` | HPC2 gadget structure for output share 0 | `final/rtl/pams_jqr.v` lines 4–19 (read by hand) | TikZ in `appendices/circuit_walkthrough.tex` | `hpc2` | conceptual |
| 15 | `fig:hpc2-mapped` | complete mapped HPC2 module: 63 cells | `competitors/runs/syn_pams_jqr_p0/mapped.json`, module `hpc2` | `generate_figures.py gates` (`dot_hpc2`): full module export, Graphviz; cell list in `paper/data/hpc2_mapped_cells.json`; source `figures/gates/hpc2_mapped.dot` | `hpc2` variant v0 | extracted gate level |
| 16 | `fig:layout` | routed layouts, both designs | `final/runs/pnr_{pams_jqr,base_jq}_T1.2_s1/final.def` + Nangate45 tech/macro LEF | `generate_figures.py layout`: OpenROAD `save_image -resolution 0.1` headless (`scripts/layout_image.tcl`), downsampled ×2 | both | EDA layout export |

## The figures the directive requests

| requested | figure |
|---|---|
| area | 6 |
| die | 7 |
| timing | 10 |
| gadgets | 8 |
| randomness | 9 |
| area-delay | 11 |
| placement | 4 |
| critical paths | 12 |
| routing robustness | 13 |
| real mapped-gate figure | 3 and 15 |
| real OpenROAD layout | 16 |

## Notes on each extracted figure

- **Figure 3.** Only the cells inside the fan-in cone of the three named gadgets are shown, to depth 3. Some internal nets are labelled "(ABC-internal net)" because ABC renamed them, so no RTL name survives. Synthesis merged and transformed logic: the figure shows the mapped cells as they are, and the text does not claim a one-to-one equation-to-gate correspondence. Since the final review, the receiving pin is encoded by edge style (solid = gadget port a / cell input A, dashed = b / B) instead of edge labels, and Graphviz spacing was widened so that no edge crosses a node. The netlist content is unchanged.
- **Figures 2, 5 and 14 (conceptual).** These were revised in the final review (`review/FIGURE_AND_RTL_AUDIT.md`):
  - Figure 2 draws share 0 next to the public lane, so the Low_c arrow crosses no other lane.
  - Figure 5's public arrow now enters domain 0. It previously pointed into domain 2.
  - Figure 14 was redrawn without overlaps from RTL lines 10–14.
- **Figure 15.** Graphviz spacing was widened in the final review, so that no edge crosses a cell. The cell list is unchanged (`data/hpc2_mapped_cells.json`).
- **Figure 4.** Tap and filler cells are omitted. Buffers include the OpenROAD timing-repair buffers (`+ SOURCE TIMING`), which are drawn last. The two panels share one scale.
- **Figure 12.** The first bar is the clock network latency at the launch flip-flop. The cell names are those in `timing.rpt`. There are 21 combinational cells on the PAMS path.
- **Figure 16.** OpenROAD's own renderer at 0.1 µm per pixel, halved for the document. Both panels are at the same scale, so the PAMS image is 0.903 times the width of the baseline image.

## SHA-256 of the figure inputs

These inputs were used for the figures in this build. Hashes were computed on 2026-10-21.

| file | sha256 |
|---|---|
| `models/pams.py` | `ea6dcb55112eae9cf1b75febe3f828705eca89c5dbf4855ea07fef5ace9b2644` |
| `final/rtl/pams_jqr.v` | `804fd73a263baacb371033015171519213d84cfa817dee9ba6ae2b3760ba0e7f` |
| `final/rtl/base_jq.v` | `e573286a2b1b4ead019699538be21b454bab359fdaeb4f62e273d137458f6533` |
| `competitors/runs/syn_pams_jqr_p0/mapped.json` (gitignored) | `044e72aaad2931afac24a056ad3e9debbc5966295bab9797252e96612c28e1d3` |
| `competitors/runs/cbench.json` | `6b0bb89f2565b32013423a72aed1592bdd9389c8e4cde74b29b7e6881afe0a2f` |
| `final/runs/pnr_stats.json` | `75688e772f772aea141eac5d53728d8fa7aa7143063d677f332063889eaa4518` |
| `final/data/gadget_breakdown.csv` | `8ef16eac3bb1aa59dee724f1689f60ab86cd90c08386ad9ddbc95ce013936106` |
| `final/runs/pnr_pams_jqr_T1.2_s1/final.def` (gitignored) | `1b02597357e50fee6c7739b41ae9d67716554efccab420ebd032e7d6854d4e79` |
| `final/runs/pnr_base_jq_T1.2_s1/final.def` (gitignored) | `0431eeba6b634ca75d65ba6d1507ea9e2504652b5a6f1376ab6ffbb94a060dd8` |
| `final/runs/pnr_pams_jqr_T1.2_s1/final.v` (gitignored) | `50be7b9b46ce6217d3d69a0bf4eb8814904ecf25e76d396eb3b17c9ebbcefd57` |
| `final/runs/pnr_base_jq_T1.2_s1/final.v` (gitignored) | `90501b058cff8c4fdff83f8433999d90a11171e4a579dfa9f31ebb89512b746d` |
| `final/runs/pnr_pams_jqr_T1.2_s1/timing.rpt` | `ba2ba369894e83b051cfb93f9242bcd23a1c3d558d7e8afc89bd810fa9192d98` |
| `final/runs/pnr_base_jq_T1.2_s1/timing.rpt` | `f4a4f38be932be8c802a1b814b8e4b61e00a41c2b347469e48135189f22679da` |

`final/PUBLICATION_MANIFEST.md` hashes the canonical T2.0 s1 routed outputs, but not the T1.2 s1 run used for Figures 4, 12 and 16. The table above records that run.
