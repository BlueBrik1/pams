# PAMS second-order masking: independent security verification (Phase XII)

**Verdict: PARTIALLY VERIFIED.**

**Established for the frozen PAMS and baseline netlists:**
- glitch-robust 2-probing security with ideal randomness;
- covered by: the 15 synthesis mappings, both P&R input netlists, and all six routed netlists.

**The evidence is a formally justified composition:**
- **Gadget:** each distinct mapped gadget was proven glitch-robust 2-PINI by SILVER, an established formal tool. It was also tested by PROLEAD with glitches, transitions and pipelining.
- **Composition:** the published PINI trivial-composition theorem applies to the lane.
- **Preconditions:** checked mechanically on every netlist.
- **Whole lane:** PROLEAD, an established tool, ran fixed-vs-random leakage detection over the complete gate-level lanes.
- **Negative controls:** every check detects its own deliberately broken designs.

**Not established:**
1. **Transitions:** robustness against transitions combined with glitches. No published composition theorem covers this pipelined structure, because HPC2 is not O-PINI and every gadget has adjacent executions. The evidence is statistical (PROLEAD) only.
2. **Randomness:** the randomness source. The proof assumes ideal fresh uniform bits; the design takes them as an input port. The Trivium-64 cost model would make the guarantee computational, and leaves its own leakage outside the model.
3. **Physical leakage:** nothing beyond the probing model was assessed (no couplings, no TVLA). Published attacks show that t-probing security of the FO comparison is not sufficient in practice.
4. **Integration:** the upstream sharing and the downstream implicit-rejection consumer are assumed, not verified.

No genuine violation of the stated property was found, so the verdict is not FAILED. The complete intended contract is not established, so it is not VERIFIED.

Directory map: `silver/`, `prolead/`, `structure/`, `math/`, `tools/` (builds). All raw logs and JSON results are committed. Tool sources and sysroot are in `~/lwe_agent_handoff/phase2/ext/tools/sca/`.

## 1. Security contract
### 1.1 Intended versus actually established
| property (Phase XII brief) | established by the frozen RTL / netlists? | evidence |
|---|---|---|
| 3 shares, second order | **yes, in the glitch-robust probing model, ideal randomness** | §3–§5 |
| glitch-robust probing security (explicit leakage model) | **yes** (model in §1.2) | SILVER gadget proof + composition theorem + precondition check + PROLEAD lane |
| composable security (PINI) | **yes** for the lane as a glitch-robust 2-PINI composition; the output sharing is a PINI output | §4 |
| exact ML-KEM ciphertext verification | **yes** for canonical input shares x_i ∈ [0, q) | `math/`, FINAL report §3 |
| protected Boolean output for masked implicit rejection | **output side yes:** a 3-share Boolean sharing, share i in domain i (O check). **Consumer not verified.** | §4 |
| fresh, correctly distributed randomness | **not implemented in the design.** `rnd` is an input port; ideal i.i.d. bits are assumed. The Trivium-64 model gives a computational assumption only | §6 |
| no secret-dependent timing | **yes:** fixed latency; cvalid/dvalid depend on public inputs only, in every netlist | `structure/control_results.json` |
| glitch + transition robustness | **not proven** (no applicable theorem); PROLEAD finds no leakage | §5 |
| physical security (couplings, horizontal / vertical attacks, TVLA) | **no** | §7 |

### 1.2 Leakage model used for the verified claim
- **Glitch-robust t-probing model** (Faust et al. 2018; Cassiers et al., HPC, IEEE TC 2021), t = 2:
  - a probe on a combinational wire reveals every register output and primary input in its combinational fan-in cone, for that cycle;
  - a probe on a register reveals its value.
- **Transitions:** PROLEAD runs additionally include transitions; this is an extra model, and no claim is made for it (§5).
- **Couplings** are out of scope.

