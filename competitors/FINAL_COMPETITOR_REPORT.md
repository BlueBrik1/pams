# Phase XIII final report: PAMS against the strongest conventional competitors

## Verdict: **PAMS IS PARETO-COMPETITIVE**
**The frozen `rtl/pams.v` is not the fastest design evaluated:**
- Conventional Simple-method lanes with more share-wise pipelining are faster:
  - base_p 1.388 ns (routed 1.527);
  - base_jq 1.057 ns (routed 1.222);
  - against frozen PAMS: 1.487 ns (routed 1.613).
- Each of them is 18–34 % larger than frozen PAMS (synthesis area). No competitor is both smaller and faster than frozen PAMS, so PAMS is not dominated.

**With the same generic optimizations applied to PAMS:**
- pams_jpr and pams_jqr are smaller and faster than every evaluated competitor at the same pipeline depth, in synthesis and in routed medians.
- At the deepest depth built (+2), the delay margin is 2.3 % in synthesis and 4.9 % routed, which is within P&R variation.
- So **"PAMS REMAINS BEST" is not claimed.** The robust advantage is area, gadgets and randomness at equal delay, not delay.

## Strongest competitor
| role | design | provenance | synth area / delay | routed cell / period / die |
|---|---|---|---|---|
| smallest competitor | **base_j** | Simple (Fritzmann 2022 / D'Anvers 2023) at the optimized t = 13, A = 1; carry-free zero test; JIT operand alignment | 19,915 µm² / 1.646 ns | 21,924 / 1.818 / 41,223 |
| fastest competitor | **base_jq** | base_j + two-stage pipelined constant multiplier | 21,097 / 1.057 | 23,290 / 1.222 / 43,694 |

- **Overall strongest:** base_jq. It is the fastest design measured apart from pams_jqr, and it is within 6 % of the smallest competitor's area.
- **Dominated families:**
  - Bos family (≥ 26,843 µm², 91 gadgets);
  - HOCompress precision (one bit wider than Simple at every depth);
  - Brent–Kung prefix carry (+18 gadgets; it trades registers for gadgets);
  - Coron arithmetic route (lower bound ≥ 33,500 µm²).

## Revised improvement numbers
Positive = PAMS better; synthesis medians of 5 mappings; routed medians over utilizations 45/50/55 %.

| comparison | synth area | synth delay | routed cell | routed period | routed die | random bits |
|---|---|---|---|---|---|---|
| frozen pams vs frozen base (Phase XI claim) | **+21.3 %** | **+9.8 %** | +21.3 % | +10.5 % | +20.7 % | +29.8 % |
| frozen pams vs smallest competitor (base_j) | +14.6 % | +9.7 % | +14.7 % | +11.3 % | +13.8 % | +29.8 % |
| frozen pams vs fastest competitor (base_jq) | +19.4 % | **−40.6 %** | +19.7 % | **−31.9 %** | +18.7 % | +29.8 % |
| frozen pams vs base_p | +22.5 % | **−7.1 %** | +22.8 % | **−5.6 %** | +22.1 % | +29.8 % |
| depth +1 matched: pams_jpr vs base_jp / base_p | +19.0 % / +26.0 % | +20.1 % / +16.2 % | +19.5 % / +26.1 % | +20.9 % / +18.3 % | +18.5 % / +25.4 % | +29.8 % |
| depth +2 matched: pams_jqr vs base_jq | **+19.3 %** | **+2.3 %** | **+19.7 %** | **+4.9 %** (within P&R spread) | **+18.5 %** | +29.8 % |
| iso-delay: pams_jpr (depth +1) vs base_jq (depth +2) | +23.0 % | −10.0 % | +23.1 % | −2.1 % | +22.1 % | +29.8 % |

**How the Phase XI claims change:**
- **Area:** −21.3 % against base.v becomes **−19 to −20 %** against the strongest fairly matched competitor at the same pipeline depth, and −14.6 % for frozen PAMS against the smallest competitor.
- **Delay:** −9.8 % (synthesis) / −10.4 % (routed) against base.v **does not survive as a general claim.** It holds at depth 0 (frozen versus frozen, and against base_j) and at depth +1, but frozen PAMS is slower than pipelined competitors. At depth +2 the matched margin is 2–5 %, inside the variation.
- **Randomness (29.8 %) and gadget count (−30 %):** unchanged. No competitor optimization reduced them.

## Answers to the audit questions
1. **Is `base.v` genuinely a strong implementation of the conventional method?**
   - **Algorithmically yes:** t = 13 with A = 1 is the minimum exact precision for Simple, one bit narrower than the published code and HOCompress. Its carry-free zero test is sound.
   - **As RTL, no:** it carries ≈ 1,565 operand-alignment-dominated flip-flops, and its delay is limited by an unpipelined front end.
   - Two generic changes improve it to 19,915 µm² (−7.8 %) or to 1.057 ns (−35.9 %).
2. **Which competing algorithm is strongest after optimization?**
   - The Simple method (Fritzmann 2022 / D'Anvers 2023) with ripple carry, JIT alignment and front-end pipelining: base_j for area, base_jq for delay.
   - Bos-style interval checking, HOCompress precision, Brent–Kung (X2X-style) adders and Coron arithmetic tests are all dominated by Simple.
3. **Does PAMS retain its area advantage?** **Yes, robustly:**
   - 14.6–19.4 % for frozen PAMS against the competitors' Pareto front;
   - 19.0–19.3 % at matched depth;
   - routed cell area 14.7–26.1 %.
   - No PAMS mapping is as large as the smallest competitor mapping.
   - Cause: 40 versus 57 gadgets and a 14- versus 24-bit lane, which is fundamental, not RTL quality.
4. **Does PAMS retain its delay advantage?**
   - **Only at a fixed pipeline depth, and only clearly at depth 0 and +1** (9.7–20.9 %).
   - Frozen PAMS loses to pipelined competitors, by up to 40.6 % against base_jq.
   - At depth +2, the matched advantage shrinks to 2.3 % / 4.9 % routed, within P&R variation.
   - Both families stay front-end limited: the share-wise multiplier and, for PAMS, its public window logic.
5. **Are the differences larger than mapping variation?**
   - **Area:** yes, by ≥ 20× (spread ≤ 0.6 %).
   - **Delay at depth 0 and +1:** yes; worst-case pairs are separated by ≥ 10 % (frozen) and ≥ 17 % (depth +1, routed).
   - **Delay at depth +2:** no. base_jq's routed u45 (1.150 ns) beats pams_jqr's u50 (1.162 ns).
6. **Does any competitor dominate PAMS?**
   - **No.** Every competitor faster than frozen PAMS is at least 18 % larger, by synthesis area relative to PAMS: base_jp +18 %, hoc_jp +23 %, base_jq +24 %, hoc_jq +28 %, base_p +29 %, base_q +34 %.
   - No competitor is smaller than any PAMS variant.
7. **Does the architectural novelty claim survive a stronger performance comparison?**
   - **Yes, in narrowed form.** The Phase XII class-B novelty (a combination, not a mechanism) is unaffected.
   - Its hardware consequence survives: one d-independent 14-bit lane with 30 % fewer gadgets and random bits, and ≈ 19 % less area than the strongest matched conventional lane.
   - The **delay** benefit is not an intrinsic property of the architecture. It comes from a narrower multiplier and is a pipelining artifact at any fixed depth.
8. **What is the narrowest defensible claim we can make in a paper?**
   > For exact, second-order (3-share, HPC2, glitch-robust PINI) masked ML-KEM ciphertext verification at one coefficient per cycle, PAMS needs 40 instead of 57 HPC2 gadgets and 120 instead of 171 fresh random bits per cycle. It reduces mapped area by 19–20 % (routed cell area 19–20 %, die 18–19 %) compared with the strongest conventional (Simple-method) lane we could build, at equal pipeline depth and equal or slightly better delay, under one Nangate45 synthesis and P&R flow.

   **Not defensible:**
   - "faster" in general;
   - "beats all published implementations" (no published second-order ASIC verifier exists to compare against);
   - any result outside this flow and library.

## What was not done
- **Pipelining depth:** depth +3 and beyond, for both families. Both remain front-end limited; at enough depth the delays are expected to converge.
- **Timing closure:** P&R at a tight timing target (all at the Phase XI 2.0 ns target).
- **Gadget families:** other gadgets (HPC3, DOM). They are excluded by the security contract, and they would apply to both families.
- **Competitor security testing:** lane-level PROLEAD of the competitors. Competitors and PAMS variants are composition-checked on every netlist, but only the frozen designs have lane-PROLEAD evidence (Phase XII).
- **Circuit-level baseline:** no published second-order exact ASIC verifier exists to reproduce.

## Artifacts
- **Documents:** DESIGN_CONTRACT.md, PRIOR_ART_BASELINES.md, CANDIDATES.md, BENCHMARKS.md, FAIRNESS_AUDIT.md, EXPERIMENT_LOG.md.
- **Code and scripts:** `models/` (cgen.py generator, cbench.py benchmark, pnr_c.sh / pnr_batch.sh P&R, routed_check.sh, tables.py).
- **RTL:** `rtl/`, generated.
- **Results:** `runs/` (cbench.json, tables.md, P&R metrics and logs, routed checks).
- **Frozen work:** Phase XI and Phase XII artifacts are unchanged.
