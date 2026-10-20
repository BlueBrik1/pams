#!/usr/bin/env python3
"""Independent audit of the PAMS mathematics (does not import models/*). Run after ./lemma 14 and ./lemma 13
(reach_K*.bin). Everything is derived from FIPS 203 Compress and from the constant logic as written in rtl/pams.v
and rtl/base.v (Verilog widths emulated). Writes audit_results.json.

Checks
  A  FIPS 203 intervals: Compress_d(x) = c  <=>  x in [a_c, a_{c+1}) cyclically; a_c closed form
  B  RTL multipliers: (x*10321339)>>21 == floor(x 2^14/q), (x*10569051393)>>21 == floor(x 2^24/q), all 12-bit x
  C  RTL public constants low0/th0 (12/14-bit wraps as in pams.v) == floor(a_c 2^14/q), Low_{c+1}-Low_c-1; th < 2^11
  D  PAMS decision [((S - Low_c + 2) mod 2^14) < Theta_c] with S = F(x) - j, for every (x, j in {0,1,2}, c, d):
     exact; also the split form [Z[13:11]=0 and Z[10:0] < Theta[10:0]]
  E  baseline decision (base.v constants): Z = S' - (2c-1)2^12 + 1 mod 2^(13+d), [top d bits zero]; S' = F_{13+d}(x)-j
  F  K = 13 lower bound restricted to (x, j) pairs that real share triples reach (reach_K13.bin), with witnesses
  G  variant with the anchor applied in Z_q before switching: x0' = x0 - a_c mod q, decision [(S'+2) mod 2^14 < T_w]
"""
import json, os, sys

Q = 3329
HERE = os.path.dirname(os.path.abspath(__file__))
DS = (4, 5, 10, 11)
R = {}


def compress(x, d): return ((x << (d + 1)) + Q) // (2 * Q) % (1 << d)
def F(v, K): return (v << K) // Q


def starts(d):
    return [next(x for x in range(Q) if compress(x, d) == c and compress((x - 1) % Q, d) != c) for c in range(1 << d)]