### 1.3 Assumptions (both lanes identically)
- **A1 (input sharing):** each coefficient arrives as x_0 + x_1 + x_2 ≡ x (mod q) with x_i ∈ [0, q) canonical.
  - Any two shares are jointly uniform.
  - Sharings of different coefficients and ciphertexts are mutually independent, or produced by a PINI upstream.
  - The RTL does not check canonicity. The multipliers are exact only on [0, q): they fail at x_i = 3329 (and at 4005 for PAMS). See `math/audit_results.json`.
- **A2 (randomness):** 120 (PAMS) or 171 (baseline) i.i.d. uniform bits on `rnd`, every cycle.
- **A3 (consumer):** the output sharing `dec` (valid when dvalid = 1) and the test outputs `cdec` go only to PINI-compatible consumers and are never recombined.
- **A4 (implementation):** the netlist reaches silicon as verified: registers are not retimed and gadget gates are not merged. §4 checks this up to the routed netlist. Timing is clean as reported by Phase XI P&R (hold met).

## 2. What the RTL actually implements (inspection of `rtl/pams.v` and `rtl/base.v`)
**HPC2 gadget (`module hpc2`, 30 DFFs):**
- **Registers:** ra, rb, rr hold a, b, r; rbr[ij] = b_j ⊕ r_ij is registered; then p0 = ra·rb, u_ij = ¬ra_i·rr_ij and v_ij = ra_i·rbr_ij are registered.
- **Output:** c_i = p0_i ⊕ ⊕_j (u_ij ⊕ v_ij), a combinational XOR of registers. Latency is 2.
- **Comparison with the published gadget:** this is Cassiers–Standaert Alg. 1 (TCHES 2021(2)), with the extra input registers that pipelining requires.
- **Randomness:** each r_ij is used in u_ij (registered copy) and v_ij (through rbr) of the same invocation, by design. Fresh r is consumed every cycle.
- **Mapped form:** both distinct synthesized variants (`silver/results.json`: used in 12 and 3 of the 15 mappings) are 30 DFF_X1 + 15 AND2 + 6 XOR2 + 12 XNOR2. ¬a comes from the DFF QN outputs.

**Share-wise logic:**
- multipliers y_i = ⌊x_i·2^K/q⌋;
- −Low_c + 2 (PAMS) or −(2c − 1)·2^12 + 1 (baseline), applied to share 0 only;
- XORs of the CSA;
- public-θ XORs and NOTs on share 0;
- delay registers;
- AND with public bits.

**Nonlinear operations:** each is an hpc2 instance:
- **PAMS:** 13 CSA majorities, 10 carries, 3 top-region gadgets, 10 comparator gadgets, 2 final-combination gadgets, plus the accumulator pair: **40 in total**;
- **baseline:** 57.

**Arithmetic-to-Boolean domain change:** none as a gadget. y_i is used as share i of a Boolean sharing with zeros elsewhere, e.g. ug101 a = (y0, y1, 0), b = (y0, 0, y2).

**Accumulator:**
- acc_in = init ? (1, 0, 0) : acc_out, with init = fp[28] | fprev (public);
- uacc = HPC2(acc_in, cdec), whose 2-cycle latency gives two interleaved chains (execution k feeds k + 2);
- ufin = HPC2(acc_last, acc_out) combines the chains;
- dec is driven continuously; dvalid marks the cycle in which it covers exactly the ciphertext.

**Control:**
- vp/fp/lp/f2p shift registers of vin/first/last; lastp.
- No reset and no data-dependent control.

**Randomness wiring:** gadget k uses rnd[3k + 2 : 3k]. Every bit is used by exactly one gadget (R check, §4).

**Feedback:** only the accumulator (through a public mux).

**Consecutive coefficients and ciphertexts:**
- every register always carries the same share index (static domains);
- a new ciphertext restarts both chains through `first`.

