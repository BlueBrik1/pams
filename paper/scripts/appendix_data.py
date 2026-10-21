#!/usr/bin/env python3
"""Data tables for Appendices A and B, each value checked twice before it is written:
  data/tab_windows.tex  - public window constants for d = 4 and d = 5: a_c, r_c, qq(r_c), Low_c, Theta_c,
                          closed forms (Equations 7, 8 / 20-22) asserted equal to the definitions F(a_c), F(a_{c+1}) - F(a_c) - 1.
  data/tab_trace_e1.tex - cycle-by-cycle registers of final/rtl/pams_jqr.v (iverilog) for example E1 applied alone,
                          asserted equal to the reference values in data/examples.json (run examples.py first).
usage: python3 -I appendix_data.py"""
import json, subprocess, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode = True
PAPER = Path(__file__).resolve().parents[1]; MV = PAPER.parent
sys.path.insert(0, str(MV / 'models'))
import pams as P  # noqa: E402
Q, K = 3329, 14; MOD = 1 << K; F = lambda v: (v << K) // Q


def windows():
    out = []
    for d in (4, 5):
        n, e, a = 1 << d, 13 - d, P.starts(d)
        qq = lambda r: (r << e) // Q
        for c in range(n):
            r = ((1 - 2 * c) * Q) % (2 << d); rn = (r - 2 * Q) % (2 << d)
            assert rn == ((1 - 2 * (c + 1)) * Q) % (2 << d)
            low = ((2 * c - 1) * (1 << e) + qq(r)) % MOD
            th = (2 << e) - 1 + qq(rn) - qq(r)
            assert low == F(a[c]) % MOD == P.low_formula(c, d, K), (d, c)
            assert th == (F(a[(c + 1) % n]) - F(a[c]) - 1) % MOD, (d, c)
            assert all(P.compress(x % Q, d) == c for x in range(a[c], a[c] + (a[(c + 1) % n] - a[c]) % Q))
            out.append((d, c, a[c], (a[(c + 1) % n] - a[c]) % Q, r, qq(r), qq(rn), low, th))
    rows = [f'{d} & {c} & {ac} & {w} & {r} & {q0} & {q1} & {lo} & {th} \\\\' + (' \\midrule' if (d, c) == (4, 15) else '')
            for d, c, ac, w, r, q0, q1, lo, th in out]
    (PAPER / 'data/tab_windows.tex').write_text('\n'.join(rows) + '\n\\bottomrule\n')  # rule inside: \input before \bottomrule breaks \noalign
    print('windows: %d rows, closed forms == definitions' % len(rows))


TB = """`timescale 1ns/1ps
module tb; reg clk = 0; always #5 clk = ~clk;
  reg [11:0] x0 = 0, x1 = 0, x2 = 0; reg [10:0] c = 1; reg [1:0] mode = 0; reg vin = 0, first = 0, last = 0; reg [119:0] rnd = 0;
  wire [2:0] cdec, dec; wire cvalid, dvalid; integer t;
  pams_jqr_lane u (.clk(clk), .x0(x0), .x1(x1), .x2(x2), .c(c), .mode(mode), .vin(vin), .first(first), .last(last),
    .rnd(rnd), .cdec(cdec), .cvalid(cvalid), .dec(dec), .dvalid(dvalid));
  initial begin
    for (t = 0; t <= 36; t = t + 1) begin
      @(negedge clk); rnd = {$urandom, $urandom, $urandom, $urandom};
      if (t == 0) begin x0 = %d; x1 = %d; x2 = %d; c = %d; mode = %d; vin = 1; first = 1; last = 1; end
      else begin x0 = 0; x1 = 0; x2 = 0; c = 1; mode = 0; vin = 0; first = 0; last = 0; end
      if (t > 0) $display("S %%0d | %%0d %%0d %%0d | %%0d %%0d %%0d | %%0d %%0d %%0d %%0d %%0d %%0d | %%0d %%0d %%0d | %%0d %%0d %%0d | %%0d %%0d %%0d %%0d %%0d %%0d %%0d %%0d | %%0d %%0d %%0d %%0d %%0d",
        t, u.x0q, u.x1q, u.x2q, u.x0r, u.x1r, u.x2r, u.mh0, u.ml0, u.mh1, u.ml1, u.mh2, u.ml2, u.s0p, u.s1p, u.s2p, u.y0, u.y1, u.y2,
        u.c0, u.d0, u.qcr, u.qnr, u.e0r, u.lowrq, u.lowp, u.th2, ^u.g111, ^u.g1542, cvalid, ^cdec, cdec);
    end
    $finish;
  end
endmodule
"""


