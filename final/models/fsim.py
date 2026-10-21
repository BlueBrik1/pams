#!/usr/bin/env python3
"""Final functional verification of the publication circuits with the frozen testbench (models/sim.py run(); only its
stimulus is replaced). Systematic stimulus instead of random:
  B: every interval boundary of every (d, c): x in {a_c - 1, a_c, a_(c+1) - 1, a_(c+1)} (mod q) against c  (12,416)
  E: every x in [0, q) for every d, against c = Compress_d(x) and c + 1 (mod 2^d)                    (26,632)
Share patterns rotate over: random, (x,0,0), (0,x,0), (0,0,x), (q-1, q-1, x+2), (x-2(q-1)... ) -- all canonical.
Ciphertexts: consecutive groups of 2..9 coefficients; expected decision = AND over the group.
usage: fsim.py DESIGN [NETLIST.v]        (DESIGN's RTL is competitors/rtl/DESIGN.v; NETLIST: gate-level check)"""
import random, sys
from pathlib import Path
sys.dont_write_bytecode = True
MV = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MV / 'models'))
import sim   # noqa: E402  (frozen; read-only)
import pams as P  # noqa: E402
sim.H = MV / 'competitors' / 'models'        # sim reads <H.parents[0]>/rtl/<design>.v
Q = 3329; DS = (4, 5, 10, 11); MODE = {4: 0, 5: 1, 10: 2, 11: 3}


def coeffs():
    out = []
    for d in DS:
        a = P.starts(d); n = 1 << d
        for c in range(n):
            for x in (a[c] - 1, a[c], a[(c + 1) % n] - 1, a[(c + 1) % n]):
                out.append((x % Q, d, c))
        for x in range(Q):
            cx = P.compress(x, d); out += [(x, d, cx), (x, d, (cx + 1) % n)]
    return out


def stimulus(n, seed):
    rng = random.Random(seed); rows, cexp, dexp = [], [], []
    cs = coeffs(); i = 0
    while i < len(cs):
        L = min(rng.randint(2, 9), len(cs) - i); ok = True
        for j in range(L):
            x, d, c = cs[i + j]; k = (i + j) % 6
            if k == 0: x0, x1 = rng.randrange(Q), rng.randrange(Q)
            elif k == 1: x0, x1 = x, 0
            elif k == 2: x0, x1 = 0, x
            elif k == 3: x0, x1 = 0, 0
            elif k == 4: x0, x1 = Q - 1, Q - 1
            else: x0, x1 = rng.randrange(Q), Q - 1
            x2 = (x - x0 - x1) % Q
            assert (x0 + x1 + x2) % Q == x and all(0 <= s < Q for s in (x0, x1, x2))
            e = int(P.compress(x, d) == c); ok &= bool(e); cexp.append(e)
            rows.append(f'{x0:03x}{x1:03x}{x2:03x}{c:03x}{MODE[d]:01x}{int(j == 0):01x}{int(j == L - 1):01x}')
        dexp.append(int(ok)); i += L
    return rows, cexp, dexp


sim.stimulus = stimulus
if __name__ == '__main__':
    ok = sim.run(sys.argv[1], 0, 1, sys.argv[2] if len(sys.argv) > 2 else None)
    sys.exit(0 if ok else 1)
