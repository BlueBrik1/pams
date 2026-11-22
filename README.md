# PAMS

**Pre-Aligned Modulus Switching for Exact Second-Order Masked ML-KEM Ciphertext Verification in Hardware**

PAMS checks whether a secret coefficient, held in three arithmetic shares, compresses to the coefficient received in an ML-KEM ciphertext. It performs the check without reconstructing the secret and uses the same 14-bit datapath for all four ML-KEM compression widths.

In a matched hardware comparison, the PAMS verification lane used **19.5% less routed standard-cell area** and **29.8% fewer fresh random bits per cycle** at comparable clock periods. Both designs processed one coefficient per cycle.

## How it works

During decapsulation, ML-KEM re-encrypts a recovered message and checks that the result matches the received ciphertext. For each coefficient, the verification lane must decide whether `Compress_d(x) = c`, where `x` is secret, `c` is public, and `d` is 4, 5, 10, or 11.

For a given `c` and `d`, the secret values that compress to `c` form a known interval modulo 3329. PAMS uses that interval to perform the check directly.

1. Switch each of the three arithmetic shares independently into the same 14-bit representation.
2. Apply a fixed correction for the bounded rounding error and use the public interval start to shift the comparison.
3. Compare the masked result against a public threshold derived from `c` and `d`.

The threshold changes with the received coefficient and compression width. The protected computation stays 14 bits wide. The construction preserves the exact decision at interval boundaries, including the interval that wraps around zero.

## Results

The baseline is an optimized implementation of the conventional **Simple** method using the same masking gadgets and design flow.

| Verification-lane metric | Simple baseline | PAMS |
|---|---:|---:|
| Protected HPC2 gadgets | 57 | 40 |
| Fresh random bits per cycle | 171 | 120 |
| Protected width at `d = 11` | 24 bits | 14 bits |
| Sustained throughput | 1 coefficient per cycle | 1 coefficient per cycle |

The 19.5% area reduction was measured after place and route at the 2.0 ns and 1.2 ns clock targets using OpenROAD and the Nangate45 standard-cell library. These figures are design-tool estimates for the verification lane. Whole-core savings depend on how the lane and its randomness supply are integrated.

## Security evidence

The three-share design targets second-order security in the glitch-robust probing model, assuming ideal fresh randomness and uniformly generated input shares. The evaluation combines SILVER gadget verification, structural checks on the netlist, and focused PROLEAD simulations.

Physical leakage on fabricated silicon, transition leakage, and the implementation of the randomness source remain open evaluation questions.

## Research contribution

PAMS combines published techniques for share-wise modulus switching, precision selection, and interval comparison. Its contribution is the way these techniques are combined to keep the protected verification width independent of `d`, together with a hardware evaluation against a matched exact baseline.
