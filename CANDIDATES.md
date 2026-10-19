# Candidate mechanisms (Phase XI)

| id | idea | analysis | result | status |
|---|---|---|---|---|
| **PAMS** | **pre-aligned modulus switching:** anchor at the integer interval start, Low_c = ⌊a_c 2^14/q⌋; switch shares to 2^14 (independent of d); decide [Z < Θ_c] with a public per-coefficient threshold | exhaustive exactness; K = 13 provably impossible for any rule; width 14 vs 24 | **−30% gadgets** (40 vs 57), −30% randomness (120 vs 171 bits/cycle) | **survivor (implemented)** |
| PAMS-split | Θ_c < 2^11 for all (c, d): carry-free zero test of Z[13:11] + comparator over 11 bits | same gadget count; shorter ripple | −21.3% area, −9.8% delay vs baseline (synthesis) | **final candidate** (`rtl/pams.v`) |
| PAMS-ripple | plain 14-bit ripple comparator | — | −13.2% area, −9.4% delay | retained (`rtl/pams_r.v`, ablation) |
| PAMS with prefix (log-depth) adder/comparator | latency and alignment registers down, gadgets up | count: comparator + adder ≈ 99 gadgets vs 38 | gadgets dominate area | rejected (model) |
| PAMS with power-of-two windows (top-bits rule per c) | offset Z so that members map to an aligned [0, 2^m) | alignment exists only when q/w is just above a power of two: fails for one of the two widths of every d at K = 14; needs K ≥ 19 overall | rejected (derivation) |
| Simple at t = 12 with a two-sided window | separable at t ≤ 12 (`impossible.py`), but needs a per-c comparator at width d + 12 | dominated by PAMS (same decision type, wider) | rejected |
| Fermat zero test (x′^{q−1}) over F_q | arithmetic-only predicate | ≈ 14 masked mod-q multiplications per coefficient | far more expensive than bit-level gadgets | rejected (count) |
| multiplier-free / approximate per-share scaling | cheaper constant multipliers | any extra per-share error widens the error set beyond {0, 1, 2}, so K = 14 no longer separates | rejected (exactness) |
| commutative / probabilistic aggregation | fewer nonlinear operations | not exact (false-accept probability) | excluded by contract |

## Ablation (synthesis, flow B, 5 mappings each)
| design | area µm² | Δ vs base | tclk ns | Δ | gadgets | random bits/cycle |
|---|---|---|---|---|---|---|
| base (Simple, optimized) | 21,598 | — | 1.649 | — | 57 | 171 |
| PAMS-ripple | 18,745 | −13.2% | 1.494 | −9.4% | 40 | 120 |
| PAMS-split | 16,998 | −21.3% | 1.487 | −9.8% | 40 | 120 |
