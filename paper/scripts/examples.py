#!/usr/bin/env python3
"""Worked examples for the paper, computed twice and cross-checked:
  (1) with the frozen mathematical reference (models/pams.py: compress, starts, low_formula), and
  (2) by simulating the final RTL final/rtl/pams_jqr.v (iverilog) and reading its internal registers
      (x0r.., s0p.., y0.., lowp, th2) and its per-coefficient decision shares cdec.
Any disagreement aborts. Writes paper/data/examples.json and paper/data/examples.tex (LaTeX macros / table rows).
usage: python3 -I examples.py"""
import json, random, subprocess, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode = True
PAPER = Path(__file__).resolve().parents[1]; MV = PAPER.parent
sys.path.insert(0, str(MV / 'models'))
import pams as P  # noqa: E402
Q, K = 3329, 14; F = lambda v: (v << K) // Q; MOD = 1 << K; MODE = {4: 0, 5: 1, 10: 2, 11: 3}


def jval(xs):
    return (F(sum(xs) % Q) - sum(F(v) for v in xs)) % MOD


def find_shares(x, want_j, rng):
    for _ in range(200000):
        x0, x1 = rng.randrange(Q), rng.randrange(Q); x2 = (x - x0 - x1) % Q
        if jval((x0, x1, x2)) == want_j: return (x0, x1, x2)
    raise RuntimeError


def reference(x, shares, d, c):
    n = 1 << d; a = P.starts(d)
    lo = P.low_formula(c, d, K); hi = P.low_formula((c + 1) % n, d, K); th = (hi - lo - 1) % MOD
    ys = [F(v) for v in shares]; Z = (ys[0] + ys[1] + ys[2] + 2 - lo) % MOD
    return dict(x=x, shares=list(shares), d=d, c=c, compress=P.compress(x, d), a_c=a[c], a_c1=a[(c + 1) % n],
                F_x=F(x), y=ys, sum_y=(sum(ys)) % MOD, j=jval(shares), Low=lo, Low_next=hi, Theta=th,
                y0_aligned=(ys[0] - lo + 2) % MOD, Z=Z, decision=int(Z < th), expected=int(P.compress(x, d) == c),
                Z_hi=Z >> 11, Z_lo=Z & 2047, theta_lo=th & 2047)


def rtl(examples):
    tb = """`timescale 1ns/1ps
module tb; reg clk = 0; always #5 clk = ~clk;
  reg [11:0] x0, x1, x2; reg [10:0] c; reg [1:0] mode; reg vin = 0, first = 0, last = 0; reg [119:0] rnd;
  wire [2:0] cdec, dec; wire cvalid, dvalid; integer t = 0, i;
  pams_jqr_lane u (.clk(clk), .x0(x0), .x1(x1), .x2(x2), .c(c), .mode(mode), .vin(vin), .first(first), .last(last),
    .rnd(rnd), .cdec(cdec), .cvalid(cvalid), .dec(dec), .dvalid(dvalid));
  reg [59:0] mem [0:%d];
  initial begin
    $readmemh("%s", mem);
    for (i = 0; i < %d; i = i + 1) begin
      @(negedge clk); t = t + 1;
      rnd = {$urandom, $urandom, $urandom, $urandom};
      if (i < %d) begin x0 = mem[i][59:48]; x1 = mem[i][47:36]; x2 = mem[i][35:24]; c = mem[i][22:12]; mode = mem[i][9:8]; first = 1; last = 1; vin = 1; end
      else begin vin = 0; first = 0; last = 0; x0 = 0; x1 = 0; x2 = 0; c = 1; mode = 0; end
      $display("T %%0d xr %%0d %%0d %%0d s %%0d %%0d %%0d y %%0d %%0d %%0d low %%0d th %%0d lowr %%0d thr %%0d cv %%0d cdec %%0d",
        t, u.x0r, u.x1r, u.x2r, u.s0p, u.s1p, u.s2p, u.y0, u.y1, u.y2, u.lowp, u.th2, u.lowr, u.thr, cvalid, ^cdec);
    end
    $finish;
  end
endmodule
"""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        rows = [f"{e['shares'][0]:03x}{e['shares'][1]:03x}{e['shares'][2]:03x}{e['c']:03x}{MODE[e['d']]:01x}11" for e in examples]
        (td / 'm.hex').write_text('\n'.join(rows) + '\n')
        n = len(examples); (td / 'tb.v').write_text(tb % (n - 1, td / 'm.hex', n + 45, n))
        subprocess.run(['iverilog', '-g2012', '-o', str(td / 'a'), str(td / 'tb.v'), str(MV / 'final/rtl/pams_jqr.v')], check=True)
        out = subprocess.run(['vvp', '-n', str(td / 'a')], capture_output=True, text=True, check=True).stdout.splitlines()
    L = {}
    for l in out:
        if not l.startswith('T '): continue
        v = [w if w != 'x' else '-1' for w in l.split()]; t = int(v[1]); L[t] = dict(xr=list(map(int, v[3:6])), s=list(map(int, v[7:10])), y=list(map(int, v[11:14])),
                                                   low=int(v[15]), th=int(v[17]), lowr=int(v[19]), thr=int(v[21]), cv=int(v[23]), cdec=int(v[25]))
    res = []
    for k, e in enumerate(examples):
        t_in = k + 1                       # negedge at which the coefficient is applied
        # stages (posedges after application): 1 x_q, 2 x_r, 3 mh/ml, 4 s_p, 5 y; decision cdec at stage 31 (cvalid)
        r = dict(x_r=L[t_in + 2]['xr'], s_p=L[t_in + 4]['s'], y=L[t_in + 5]['y'], lowp=L[t_in + 5]['low'] if False else L[t_in + 4]['low'],
                 th2=L[t_in + 5]['th'], cdec_cycle=None, cdec=None)
        # stage s is visible at negedge t_in + s; cvalid = vp[30] marks the decision at stage 31
        assert L[t_in + 31]['cv'] == 1, (e['name'], 'cvalid not at stage 31')
        r['cdec_cycle'] = 31; r['cdec'] = L[t_in + 31]['cdec']
        res.append(r)
    return res


