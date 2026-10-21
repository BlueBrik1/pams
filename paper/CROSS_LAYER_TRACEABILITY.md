# Cross-layer traceability

This document traces each operation of PAMS through five layers: the equation, the Verilog, the gates, the layout and the measured cost. The concise forms are Table 3 (Section 3.1 H) and Table 24 (Appendix D.8).

- **Design:** `final/rtl/pams_jqr.v`, SHA-256 `804fd73a…3760ba0e7f`, 2,747 lines.
- **Gate level:** synthesis mapping 0, `competitors/runs/syn_pams_jqr_p0/mapped.{v,json}` (Yosys 0.33 + ABC, Nangate45, flow B).
- **Physical:** the routed run `final/runs/pnr_pams_jqr_T1.2_s1` unless stated otherwise.
- **Stage s:** the value is held after s rising clock edges counted from the cycle the coefficient is applied.

## How to read the gate-level column

Synthesis preserves exactly three things that can be traced by name:

1. **Register names.** Every flip-flop's Q net carries its RTL register name, such as `x1r[5]`, `ml1[23]` or `r106`.
2. **Gadget boundaries.** `hpc2` is synthesized with `keep_hierarchy`, so each `ug…` instance survives as one instance of a verified mapped variant (v0 or v1).
3. **Share-domain connectivity.** This is checked by `validation/structure/compcheck.py`.

Combinational logic between registers does **not** keep RTL names. ABC restructures it freely: XOR chains become XNOR trees, inverters are absorbed, and constant multipliers become carry-save trees. For such logic, the gate-level region is therefore given as the fan-in cone of named registers. The mapping from RTL expressions to gates is many-to-one, and no one-to-one gate correspondence is claimed.

## Operation table