## 3. Gadget level: established tools
### 3.1 SILVER (formal, exact, BDD-based; glitch-robust model; single invocation, no transitions)
- **Tool:** SILVER (Knichel, Sasdrich, Moradi, ASIACRYPT 2020), git 0a3c85f (2025-06-06), with Sylvan 5e9da97 as pinned by its README. Build: `tools/build_silver.sh`.
- **Command:** `bin/verify --verilog=1 --verilog-libname=NANG45 --verilog-design_file=<gadget> --verilog-module_name=hpc2` (`silver/run_silver.py`).
- **Input:** the mapped gadget text, copied verbatim from `runs/syn_*/mapped.v`. The only changes are SILVER port annotations, removal of three dead `assign rXY = r[k]` aliases, and duplicate port-wire declarations. SILVER's NANG45 cell model covers exactly the cells used (DFF_X1 Q/QN, AND2, XOR2, XNOR2), so no cell is decomposed.

| run | probing std / robust | NI std / robust | SNI std / robust | PINI std / robust | uniformity |
|---|---|---|---|---|---|
| hpc2_mapped_v0 (12 mappings) | ≤2 / ≤2 | ≤2 / ≤2 | ≤2 / **≤1** | ≤2 / **≤2** | PASS |
| hpc2_mapped_v1 (3 mappings) | ≤2 / ≤2 | ≤2 / ≤2 | ≤2 / **≤1** | ≤2 / **≤2** | PASS |
| NC unregistered refresh (v_ij uses b_j ⊕ r_ij straight from the XOR) | ≤2 / ≤2 | ≤2 / ≤2 | ≤2 / ≤1 | ≤2 / **≤1 (FAIL)** | PASS |
| NC mask reuse (r12 := r01) | FAIL at every notion | | | | FAIL |
| NC recombination (c0 := c0 ⊕ c1) | ≤1 / ≤1 (FAIL) | ≤1 / ≤0 | ≤1 / ≤0 | ≤1 / ≤0 | FAIL |

How to read the table:
- Entries give the largest secure order.
- The gadget is glitch-robust 2-PINI and 2-probing secure.
- Robust SNI holds only to order 1. This is expected: HPC2 outputs are combinational, and composition relies on PINI, not SNI.
- The classic HPC/DOM glitch flaw (unregistered refresh) is still standard-probing secure but fails robust PINI. SILVER detects exactly the composability failure the model is meant to catch.
- **The P&R input gadgets** (`runs/pnrsyn_*`) are byte-identical to the verified variants (`structure/negctl_results.json`).

### 3.2 PROLEAD (statistical; glitches + transitions; multivariate; pipelined use)
- **Tool:** PROLEAD v3.1.0 (Müller & Moradi, TCHES 2022), tag v3.1.0 (commit 91338e0, 2025-02-25), with library `prolead/library.json`: its NANG45 entry plus the alias CLKBUF_X3. Build: `tools/build_prolead.sh`.
- **Configuration:**
  - the same gadget texts, with the same function-preserving clean-up;
  - four back-to-back invocations, then zeros;
  - fresh r every cycle;
  - fixed group (a, b) = (1,1), (0,1), (1,0), (1,1) versus random;
  - order 2, `transitional_leakage: true`, `relaxed_model: false`, `variate: multivariate` (probes in different cycles), cycles 1–6, 2²² = 4,194,304 simulations;
  - G-test threshold −log10 p = 5 (the PROLEAD default).

| run | probing sets | max −log10 p | result |
|---|---|---|---|
| hpc2_mapped_v0 | 6,984 | 4.58 (first campaign); 4.22 (re-run, `campaign2.log`) | no leakage |
| hpc2_mapped_v1 | 6,984 | 4.17 (first campaign); 4.59 (re-run, `campaign2.log`) | no leakage |
| NC unregistered refresh | 3,903 | ∞ (p underflows) | **leakage** |
| NC mask reuse | 6,398 | ∞ | **leakage** |
| NC recombination | 6,403 | ∞ | **leakage** |