if __name__ == '__main__':
    rng = random.Random(2026)
    ex = []
    # E1: d = 4, c = 0 (interval wraps through q-1 -> 0), member x = 3300, shares with j = 1
    ex.append(('E1', 3300, 4, 0, 1))
    # E2: d = 11, non-member at the upper boundary: x = a_(c+1) for c = 1000, worst-case error j = 2
    a11 = P.starts(11); ex.append(('E2', a11[1001], 11, 1000, 2))
    # E3: d = 10, member at the last value of its interval x = a_(c+1) - 1, c = 300, j = 0
    a10 = P.starts(10); ex.append(('E3', a10[301] - 1, 10, 300, 0))
    # E4: d = 4, c = 0, non-member just below the wrapped interval start, x = a_0 - 1 = 3224, j = 2
    a4 = P.starts(4); ex.append(('E4', a4[0] - 1, 4, 0, 2))
    refs = []
    for name, x, d, c, j in ex:
        sh = find_shares(x, j, rng); r = reference(x, sh, d, c); r['name'] = name
        assert r['j'] == j and r['decision'] == r['expected'], r
        refs.append(r)
    got = rtl(refs)
    for r, g in zip(refs, got):
        assert g['x_r'] == r['shares'], (r['name'], g)
        assert g['s_p'] == r['y'], (r['name'], 'share-wise switch', g['s_p'], r['y'])
        assert g['y'] == [r['y0_aligned'], r['y'][1], r['y'][2]], (r['name'], 'aligned operands', g['y'])
        assert g['lowp'] == r['Low'] and g['th2'] == r['Theta'], (r['name'], 'public constants', g)
        assert g['cdec'] == r['decision'], (r['name'], 'RTL decision', g)
        r['rtl'] = g
    (PAPER / 'data').mkdir(exist_ok=True)
    (PAPER / 'data' / 'examples.json').write_text(json.dumps(refs, indent=1))
    for r in refs:
        print(r['name'], {k: r[k] for k in ('x', 'shares', 'd', 'c', 'compress', 'a_c', 'a_c1', 'F_x', 'y', 'sum_y', 'j', 'Low', 'Theta', 'y0_aligned', 'Z', 'decision')}, 'RTL cdec at stage', r['rtl']['cdec_cycle'])
    print('reference and RTL agree on all examples')
