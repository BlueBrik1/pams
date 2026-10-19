# Mathematics of exact masked ciphertext verification (ML-KEM, q = 3329, 3 shares)

Scripts: `models/pams.py` (exactness), `models/impossible.py` (width lower bounds in the model), `models/gen.py` (circuits).

## 1. Function
- For d ∈ {4, 5, 10, 11} (d_v = 4/4/5 and d_u = 10/10/11 for ML-KEM-512/768/1024), FIPS 203 defines Compress_d(x) = ⌈2^d x / q⌋ mod 2^d.
- **Per coefficient:** P_d(x, c) = [Compress_d(x) = c], with x ∈ Z_q given as three arithmetic shares x_0 + x_1 + x_2 ≡ x (mod q), x_i ∈ [0, q), and c ∈ [0, 2^d) public.
- **Decision:** D = ∧ over all coefficients of u (d = d_u) and v (d = d_v) of P_d. It must be output as a Boolean sharing.
- **The contract covers every correctly sized ciphertext:** every c ∈ [0, 2^d) is legal input, and invalid ciphertexts simply give D = 0.

**Interval form.** Because q is odd there are no ties, so Compress_d(x) = c ⇔ (2c − 1)q/2^{d+1} < x < (2c + 1)q/2^{d+1} (mod q). Hence
- I_d(c) = [a_c, a_{c+1}) (cyclic in Z_q), with a_c = ⌈(2c − 1) q / 2^{d+1}⌉ mod q;
- the closed form equals the interval starts for all c, d (exhaustive, `pams.py`);
- widths: w_c ∈ {208, 209} (d = 4), {104, 105} (5), {3, 4} (10), {1, 2} (11).

## 2. Share-wise modulus switching lemma (exact, integer error)
For any K, let F(x) = ⌊x 2^K / q⌋ and y_i = F(x_i). Then **Σ y_i ≡ F(x) − j (mod 2^K) with j ∈ {0, 1, 2}**, where x ∈ [0, q) is the canonical value.

*Proof.*
- Write r_i = x_i 2^K mod q. Then F(x_i) = (x_i 2^K − r_i)/q.
- Σ x_i = x + kq with k ∈ {0, 1, 2}, so Σ F(x_i) = x 2^K/q + k 2^K − (Σ r_i)/q.
- Since Σ r_i ≡ x 2^K (mod q) and 0 ≤ Σ r_i < 3q, we have Σ r_i = r + jq with r = x 2^K mod q and j ∈ {0, 1, 2}.
- Therefore Σ F(x_i) = (x 2^K − r)/q − j + k 2^K = F(x) − j + k 2^K. ∎

(The lemma is also checked on 2·10⁵ random triples at K = 14 and 5·10⁴ at K = 24.)

**Consequence.** Any decision computed as a function of Z = (Σ y_i + public offset) mod 2^K is exact for *all* share triples iff it is exact for all (x, j, c, d) with j ∈ {0, 1, 2}. That is a finite domain: 3329 · 3 · (2^4 + 2^5 + 2^10 + 2^11) cases, checked exhaustively. The exhaustive enumeration together with the lemma is a complete proof of exactness for the specified decision rules.

## 3. Baseline: Simple (Fritzmann et al. 2022; D'Anvers et al. 2023), strongest member
- **Definition:** y_i = ⌊x_i 2^{d+t}/q⌋ and Z = Σ y_i − (c − ½) 2^t + A (mod 2^{d+t}). The decision is [the top d bits of Z are zero], equivalently Z < 2^t.
- **Exhaustive results:**
  - t = 13 with **A = 1** is exact for all d. The naive A = 0 fails: 2 mismatches at d = 11.
  - t = 12 has **no** exact offset A ∈ [−300, 300), and neither does t = 11.
  - At t = 11 or 12 the members and non-members are still separable (`impossible.py`, no collisions). An exact rule there would therefore need a per-c two-sided window comparator, i.e. a PAMS-type decision at a larger width, which PAMS dominates.
- **Hardware form** (one lane for all d): y_i = ⌊x_i 2^24/q⌋ ≫ (11 − d), giving a 24-bit lane. The low t = 13 bits contribute only a carry; the top region is bits 13 … 12 + d.

## 4. Candidate: pre-aligned modulus switching (PAMS)
- **Definition:** K = 14, Low_c = ⌊a_c 2^K/q⌋, Z = Σ y_i − Low_c + 2 (mod 2^14), Θ_c = Low_{c+1} − Low_c − 1. The decision is **[Z < Θ_c]**.
- **Exactness:** exhaustive over (x, j, c, d): **exact for all d** with offsets (A, B) = (2, −1).
- **Minimal width (in this model):** at K = 13, a member and a non-member of the same interval produce equal Z for every d (`impossible.py`). So *no* decision function of Z is exact, and **K = 14 is the minimum**.

**Why PAMS can be narrower.**
- The anchor Low_c is integer-aligned on the Z_q grid: it is the image of the integer interval start a_c.
- So the switched domain only has to separate neighbouring integers of Z_q under the error j ∈ {0, 1, 2}. The step 2^K/q must satisfy ⌊2^K/q⌋ ≥ 3, i.e. 2^K ≥ 3q, so K = 14. This is **independent of d**.
- The baseline anchors at a half-integer of the compressed grid and tests a fixed aligned block [0, 2^t). That needs fractional precision 2^t ≳ 6q, which costs d + 13 bits.
- PAMS pays for its narrow width with a per-coefficient public threshold Θ_c instead of a fixed aligned block. Section 6 shows that this threshold folds into the carry ripple.