The two function-changing controls run with the output check disabled (`expected_output` '$').

**Tool anomaly:** PROLEAD sporadically aborts at the start of evaluation with `GR_MUST_SUCCEED failure: src/fmpz_mod_poly/inv_series.c`, inside FLINT. It happened in 1 of 10 gadget runs and in 4 lane runs (§4.3). The aborted runs are re-run; `attempts` is recorded in each result JSON. No aborted run is counted as a result.

## 4. Composition and netlist level
### 4.1 Composition argument
The argument rests on four facts:
1. **Gadget:** HPC2 as mapped is glitch-robust 2-PINI (SILVER, §3.1).
2. **Share-wise logic** is trivially glitch-robust PINI: every gate's inputs lie in one share domain plus public data.
3. **Composition theorem:** a composition of glitch-robust t-PINI gadgets in which wires connect only equal share indices is glitch-robust t-PINI. This is the trivial composition theorem of Cassiers & Standaert (IEEE TIFS 2020), extended to glitches in the HPC paper (Cassiers, Grégoire, Levi, Standaert, IEEE TC 2021).
4. **Repeated use:** in the glitch-only model a probe sees one cycle. Each pipeline gadget's gates belong to one execution per cycle, so the time-unrolled lane is an acyclic composition of gadget executions. The accumulator feedback runs through registers and becomes acyclic when unrolled.

**Consequence:** any 2 probes are simulatable from the input shares with at most 2 indices I, across all coefficients. Under A1 these are jointly independent of the secrets.

### 4.2 Mechanical check of the theorem's preconditions (`structure/compcheck.py`, home-made, independent re-implementation)
This is a structural check of the theorem's hypotheses. It is not a leakage-verification tool.

Checks:
- **D:** no net outside the gadgets depends on two share domains;
- **R:** every `rnd` bit reaches only the r-port of exactly one gadget, with 3 distinct bits per gadget and nothing else mixing randomness;
- **P:** gadget input a[i] and b[i] carry only domain i or public data;
- **O:** output share i of `cdec` and `dec` is domain i;
- **G (routed netlists only):** every gadget instance in OpenROAD's flattened `final.v` equals the reference gadget cell by cell and pin by pin. Buffers and drive-strength changes from P&R are collapsed; tie cells are treated as constants.

| netlists | gadgets | D | R | P | O | G |
|---|---|---|---|---|---|---|
| syn_pams_p0…p4, pnrsyn_pams | 40 | 0 | 0 | 0 | 0 | — |
| pnr2_pams_u45/50/55 (routed) | 40 | 0 | 0 | 0 | 0 | 0 mismatches |
| syn_base_p0…p4, pnrsyn_base | 57 | 0 | 0 | 0 | 0 | — |
| pnr2_base_u45/50/55 (routed) | 57 | 0 | 0 | 0 | 0 | 0 mismatches |

**Negative controls** (`structure/negctl_results.json`), all detected:
- exposed decision: D = 2;
- partial recombination: D = 1;
- mask reuse inside one gadget: R = 2;
- (each in both lanes);
- Phase XI's deliberately leaky lane: D = 71, P = 8.

**Answer to "did keep_hierarchy preserve the security boundaries?"** Yes:
- every synthesis netlist keeps 40/57 hpc2 instances of the verified module;
- the routed netlists keep every gadget cell under its instance prefix with identical connectivity;
- the P&R changes inside gadgets are buffers, resized cells and tie cells for the constant-0 shares of first-layer gadgets;
- no cross-domain or randomness-mixing logic was introduced anywhere;
- all 2,509 (PAMS) and 3,275 (baseline) flip-flops survive routing.

### 4.3 PROLEAD on the complete lanes (statistical, glitches + transitions)
PROLEAD analyses the gate-level frozen lane end to end, without relying on the composition theorem.

