# Design contract (Phase XIII): what every competitor must implement

Every design compared in this phase implements this contract unchanged. It is the Phase XI contract (BASELINE.md, "Common implementation contract"), stated explicitly. Any deviation is listed per design in FAIRNESS_AUDIT.md.

## Function
- **Parameters:** q = 3329; d ∈ {4, 5, 10, 11} (ML-KEM-512/768/1024 `d_u`, `d_v`), selectable per coefficient by `mode` (0 → 4, 1 → 5, 2 → 10, 3 → 11).
- **Per coefficient:** given the uncompressed re-encryption coefficient x (secret, shared) and the public received ciphertext coefficient c, compute b = [Compress_d(x) = c] with FIPS 203 Compress_d(x) = ⌈x · 2^d / q⌋ mod 2^d.
  - The comparison is **exact for every x ∈ [0, q) and every c ∈ [0, 2^d)**: no false accept, no false reject.
  - Probabilistic compressions or comparisons with any nonzero error probability are **excluded** from the ranking.
- **Per ciphertext:** the AND of b over all coefficients between `first` and `last`. Every design uses the same accumulator: one HPC2 with 2-cycle feedback (two interleaved chains) plus one final HPC2.

## Interface (identical port list; module `<design>_lane`)

| port | width | meaning |
|---|---|---|
| `x0`, `x1`, `x2` | 12 each | arithmetic shares, x = x0 + x1 + x2 mod q |
| `c` | 11 | public ciphertext coefficient |
| `mode` | 2 | selects d (encoding above) |
| `vin`, `first`, `last` | 1 each | public stream control |
| `rnd` | R | fresh random bits, every cycle |
| `cdec[2:0]`, `cvalid` | 3 + 1 | per-coefficient decision shares (test visibility) |
| `dec[2:0]`, `dvalid` | 3 + 1 | whole-ciphertext decision shares |

- **Input assumption:** shares are canonical (x_i ∈ [0, q)). This is the same assumption as Phase XI and the Phase XII audit; the PAMS and Simple multipliers are exact only on [0, q).
- **Output:** a 3-share Boolean sharing of the decision. It is never recombined inside the lane.

## Throughput, latency and timing
- **Initiation interval 1:** one coefficient per clock cycle, sustained, with no stalls.
- **Latency:** fixed, data-independent pipeline latency; reported per design. A shorter latency is not credited unless it also changes area or delay.
- **Timing behaviour:** constant time. `cvalid` / `dvalid` depend only on `vin` / `first` / `last` (checked for the frozen designs in Phase XII; the competitors use the same control pipeline code).

## Security model (same for every design in the primary ranking)
- **Masking:** second-order, 3 shares, glitch-robust probing model.
- **Gadget:** every nonlinear operation is the same HPC2 gadget, byte-identical to the frozen `hpc2` module. Phase XII verified it with SILVER as glitch-robust 2-PINI.
- **Composition:**
  - everything outside the gadgets is share-local (XOR, NOT, AND with public data, registers, share-local arithmetic on a single share);
  - trivial PINI composition gives glitch-robust 2-probing security of the lane.
- **Mechanical checks:** the composition preconditions are checked on every mapped netlist with `models/domaincheck.py` (Phase XI) and `validation/structure/compcheck.py` (Phase XII), using the same rules as for the frozen designs:
  - no cross-domain mixing outside gadgets;
  - each random bit goes to exactly one gadget r-port;
  - gadget port domains and output domains are correct.
- **Not checked per competitor** (identical in kind to the frozen designs; see FAIRNESS_AUDIT.md):
  - transition robustness;
  - PRNG security;
  - lane-level PROLEAD.
- **Randomness:** 3 fresh bits per gadget per cycle. The comparison counts randomness as bits per cycle. Generators are external, as in Phase XI.

## Hardware conditions (matched)
- **Library:** Nangate45 typical (`current/lib/NangateOpenCellLibrary_typical.lib`).
- **Synthesis, flow B** (`bfbench.synth`, unchanged):
  - Yosys 0.33: `synth -flatten -noabc`, `dfflibmap`;
  - ABC: `-constr` (BUF_X1 drive, 5 fF load), `-D 500`;
  - HPC2 `keep_hierarchy`.
- **Mappings:** five, identical for every design (`bench.MAPS`): ABC -D 500 with 0/3/6 pad modules, -D 400, -D 650. The median is reported with [min, max].
- **STA:** OpenSTA data-path groups (in2reg, reg2reg, reg2out, in2out), I/O at the clock edge, 0.05 ns input transition, 5 fF output load.
- **P&R (finalists):** the Phase XI batch-2 flow, with no other change:
  - `tools/run_pnr_mv.sh` / `tools/pnr_mv.tcl`;
  - OpenROAD (ORFS 26Q3);
  - flow-C synthesis (don't-use-pruned library);
  - 2.0 ns target, density 0.6, utilizations 45/50/55 %;
  - `repair_timing -hold -max_buffer_percent 60`;
  - RCX extraction.
- **Memory model:** none. Coefficients stream in. No RAM or ROM in any design. Public per-coefficient constants are computed from (c, d) in logic inside the lane.
- **Output consumption:** shares stay registered at the outputs exactly as in the frozen designs.

## Functional acceptance (every design, before any number is reported)
1. **RTL simulation** (`models/sim.py` via `competitors/models/cbench.py`):
   - 6,000 coefficients with all four d mixed;
   - boundary-heavy stimulus: x within ±2 of both interval ends, plus wraparound at 0 / q − 1, random and all-matching values;
   - ciphertexts of 2–9 coefficients;
   - fresh random shares and fresh gadget randomness every cycle.
   - The test recombines the per-coefficient and per-ciphertext decision shares and compares them with Compress equality. Requirement: 0 mismatches.
2. **Gate-level re-simulation of every mapping:** 1,500 coefficients, 0 mismatches.
3. **Exhaustive mathematical check** (`cgen.py`, run before any RTL is written):
   - every decision rule is checked for all x ∈ [0, q), all d and all c;
   - for the share-wise floors, it is also checked for every floor-sum error e ∈ {0, 1, 2}, a superset of the reachable errors.
