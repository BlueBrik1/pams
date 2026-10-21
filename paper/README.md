# PAMS paper — manuscript sources

LaTeX sources of *PAMS: Pre-Aligned Modulus Switching for Exact Second-Order Masked ML-KEM Ciphertext Verification in Hardware*. The manuscript describes the frozen research snapshot `pams-publication-freeze-v1` (commit `d033f76`).

- **Status:** manuscript draft. It has not been submitted to, or formatted for, any venue.
- **Authors:** the author block is a placeholder. See `AI_USAGE_DISCLOSURE.md`.
- **Built PDF:** `PAMS_paper.pdf`, 47 pages:
  - main text: pp. 1–19;
  - references: pp. 19–21;
  - Appendix A (mathematics): pp. 22–27;
  - Appendix B (Verilog): pp. 28–35;
  - Appendix C (gates and layout): pp. 36–40;
  - Appendix D (evidence): pp. 41–47.

## Build

```sh
bash scripts/build.sh        # pdflatex + bibtex + 2x pdflatex -> main.pdf, copied to PAMS_paper.pdf; log in build.log
bash scripts/build.sh -f     # first regenerate every data-derived table and figure (needs the local run directories, see below)
```

### TeX installation

The paper was built with TinyTeX (TeX Live 2026, pdfTeX 1.40.29). It was installed user-locally in `~/.TinyTeX` with `--no-path`, so no system files were changed. `build.sh` puts `~/.TinyTeX/bin/*` on `PATH`. Any TeX Live with the packages below also works.

`scripts/tex_setup.sh` installs the packages with `tlmgr`. The packages `main.tex` loads are:

- **Page and fonts:** geometry, fontenc, lmodern, microtype.
- **Mathematics:** amsmath, amssymb, amsthm, mathtools, bm.
- **Graphics:** graphicx, xcolor, tikz (pgf).
- **Tables:** booktabs, multirow, tabularx, makecell, threeparttable.
- **Code and captions:** listings, caption, subcaption.
- **Lists and units:** enumitem, siunitx.
- **Floats:** float, stfloats, afterpage, placeins.
- **References:** natbib, hyperref, cleveref.

The tlmgr bundles that supply them are `tools`, `sttools`, `preprint`, `graphics` and `oberdiek`.

### Figure and table generation

| script | writes | reads |
|---|---|---|
| `scripts/examples.py` | `data/examples.json` (worked examples E1–E4) | `models/pams.py`; simulates `final/rtl/pams_jqr.v` with Icarus Verilog and asserts that the RTL registers match the reference |
| `scripts/appendix_data.py` | `data/tab_windows.tex`, `data/tab_trace_e1.tex` | `models/pams.py`, `data/examples.json`; simulates the RTL and asserts each value |
| `scripts/resources.py` | `data/resources.json` (area by function) | `competitors/runs/syn_pams_jqr_p0/mapped.json` and the baseline equivalent |
| `scripts/tables.py` | `data/tab_pnr_runs.tex`, `data/tab_competitors.tex` | `final/runs/pnr_stats.json`, `final/runs/pnr_*/final.v`, `competitors/runs/cbench.json` |
| `scripts/generate_figures.py [results\|physical\|layout\|gates\|math]` | `figures/**` and `data/*.json` | see `FIGURE_PROVENANCE.md` |

All scripts open the research artifacts read-only. Nothing outside `paper/` is written.

The `layout` part runs OpenROAD headless (`QT_QPA_PLATFORM=offscreen`, script `scripts/layout_image.tcl`). `build.sh -f` does not run it, because the PNGs are committed.

**Inputs that are not in git.** Several large regenerable inputs are gitignored by the research repository:

- `final/runs/pnr_*/final.def` and `final/runs/pnr_*/final.v`;
- `competitors/runs/syn_*/mapped.json`.

Their SHA-256 hashes are listed in `FIGURE_PROVENANCE.md`. They are re-created by the Phase XIV flow (`final/FINAL_REPRODUCIBILITY.md`). The generated figures and tables are committed, so `build.sh` without `-f` works from a clean clone.

### Helpers used only while preparing the manuscript

- `scripts/preview.sh`, `scripts/pv.sh`, `scripts/pages.sh`, `scripts/contact.py`: render pages to `_preview/` for visual inspection (poppler `pdftoppm`).
- `scripts/overfull.py`: reports overfull boxes from the log.
- `scripts/md2tex.py`, `scripts/wrap_tables.py`: one-off source conversions.
- `scripts/envcheck.sh`, `scripts/tex_setup.sh`: environment check and TeX package installation.
- `scripts/layout_try.sh`, `scripts/run_figs.sh`: wrappers for the OpenROAD image export and the figure run.

## Layout

```
main.tex                  preamble, macros, section/appendix order
references.bib            bibliography (fields not verified were omitted, see PAPER_REVIEW.md)
sections/                 abstract, 1 introduction ... 8 conclusion
appendices/               A mathematical_derivations, B verilog_walkthrough, C circuit_walkthrough, D extended_evidence
figures/architecture/     hand-drawn TikZ datapath (conceptual)
figures/mathematics/      Figure 1 (from the reference model)
figures/gates/            Graphviz drawings extracted from the synthesized netlist (+ .dot sources)
figures/physical/         DEF placement map, critical-path bars, OpenROAD layout renders
figures/results/          Figures 6-11, 13 (from the P&R / synthesis data)
data/                     generated tables and the JSON the figures and text were checked against
scripts/                  generators and build
```

Verilog listings in the paper are included verbatim, with their line numbers, from `../final/rtl/pams_jqr.v` and `../final/rtl/base_jq.v` (`\lstinputlisting`). If those files changed, the listings would change with them. Their hashes are in Appendix D.10.

## Companion documents

- `FIGURE_PROVENANCE.md`: the source, method and type of every figure.
- `CROSS_LAYER_TRACEABILITY.md`: maps each equation to RTL, gates, layout and cost.
- `AI_USAGE_DISCLOSURE.md`: how the research and the manuscript were produced; what the authors must confirm.
- `PAPER_REVIEW.md`: the adversarial self-review, the corrections made and the open issues.