def trace():
    E = {e['name']: e for e in json.loads((PAPER / 'data/examples.json').read_text())}['E1']
    mode = {4: 0, 5: 1, 10: 2, 11: 3}[E['d']]
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); (td / 'tb.v').write_text(TB % (*E['shares'], E['c'], mode))
        subprocess.run(['iverilog', '-g2012', '-o', str(td / 'a'), str(td / 'tb.v'), str(MV / 'final/rtl/pams_jqr.v')], check=True)
        out = subprocess.run(['vvp', '-n', str(td / 'a')], capture_output=True, text=True, check=True).stdout.splitlines()
    S = {}
    for l in out:
        if l.startswith('S '):
            v = [w for w in l.replace('|', ' ').split()]; S[int(v[1])] = [int(w) if w.lstrip('-').isdigit() else w for w in v[2:]]
    sh, ys, ya = E['shares'], E['y'], [E['y0_aligned'], E['y'][1], E['y'][2]]
    b0 = [(v & 1) for v in ya]; maj0 = (b0[0] & b0[1]) | (b0[0] & b0[2]) | (b0[1] & b0[2])
    M = 10321339
    # filler coefficients (x = 0, c = 1, d = 4) decide 0, so a decision 1 at stage 31 can only be E1's
  # stage s = values held after s rising edges (printed at the following negedge)
    assert S[1][0:3] == sh and S[2][3:6] == sh, 'input registers'
    assert S[3][6:12] == [(v >> 6) * M if k == 0 else (v & 63) * M for v in sh for k in (0, 1)], 'partial products'
    assert S[4][12:15] == ys and S[5][15:18] == ya, 'switched / aligned shares'
    assert S[1][18:20] == [E['c'], E['d']] and S[2][22] == 13 - E['d'], 'public stage 1-2'
    assert S[3][23] == E['Low'] and S[4][24] == E['Low'] and S[5][25] == E['Theta'], 'public constants'
    assert S[7][26] == maj0, 'first CSA gadget ug111 (recombined) != maj of bit 0'
    assert S[31][28] == 1 and S[31][29] == E['decision'] and all(S[s][28] in (0, 'x') for s in S if s != 31) and S[30][29] == S[32][29] == 0, 'cvalid / decision at stage 31 only'
    assert S[31][27] == E['decision'], 'final gadget ug1542 (recombined)'
    d, c = E['d'], E['c']; e = 13 - d; r = ((1 - 2 * c) * Q) % (2 << d); rn = (r - 2 * Q) % (2 << d)
    assert S[2][20:23] == [(r << e) // Q, (rn << e) // Q, e], 'qq(r_c), qq(r_c+1), e'
    j = lambda v: ', '.join(str(w) for w in v)
    cd = S[31][30]; csh = [(cd >> i) & 1 for i in range(3)]
    rows = [(1, r'\sig{x$i$q}; \sig{c0}, \sig{d0}', j(S[1][0:3]) + '; ' + j(S[1][18:20]), 'registered shares $x_i$; $c$, $d$'),
            (2, r'\sig{x$i$r}; \sig{qcr}, \sig{qnr}, \sig{e0r}', j(S[2][3:6]) + '; ' + j(S[2][20:23]), r'$x_i$; $\mathrm{qq}(r_c)$, $\mathrm{qq}(r_{c+1})$, $e$'),
            (3, r'\sig{mh$i$}, \sig{ml$i$}', j(S[3][6:12]), r'$\lfloor x_i/64\rfloor M$, $(x_i \bmod 64) M$ for $i = 0, 1, 2$'),
            (3, r'\sig{lowrq}', str(S[3][23]), r'$\Low_c$ (Equation~(7))'),
            (4, r'\sig{s$i$p}; \sig{lowp}', j(S[4][12:15]) + '; ' + str(S[4][24]), r'$F_{14}(x_i)$; $\Low_c$'),
            (5, r'\sig{y$i$}; \sig{th2}', j(S[5][15:18]) + '; ' + str(S[5][25]), r'$\hat y_0, y_1, y_2$; $\Theta_c$'),
            (7, r'\sig{g111} (recombined)', str(S[7][26]), r'$T_1 = \mathrm{maj}$ of bit 0 of the three operands'),
            (31, r'\sig{g1542} (recombined); \sig{cvalid}', f'{S[31][27]}; {S[31][28]}', r'$b = [Z < \Theta_c]$; decision marker'),
            (31, r'\sig{cdec} shares $(b_0, b_1, b_2)$', j(csh), r'$b_0 \oplus b_1 \oplus b_2 = %d$' % (csh[0] ^ csh[1] ^ csh[2]))]
    rows = [f'{st} & {sg} & \\texttt{{{v}}} & {m} \\\\' for st, sg, v, m in rows]
    shown = [1, 2, 3, 4, 5, 7, 31]
    (PAPER / 'data/tab_trace_e1.tex').write_text('\n'.join(rows) + '\n\\bottomrule\n')
    print('trace E1: RTL registers == reference at stages', shown, '; cdec shares at 31 =', S[31][30])


if __name__ == '__main__':
    windows(); trace()
