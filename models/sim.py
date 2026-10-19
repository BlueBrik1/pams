#!/usr/bin/env python3
"""Functional RTL check of a generated lane (iverilog): random 3-share inputs with boundary-focused coefficients,
fresh random gadget bits every cycle; per-coefficient decision shares and whole-ciphertext decision shares are
recombined and compared with FIPS 203 Compress equality.
Coefficients:
- x within +-2 of both interval ends of the chosen c, plus random and matching values;
- all four compression widths, mixed in one stream;
- ciphertexts of 2..9 coefficients, about half of them all-matching.
usage: python3 -I sim.py base|pams [N_coeffs=20000] [seed=1] [netlist.v]   (netlist: gate-level check)"""
import random, subprocess, sys, tempfile
from pathlib import Path
H = Path(__file__).resolve().parent; sys.path.insert(0, str(H))
import pams as P
Q = 3329; DS = (4, 5, 10, 11)

def stimulus(n, seed):
    rng = random.Random(seed); starts = {d: P.starts(d) for d in DS}; rows = []; cexp = []; dexp = []
    while len(rows) < n:
        L = rng.randint(2, 9); match_all = rng.random() < 0.5; ok = True
        for i in range(L):
            mode = rng.randrange(4); d = DS[mode]; c = rng.randrange(1 << d); a = starts[d]
            lo, hi = a[c], a[(c + 1) % (1 << d)]
            if match_all:
                w = (hi - lo) % Q or Q; x = (lo + rng.randrange(w)) % Q
                if rng.random() < 0.5: x = (lo if rng.random() < 0.5 else hi - 1) % Q
            else:
                pick = rng.randrange(4)
                x = [(lo + rng.randint(-2, 1)) % Q, (hi + rng.randint(-2, 1)) % Q, rng.randrange(Q), (lo + rng.randrange(max(1, (hi - lo) % Q))) % Q][pick]
            x0, x1 = rng.randrange(Q), rng.randrange(Q); x2 = (x - x0 - x1) % Q
            e = int(P.compress(x, d) == c); ok &= bool(e); cexp.append(e)
            rows.append(f'{x0:03x}{x1:03x}{x2:03x}{c:03x}{mode:01x}{int(i == 0):01x}{int(i == L - 1):01x}')
        dexp.append(int(ok))
    return rows, cexp, dexp

def run(design, n, seed, netlist=None):
    import re
    v = (Path(netlist) if netlist else H.parents[0] / 'rtl' / f'{design}.v')
    src = (H.parents[0] / 'rtl' / f'{design}.v').read_text()
    R = int(re.search(r'input wire \[(\d+):0\] rnd', src).group(1)) + 1
    rows, cexp, dexp = stimulus(n, seed)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); (td / 'stim.hex').write_text('\n'.join(rows) + '\n')
        words = (R + 31) // 32
        tb = f'''`timescale 1ns/1ps
module tb; reg clk = 0; always #5 clk = ~clk;
  reg [11:0] x0, x1, x2; reg [10:0] c; reg [1:0] mode; reg vin = 0, first = 0, last = 0; reg [{32 * words - 1}:0] rnd;
  wire [2:0] cdec, dec; wire cvalid, dvalid;
  {design}_lane u (.clk(clk), .x0(x0), .x1(x1), .x2(x2), .c(c), .mode(mode), .vin(vin), .first(first), .last(last),
    .rnd(rnd[{R - 1}:0]), .cdec(cdec), .cvalid(cvalid), .dec(dec), .dvalid(dvalid));
  reg [59:0] mem [0:{len(rows) - 1}]; integer i, k;   // x0 x1 x2 c(12) mode(4) first(4) last(4)
  initial begin
    $readmemh("{td / 'stim.hex'}", mem);
    for (i = 0; i < {len(rows) + 120}; i = i + 1) begin
      @(negedge clk);
      for (k = 0; k < {words}; k = k + 1) rnd[32 * k +: 32] = $urandom;
      if (i < {len(rows)}) begin
        x0 = mem[i][59:48]; x1 = mem[i][47:36]; x2 = mem[i][35:24]; c = mem[i][22:12]; mode = mem[i][9:8]; first = mem[i][4]; last = mem[i][0]; vin = 1; end
      else begin vin = 0; first = 0; last = 0; end
    end
    $finish;
  end
  always @(posedge clk) begin if (cvalid) $display("C %0d", ^cdec); if (dvalid) $display("D %0d", ^dec); end
endmodule
'''
        (td / 'tb.v').write_text(tb)
        libs = [str(v)]                          # gate.v from bfbench.synth is self-contained (liberty functions inlined)
        r = subprocess.run(['iverilog', '-g2012', '-o', str(td / 'a.out'), str(td / 'tb.v')] + libs, capture_output=True, text=True)
        if r.returncode: print(r.stderr[:2000]); raise SystemExit(1)
        out = subprocess.run(['vvp', '-n', str(td / 'a.out')], capture_output=True, text=True).stdout.split('\n')
    if any(' x' in l for l in out): print('X lines:', [l for l in out if ' x' in l][:5], 'first lines:', out[:3])
    cs = [int(l.split()[1]) for l in out if l.startswith('C ')]; ds = [int(l.split()[1]) if l.split()[1] in '01' else -1 for l in out if l.startswith('D ')]
    assert len(cs) == len(cexp), (len(cs), len(cexp))
    bad = [i for i, (a, b) in enumerate(zip(cs, cexp)) if a != b]
    badd = [i for i, (a, b) in enumerate(zip(ds, dexp)) if a != b]
    print(f'{design}{" (gate-level)" if netlist else ""}: {len(cs)} coefficients, {sum(cexp)} matching; mismatches {len(bad)}; '
          f'{len(ds)}/{len(dexp)} ciphertext decisions ({sum(dexp)} accept), mismatches {len(badd)}')
    return not bad and not badd and len(ds) == len(dexp)

if __name__ == '__main__':
    d = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 20000; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    sys.exit(0 if run(d, n, seed, sys.argv[4] if len(sys.argv) > 4 else None) else 1)
