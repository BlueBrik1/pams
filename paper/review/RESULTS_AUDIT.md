# Experimental-results audit (final manuscript review, 2026-10-21)

**Method:** `paper/scripts/audit_results.py` (new) recomputes every headline value directly from the frozen evidence. It reads, read-only:
- `final/runs/pnr_stats.json` (42 runs);
- `competitors/runs/cbench.json` (5 synthesis mappings per design);
- `final/data/gadget_breakdown.csv`.

It also recomputes the exact rank-sum p-values over all C(14,7) label assignments. Its output is in `review/results_audit.json`. Routing runtimes were read from `final/runs/pnr_*_T1.1_s*.log`. Every value was compared with the manuscript (abstract, Section 1, Table 6, Sections 6.1–6.5, Section 8, and Appendix D) and with `final/FINAL_RESEARCH_VERDICT.md`.

**Result:** all headline values are **confirmed**. Six statements were corrected in interpretation or labelling; no frozen number changed.

## Claim-to-source table

| claim (manuscript) | manuscript value | recomputed | source | status |
|---|---|---|---|---|
| HPC2 gadgets | 40 vs 57 (−29.8 %) | 40 / 57; CSA 13/23, carry 10/12, comparator 10/0, top 4/20, final 1/0, accumulator 2/2 | `gadget_breakdown.csv`; RTL instance count (`audit_rtl.py`) | confirmed |
| fresh random bits per cycle | 120 vs 171 (−29.8 %) | 120 / 171; rnd widths [119:0] / [170:0] | same; RTL | confirmed. The generator is excluded from area, as stated. |
| synthesized cell area | 17,022 [17,001, 17,022] vs 21,097 (−19.3 %) | 17,022.1 [17,000.6, 17,022.1] vs 21,097.0 | `cbench.json` | confirmed |
| synthesized delay | 1.033 [1.033, 1.041] vs 1.057 ns | 1.0326 [1.0326, 1.0411] vs 1.0573 | `cbench.json` | confirmed |
| routed cell area @ 2.0 ns | 18,734 [18,706, 18,771] vs 23,285 [23,266, 23,309] (−19.5 %) | 18,734.4 [18,705.9, 18,771.1] vs 23,284.6 [23,266.5, 23,309.0]; −19.54 % | `pnr_stats.json` | confirmed |
| routed cell area @ 1.2 ns | 18,750 vs 23,304 (−19.5 %) | 18,749.5 vs 23,303.7; −19.54 % | same | confirmed |
| routed cell area @ 1.1 ns | "19.5 % at every target" (old) | PAMS 18,786 (7 valid) vs baseline 23,366.5 (1 valid run; also the median of the 5 finished runs); −19.60 % | same | **corrected wording:** 19.6 % at 1.1 ns, with its basis stated |
| every PAMS run smaller than every baseline run | p = 0.0006 | true at every target for all finished runs; p = 0.000583 at 2.0 and 1.2 ns (7 + 7, minimum attainable) | same | confirmed. The **scope** of p is now stated: layout distributions of one netlist per design in this flow. |
| die area | 35,596 vs 43,694 (−18.5 %) | 35,596.4 vs 43,693.5; −18.53 % | same | confirmed |
| achieved period @ 2.0 ns | 1.156 [1.146, 1.165] vs 1.198 [1.142, 1.255]; 3.6 %, p = 0.073, inconclusive | 1.1555 [1.1463, 1.1654] vs 1.1982 [1.1417, 1.2552]; 3.56 %; p = 0.0728 | same | confirmed |
| achieved period @ 1.2 ns | 1.094 vs 1.105; 1.0 % (11 ps), p = 0.0006 | 1.0936 vs 1.1049; 1.02 %; p = 0.000583 | same | confirmed. The sentence was rephrased from "faster in every seed" to "lower period in every seed", with the scope of the statistic (previous session) and the conclusion "comparable clock periods". |
| achieved period @ 1.1 ns | 1.068 [1.062, 1.070] (7/7) vs 1.066 (1/7), −0.2 % (single run) | 1.0676 [1.0623, 1.0700] vs 1.0658 (one valid run) | same | confirmed. No baseline distribution is computed from the single run. |
| area × delay | Table 6: 20,532 vs 25,761 @ 1.2 ns (20.3 %); text: "19–23 % lower" | 22.5 % @ 2.0; 20.3 % @ 1.2; 19.4 % @ 1.1 against the single valid baseline run | same | **corrected:** per-target values, the 1.1 ns figure labelled as one observation, and "the gain comes almost entirely from area" added |
| flip-flops | 2,494 vs 3,210 | 1,294 + 40·30 = 2,494; 1,500 + 57·30 = 3,210 | `cbench.json` | confirmed |
| buffers @ 1.2 ns | 1,558 vs 2,081 | 1,558 / 2,081 (medians) | `pnr_stats.json` | confirmed |
| routed wirelength @ 1.1 ns | 58,067–58,506 vs 72,529–73,494 µm, 20 % less | 58,067–58,506 vs 72,529–73,494 (finished runs) | same | confirmed |
| 1.1 ns routability | PAMS 7/7 DRC-clean; baseline 1/7 valid, 4 with 1–6 DRC, 2 stopped | the same; DRC 3, 1, 6, 3 (seeds 2, 3, 4, 7); seeds 1 and 6 stopped | same | confirmed |
| PAMS routed "in about 1.3 minutes"; baseline 31–63 min | as stated | PAMS wall clock 1 m 13 s–1 m 21 s; baseline finished runs 31.5, 39.9, 62.8, 54.6 min; stopped runs 126 and 90 min | `final/runs/pnr_*_T1.1_s*.log` (`real`) | confirmed. **Added:** router runtime and convergence describe the flow, not circuit speed. |
| latency | 31 / 35 vs 33 / 37 cycles | decision_latency 31 / 33, + 4 to dvalid | `cbench.json`; RTL simulation (cvalid at stage 31) | confirmed |
| throughput | 1 coefficient / cycle; 1,280 coefficients → about 1,315 cycles | 1,280 + 35 = 1,315 | RTL | confirmed |
| routing overhead | about 1,700 / 2,200 µm² | 18,734 − 17,022 = 1,712; 23,285 − 21,097 = 2,188 | — | confirmed |
| seed spread "about 70× smaller than the gap" | 4,550 gap vs 65 µm² range | 4,550 / 65 ≈ 70 | — | confirmed |
| area decomposition (Tables 7 and 19) | −4,075 µm² total | sums exactly to the synthesized totals (`data/resources.json`) | `paper/scripts/resources.py` on `mapped.json` | confirmed (previous session); attribution of shared logic is approximate, as stated |
| historical comparison (Section 6.5) | 21.3 % area and 10.4 % period vs the original baseline | labelled as historical, against the unpipelined original baseline | `FINAL_RESEARCH_VERDICT.md` §11 | confirmed: not used as a final result |