**Harness (`prolead/run_lane.py`, `prolead/jnet.py`, `prolead/lane/tb_gen.v`):**
- **Netlist:** `runs/syn_<d>_p0/mapped.json` is emitted as bit-level structural Verilog. It comes from the same Yosys run as `mapped.v`; identical cell multisets are checked. Every cell and pin is kept; aliasing `assign`s collapse; three x-driven dead netnames are dropped after checking that no cell reads them.
- **Why a fixture:** PROLEAD v3.1.0 samples *all* random inputs in the configured input field. With an arithmetic field mod 3329 the fresh-randomness bits would not be uniform, so the arithmetic sharing is produced by a fixture instead.
- **Fixture (`tb_gen`):** x1 = ⌊R1·q/2^32⌋, x2 = ⌊R2·q/2^32⌋ from fresh uniform 32-bit words (each within statistical distance < 2^−20 of uniform), and x0 = (x − x1 − x2) mod q. Its outputs are registered, and its signals are excluded from probe placement.
- **One simulation:** a 36-coefficient ciphertext (18 coefficients with d = 11, then 18 with d = 5), streamed one per cycle so the pipeline is full. The fixed group uses boundary-adjacent coefficients that all match (decision 1); the random group uses random x. Fresh rnd every cycle.
- **Functional check:** PROLEAD's output check pins the end cycle: the masked decision must be 1 for the fixed group at dvalid. A self-test with one deliberately wrong c fails that check.
- **Probe placement:** flip-flop D-pin nets, gadget a/b/r-pin nets and outputs. In the robust model every other wire's extended probe is a subset of one of these; PROLEAD's own `IsObsolete` keeps only nets that feed registers exclusively.
- **Minimization:** "trivial" (duplicates only). PROLEAD's "aggressive" subset elimination is an O(N²) single-threaded loop and did not finish in 30 min at about 500k sets.

**Multiple testing:**
- With N probing sets tested, the median of the maximum −log10 p under no leakage is −log10(1 − 2^(−1/N)) ≈ log10(N / ln 2); this is the "null max" column below (`prolead/lane_table.py` → `lane_table.json`).
- The PROLEAD default threshold of 5 is per set, not family-wise. A maximum near the null max is therefore not leakage on its own.
- Every flagged maximum of a frozen lane was re-tested alone (PROBES restricted to the nets of that set) with more simulations.

**Confirmation method and its caveat:**
- PROLEAD 3.1.0 never seeds `rand()` in hardware mode: `src/Util/Util.cpp` `GenerateThreadRng` calls `rand()`, and `srand` exists only in the software path.
- A rerun therefore replays the same random inputs, and a confirmation at the same simulation count is **not** an independent test. It happened once (the base order-1 set, 5.46 → 5.11 at the same 4,194,304 simulations).
- Each valid confirmation therefore uses a larger simulation count. Its first N simulations equal the screening data; the rest are new.
  - A real leak grows ~linearly in −log10 p with the number of simulations.
  - A multiple-testing artefact decays toward the single-test null (median 0.3).

**Results:** frozen lanes, 36-coefficient ciphertext, transitions on, robust glitch model.

| run | order | cycles | simulations | probing sets | max −log10 p | null max | top set | outcome |
|---|---|---|---|---|---|---|---|---|
| PAMS | 1 | 1–70 (all) | 4,194,304 | 67,130 | 4.47 | 4.99 | ug681 u[2] @30 | no leakage |
| PAMS | 1 | 34 | 65,536 | 910 | 2.63 | 3.12 | — | no leakage |
| PAMS | 2 | 34 | 65,536 | 459,212 | 6.08 | 5.82 | ug133 p0[1] & ug2150 u[0] | flagged; **confirmation: 0.24** at 4,194,304 → artefact |
| PAMS | 2 | 34 | 1,048,576 | 459,212 | 5.96 | 5.82 | ug2250 p0[0] & ug681 u[1] | flagged; **confirmation: 1.81** at 4,194,304 → artefact |
| base | 1 | 1–72 (all) | 4,194,304 | 95,976 | 5.46 | 5.14 | ug476 u[4] @65 | flagged; same-count rerun 5.11 (not independent, see above); **confirmation: 1.59** at 16,777,216 (12.6 M new), declining steadily over the last 4 M → artefact |
| base | 2 | 36 | 1,048,576 | 887,642 | 6.79 | 6.11 | ug129 u[4] & ug1918 rbr[2] | flagged; **confirmation: 1.20** at 4,194,304 → artefact |

