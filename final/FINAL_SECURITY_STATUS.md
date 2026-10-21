# Final security status of the publication circuit (`pams_jqr`) and the strongest baseline (`base_jq`)

## Supported claim
> `pams_jqr` (and `base_jq`) is **second-order secure in the glitch-robust probing model** (3 shares; any 2 glitch-extended probes) **under ideal fresh randomness and canonical input shares**.
>
> The argument:
> - **(i)** every nonlinear gate is inside an HPC2 gadget whose mapped netlist SILVER proves glitch-robust 2-PINI;
> - **(ii)** all other logic is share-local or public, which is mechanically checked on every synthesized and routed netlist;
> - **(iii)** the trivial PINI composition theorem then applies.

**Not claimed:**
- robustness against transitions, or against glitches combined with transitions;
- the security of any randomness generator;
- physical (coupling, power or EM) security;
- security of the integration (upstream sharing, downstream consumer).

## 1. Formally verified (established tool)
| item | tool | result | applies to the final RTL because |
|---|---|---|---|
| mapped HPC2 gadget, both synthesized variants (v0, v1) | SILVER (Phase XII, `validation/silver/`) | probing, NI, PINI and uniformity secure at order 2 in the standard and robust (glitch) models; robust SNI holds only at order 1 (HPC2 is PINI, not SNI) | every gadget instance in all 5 synthesis mappings and in the P&R input netlist of pams_jqr, base_jq, pams_jpr and base_jp is **byte-identical** to v0 or v1 (`final/runs/gadget_identity.json`, 24/24 netlists) |
| negative controls (unregistered refresh, mask reuse, recombination) | SILVER | detected | — |

## 2. Composition-checked (home-made structural check of the theorem's preconditions; not a leakage tool)
`validation/structure/compcheck.py` (Phase XII, with negative controls), used unchanged:

| check | meaning | pams_jqr | base_jq |
|---|---|---|---|
| D | no net outside gadgets depends on two share domains | 0 violations (5 synthesis mappings + P&R input + every routed run) | 0 |
| R | each random bit reaches exactly one gadget r-port; 3 distinct bits per gadget | 0 | 0 |
| P | gadget input share i carries only domain i (+ public) | 0 | 0 |
| O | output share i of cdec / dec is domain i | 0 | 0 |
| G | each routed gadget equals the verified gadget cell by cell (P&R buffers and resizing collapsed) | 0 mismatches in every routed run (`final/runs/routed_check_final.jsonl`) | 0 |

**Constant time:** cvalid / dvalid depend on no share and no random bit in all 12 final synthesis / P&R-input netlists (`final/runs/control_final.json`). Latency is fixed.

## 3. Statistically tested (PROLEAD, established tool)
**Phase XII, frozen `pams.v` / `base.v`:** the full lane campaign (`validation/SECURITY_VERIFICATION.md` §4.3):
- first order at every cycle with 4.2 M simulations;
- second order at the steady-state cycle with 1 M simulations;
- every flagged maximum decayed on confirmation (up to 16.8 M simulations);
- 4 negative controls detected;
- gadget level: order 2, transitions, multivariate, 4.2 M simulations, no leakage; 3 negative controls detected.

**Phase XIV, final `pams_jqr`: focused campaign** (`final/prolead/`). It uses the same harness, fixture, PROLEAD build, probe placement and leakage model (robust glitches + transitions), on the mapping-0 synthesis netlist `competitors/runs/syn_pams_jqr_p0`:

| run | order | cycles | simulations | probing sets | max −log10 p | null max | outcome |
|---|---|---|---|---|---|---|---|
| self-test: one fixed-group coefficient deliberately wrong (BADC = 7) | 1 | 36 | 4,096 | 994 | — | — | PROLEAD aborts with "received output does not match the expected output": the output check pins the end cycle correctly at the new latency (31 + 5) |
| pams_jqr | 1 | 1–72 (all) | 1,048,576 | 71,568 | 5.53 (ug767 u[1] @47) | 5.01 | flagged; **confirmation alone with 4,194,304 simulations: 0.78**, decaying steadily over the 3.1 M new simulations → multiple-testing artefact |
| pams_jqr | 2 | 36 (steady state) | 262,144 | 493,055 | 5.21 (ug1331 v[2] & ug1470 rbr[2]) | 5.85 | below the null max; **confirmation with 4,194,304: 0.44** → no leakage |
| NC partial recombination (cdec0 ⊕ cdec1 to an output) | 2 | 36 | 65,536 | 494,047 | **41.4** | 5.85 | **leakage detected** (control works on this netlist) |

**Reading:**
- No leakage of pams_jqr survives confirmation.
- The injected flaw is found with a margin of 35 above the null.

**Smaller than the Phase XII campaign:**
- first order: 1 M versus 4.2 M simulations;
- second order: 262 k versus 1 M simulations;
- only one negative control.

It is statistical evidence, not a proof, and it covers only the mapping-0 netlist.

## 4. What changed between frozen PAMS (Phase XII evidence) and pams_jqr
| change | circuit effect | security effect |
|---|---|---|
| j: just-in-time operand delays | the single-domain bits y_i[k] are delayed in share-local register chains instead of the 3-share S_k, T_k | share-local registers only; the gadget network, the gadget inputs (same values, same cycle) and the random-bit allocation are unchanged |
| q: two-stage share-wise multiplier | share-local registers inside each share's constant multiplier | share-local |
| r: public window logic split over existing stages | registers on public data | none (public) |
| decision mathematics, gadget count (40), randomness (120 bits) | unchanged | — |

Consequences:
- The composition argument for frozen PAMS carries over verbatim. Its preconditions were re-checked on the final netlists (§2).
- The Phase XII **lane-level PROLEAD campaign** (up to 16.8 M simulations) was run on **frozen** `pams.v` / `base.v`, not on `pams_jqr`. The final circuit has only the focused campaign of §3. This document does **not** claim identical whole-lane testing.

## 5. Same contract for the baseline
`base_jq` uses the same gadget (byte-identical mapped variants), the same composition style, the same accumulator and the same generic optimizations (j, q). It passes the same structural checks (§2). Its security status equals that of pams_jqr, with one exception: no PROLEAD lane test was run on base_jq in this phase; frozen base.v was tested in Phase XII.

## 6. Remaining limitations (both designs alike)
1. **Transitions:** HPC2 is not O-PINI, and every gadget executes every cycle. The accumulator chain feeds execution k into k + 2. No published composition theorem gives transition robustness for this structure (Cassiers & Standaert, TCHES 2021(2)). The evidence is statistical only.
   - **Possible repairs, not implemented:** an O-PINI accumulator (HPC2 + zero-sharing), or idle cycles.
2. **Randomness:** the design takes R fresh bits per cycle as an input. With a deterministic PRNG (e.g. the Trivium-64 cost model of Phase XI), the guarantee becomes computational, and the PRNG's own leakage is outside the analysis (Cassiers et al., CiC 2024). The generator instances must be independently seeded.
3. **Canonical shares:** non-canonical shares (x_i ≥ 3329) break correctness, not masking. No validator is included.
4. **Physical security:** no TVLA, no coupling model. Attacks on the FO comparison function itself (Hermelink et al., CCS 2024; Ranney et al. 2026) apply to any masked comparator and are not addressed by probing security.
5. **Tools not used:** maskVerif (OCaml/opam unavailable without root) and Coco (CPU co-verification, not applicable).
6. **PROLEAD caveat:** PROLEAD 3.1.0 does not seed its RNG in hardware mode, so reruns replay the same random inputs. Confirmations therefore use larger simulation counts (Phase XII §4.3).
