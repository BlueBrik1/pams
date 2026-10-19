# Security argument (second-order, 3 shares) and its evidence

## Leakage model and target
- **Target:** glitch-robust 2-probing security (robust probing model).
  - A probe on a combinational wire reveals every stable signal (register outputs, primary inputs) in its combinational fan-in cone within the cycle.
  - A probe on a register reveals its value.
  - **Transitions (memory-on-register effects) and coupling are not covered.**
- **Composition notion:** PINI (Cassiers & Standaert, IEEE TIFS 2020).
  - For any t₁ internal probes plus output probes on share indices O (t₁ + |O| ≤ 2), the observation is simulatable from the input shares with indices I ∪ O for some |I| ≤ t₁.
  - Glitch-robust PINI gadgets compose trivially, including through feedback, provided every share index stays in its own domain.
- **Inputs:**
  - the three arithmetic shares x_0, x_1, x_2 ∈ [0, q), a uniform sharing produced by a PINI-compatible upstream (domain i receives x_i only);
  - public c and parameter set;
  - fresh uniform random bits each cycle.
- **Output:** a Boolean sharing (3 shares) of the decision, to be consumed by a PINI implicit-rejection selector (outside the boundary).

## Composition argument (both lanes; identical structure)
1. **Share-local operations are trivially PINI.** These are:
   - the share-wise scaling y_i = ⌊x_i 2^K/q⌋;
   - public offset subtraction on share 0;
   - share-wise XOR;
   - NOT and public-controlled negation on share 0;
   - AND with a public bit;
   - share-wise pipeline registers.
   Every output share i depends only on input share i and public data, so a glitch-extended probe in domain i sees domain i only.
2. **Arithmetic-to-Boolean domain mapping.** The value y_i becomes share i of a Boolean sharing with zero shares elsewhere. Domain i still holds only y_i, which is a function of x_i alone.
3. **Every nonlinear operation is an HPC2 AND gadget** (Cassiers, Grégoire, Levi, Standaert, IEEE TC 2021). The paper proves it glitch-robust t-PINI with d(d+1)/2 = 3 fresh random bits per gadget per cycle for 3 shares. The accumulator is the same gadget used with feedback.
4. **Composition.** By (1)–(3) and PINI composition, the lane is glitch-robust 2-PINI. Any two probes are simulatable from at most two input shares (x_i, x_j), which are jointly uniform and independent of x. The output sharing is PINI-compatible.
5. **Constant time.** Fixed latency (base 31 cycles, PAMS 29), no data-dependent control, and public-only control signals (c, parameter set, first/last).

## Evidence (by type)
| type | what | result |
|---|---|---|
| functional equivalence | exhaustive (x, j, c, d) proof + lemma (MATHEMATICS §2–4); RTL simulation with random shares and fresh randomness (3,000–8,000 boundary-focused coefficients, mixed d, ciphertext aggregation); gate-level simulation of every synthesized mapping | exact; 0 mismatches |
| gadget-level formal check (home-made, exhaustive) | `models/hpc2check.py`: every probe set of size ≤ 2 over the 63 probe positions of the HPC2 RTL, glitch-extended; probing security and PINI | **0 failures** |
| negative control of that check | `hpc2check.py --broken` (b_j ⊕ r_ij not registered before meeting a_i) | **108 PINI failures**: the checker detects the classic glitch flaw |
| structural domain check (home-made) | `models/domaincheck.py` on every mapped netlist (liberty pin directions): no cell outside a gadget mixes share domains; randomness only reaches gadget r ports; output share i is domain i | **0 violations** for all 15 mappings (base, pams, pams_r) |
| negative control of that check | lane with one deliberate cross-domain XOR (`gen.py --leak`) | **79 violations** detected |
| established tool-based leakage verification | maskVerif / SILVER / PROLEAD / Coco | **not run** (not installed; not attempted) |
| physical side-channel evidence | TVLA / power traces | **none** |

## Unresolved risks and assumptions
1. **No established verification tool was used.** The home-made checks cover:
   - the gadget, exhaustively (as written in RTL);
   - domain separation outside gadgets, structurally.
   They do not cover glitch-extended probes spanning gadget boundaries beyond what PINI composition guarantees, transitions, or coupling.
2. **Synthesis and P&R.**
   - HPC2 is kept as a hierarchical module (`keep_hierarchy`) and the domain check runs on the mapped netlists.
   - Gadget internals after mapping are not re-verified at gate level.
   - A production flow must preserve gadget boundaries and register stages (no retiming), and should use the technology-specific primitives discussed in Adams Bridge's integration notes.
3. **Randomness.**
   - 120 (PAMS) or 171 (baseline) uniformly random, fresh bits per cycle are assumed.
   - The cost model uses Trivium-64 instances (`rtl/trivium64.v`, checked against a reference), seeded from a TRNG not included here.
   - The security of a PRNG-fed masking scheme also relies on that generator.
4. **Upstream and downstream.** Canonical share range and PINI-compatible production of the shares upstream are assumed. The decision sharing must be consumed by a protected selector and never recombined.
5. **Composition at higher orders or with other gadget families** (DOM, HPC3) is not evaluated.
6. **Both lanes rest on exactly the same assumptions.** The comparison isolates the algorithm. Relative claims (area, delay) do not depend on these risks, but absolute security claims do.

**Classification:**
- Functional correctness: established.
- Second-order security: argued compositionally, with the gadget formally checked by a home-made exhaustive tool and negative controls.
- Tool-based verification with established tools and physical evidence: **missing**.
