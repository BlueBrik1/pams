#!/usr/bin/env python3
"""Generator for second-order (3-share) masked ML-KEM ciphertext-verification lanes, one coefficient per cycle.

Both designs are built from the same parts:
- HPC2 AND gadget (Cassiers et al., TCHES 2021; 3 shares, 3 fresh random bits, latency 2);
- the same share-wise linear operations;
- the same automatic pipeline aligner (operands are delayed share-wise to the later operand's stage);
- the same interleaved AND accumulator for the whole-ciphertext decision.
The only difference is the verification algorithm.

designs:
  base  "Simple" exact comparison (Fritzmann et al. 2022 / D'Anvers et al. 2023), optimised:
        y_i = floor(x_i 2^(13+d) / q) (one 24-bit constant multiplier per share + mode shift);
        y_0 -= (2c - 1) 2^12 - 1;
        decision = [bits 13 .. 13+d-1 of y_0 + y_1 + y_2 are all zero]
        (CSA; ripple carry into bit 13; carry-free zero test of the top region; OR tree).
  pams  pre-aligned modulus switching (this work): y_i = floor(x_i 2^14 / q); y_0 -= Low_c - 2;
        decision = [(y_0 + y_1 + y_2) mod 2^14 < Theta_c] (CSA; ripple carry fused with a ripple comparator).
Outputs Verilog (masked_verification/rtl/<design>.v) and prints gadget / register / randomness counts.
usage: python3 -I gen.py base|pams [--leak]   (--leak: deliberately broken negative control)"""
import sys
from pathlib import Path
Q = 3329
OUT = Path(__file__).resolve().parents[1] / 'rtl'