| # | operation | equation | Verilog lines | RTL signals | stage | gate-level region (mapping 0) | routed / physical | figures | synthesized area |
|---|---|---|---|---|---|---|---|---|---|
| 1 | arithmetic-share input | (4) | 21–26, 42–43 | `x0..x2` → `x0q..x2q` → `x0r..x2r` | 1–2 | 72 `DFF_X1` with Q = `x?q[11:0]` (36) and `x?r[11:0]` (36) | launch registers of the worst routed path at 1.2 ns (`x1r[5]`) | 2, 12 | 326 µm² |
| 2 | mode decode | — | 25–26 | `mode` → `d0`; `c` → `c0` | 1 | 11 `DFF_X1` (group "input registers (public c, d)") + decode logic | — | 2 | 50 µm² (flip-flops) |
| 3 | public residues and qq | (21), A.5 | 28–40 | `e0`, `rmask`, `pr`, `rc`, `rn`, `qc`, `qn` | 1→2 | fan-in cones of `qcr[2:0]`, `qnr[2:0]` (12-bit constant multiplier, masks, 4-comparator `qq`) | — | 2 | part of 1,337 µm² public logic |
| 4 | public anchor Low_c | (7), (20)–(21) | 41–44, 48–54 | `qcr`, `e0r`, `c0r` → `lowr` → `lowrq` → `lowp` | 2–4 | fan-in cone of `lowrq[13:0]`: shifter + small adder | worst routed path at 2.0 ns (`e0r → lowrq`) and at 1.1 ns (`c0r → lowrq`) | 2 | (1,337 µm², with 5) |
| 5 | public threshold Θ_c | (8), (22) | 39–40, 45, 48–56 | `qnr`, `qcr` → `thr` → `thrq` → `thp` → `th2` | 2–5 | fan-in cones of `thrq`, `thp`, `th2` | — | 2 | (1,337 µm², with 4) |
| 6 | share-wise modulus switch F₁₄(x_i) | (9) | 46–54 | `mh?`, `ml?` (stage 3), `m?` (comb.), `s?` → `s?p` (stage 4) | 3–4 | fan-in cones of `mh?`/`ml?` (constant multiplier by M = 10321339: XOR/XNOR trees + AOI/OAI carry chains) and of `s?p` (recombination adder m_i = 2⁶·mh_i + ml_i < 2³⁵, bits 34–21 kept) | worst routed path at 1.2 ns, both designs: share-wise multiplier stage (Figure 12); orange cells in Figure 4 | 2, 4, 12 | 3,528 µm² (registers + logic, 3 shares) |
| 7 | anchoring of share 0 | (10) | 56 | `y0 <= s0p - lowp + 2` | 5 | 14 `DFF_X1` (Q = `y0`) + 14-bit subtract-add; about 87 cells, 104 µm² | — | 2 | 294 µm² (all `y?` registers + logic) |
| 8 | other shares | (10) | 56 | `y1 <= s1p`, `y2 <= s2p` | 5 | 28 `DFF_X1` | — | 2 | (in 294 µm²) |
| 9 | CSA (3 → 2 operands) | (11), B.6 | 58–1537 | S_k = ⊕ share-local (`x…` wires); T_k majorities `ug111, ug153, ug227, ug319, ug429, ug557, ug703, ug867, ug1049, ug1249, ug1341, ug1417, ug1449` | 5–31 | 13 `hpc2` instances | blue cells in Figure 4 | 3, 8 | 13 × 180.35 µm² |
| 10 | ripple carry | (11) | 58–1537 | `ug134, ug187, ug267, ug365, ug481, ug615, ug767, ug937, ug1125, ug1331` | 5–31 | 10 `hpc2` | blue | 3, 8 | 10 × 180.35 µm² |
| 11 | low comparator [Z₁₀:₀ < Θ₁₀:₀] | (12), (24) | 58–1537 | `ug128, ug173, ug251, ug347, ug461, ug593, ug743, ug911, ug1097, ug1301` | 5–31 | 10 `hpc2`; θ bits enter through share-0 XOR / AND-with-public (`a…`) cells | blue | 3, 8 | 10 × 180.35 µm² |
| 12 | top-bit zero test [Z₁₃:₁₁ = 0] | (24) | 58–1537 | ORs `ug1438, ug1470`; OR tree `ug1483`; AND `ug1535` | 5–31 | 4 `hpc2` | blue | 8 | 4 × 180.35 µm² |
| 13 | final decision b | (12) | 1500–1537 (instance), 2733 (`cdec`) | `ug1542` → `cdec` | 31 | 1 `hpc2` | — | 2 | 180.35 µm² |
| 14 | operand alignment | B.8 | 58–1499, 1538–2729 | 1,190 delay assignments `r…` | 5–31 | **782** `DFF_X1` (Yosys merges RTL registers with the same source and depth): 406 y bits, 240 θ bits, 100 share-local wires, 36 gadget outputs | green cells in Figure 4 | 4 | 3,558 µm² |
| 15 | share-local XOR network | B.6 | 58–1499 | `x…`, `n…`, `a…` wires | comb. | 162 XOR/XNOR cells at gadget inputs (restructured by ABC) | — | 3 | 256 µm² |
| 16 | HPC2 gadget (internal) | B.2 | 4–19 | `ra, rb, rr, rbr, p0, u, v` | 2 cycles | 63 cells per instance: 30 `DFF_X1`, 15 `AND2_X1`, 6 `XOR2_X1`, 12 `XNOR2_X1`; variants v0 / v1, both SILVER-verified | the routed G-check confirms every instance equals the verified gadget | 14 (conceptual), 15 (extracted) | 180.35 µm² each |
| 17 | ciphertext accumulation D = ∧b | (3) | 2730–2746 | `vp/fp/lp`, `init_p`, `acc_in`, `uacc`, `acc_out`, `ufin`, `dec`, `dvalid` | 31–35 | 2 `hpc2` + 3 `DFF_X1` + control shift registers | — | 2 | 361 µm² (gadgets) + 457 µm² (control, inputs) |

The gadget instances are checked in two ways:

- **Identity.** In each of the 24 final netlists checked, every gadget instance matches mapped variant v0 or v1 (`final/runs/gadget_identity.json`).
- **Structure.** The checks of `compcheck.py` (D, R, P, O and G) passed on 40 routed netlists (`final/runs/routed_check_final.json`).

The 40 / 57 gadget count is the same in the RTL and in the synthesized and routed netlists.

## Per-equation map