**Negative controls**, function-changing edits of the same JSON netlist (`jnet.NC`), all detected:

| control | lane | order | simulations | probing sets | max −log10 p |
|---|---|---|---|---|---|
| exposed decision: XOR of the 3 cdec shares to an output | PAMS | 1 | 65,536 | 5,760 | **∞** |
| partial recombination: cdec0 ⊕ cdec1 to an output | PAMS | 2 | 65,536 | 460,169 | **48.9** |
| partial recombination | base | 2 | 65,536 | 888,973 | **22.5** |
| mask reuse inside one datapath gadget (r = [r0, r1, r0]) | PAMS | 2 | 262,144 | 458,254 | **∞** |

**Reading:**
- In both frozen lanes no probing set shows leakage that survives confirmation, at first order over every cycle and at second order at the steady-state cycle.
- Each injected flaw is detected at the same or a smaller simulation count, with margins of 16 to ∞ above the null max.
- This is statistical evidence at the stated simulation counts. It is not a proof.

**Anomalies:**
- FLINT `GR_MUST_SUCCEED` aborts occurred in 1 of 10 gadget runs and in 4 lane runs: three early pipe-cleaner runs (PAMS at 64 and 4,096 simulations, base at 64) and the first NC mask-reuse attempt.
- The first NC exposed-decision attempt failed for a different reason: a harness KeyError, fixed in `jnet.py`.
- All were re-run successfully. The aborted directories are kept with `returncode: -6`, and none is counted as a result.

## 5. Transitions
- **What PROLEAD shows:** no leakage at the gadget level with transitions (multivariate, pipelined) or across the whole lane (above).
- **Why this is not a proof:**
  - Cassiers & Standaert, TCHES 2021(2), §3 and §5.3:
    - glitch-robust PINI composition does **not** imply transition robustness;
    - their Theorem 2 needs iterated transition-robust O-PINI gadgets, or PINI gadgets **without adjacent executions**;
    - HPC2 is shown **not** to be O-PINI (p. 149, counterexample with d = 3);
    - in both lanes every HPC2 instance has a new execution every cycle.
  - The datapath gadgets' consecutive executions are mutually independent (different coefficients), which is the paper's "parallel" situation.
  - The accumulator chain is not: execution k + 2 consumes execution k's output.
  - No published theorem covers this structure, and none of the tools used proves it.
