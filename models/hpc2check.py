#!/usr/bin/env python3
"""Exhaustive glitch-extended 2-probe check of the HPC2 gadget exactly as written in gen.py (3 shares).

Model:
- Every wire of the gadget is a probe position.
- A probe on a combinational wire reveals its glitch-extended cone, i.e. all stable signals (registers / primary
  inputs) feeding it within the clock cycle.
- A probe on a register reveals the register.
Checks, for every set of at most 2 probes (internal and/or output shares):
1. probing security: the joint distribution of the revealed values is independent of the secrets (a, b);
2. PINI (Cassiers-Standaert): with t1 internal probes and output probes on share indices O, the revealed values are a
   randomised function of the input shares with indices I u O only, for some |I| <= t1.
Inputs a_i, b_i are arbitrary share values (all 64 combinations); randomness r01, r02, r12 uniform (8 combinations).
This verifies the gadget implementation only; composition is argued in SECURITY.md.
usage: python3 -I hpc2check.py [--broken]"""
import itertools, sys
from collections import Counter
BROKEN = '--broken' in sys.argv   # negative control: b_j ^ r_ij not registered before meeting a_i (glitchy)

PAIRS = [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]     # rbr / u / v index order in gen.py
RIDX = {frozenset((0, 1)): 0, frozenset((0, 2)): 1, frozenset((1, 2)): 2}

def signals():
    """name -> (kind, function(env) -> value, cone list of stable names).
    env holds: a0..a2, b0..b2, r0..r2 (inputs); stage-1 / stage-2 register values are derived."""
    S = {}
    for i in range(3):
        S[f'a{i}'] = ('in', None, [f'a{i}']); S[f'b{i}'] = ('in', None, [f'b{i}'])
    for k in range(3): S[f'r{k}'] = ('in', None, [f'r{k}'])
    for n, (i, j) in enumerate(PAIRS):                       # combinational b_j ^ r_ij before its register
        S[f'bxr{n}'] = ('comb', None, [f'b{j}', f'r{RIDX[frozenset((i, j))]}'])
    for i in range(3):
        S[f'ra{i}'] = ('reg', None, [f'ra{i}']); S[f'rb{i}'] = ('reg', None, [f'rb{i}'])
    for k in range(3): S[f'rr{k}'] = ('reg', None, [f'rr{k}'])
    for n in range(6): S[f'rbr{n}'] = ('reg', None, [f'rbr{n}'])
    for i in range(3): S[f'w_p0{i}'] = ('comb', None, [f'ra{i}', f'rb{i}'])
    for n, (i, j) in enumerate(PAIRS):
        S[f'w_u{n}'] = ('comb', None, [f'ra{i}', f'rr{RIDX[frozenset((i, j))]}'])
        S[f'w_v{n}'] = ('comb', None, [f'ra{i}', f'b{j}', f'r{RIDX[frozenset((i, j))]}'] if BROKEN else [f'ra{i}', f'rbr{n}'])
    for i in range(3): S[f'p0{i}'] = ('reg', None, [f'p0{i}'])
    for n in range(6): S[f'u{n}'] = ('reg', None, [f'u{n}']); S[f'v{n}'] = ('reg', None, [f'v{n}'])
    for i in range(3):                                       # output shares (combinational XOR of 5 registers)
        own = [n for n, (ii, _) in enumerate(PAIRS) if ii == i]
        S[f'c{i}'] = ('out', i, [f'p0{i}'] + [f'u{n}' for n in own] + [f'v{n}' for n in own])
    return S

def evaluate(a, b, r):
    e = {**{f'a{i}': a[i] for i in range(3)}, **{f'b{i}': b[i] for i in range(3)}, **{f'r{k}': r[k] for k in range(3)}}
    for i in range(3): e[f'ra{i}'] = a[i]; e[f'rb{i}'] = b[i]
    for k in range(3): e[f'rr{k}'] = r[k]
    for n, (i, j) in enumerate(PAIRS): e[f'rbr{n}'] = b[j] ^ r[RIDX[frozenset((i, j))]]
    for i in range(3): e[f'p0{i}'] = a[i] & b[i]
    for n, (i, j) in enumerate(PAIRS):
        e[f'u{n}'] = (1 - a[i]) & r[RIDX[frozenset((i, j))]]; e[f'v{n}'] = a[i] & e[f'rbr{n}']
    return e

def check():
    S = signals(); names = list(S)
    # correctness
    for a in itertools.product((0, 1), repeat=3):
        for b in itertools.product((0, 1), repeat=3):
            for r in itertools.product((0, 1), repeat=3):
                e = evaluate(a, b, r)
                c = [e[f'p0{i}'] ^ e[f'u{n}'] ^ e[f'v{n}'] ^ e[f'u{m}'] ^ e[f'v{m}'] for i, (n, m) in enumerate([(0, 1), (2, 3), (4, 5)])]
                assert c[0] ^ c[1] ^ c[2] == (a[0] ^ a[1] ^ a[2]) & (b[0] ^ b[1] ^ b[2])
    shares = list(itertools.product((0, 1), repeat=6)); rands = list(itertools.product((0, 1), repeat=3))
    def view(probes, sh, r):
        e = evaluate(sh[:3], sh[3:], r)
        if any(S[p][0] == 'out' for p in probes):
            for i in range(3):
                e[f'c{i}'] = e[f'p0{i}'] ^ e[f'u{2*i}'] ^ e[f'v{2*i}'] ^ e[f'u{2*i+1}'] ^ e[f'v{2*i+1}']
        return tuple(e[p] if S[p][0] == 'out' else tuple(e[x] for x in S[p][2]) for p in probes)
    sets = [(p,) for p in names] + list(itertools.combinations(names, 2))
    bad_sec = bad_pini = 0
    for P in sets:
        # 1. probing security over uniform sharings of each secret pair
        dists = []
        for a, b in itertools.product((0, 1), repeat=2):
            d = Counter()
            for a0, a1, b0, b1 in itertools.product((0, 1), repeat=4):
                sh = (a0, a1, a ^ a0 ^ a1, b0, b1, b ^ b0 ^ b1)
                for r in rands: d[view(P, sh, r)] += 1
            dists.append(d)
        if any(d != dists[0] for d in dists): bad_sec += 1; print('SECURITY FAIL', P)
        # 2. PINI: find I (|I| <= t1) such that the view distribution depends only on shares in I u O
        O = {S[p][1] for p in P if S[p][0] == 'out'}; t1 = sum(S[p][0] != 'out' for p in P)
        ok = False
        for I in itertools.chain.from_iterable(itertools.combinations(range(3), k) for k in range(t1 + 1)):
            keep = set(I) | O; table = {}
            good = True
            for sh in shares:
                key = tuple(sh[i] for i in keep) + tuple(sh[3 + i] for i in keep)
                d = Counter(view(P, sh, r) for r in rands)
                if table.setdefault(key, d) != d: good = False; break
            if good: ok = True; break
        if not ok: bad_pini += 1; print('PINI FAIL', P)
    print(f'HPC2 (3 shares): {len(names)} probe positions, {len(sets)} probe sets of size <= 2: '
          f'security failures {bad_sec}, PINI failures {bad_pini}')
    return bad_sec == 0 and bad_pini == 0

if __name__ == '__main__':
    raise SystemExit(0 if check() else 1)