## Corrections applied

1. **Table 6 caption.** "median over the 7 valid seeds at each target" was false at 1.1 ns. It now states 7 per design at 2.0 and 1.2 ns, and 7 vs 1 at 1.1 ns, so that row is a single observation.
2. **Section 6.1, "Consistent across targets".** Per-target values are given, with the 1.1 ns basis (one valid run, or the median of five finished runs).
3. **Section 6.1, "No overlap".** It is restricted to finished runs. The p-value applies at 2.0 and 1.2 ns only, and the text says it separates layout distributions of one netlist in this flow and implies nothing about other technologies, flows or silicon.
4. **Section 6.3, area-delay.** "19–23 % lower" was replaced by the per-target medians and the labelled single-run value at 1.1 ns, plus the observation that the gain comes from area.
5. **Section 6.4.** A sentence was added: router runtime and convergence are not circuit speed, and the achieved periods at 1.1 ns are equal.
6. **Section 6.3, 1.2 ns** (rephrased earlier in this session, kept). "lower period in every seed (p = 0.0006), but only by 11 ps" now carries the scope of the statistic.

## Statistical interpretation (checked)
- The seven seeds vary the placement of one netlist under one flow. The paper states this in Section 5.3 ("What the seeds sample"), Section 6.1 and Section 6.3, and makes no claim about chips, fabrication or other technologies.
- p = 0.0006 is the minimum attainable with 7 + 7 runs, and the paper says so.
- At 1.1 ns no baseline timing distribution is formed; the single valid run is labelled.
- The strongest result, as stated in the conclusion, is the consistent area reduction under the evaluated conditions. Speed is "comparable, without a demonstrated general speed advantage".

## Not re-checked in this review
- The synthesis and P&R runs themselves (frozen; not re-run).
- The functional-simulation logs (frozen; summarised in Table 22 from `final/runs/fsim_*.log`, previous session).
