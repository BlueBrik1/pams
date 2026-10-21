# Final design specification

## 1. Canonical circuits
| role | file (publication copy) | origin (byte-identical) | generator |
|---|---|---|---|
| **PAMS, publication candidate** | `final/rtl/pams_jqr.v` | `competitors/rtl/pams_jqr.v` | `competitors/models/cgen.py pams_jqr` |
| **strongest conventional competitor** | `final/rtl/base_jq.v` | `competitors/rtl/base_jq.v` | `competitors/models/cgen.py base_jq` |
| historical PAMS (Phase XI, frozen) | `rtl/pams.v` | — | `models/gen.py pams` |
| historical baseline (Phase XI, frozen) | `rtl/base.v` | — | `models/gen.py base` |

SHA-256 hashes are in PUBLICATION_MANIFEST.md. Every module contains the same `hpc2` gadget text (Cassiers et al. HPC2, 3 shares).

## 2. Top-level interface (identical for both)
```
module <pams_jqr|base_jq>_lane (
  input  clk,
  input  [11:0] x0, x1, x2,     // arithmetic shares of the re-encrypted coefficient, canonical: 0 <= x_i < 3329
  input  [10:0] c,              // public received ciphertext coefficient (low d bits used)
  input  [1:0]  mode,           // 0: d=4, 1: d=5, 2: d=10, 3: d=11 (per coefficient)
  input  vin, first, last,      // stream control: valid, first / last coefficient of a ciphertext
  input  [R-1:0] rnd,           // fresh uniform random bits every cycle: R = 120 (PAMS), 171 (baseline)
  output [2:0] cdec, cvalid,    // per-coefficient decision shares (test visibility only; must not be recombined)
  output [2:0] dec,  dvalid);   // whole-ciphertext decision shares (b = dec[0]^dec[1]^dec[2]), valid when dvalid
```
- No reset. The pipeline is self-clearing through the valid / first / last pipeline.
- **Throughput:** one coefficient per cycle, sustained (initiation interval 1, no stalls).

## 3. Pipeline (stage = number of clock edges after the coefficient enters)
```
                      pams_jqr                                           base_jq
stage 1  x_iq, c0, d0 (input registers)                    x_iq, c0, d0
stage 2  x_ir | public part 1: qc, qn, e, c (window logic)  x_ir | offset (2c-1)2^12 - 1, region mask, shift 11-d
stage 3  partial products x_i[11:6]*M, x_i[5:0]*M          partial products (M = 10569051393, 34 bit)
         | public part 2: Low_c, Theta_c                    | public delayed
stage 4  s_i = (pp_hi<<6 + pp_lo) >> 21  (14 bit)          f_i = (pp_hi<<6 + pp_lo) >> 21  (24 bit)
stage 5  y_0 = s_0 - Low_c + 2, y_1, y_2; Theta            y_i = f_i >> (11-d); y_0 -= offset; region enable
         ---- masked kernel (HPC2, 2 cycles per gadget level) ----
         CSA (13 maj) -> ripple carry + ripple comparator    CSA (23 maj) -> ripple carry to bit 13 (12)
         vs Theta (10 + 10) -> zero test Z[13:11] (4) -> AND  -> carry-free zero test bits 13..23 (10 OR + 10 tree)
stage 31 per-coefficient decision cdec, cvalid             stage 33
         ---- accumulator: HPC2 with 2-cycle feedback (two interleaved chains) + final HPC2 ----
+4       dec, dvalid (ciphertext decision)                 +4
latency  35 cycles to dvalid after the last coefficient    37 cycles
```
The just-in-time ("j") delay of the operand bits is distributed: bit k of y_i is delayed in a single-domain register chain until the ripple stage that consumes it (≈ stage 5 + 2k).

## 4. Functional modules and resources (synthesis medians, 5 mappings; `competitors/runs/cbench.json`)
| quantity | pams_jqr | base_jq | difference |
|---|---|---|---|
| HPC2 gadgets (kernel + accumulator) | 38 + 2 = **40** | 55 + 2 = **57** | −29.8 % |
| fresh random bits per cycle (3 per gadget) | **120** | **171** | −29.8 % |
| masked lane width | 14 bit | 24 bit | |
| share-wise constant | M = 10321339 (24 bit), shift 21 | M = 10569051393 (34 bit), shift 21, + mode shifter | |
| public per-coefficient logic | Low_c, Θ_c: one constant multiply by q, 8 constant comparisons, small adders | offset and region mask: shifts | |
| flip-flops, top level (gadgets: 30 FF each) | 1,294 | 1,500 | |
| combinational cells, top level | 3,366 | 3,175 | |
| cell area (synthesis, Nangate45) | 17,022 µm² | 21,097 µm² | −19.3 % |
| worst-path delay (synthesis) | 1.033 ns | 1.057 ns | −2.3 % |
| per-coefficient decision latency | 31 cycles | 33 cycles | |
| ciphertext decision after the last coefficient | 35 cycles | 37 cycles | |
| throughput | 1 coefficient per cycle | 1 coefficient per cycle | equal |

Post-route figures are in FINAL_BENCHMARKS.md.

## 5. Critical paths (synthesis STA, mapping 0; `final/runs/pubpaths_*.txt`: worst arrival + setup per register group)
| register group (what it holds) | pams_jqr | base_jq |
|---|---|---|
| public window / offset, first stage | qc, qn: 0.925 ns | offset, mask: 0.586 / 0.595 ns |
| public, second stage | **Low_c: 1.033 ns** (critical) | delayed copies: 0.117 ns |
| partial products (share-wise) | 0.994 / 1.016 ns | **1.027 / 1.022 ns** (critical) |
| partial-product sum (share-wise) | 0.784 ns | 1.017 ns |
| offset / shift into y (share-wise) | 0.620 ns | 0.995 ns |

**Readings:**
- Both designs are front-end limited, with every stage balanced near 1.0 ns. No masked-kernel path is critical in either.
- PAMS's narrower datapath leaves slack in its later share-wise stages; its limit is its public window logic.
- The baseline's public logic needs at most 0.595 ns, so the baseline has no equivalent of PAMS's "r" retiming to exploit. Its limit is the 34-bit share-wise constant multiplier.

**After routing**, the reported critical path start / end points per run are recorded in `final/runs/pnr_stats.json` (`crit` fields).

## 6. Differences between PAMS and the strongest baseline
1. **Decision rule:**
   - PAMS: Z < Θ_c on a fixed 14-bit switched value anchored at the integer interval start;
   - Simple: top d bits of a (d + 13)-bit switched value equal 0, after subtracting the scaled half-integer c − ½.
2. **Width:** 14 bits for every d, against 24 bits (driven by d = 11).
3. **Gadgets:** 40 against 57 (CSA 13 vs 23; decision logic 25 vs 32).
4. **Public logic:** PAMS has more of it (Low_c, Θ_c). It is unmasked and pipelined.
5. **Everything else is identical:** gadget, linear share-wise style, alignment generator, accumulator, control pipeline, generic optimizations j and q (PAMS additionally r, see §5).

## 7. Assumptions and requirements
- **Canonical shares:** 0 ≤ x_i < 3329 (both designs). This is an interface requirement on the upstream masked re-encryption; neither design validates it.
- **Randomness:** `rnd` must carry R fresh, uniform, independent bits every cycle. Each bit feeds exactly one gadget (checked). No generator is included.
- **Output consumers:** `cdec` and `dec` must only enter PINI-compatible masked logic (e.g. a masked implicit-rejection select). They must never be recombined.