- **Status:** transition (and glitch + transition) robustness is **unverified, with no counterexample found**.
- **Possible repairs (not implemented):** an O-PINI accumulator (HPC2 plus a zero-sharing refresh, the paper's O-PINI1), or an idle cycle in the chain. These would make Theorem 2 applicable at a small cost in randomness or latency.

## 6. Randomness audit
- **Assumed:** 3 fresh uniform bits per gadget per cycle, i.e. 120 (PAMS) / 171 (baseline) bits per cycle; information-theoretic i.i.d. bits (HPC2's PINI proof).
- **Wiring, verified (R check):**
  - the three bits of each gadget are distinct;
  - no bit is shared between gadgets;
  - no bit enters lane logic outside a gadget's r-port;
  - all 120/171 bits are used.
  - Inside a gadget, r_ij(t) is used by v_ij at t (through rbr) and by u_ij at t + 1 (through rr). This is the same invocation by design.
- **Implemented:** nothing. `rnd` is a primary input. Phase XI's cost figures model ⌈R/64⌉ unrolled Trivium-64 instances (2 or 3) and exclude the TRNG, seeding and reseeding. The model:
  - loads the raw 288-bit state directly, with no key/IV setup or warm-up;
  - leaves unspecified how keystream bits map to gadget bits.
- **Security implications:**
  1. **Computational, not information-theoretic.** With a deterministic PRNG the probing argument holds only against adversaries for whom the keystream is indistinguishable from uniform. It is a computational reduction to Trivium's security, not the t-probing guarantee.
  2. **The PRNG's own leakage is outside the probing analysis.** One probe on a Trivium state bit, or a glitch-extended probe on a keystream XOR, reveals bits that later appear as masks in several gadgets and cycles. That exceeds the "one probe = one value" accounting of the 2-probing argument. Cassiers, Masure, Momin, Moos, Moradi, Standaert, *Randomness Generation for Secure Hardware Masking – Unrolled Trivium to the Rescue*, IACR CiC 1(2) 2024:
     - recommend unrolled Trivium precisely because a black-box-secure primitive lets masking and RNG be analysed independently;
     - note that the adversary then sees only the PRNG's leakage;
     - note that the initialization can be replaced by a truly random seed of sufficient length, consistent with the direct state load here, if the 288-bit seed is uniform;
     - also show that linear generators (unrolled LFSRs) can break probing security.
     The Trivium choice is therefore defensible, but its leakage resistance is an *additional* assumption.
  3. **Instance independence.** The 2–3 instances must have independent seeds. Equal seeds would duplicate masks across gadgets, the kind of reuse NC mask reuse shows to be fatal.
  4. **Reseeding:** Trivium is specified for ≤ 2^64 keystream bits per key/IV. At 64 bits per cycle this is not a practical limit, but no reseeding policy exists.
- **Conclusion:** the randomness requirement is correctly *counted* and *wired*. The guarantee is information-theoretic only under A2. With the modeled Trivium it becomes computational plus an unanalysed PRNG-leakage assumption. This holds equally for both lanes, so the relative comparison is unaffected.

## 7. Remaining limitations
- **Physical leakage:**
  - Hermelink, Ning, (Petri,) Strieder, *The Insecurity of Masked Comparisons: SCAs on ML-KEM's FO-Transform*, CCS 2024 (ePrint 2024/060; abstract only, full text blocked): attacks on t-probing-secure higher-order masked comparisons through vertical analysis of chosen-ciphertext distributions, not prevented by realistic orders.
  - Ranney et al., arXiv 2606.31681 (2026): an FPGA implementation of a higher-order masked comparison leaks at first order through parallelism.
  - Both concern the FO-comparison *function*, so they apply to PAMS and to the baseline alike. No TVLA was possible here, because no hardware is available.
- **Couplings and routing:** not modelled. The routed-netlist checks are logical, not electrical.
- **Integration:** A1 and A3 are interface assumptions. The per-coefficient decision shares (`cdec`) are exported for testing and must not be connected to unprotected logic.
- **PROLEAD coverage:**
  - statistical, with the simulation counts stated;
  - second order only at one steady-state cycle per lane (pipeline full, accumulator running); first order at every cycle;
  - probing sets near the dvalid cycle were not tested at second order.
- **Home-made components:** `compcheck.py` (preconditions) and `math/` (exactness). Both have negative controls or exhaustive checks, but they are not established tools.
- **maskVerif and Coco were not used:**
  - maskVerif needs OCaml/opam, which is absent with no root access, and it would only re-check the gadget that SILVER already proves;
  - Coco targets CPU and software co-verification (Ibex) and does not fit a pure hardware netlist;
  - coco-alma's SAT-based multi-cycle verification at second order on 4.6k–5k cells plus 40–57 gadgets was not attempted.