**Public window constants** (closed forms, verified through the RTL tests). With e = 13 − d and r_c = ((1 − 2c) q) mod 2^{d+1}:
- Low_c = (2c − 1) 2^e + ⌊r_c 2^e / q⌋ (mod 2^14). The term (2c − 1) 2^e is an integer and ⌊r_c 2^e/q⌋ ∈ [0, 4].
- r_{c+1} = (r_c − 2q) mod 2^{d+1}.
- Θ_c = 2^{e+1} − 1 + ⌊r_{c+1} 2^e/q⌋ − ⌊r_c 2^e/q⌋.
- The wrap from c = 2^d − 1 to 0 is consistent, because 2^{d+1+e} = 2^14 and r_{2^d} = r_0.
- 3 ≤ Θ_c ≤ 1027 < 2^11 for every (c, d).

## 5. Masked kernel building blocks (identical in both lanes)
- **Share-domain operands.** y_i is used as share i of a Boolean sharing whose other shares are 0: (y_0, 0, 0), (0, y_1, 0), (0, 0, y_2).
- **CSA.** y_0 + y_1 + y_2 = S + 2C with S = y_0 ⊕ y_1 ⊕ y_2 (linear, no gadget) and C = maj(y_0, y_1, y_2).
  - maj(a, b, c) = ((a ⊕ b) ∧ (a ⊕ c)) ⊕ a costs **one AND gadget per bit**.
  - Mod 2^n only C_0 … C_{n−2} are needed; T = 2C.
- **Ripple carry.** c_1 = 0, c_2 = S_1 T_1, and c_{k+1} = maj(S_k, T_k, c_k) at one gadget per bit. The sum bit is z_k = S_k ⊕ T_k ⊕ c_k.
- **Carry-free zero test** (top region [m, n) with carry-in c_m).
  - **Claim:** (S + T + c_m)[n−1:m] = 0 ⇔ ∀k ∈ [m, n): S_k ⊕ T_k ⊕ c′_k = 0, where c′_m = c_m and c′_{k+1} = S_k ∨ T_k.
  - **Proof:**
    - (⇒) If every sum bit is 0, then c_k = S_k ⊕ T_k. So c_{k+1} = maj(S_k, T_k, S_k ⊕ T_k) = S_k ∨ T_k = c′_{k+1}, and every test holds.
    - (⇐) By induction the true carries equal c′, so every sum bit is 0. ∎
  - Each c′_k is independent of the ripple, so the region costs one OR gadget per bit plus an OR tree, all computed in parallel.
- **Ripple comparator with a public threshold.**
  - Let lt_{k+1} = [Z[k:0] < Θ[k:0]] = (¬z_k ∧ θ_k) ∨ ([z_k = θ_k] ∧ lt_k), with lt_0 = 0.
  - With θ_k public, this equals ((z_k ⊕ ¬θ_k) ∧ (lt_k ⊕ θ_k)) ⊕ θ_k: **one AND gadget**, all negations public and on share 0.
  - lt_1 = θ_0 ∧ ¬z_0 is linear.
- **Split comparator** (PAMS). Since Θ_c < 2^11, [Z < Θ] = [Z[13:11] = 0] ∧ [Z[10:0] < Θ[10:0]]. The top 3 bits use the carry-free test, so the ripple ends at bit 11.

## 6. Cost (AND gadgets per lane, measured from the generated circuits)
| part | baseline (n = 24, t = 13) | PAMS (n = 14, m = 11) |
|---|---|---|
| CSA majorities | 23 | 13 |
| ripple carries | 12 (c_2 … c_13) | 10 (c_2 … c_11) |
| top region (carry-free ORs + tree) | 10 + 10 | 2 + 1 |
| comparator | — | 10 (lt_2 … lt_11) |
| final combination | 0 (+ NOT) | 2 |
| **kernel total** | **55** | **38** |
| accumulator (both) | 2 | 2 |
| **fresh random bits per cycle** (3 per gadget) | **171** | **120** |

Share-wise linear work:
- **Baseline:** three exact ⌊x · 2^24/q⌋ multipliers (M = 10569051393, 34 bits, S = 21), a mode shifter, and a 24-bit offset subtraction.
- **PAMS:** three ⌊x · 2^14/q⌋ multipliers (M = 10321339, 24 bits, S = 21), plus the public Low/Θ logic, which is one constant multiply by q, 8 small comparators and adders.

## 7. Limits of the proofs
- **Exactness** (§2–§4) is complete for the stated input contract: canonical shares x_i ∈ [0, q), any c ∈ [0, 2^d), the four d values. Non-canonical upstream share representations would need a separate argument.
- **Width minimality** holds only in the share-wise-floor model. Other conversions (e.g. prime-modulus A2B) are not covered.
- **Gadget counts** are for these ripple structures. Prefix (log-depth) structures trade gadgets for latency in both lanes alike; they were not pursued, because they increase area.
