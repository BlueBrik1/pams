#!/usr/bin/env python3
"""Exactness of masked ciphertext-coefficient verification predicates (ML-KEM, q = 3329, 3 arithmetic shares).

Target predicate:
  P_d(x, c) = [Compress_d(x) == c], with Compress_d(x) = round(2^d x / q) mod 2^d (FIPS 203)
  for x in Z_q, c in [0, 2^d), d in {4, 5, 10, 11}.

Share lemma (proved in MATHEMATICS.md; checked here on random shares):
  for x_0 + x_1 + x_2 = x (mod q), x_i in [0, q), any integer s_num and scale 2^K / q,
  sum_i floor(x_i 2^K / q) = floor(x 2^K / q) - j  (mod 2^K)  with j in {0, 1, 2}.
  So every share-wise-floored design is exact iff its decision is correct for all (x, j, c).

Designs:
- 'simple' (baseline; Fritzmann et al. 2022 / D'Anvers et al. 2023 "Simple"), at a uniform W-bit width:
  Y = sum floor(x_i 2^W / q);  Z = Y - (c - 1/2) 2^(W - d) + A  (mod 2^W);  decide [top d bits of Z == 0].
  The centering offset A (absorbing the one-sided share error j) is optimised for the baseline too.
- 'pams' (candidate: pre-aligned modulus switching), at width K:
  a_c = interval start of c in Z_q;  Low_c = floor(a_c 2^K / q);  Y = sum floor(x_i 2^K / q);
  Z = Y - Low_c + A  (mod 2^K);  decide [Z < Theta_c],  Theta_c = Low_{c+1} - Low_c + B.
  Low_c is computed from (c, d) by public logic (exact identity checked below).
usage: python3 -I pams.py"""
import random
import numpy as np
Q = 3329

def compress(x, d):
    return ((x << d) * 2 + Q) // (2 * Q) % (1 << d)     # round(2^d x / q), ties impossible (q odd)

def starts(d):
    """a_c: smallest x (cyclically) with Compress_d(x) = c; interval [a_c, a_{c+1}) mod q."""
    a = [None] * (1 << d)
    comp = [compress(x, d) for x in range(Q)]
    for x in range(Q):
        if comp[x] != comp[(x - 1) % Q]: a[comp[x]] = x
    return a

def a_formula(c, d):
    """public closed form: a_c = ceil((2c - 1) q / 2^(d+1)) mod q."""
    return (-((-(2 * c - 1) * Q) // (1 << (d + 1)))) % Q

def low_formula(c, d, K):
    """Low_c = floor(a_c 2^K / q) via (2c - 1) 2^(K-d-1) + floor(r 2^(K-d-1) / q) (mod 2^K); r = ((1-2c) q) mod 2^(d+1)."""
    r = ((1 - 2 * c) * Q) % (1 << (d + 1))
    return ((2 * c - 1) * (1 << (K - d - 1)) + (r << (K - d - 1)) // Q) % (1 << K)

def check_simple(W, d, A=0):
    x = np.arange(Q, dtype=np.int64)
    F = (x << W) // Q
    truth_c = np.array([compress(int(v), d) for v in x])
    bad = 0
    for j in range(3):
        for c in range(1 << d):
            Z = (F - j - (((2 * c - 1) << (W - d - 1))) + A) % (1 << W)
            dec = (Z >> (W - d)) == 0
            bad += int(np.count_nonzero(dec != (truth_c == c)))
    return bad

def check_pams(K, d, A, B):
    x = np.arange(Q, dtype=np.int64)
    F = (x << K) // Q
    a = starts(d)
    truth_c = np.array([compress(int(v), d) for v in x])
    bad = 0
    for c in range(1 << d):
        lo = low_formula(c, d, K); hi = low_formula((c + 1) % (1 << d), d, K)
        assert lo == (a[c] << K) // Q, (c, d)                      # public closed form == definition
        theta = (hi - lo + B) % (1 << K)
        for j in range(3):
            Z = (F - j - lo + A) % (1 << K)
            bad += int(np.count_nonzero((Z < theta) != (truth_c == c)))
    return bad

def lemma_random(K, trials=200000):
    rng = random.Random(1)
    for _ in range(trials):
        xs = [rng.randrange(Q) for _ in range(3)]; x = sum(xs) % Q
        j = ((x << K) // Q - sum((v << K) // Q for v in xs)) % (1 << K)
        assert j in (0, 1, 2), (xs, j)
    return trials

if __name__ == '__main__':
    for d in (4, 5, 10, 11):
        assert all(a_formula(c, d) == s for c, s in enumerate(starts(d)))
    print('a_c closed form == interval starts for d = 4, 5, 10, 11: PASS')
    print('share lemma j in {0,1,2}:', lemma_random(14), 'random triples PASS (K=14);', lemma_random(24, 50000), 'PASS (W=24)')
    for W in (22, 23, 24):
        for A in range(0, 4):
            print(f'simple W={W} A={A}: mismatches per d', {d: check_simple(W, d, A) for d in (4, 5, 10, 11)})
    for K in (13, 14):
        best = None
        for A in range(0, 4):
            for B in range(-3, 4):
                bad = sum(check_pams(K, d, A, B) for d in (4, 5, 10, 11))
                if bad == 0: best = (A, B); break
            if best: break
        print(f'pams K={K}: exact offsets (A, B) =', best)
