# AI usage disclosure

This record describes how the PAMS research and this manuscript were produced, as far as the session that wrote it can establish. **The authors must review and complete it before any submission or circulation.**

## What an AI system did

The work was carried out by **Claude Code**, Anthropic's agentic coding tool, running the model **Claude Opus 5.5** (`claude-opus-5-5`). It worked in a local repository (`phase2/masked_verification/`) on the user's machine, under the direction of the user, who issued a written directive for each research phase. The directives set goals, constraints and deliverables. Within them, the AI system did the following.

**Research and design**
- the literature and prior-art search;
- deriving the PAMS construction and its exactness argument;
- choosing the baseline and the competitor designs.

**Engineering**
- writing the generators (`models/gen.py`, `competitors/models/cgen.py`) that produce the Verilog;
- writing the verification scripts;
- writing the synthesis and place-and-route flow scripts;
- running every tool: Yosys, ABC, OpenROAD, OpenSTA, Icarus Verilog, SILVER and PROLEAD.

**Verification and evaluation**
- the exhaustive mathematical checks and the structural checker;
- the functional simulations;
- the seeded P&R campaign and the statistics.

**Manuscript**
- every section, appendix and table of this paper;
- the figure generators and the hand-drawn TikZ diagrams;
- the bibliography;
- the companion documents, including this one;
- the adversarial self-review in `PAPER_REVIEW.md`.

The design files and measurement results are outputs of the open-source EDA tools listed above, run by the AI system. The paper reports those outputs. It does not report AI-estimated numbers. Where the text gives a number, the number was read from a tool output or computed by a script in the repository. `FIGURE_PROVENANCE.md` and Appendix D list the sources.

## What no AI system did

- **No figure was produced by an image-generation model.** All plots come from matplotlib or Graphviz scripts run on tool output. The layout renders are OpenROAD's own. The conceptual diagrams are hand-written TikZ code and are labelled as conceptual.
- **No external paid service or cloud EDA service was used.** All tools ran locally.
- **The bibliography contains no invented entries.** Fields that could not be confirmed, such as some DOIs and page ranges, were left out rather than guessed. See `PAPER_REVIEW.md`.

## Human contributions: to be completed by the authors

This session does not know the following, and none of it has been filled in:

- [ ] **Authors and affiliations.** The title page carries an editable placeholder. No affiliation is implied.
- [ ] **The human role.** Describe what the human participants did: problem selection, the phase directives, review of results and text, and any independent re-runs or checks.
- [ ] **Independent verification.** State whether a person has independently re-run the main results (`final/FINAL_REPRODUCIBILITY.md`), checked the proofs in Section 3.1 and Appendix A, or read the RTL. If no one has, say so.
- [ ] **Venue policy.** Check the AI-use policy of any venue the paper is sent to, and adapt this disclosure (for example, an acknowledgment or methods statement) to it. The paper is not formatted for, submitted to or accepted by any venue.
- [ ] **Accountability.** Confirm which named persons take responsibility for the content.

## Suggested acknowledgment text (edit as appropriate)

> The design exploration, implementation, verification, evaluation and the drafting of this manuscript were performed with the AI coding agent Claude Code (model Claude Opus 5.5, Anthropic) under the direction of the authors. All reported numbers come from open-source EDA and verification tools whose inputs, scripts and outputs are included in the artifact. The authors [reviewed / independently re-ran …] and take responsibility for the content.
