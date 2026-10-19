#!/usr/bin/env python3
"""Width lower bounds within the share-wise-floor model (any decision rule on the switched value Z).
For a width K, scale 2^K/q and anchor rule, the decision must be a function of Z = (F(x) - j - anchor) mod 2^K with
j in {0, 1, 2}. If some member x and some non-member x' of the same interval (same c, d, hence the same anchor) give
equal Z for some j, j', then no decision function of Z is exact.
- pams anchor Low_c = floor(a_c 2^K / q);
- 'simple' anchor (c - 1/2) 2^(K-d), with the scale 2^K / q, K = d + t.
usage: python3 -I impossible.py"""
import sys; sys.path.insert(0, '.')
import pams as P
Q = 3329
def collide(K, d, anchor):
    F = [(x << K) // Q for x in range(Q)]; comp = [P.compress(x, d) for x in range(Q)]
    for c in range(1 << d):
        A = anchor(c)
        mem = {(F[x] - j - A) % (1 << K) for x in range(Q) if comp[x] == c for j in range(3)}
        non = {(F[x] - j - A) % (1 << K) for x in range(Q) if comp[x] != c for j in range(3)}
        if mem & non: return c
    return None
if __name__ == "__main__":
    for K in (13, 14):
        r = {d: collide(K, d, lambda c, d=d: P.low_formula(c, d, K)) for d in (4, 5, 10, 11)}
        print(f'pams K={K}: colliding c per d (None = separable):', r)
    for t in (11, 12, 13):
        r = {d: collide(d + t, d, lambda c, d=d: ((2 * c - 1) << (t - 1))) for d in (4, 5, 10, 11)}
        print(f'simple t={t}: colliding c per d (None = separable):', r)