def floor_mult(K):
    """exact floor(x 2^K / q) = (x * M) >> S for all x < q, smallest S (mulsearch.py; C = 0 for K = 14 and 24)."""
    for S in range(1, 40):
        for M in (-(-(1 << (K + S)) // Q), (1 << (K + S)) // Q):
            if all((x * M) >> S == (x << K) // Q for x in range(Q)): return M, S
    raise ValueError

class Ckt:
    def __init__(self):
        self.decl, self.body, self.seq = [], [], []
        self.n = 100; self.gadgets = 0; self.ffs = 0      # wire-name counter starts at 100 (no clash with ports x0..x2)
    def new(self, base): self.n += 1; return f'{base}{self.n}'
    # masked signal: dict(w=[w0, w1, w2] wire names or None for constant-0 share, t=stage)
    def m(self, w, t): return dict(w=w, t=t)
    def p(self, w, t): return dict(w=w, t=t, pub=True)
    def delay(self, s, k):
        if k <= 0: return s
        ws = s['w'] if not s.get('pub') else [s['w']]
        out = []
        for w in ws:
            if w is None or w in ("1'b0", "1'b1"): out.append(w); continue
            cur = w
            for _ in range(k):
                r = self.new('r'); self.decl.append(f'reg {r};'); self.seq.append(f'{r} <= {cur};'); self.ffs += 1; cur = r
            out.append(cur)
        return self.p(out[0], s['t'] + k) if s.get('pub') else self.m(out, s['t'] + k)
    def align(self, *ss):
        t = max(s['t'] for s in ss); return [self.delay(s, t - s['t']) for s in ss]
    def _x(self, a, b):
        if a is None: return b
        if b is None: return a
        w = self.new('x'); self.decl.append(f'wire {w} = {a} ^ {b};'); return w
    def xor(self, a, b):
        a, b = self.align(a, b); return self.m([self._x(u, v) for u, v in zip(a['w'], b['w'])], a['t'])
    def xor_pub(self, a, p):          # XOR a public bit into share 0
        a, p = self.align(a, p); w = list(a['w']); w[0] = self._x(w[0], p['w']) if w[0] else p['w']; return self.m(w, a['t'])
    def not_(self, a):
        w = list(a['w']); n = self.new('n')
        self.decl.append(f'wire {n} = ~{w[0] if w[0] else "1" + chr(39) + "b0"};'); w[0] = n; return self.m(w, a['t'])
    def and_pub(self, a, p):          # share-wise AND with a public bit (linear)
        a, p = self.align(a, p); out = []
        for w in a['w']:
            if w is None: out.append(None); continue
            n = self.new('a'); self.decl.append(f'wire {n} = {w} & {p["w"]};'); out.append(n)
        return self.m(out, a['t'])
    def hpc2(self, a, b):
        a, b = self.align(a, b); g = self.gadgets; self.gadgets += 1
        sh = lambda s: '{' + ', '.join(w if w else "1'b0" for w in reversed(s['w'])) + '}'
        c = self.new('g'); self.decl.append(f'wire [2:0] {c};')
        self.body.append(f'hpc2 u{c} (.clk(clk), .a({sh(a)}), .b({sh(b)}), .r(rnd[{3 * g + 2}:{3 * g}]), .c({c}));')
        self.ffs += 30
        return self.m([f'{c}[0]', f'{c}[1]', f'{c}[2]'], a['t'] + 2)
    def or_(self, a, b): return self.not_(self.hpc2(self.not_(a), self.not_(b)))
    def maj(self, a, b, c): return self.xor(self.hpc2(self.xor(a, b), self.xor(a, c)), a)

def kernel_pams(C, y, theta, n=14):
    """[ (y0 + y1 + y2) mod 2^n < theta ] with y_i[k] in share domain i, theta public bits."""
    S = [C.xor(C.xor(y[0][k], y[1][k]), y[2][k]) for k in range(n)]
    Cp = [C.maj(y[0][k], y[1][k], y[2][k]) for k in range(n - 1)]
    T = [None] + Cp                                   # T = 2 C'
    lt = C.and_pub(C.not_(S[0]), theta[0])            # z_0 = S_0 (T_0 = 0, c_0 = 0)
    carry = None
    for k in range(1, n):
        cin = carry
        z = C.xor(C.xor(S[k], T[k]), cin) if cin is not None else C.xor(S[k], T[k])
        nt = C.p(f'~{theta[k]["w"]}', theta[k]['t'])
        lt = C.xor_pub(C.hpc2(C.xor_pub(z, nt), C.xor_pub(lt, theta[k])), theta[k])
        if k < n - 1:                                 # carry into k+1
            carry = C.hpc2(S[k], T[k]) if cin is None else C.maj(S[k], T[k], cin)
    return lt

def kernel_pams2(C, y, theta, n=14, m=11):
    """as kernel_pams, using Theta_c < 2^m for every (c, d): decision = [Z[n-1:m] == 0] and [Z[m-1:0] < Theta].
    Top bits: carry-free zero test (only bit m needs the ripple carry); comparator ripple over the low m bits."""
    S = [C.xor(C.xor(y[0][k], y[1][k]), y[2][k]) for k in range(n)]
    Cp = [C.maj(y[0][k], y[1][k], y[2][k]) for k in range(n - 1)]
    T = [None] + Cp
    lt = C.and_pub(C.not_(S[0]), theta[0]); carry = None
    for k in range(1, m):
        z = C.xor(C.xor(S[k], T[k]), carry) if carry is not None else C.xor(S[k], T[k])
        nt = C.p(f'~{theta[k]["w"]}', theta[k]['t'])
        lt = C.xor_pub(C.hpc2(C.xor_pub(z, nt), C.xor_pub(lt, theta[k])), theta[k])
        carry = C.hpc2(S[k], T[k]) if carry is None else C.maj(S[k], T[k], carry)      # carry into k+1 (up to c_m)
    e_m = C.xor(C.xor(S[m], T[m]), carry)                                               # late: needs c_m
    early = [C.xor(C.xor(S[k], T[k]), C.or_(S[k - 1], T[k - 1])) for k in range(m + 1, n)]
    while len(early) > 1:
        nxt = [C.or_(early[i], early[i + 1]) for i in range(0, len(early) - 1, 2)]
        if len(early) % 2: nxt.append(early[-1])
        early = nxt
    top_zero = C.hpc2(C.not_(e_m), C.not_(early[0]))
    return C.hpc2(top_zero, lt)

def kernel_base(C, y, en, n=24, t=13):
    """[ bits t .. t+d-1 of (y0 + y1 + y2) are zero ]; en[k] public enables (k < t + d)."""
    S = [C.xor(C.xor(y[0][k], y[1][k]), y[2][k]) for k in range(n)]
    Cp = [C.maj(y[0][k], y[1][k], y[2][k]) for k in range(n - 1)]
    T = [None] + Cp
    carry = None
    for k in range(1, t):                             # ripple carry into bit t (c_1 = 0)
        carry = C.hpc2(S[k], T[k]) if carry is None else C.maj(S[k], T[k], carry)
    e = []
    for k in range(t, n):                             # carry-free zero test of the top region
        cp = carry if k == t else C.or_(S[k - 1], T[k - 1])
        e.append(C.and_pub(C.xor(C.xor(S[k], T[k]), cp), en[k]))
    late, early = e[0], e[1:]
    while len(early) > 1:                             # OR tree of the carry-independent bits
        nxt = [C.or_(early[i], early[i + 1]) for i in range(0, len(early) - 1, 2)]
        if len(early) % 2: nxt.append(early[-1])
        early = nxt
    return C.not_(C.or_(late, early[0]))

HPC2 = '''// HPC2 AND gadget, 3 shares (d = 2), Cassiers et al. TCHES 2021. Inputs a, b at the same cycle (a is delayed one
// cycle share-locally, as HPC2 consumes a one cycle after b); output c two cycles later. r = {r12, r02, r01}.
(* keep_hierarchy *)
module hpc2 (input wire clk, input wire [2:0] a, input wire [2:0] b, input wire [2:0] r, output wire [2:0] c);
  reg [2:0] ra, rb, rr; reg [5:0] rbr; reg [2:0] p0; reg [5:0] u, v;
  wire r01 = r[0], r02 = r[1], r12 = r[2];
  // ordered pairs (i, j): 0:(0,1) 1:(0,2) 2:(1,0) 3:(1,2) 4:(2,0) 5:(2,1)
  always @(posedge clk) begin
    ra <= a; rb <= b; rr <= r;
    rbr <= {b[1] ^ r12, b[0] ^ r02, b[2] ^ r12, b[0] ^ r01, b[2] ^ r02, b[1] ^ r01};
    p0 <= ra & rb;
    u <= {~ra[2] & rr[2], ~ra[2] & rr[1], ~ra[1] & rr[2], ~ra[1] & rr[0], ~ra[0] & rr[1], ~ra[0] & rr[0]};
    v <= {ra[2] & rbr[5], ra[2] & rbr[4], ra[1] & rbr[3], ra[1] & rbr[2], ra[0] & rbr[1], ra[0] & rbr[0]};
  end
  assign c[0] = p0[0] ^ u[0] ^ v[0] ^ u[1] ^ v[1];
  assign c[1] = p0[1] ^ u[2] ^ v[2] ^ u[3] ^ v[3];
  assign c[2] = p0[2] ^ u[4] ^ v[4] ^ u[5] ^ v[5];
endmodule
'''

def build(design):
    C = Ckt()
    if design in ('pams', 'pams_r'):
        K = 14; M, S = floor_mult(K); width = K
        front = f'''
  // stage 1: public window constants from (c, d); K = 14, e = 13 - d.
  //   r_c = ((1 - 2c) q) mod 2^(d+1);  r_{{c+1}} = (r_c - 2q) mod 2^(d+1);  qq(r) = floor(r 2^e / q) in [0, 4]
  //   Low_c = (2c - 1) 2^e + qq(r_c)  (mod 2^14);  Theta_c = Low_{{c+1}} - Low_c - 1 = 2^(e+1) - 1 + qq(r_{{c+1}}) - qq(r_c)
  function [2:0] qq(input [11:0] r, input [3:0] e);
    reg [13:0] vv;
    begin vv = {{2'b0, r}} << e;
      qq = (vv >= 14'd{Q}) + (vv >= 14'd{2 * Q}) + (vv >= 14'd{3 * Q}) + (vv >= 14'd{4 * Q}); end
  endfunction
  wire [3:0] e0 = 4'd13 - d0;
  wire [11:0] rmask = (12'd1 << (d0 + 4'd1)) - 12'd1;
  wire [11:0] pr = (12'd1 - {{c0, 1'b0}}) * 12'd{Q};
  wire [11:0] rc = pr & rmask, rn = (pr - 12'd{(2 * Q) % 4096}) & rmask;
  wire [2:0] qc = qq(rc, e0), qn = qq(rn, e0);
  wire [13:0] low0 = (({{3'b0, c0}} << 1) - 14'd1) * (14'd1 << e0) + qc;
  wire [13:0] th0 = (14'd2 << e0) - 14'd1 + qn - qc;
  reg [13:0] lowr, thr; reg [11:0] x0r, x1r, x2r;
  always @(posedge clk) begin lowr <= low0; thr <= th0; x0r <= x0q; x1r <= x1q; x2r <= x2q; end
  // stage 2: share-wise modulus switch floor(x_i 2^14 / q) = (x_i * {M}) >> {S}; share 0 pre-aligned by -Low_c + 2
  wire [47:0] m0 = {{36'b0, x0r}} * 48'd{M}, m1 = {{36'b0, x1r}} * 48'd{M}, m2 = {{36'b0, x2r}} * 48'd{M};
  wire [13:0] s0 = m0 >> {S}, s1 = m1 >> {S}, s2 = m2 >> {S};
  reg [13:0] y0, y1, y2, th2;
  always @(posedge clk) begin y0 <= s0 - lowr + 14'd2; y1 <= s1; y2 <= s2; th2 <= thr; end
'''
        y = [[C.m([f'y0[{k}]', None, None], 3) for k in range(width)], [C.m([None, f'y1[{k}]', None], 3) for k in range(width)],
             [C.m([None, None, f'y2[{k}]'], 3) for k in range(width)]]
        theta = [C.p(f'th2[{k}]', 3) for k in range(width)]
        if LEAK:                                       # negative control for domaincheck: one cross-domain XOR
            y[0][5] = C.m([C._x('y0[5]', 'y1[5]'), None, None], 3)
        b = kernel_pams2(C, y, theta, width) if design == 'pams' else kernel_pams(C, y, theta, width)
    else:
        W = 24; M, S = floor_mult(W)
        front = f'''
  // stage 1: public offset (2c - 1) 2^12 - 1 and region enables; mode shift 11 - d
  reg [23:0] offr; reg [23:0] enr; reg [2:0] shr; reg [11:0] x0r, x1r, x2r;
  always @(posedge clk) begin
    offr <= ((({{13'b0, c0}}) << 1) - 24'd1) * 24'd4096 - 24'd1;
    enr <= ((24'd1 << (5'd13 + d0)) - 24'd1) & ~24'h1fff;
    shr <= 4'd11 - d0; x0r <= x0q; x1r <= x1q; x2r <= x2q;
  end
  // stage 2: share-wise modulus switch floor(x_i 2^(13+d) / q) = ((x_i * {M}) >> {S}) >> (11 - d); share 0 offset
  wire [59:0] m0 = {{48'b0, x0r}} * 60'd{M}, m1 = {{48'b0, x1r}} * 60'd{M}, m2 = {{48'b0, x2r}} * 60'd{M};
  wire [23:0] f0 = m0 >> {S}, f1 = m1 >> {S}, f2 = m2 >> {S};
  wire [23:0] s0 = f0 >> shr, s1 = f1 >> shr, s2 = f2 >> shr;
  reg [23:0] y0, y1, y2, en2;
  always @(posedge clk) begin y0 <= s0 - offr; y1 <= s1; y2 <= s2; en2 <= enr; end
'''
        y = [[C.m([f'y0[{k}]', None, None], 3) for k in range(W)], [C.m([None, f'y1[{k}]', None], 3) for k in range(W)],
             [C.m([None, None, f'y2[{k}]'], 3) for k in range(W)]]
        en = [C.p(f'en2[{k}]', 3) for k in range(W)]
        b = kernel_base(C, y, en)
    # whole-ciphertext accumulator: one HPC2 whose 2-cycle latency interleaves even/odd chains
    lat = b['t']
    G0 = C.gadgets
    acc_body = f'''
  // accumulator: acc_in = init ? (1,0,0) : acc_out ; acc_out = HPC2(acc_in, b)  (two interleaved chains)
  wire [2:0] bsh = {{{b['w'][2]}, {b['w'][1]}, {b['w'][0]}}};
  wire [2:0] acc_out; wire [2:0] acc_in = init_p ? 3'b001 : acc_out;
  hpc2 uacc (.clk(clk), .a(acc_in), .b(bsh), .r(rnd[{3 * G0 + 2}:{3 * G0}]), .c(acc_out));
  reg [2:0] acc_last;
  always @(posedge clk) acc_last <= acc_out;
  hpc2 ufin (.clk(clk), .a(acc_last), .b(acc_out), .r(rnd[{3 * G0 + 5}:{3 * G0 + 3}]), .c(dec));
'''
    C.gadgets += 2; C.ffs += 63
    R = 3 * C.gadgets
    v = f'''// generated by masked_verification/models/gen.py ({design}); second-order (3-share) masked ML-KEM verification lane
{HPC2}
module {design}_lane (input wire clk, input wire [11:0] x0, x1, x2, input wire [10:0] c, input wire [1:0] mode,
  input wire vin, input wire first, input wire last, input wire [{R - 1}:0] rnd,
  output wire [2:0] cdec, output wire cvalid, output wire [2:0] dec, output wire dvalid);
  // mode: 0 -> d = 4, 1 -> d = 5, 2 -> d = 10, 3 -> d = 11
  reg [11:0] x0q, x1q, x2q; reg [10:0] c0; reg [3:0] d0;
  always @(posedge clk) begin x0q <= x0; x1q <= x1; x2q <= x2; c0 <= c; d0 <= mode == 2'd0 ? 4'd4 : mode == 2'd1 ? 4'd5 : mode == 2'd2 ? 4'd10 : 4'd11; end
{front}
  {chr(10).join('  ' + l for l in C.decl)}
  {chr(10).join('  ' + l for l in C.body)}
  always @(posedge clk) begin
{chr(10).join('    ' + l for l in C.seq)}
  end
  // public control pipeline: valid / first / last aligned with the per-coefficient decision (stage {lat})
  reg [{lat}:0] vp, fp, lp, f2p;
  always @(posedge clk) begin vp <= {{vp[{lat - 1}:0], vin}}; fp <= {{fp[{lat - 1}:0], first}}; lp <= {{lp[{lat - 1}:0], last}}; f2p <= {{f2p[{lat - 1}:0], first}}; end
  assign cdec = {{{b['w'][2]}, {b['w'][1]}, {b['w'][0]}}}; assign cvalid = vp[{lat - 1}];
  reg fprev; always @(posedge clk) fprev <= fp[{lat - 1}];
  wire init_p = fp[{lat - 1}] | fprev;                 // first two coefficients start the two chains
{acc_body}
  reg [3:0] lastp; always @(posedge clk) lastp <= {{lastp[2:0], lp[{lat - 1}]}};
  assign dvalid = lastp[3];
endmodule
'''
    OUT.mkdir(exist_ok=True); (OUT / f'{design}.v').write_text(v)
    print(f'{design}: HPC2 gadgets {C.gadgets} (kernel {G0}), random bits/cycle {R}, decision latency {lat} cycles, '
          f'alignment+gadget FFs ~{C.ffs}, multiplier M={M} S={S}')
    return C

LEAK = '--leak' in sys.argv
if __name__ == '__main__':
    build(sys.argv[1])