| equation (paper number) | meaning | implemented by (row above) | verified by |
|---|---|---|---|
| (1), (14) Compress_d | the target function | 9–13 as a whole | `validation/math/audit.py` A, exhaustive; functional simulation D.6 |
| (2), (15) intervals I_c | Compress_d(x) = c ⟺ x ∈ [a_c, a_{c+1}) | 4, 5 | audit A, Table 8, Table 10 |
| (5), (18) Lemma 1 | ΣF(x_i) ≡ F(x) − j | 6 | enumeration of all 3,329³ canonical triples (`validation/math/lemma.c`); audit D |
| (7), (20)–(21) Low_c | anchor | 3, 4 | `check_pams` over all 3,120 (c, d); Table 10; trace in Table 16 |
| (8), (22) Θ_c | threshold | 3, 5 | the same; Table 10 |
| (9) y_i | share-wise switch | 6 | RTL simulation vs. reference (`scripts/examples.py`, `scripts/appendix_data.py`) |
| (10) ŷ₀ | anchoring | 7 | the same |
| (11) Z | three-operand sum mod 2¹⁴ (never formed in the clear) | 9, 10 | functional simulation (RTL, gate, routed) |
| (12) b | the decision | 11–13 | exactness (Proposition 1, A.7) + functional simulation |
| (24) split comparator | [Z < Θ] = [Z₁₃:₁₁ = 0] ∧ [Z₁₀:₀ < Θ] | 11, 12 | A.8; Phase XII check D |
| (3) D | ciphertext decision | 17 | functional simulation (accepting and rejecting ciphertexts, Table 22) |

## Security layer

| property | where it holds | evidence |
|---|---|---|
| each nonlinear operation is a glitch-robust 2-PINI gadget | rows 9–13, 16, 17 | SILVER on both mapped variants (D.1) |
| every non-gadget operation is share-local or public | rows 1–8, 14, 15 | `compcheck.py` D, R, P and O checks, on 5 mappings + 40 routed netlists (D.2) |
| fresh randomness is used once per gadget | `rnd[3g+2:3g]` → gadget g | compcheck R |
| constant time | control rows 2 and 17 | cone analysis of `cvalid`/`dvalid`, 12 netlists |
| no detected leakage in simulation | whole lane | PROLEAD, orders 1 and 2 (Table 5, Table 20). This is not proof of physical security. |

## Where the layers do not line up one-to-one

- **Merged delay registers.** The RTL has 1,190 delay-register assignments; synthesis keeps 782 flip-flops (row 14). The duplicates are the same source delayed by the same depth for different consumers.
- **Multiplier.** A partial product such as `ml1` (RTL line 49) is a single `*` operator. In gates it is a carry-save tree of XOR/XNOR/NAND cells followed by an AOI/OAI carry chain. The 21-cell routed critical path at 1.2 ns goes through such a tree (Figure 12). Individual cells cannot be assigned to individual partial-product bits.
- **XOR polarity.** ABC realizes some share-local XORs as XNOR cells and absorbs inverters (for example `x115` in Figure 3). The share domain is preserved, which is what compcheck verifies.
- **Public logic.** `qq`, the multiplications by 3,329 and the shifts are merged into one cone per register, which is why the public lane is costed as one block: 1,337 µm² for PAMS vs. 464 µm² for the baseline.

## Area roll-up (synthesis, mapping 0; Table 19)

| block | PAMS µm² | baseline µm² | Δ |
|---|---:|---:|---:|
| HPC2 gadgets (40 / 57) | 7,214 | 10,280 | −3,066 |
| alignment (delay flip-flops + logic) | 3,558 | 4,016 | −457 |
| partial products (registers + logic) | 2,993 | 3,297 | −304 |
| share inputs, x_r, switched values (incl. Yosys-named) | 860 | 1,310 | −449 |
| aligned operands y_i (registers + logic) | 294 | 827 | −533 |
| public constants (registers + logic) | 1,337 | 464 | +873 |
| public inputs c, d; control; accumulator flip-flops | 507 | 534 | −27 |
| gadget-input XOR network | 256 | 266 | −10 |
| logic shared between groups | 3 | 105 | −101 |
| **total** | **17,022** | **21,097** | **−4,075** |

The rows are summed from `paper/data/resources.json`, the same data as Table 19 in Appendix C.7; the rounded differences add up to the total within 1 µm². The grouping here merges registers with the logic attributed to them. Logic attribution follows each cell's fan-out cone and is therefore approximate where ABC shares logic between groups. The 19.5 % routed-area figure applies to this verification lane only, not to a full ML-KEM accelerator.
