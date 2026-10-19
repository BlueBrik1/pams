#!/usr/bin/env python3
"""Smallest exact constant-multiplier forms floor(x 2^K / q) = (x*M + C) >> S for all x in [0, q), and their CSD
weights (shift-add terms); used identically for both lanes.  usage: python3 -I mulsearch.py K [K ...]"""
import sys
Q = 3329
def csd(n):
    w = 0
    while n:
        if n & 1:
            d = 2 - (n & 3); n -= d; w += 1
        n >>= 1
    return w
def best(K):
    xs = range(Q); tgt = [(x << K) // Q for x in xs]; out = []
    for S in range(1, 32):
        for M in (-(-(1 << (K + S)) // Q), (1 << (K + S)) // Q):
            for C in range(0, 1 << S, max(1, (1 << S) // 64)):
                if all(((x * M + C) >> S) == t for x, t in zip(xs, tgt)):
                    out.append((S, M, C, csd(M))); break
        if out: return min(out, key=lambda o: (o[3], o[0]))
for K in map(int, sys.argv[1:]):
    S, M, C, w = best(K); print(f'K={K}: S={S} M={M} ({M.bit_length()} bits, CSD weight {w}) C={C}')
