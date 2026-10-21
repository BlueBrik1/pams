#!/usr/bin/env python3
"""Lightweight re-check of the manuscript's mathematical claims (final review; no multi-billion-case enumeration).
Checks, each asserted:
  1. interval form: Compress_d(x) = c  <=>  x in [a_c, a_{c+1}) cyclically, a_c = ceil((2c-1) q / 2^{d+1}) mod q   (all x, c, d)
  2. widths per d, number of (c, d) pairs, Theta range 3..1027, closed forms for Low_c / Theta_c (Equations 7, 8)
  3. Proposition 1 with tight bounds: over all (x, j, c, d) members have Z in [0, Theta-1], non-members Z in [Theta+1, 2^14-2],
     max(Z - Theta) = -1 over members and min = +1 over non-members (the decision depends on shares only through (x, j), Lemma 1)
  4. reachability of j: j = 2 is reachable iff rho(x) <= q-3 (3,327 values of x); j = 0, 1 always (constructive, from the proof in
     MATHEMATICS_AUDIT.md), cross-checked by random sampling of share triples
  5. Lemma 1 on 40,000 random canonical triples (the full 3329^3 enumeration is Phase XII's validation/math/lemma.c)
  6. gap of F_K: steps 4 or 5 for K = 14 (2 or 3 for K = 13), wrap step 5; the K = 13 witness (0,0,0) vs (3326,2,2) at d = 11
  7. multiplier: (x * 10321339) >> 21 == floor(x 2^14 / q) for x in [0, q), and the first failure above q
Writes paper/review/math_audit_results.json.  usage: python3 -I audit_math.py"""
import json, random, sys
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
PAPER = Path(__file__).resolve().parents[1]; MV = PAPER.parent
sys.path.insert(0, str(MV / 'models'))
import pams as P  # noqa: E402
Q, K = 3329, 14; MOD = 1 << K
F = lambda v, k=K: (v << k) // Q
R = {}

# 1-2
X = np.arange(Q, dtype=np.int64)
pairs = 0; th_all = []
for d in (4, 5, 10, 11):
    n = 1 << d; e = 13 - d
    comp = ((X << d) * 2 + Q) // (2 * Q) % n
    assert all(int(comp[x]) == P.compress(x, d) for x in range(0, Q, 7))
    a = [(-((-(2 * c - 1) * Q) // (2 << d))) % Q for c in range(n)]          # ceil((2c-1)q/2^{d+1}) mod q
    assert a == P.starts(d), d
    widths = set()
    for c in range(n):
        w = (a[(c + 1) % n] - a[c]) % Q; widths.add(w)
        mem = ((X - a[c]) % Q) < w
        assert np.array_equal(mem, comp == c), (d, c)
        r = ((1 - 2 * c) * Q) % (2 << d); rn = (r - 2 * Q) % (2 << d)
        qq = lambda v: (v << e) // Q
        low = ((2 * c - 1) * (1 << e) + qq(r)) % MOD
        th = (2 << e) - 1 + qq(rn) - qq(r)
        assert low == F(a[c]) % MOD and th == (F(a[(c + 1) % n]) - F(a[c]) - 1) % MOD and 0 <= qq(r) <= 4
        th_all.append(th); pairs += 1
    R[f'widths_d{d}'] = sorted(widths)
R['pairs'] = pairs; R['theta_min'] = min(th_all); R['theta_max'] = max(th_all)
assert pairs == 3120 and R['theta_min'] == 3 and R['theta_max'] == 1027
assert R['widths_d4'] == [208, 209] and R['widths_d5'] == [104, 105] and R['widths_d10'] == [3, 4] and R['widths_d11'] == [1, 2]

# 3
FX = (X << K) // Q
mem_max = -10**9; non_min = 10**9; cases = 0; mism = 0
for d in (4, 5, 10, 11):
    n = 1 << d; a = P.starts(d)
    comp = ((X << d) * 2 + Q) // (2 * Q) % n
    for c in range(n):
        low = F(a[c]) % MOD; th = (F(a[(c + 1) % n]) - F(a[c]) - 1) % MOD
        for j in (0, 1, 2):
            Z = (FX - j + 2 - low) % MOD
            m = comp == c
            mism += int(np.count_nonzero((Z < th) != m)); cases += Q
            if m.any(): mem_max = max(mem_max, int((Z[m] - th).max())); assert Z[m].min() >= 0
            nm = ~m
            non_min = min(non_min, int((Z[nm] - th).min())); assert int(Z[nm].max()) <= MOD - 2
R.update(cases=cases, mismatches=mism, member_max_Z_minus_Theta=mem_max, nonmember_min_Z_minus_Theta=non_min)
assert cases == 31159440 and mism == 0 and mem_max == -1 and non_min == 1

# 4
rho = (X << K) % Q
R['x_with_j2_reachable'] = int(np.count_nonzero(rho <= Q - 3))
assert R['x_with_j2_reachable'] == 3327
def jval(s): x = sum(s) % Q; return (F(x) - sum(F(v) for v in s)) % MOD
rng = random.Random(2026); seen = {}
for _ in range(200000):
    x0, x1, x2 = rng.randrange(Q), rng.randrange(Q), rng.randrange(Q)
    seen.setdefault(sum((x0, x1, x2)) % Q, set()).add(jval((x0, x1, x2)))
for x, js in seen.items():
    if 2 in js: assert rho[x] <= Q - 3, x
# constructive witnesses for every x and every claimed-reachable j
inv = pow(1 << K, -1, Q)                      # rho is a bijection; x_i = rho^{-1}(r_i)
for x in range(Q):
    r = int(rho[x])
    for j in (0, 1, 2):
        if j == 2 and r > Q - 3: continue
        rs = {0: (r, 0, 0), 1: ((Q - 1, r + 1, 0) if r <= Q - 2 else (Q - 1, Q - 1, 1)), 2: (Q - 1, Q - 1, r + 2)}[j]
        sh = tuple(v * inv % Q for v in rs)
        assert sum(sh) % Q == x and jval(sh) == j, (x, j)
R['j_reachability'] = 'j=0,1 for all x; j=2 iff rho(x) <= q-3 (constructive witnesses checked for every x)'

# 5
for _ in range(40000):
    s = [rng.randrange(Q) for _ in range(3)]
    assert jval(s) in (0, 1, 2)
R['lemma_random_triples'] = 40000

# 6
st14 = set(int(v) for v in np.diff(np.append(FX, MOD))); st13 = set(int(v) for v in np.diff(np.append((X << 13) // Q, 1 << 13)))
R['steps_K14'] = sorted(st14); R['steps_K13'] = sorted(st13)
assert st14 == {4, 5} and st13 == {2, 3} and MOD - F(Q - 1) == 5
assert (F(0, 13) * 3) % 8192 == (F(3326, 13) + 2 * F(2, 13)) % 8192 and (3326 + 2 + 2) % Q == 1 and P.starts(11)[0] == 0 and P.starts(11)[1] == 1

# 7
assert all((x * 10321339) >> 21 == F(x) for x in range(Q))
R['multiplier_first_failure_at_or_above_q'] = next(x for x in range(Q, 4096) if (x * 10321339) >> 21 != F(x))

(PAPER / 'review').mkdir(exist_ok=True)
(PAPER / 'review' / 'math_audit_results.json').write_text(json.dumps(R, indent=1))
print(json.dumps(R))
print('all mathematical checks passed')