# ---- A ----
A = {}
for d in DS:
    s = starts(d)
    closed = [(-(-((2 * c - 1) * Q) // (1 << (d + 1)))) % Q for c in range(1 << d)]   # ceil((2c-1)q/2^(d+1)) mod q
    ok = all(s[c] == closed[c] for c in range(1 << d))
    member = all((compress(x, d) == c) == (((x - s[c]) % Q) < ((s[(c + 1) % (1 << d)] - s[c]) % Q))
                 for c in range(1 << d) for x in range(Q))
    widths = sorted({(s[(c + 1) % (1 << d)] - s[c]) % Q for c in range(1 << d)})
    A[d] = {'closed_form_equals_starts': ok, 'interval_form_exact': member, 'widths': widths}
R['A_intervals'] = A

# ---- B ----
R['B_multipliers'] = {   # exact on the canonical contract range [0, q); 12-bit inputs >= q are outside the contract
    'pams_14bit_exact_on_[0,q)': all((x * 10321339) >> 21 == F(x, 14) for x in range(Q)),
    'base_24bit_exact_on_[0,q)': all((x * 10569051393) >> 21 == F(x, 24) for x in range(Q)),
    'pams_inexact_12bit_inputs': [x for x in range(4096) if (x * 10321339) >> 21 != F(x, 14)],
    'base_inexact_12bit_inputs': [x for x in range(4096) if (x * 10569051393) >> 21 != F(x, 24)],
}


# ---- C: constants exactly as pams.v computes them ----
def rtl_consts(c, d):
    w12, w14 = 0xFFF, 0x3FFF
    e = (13 - d) & 0xF
    rmask = ((1 << ((d + 1) & 0xF)) & w12) - 1 & w12
    pr = ((1 - (c << 1)) * 3329) & w12
    rc, rn = pr & rmask, (pr - 2562) & w12 & rmask
    qq = lambda r: sum(((r << e) & w14) >= t for t in (3329, 6658, 9987, 13316))
    low = ((((c << 1) - 1) * (1 << e)) + qq(rc)) & w14
    th = ((2 << e) - 1 + qq(rn) - qq(rc)) & w14
    return low, th


C = {}
for d in DS:
    s = starts(d); n = 1 << d
    lows = [F(s[c], 14) for c in range(n)]
    good = bad = 0; thmax = 0
    for c in range(n):
        low, th = rtl_consts(c, d)
        exp_th = (lows[(c + 1) % n] - lows[c] - 1) % (1 << 14)
        good += (low == lows[c] and th == exp_th); thmax = max(thmax, th)
    C[d] = {'match': good, 'of': n, 'theta_max': thmax, 'theta_below_2^11': thmax < 2048}
R['C_rtl_constants'] = C

# ---- D: PAMS decision over all (x, j, c, d) ----
D = {}
for d in DS:
    n = 1 << d; mism = 0; split_mism = 0
    consts = [rtl_consts(c, d) for c in range(n)]
    for x in range(Q):
        fx = F(x, 14); cx = compress(x, d)
        for j in range(3):
            S = (fx - j) % (1 << 14)
            for c in range(n):
                low, th = consts[c]
                Z = (S - low + 2) % (1 << 14)
                dec = Z < th
                mism += dec != (cx == c)
                split_mism += ((Z >> 11) == 0 and (Z & 2047) < (th & 2047)) != dec
    D[d] = {'mismatches': mism, 'split_form_mismatches': split_mism, 'cases': Q * 3 * n}
R['D_pams_decision'] = D

# ---- E: baseline decision (base.v: t = 13, offset A = 1) over all (x, j, c, d) ----
E = {}
for d in DS:
    n = 1 << d; Kb = 13 + d; mask = (1 << Kb) - 1; mism = 0
    for x in range(Q):
        fx = F(x, Kb); cx = compress(x, d)
        for j in range(3):
            for c in range(n):
                Z = (fx - j - (2 * c - 1) * (1 << 12) + 1) & mask
                mism += ((Z >> 13) == 0) != (cx == c)
    E[d] = {'mismatches': mism, 'cases': Q * 3 * n}
R['E_baseline_decision'] = E


# ---- F: K = 13 collisions among reachable (x, j) ----
def reach(K):
    b = open(os.path.join(HERE, f'reach_K{K}.bin'), 'rb').read()
    return [[b[3 * x + j] for j in range(3)] for x in range(Q)]


def witness_triple(x, j, K):
    for x1 in range(Q):
        for x2 in range(Q):
            x0 = (x - x1 - x2) % Q
            if (F(x, K) - F(x0, K) - F(x1, K) - F(x2, K)) % (1 << K) == j: return [x0, x1, x2]


Fk = {}
for K in (13, 14):
    rc = reach(K); res = {}
    for d in DS:
        s = starts(d); n = 1 << d; coll = 0; wit = None
        val = {}
        for x in range(Q):
            for j in range(3):
                if rc[x][j]: val.setdefault((F(x, K) - j) % (1 << K), set()).add(x)
        for c in range(n):
            for v, xs in val.items():
                ins = {x for x in xs if compress(x, d) == c}
                if ins and len(ins) < len(xs):
                    coll += 1
                    if wit is None:
                        xin, xout = min(ins), min(xs - ins)
                        jin = next(j for j in range(3) if rc[xin][j] and (F(xin, K) - j) % (1 << K) == v)
                        jout = next(j for j in range(3) if rc[xout][j] and (F(xout, K) - j) % (1 << K) == v)
                        wit = {'c': c, 'member_x': xin, 'nonmember_x': xout, 'switched_sum': v,
                               'member_shares': witness_triple(xin, jin, K), 'nonmember_shares': witness_triple(xout, jout, K)}
        res[d] = {'colliding_(c,value)_pairs': coll, 'witness': wit}
    Fk[K] = res
R['F_width_bound_reachable'] = Fk

# ---- G: anchor in Z_q (x0' = x0 - a_c mod q) then switch at K = 14 with a width-only threshold ----
G = {}
for d in DS:
    s = starts(d); n = 1 << d; mism = 0
    for c in range(n):
        w = (s[(c + 1) % n] - s[c]) % Q
        T = F(w - 1, 14) + 3
        for x in range(Q):
            xp = (x - s[c]) % Q
            for j in range(3):
                mism += (((F(xp, 14) - j + 2) % (1 << 14)) < T) != (compress(x, d) == c)
    G[d] = {'mismatches': mism}
R['G_zq_prealigned_variant'] = G

json.dump(R, open(os.path.join(HERE, 'audit_results.json'), 'w'), indent=1, default=str)
print(json.dumps(R, indent=1, default=str))
