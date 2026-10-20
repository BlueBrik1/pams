#!/usr/bin/env python3
"""Phase XIII competitor generator. Reuses the frozen Phase XI parts verbatim (models/gen.py: Ckt, HPC2 module,
floor_mult, kernel_base, kernel_pams2); only the verification kernel, the share-wise front end and the pipelining
change. The frozen generator and rtl/ are never written (gen.OUT is redirected to competitors/rtl).

designs (module <name>_lane, identical ports/contract to rtl/pams.v and rtl/base.v):
  base        frozen baseline, re-emitted by gen.build (byte-identical check against rtl/base.v)
  pams        frozen PAMS, re-emitted by gen.build (byte-identical check against rtl/pams.v)
  base_x      Simple (Fritzmann 2022 / D'Anvers 2023) through this generator; must equal 'base' (regression check)
  pams_x      PAMS-split through this generator; must equal 'pams' (regression check)
  suffixes (any order, after the family name):
    j   just-in-time CSA: the single-domain bits y_i[k] (1 FF per share bit) are delayed to the ripple stage that
        consumes them, instead of the 3-share S_k / T_k (6 FFs per bit position).  Generic, applied to all families.
    p   one extra share-wise front-end pipeline stage: register after the constant multiplier.  Generic.
    bk  (Simple only) Brent-Kung parallel-prefix carry into bit t (the adder architecture of X2X, Norga et al. 2025)
        instead of the ripple carry; HPC2 gadgets as everywhere else.
  hoc...      Coron et al. 2023 HOCompress precision: Simple datapath with alpha = 14 fractional bits (t = 14, 25-bit
              lane, rounding offset A = 0 -- exact, see check_offsets()), compare = zero test of the top d bits.
  bos...      Bos et al. 2021-style exact interval test, strongest form found (see CANDIDATES.md): x0' = (x0 - a_c) mod q
              share-locally, Boolean 14-bit sum s = x0' + x1 + x2 < 3q, and
              decision = [s < W] ^ [s < q] ^ [s < q + W] ^ [s < 2q] ^ [s < 2q + W]  (the three windows are disjoint).
usage: python3 -I cgen.py NAME [NAME ...]     writes competitors/rtl/NAME.v"""
import re, sys
from pathlib import Path
CM = Path(__file__).resolve().parent; MV = CM.parents[1]
sys.path.insert(0, str(MV / 'models'))
import gen as G  # noqa: E402
G.OUT = CM.parent / 'rtl'
Q = 3329


def parse(name):
    fam = re.match(r'(base|pams|hoc|bos)', name).group(1)
    sfx = name[len(fam):].lstrip('_')
    if sfx in ('', 'x'): return fam, dict(j=False, p=False, bk=False)
    return fam, dict(j='j' in sfx.replace('bk', ''), p='p' in sfx.replace('bk', ''), bk='bk' in sfx)


def acc(y, i, k, C, tt):            # share i, bit k of the share-wise value, delayed to stage tt
    s = y[i][k]; return C.delay(s, tt - s['t'])


def S_at(C, y, k, tt): return C.xor(C.xor(acc(y, 0, k, C, tt), acc(y, 1, k, C, tt)), acc(y, 2, k, C, tt))


def T_at(C, y, k, tt):              # T_k = maj(y[k-1]) with its output at stage tt (HPC2 latency 2)
    return C.maj(*(acc(y, i, k - 1, C, tt - 2) for i in range(3)))


class Lazy(dict):
    """memoised S_k / T_k at their earliest stage, created on first use (jit: the low bits never need them)"""
    def __init__(self, f): super().__init__(); self.f = f
    def __missing__(self, k): self[k] = v = self.f(k); return v


def early_st(C, y, n, jit, nt=None):
    """early S_k (stage t0) and T_k (stage t0 + 2). Eager in frozen order when not jit (regression identity)."""
    t0 = y[0][0]['t']; nt = n if nt is None else nt
    if jit: return Lazy(lambda k: S_at(C, y, k, t0)), Lazy(lambda k: T_at(C, y, k, t0 + 2))
    return [S_at(C, y, k, t0) for k in range(n)], [None] + [T_at(C, y, k, t0 + 2) for k in range(1, nt)]


def carry_bk(C, S, T, lo, hi):
    """Brent-Kung style carry into bit hi from bits lo..hi-1 of S + T (carry-in 0): (G, P) prefix tree, one HPC2 per
    generate, one per generate-merge, one per propagate-merge that is still needed (the lowest group's P never is)."""
    nodes = [(C.hpc2(S[k], T[k]), C.xor(S[k], T[k]), k == lo) for k in range(lo, hi)]
    while len(nodes) > 1:
        nxt = []
        for i in range(0, len(nodes) - 1, 2):
            (gl, pl, low), (gh, ph, _) = nodes[i], nodes[i + 1]
            g = C.xor(gh, C.hpc2(ph, gl))                          # g_hi and p_hi are exclusive: OR = XOR
            nxt.append((g, None if low else C.hpc2(ph, pl), low))
        if len(nodes) % 2: nxt.append(nodes[-1])
        nodes = nxt
    return nodes[0][0]


def kernel_simple(C, y, en, n, t, jit, bk):
    """kernel_base generalised: [bits t .. t+d-1 of (y0 + y1 + y2) are zero]; jit / bk as in the module doc."""
    t0 = y[0][0]['t']
    S, T = early_st(C, y, n, jit)                                    # early copies (top region, BK leaves)
    if bk:
        carry = carry_bk(C, S, T, 1, t)
    else:
        carry = None
        for k in range(1, t):                                     # ripple carry into bit t (c_1 = 0)
            tt = t0 + 2 if carry is None else carry['t']
            Sk, Tk = (S_at(C, y, k, tt), T_at(C, y, k, tt)) if jit else (S[k], T[k])
            carry = C.hpc2(Sk, Tk) if carry is None else C.maj(Sk, Tk, carry)
    e = []
    for k in range(t, n):                                         # carry-free zero test of the top region
        if k == t:
            Sk, Tk = S[k], T[k]          # boundary bit: T_t is also needed early (OR term of bit t + 1), so reuse it
            e.append(C.and_pub(C.xor(C.xor(Sk, Tk), carry), en[k]))
        else:
            cp = C.or_(S[k - 1], T[k - 1])                        # before the XOR: frozen creation order
            e.append(C.and_pub(C.xor(C.xor(S[k], T[k]), cp), en[k]))
    late, early = e[0], e[1:]
    while len(early) > 1:
        nxt = [C.or_(early[i], early[i + 1]) for i in range(0, len(early) - 1, 2)]
        if len(early) % 2: nxt.append(early[-1])
        early = nxt
    return C.not_(C.or_(late, early[0]))


def kernel_pams_split(C, y, theta, jit, n=14, m=11):
    """kernel_pams2 (frozen PAMS-split) with the optional just-in-time CSA."""
    t0 = y[0][0]['t']
    S, T = early_st(C, y, n, jit)
    lt = C.and_pub(C.not_(S[0]), theta[0]); carry = None
    for k in range(1, m):
        tt = t0 + 2 if carry is None else carry['t']
        Sk, Tk = (S_at(C, y, k, tt), T_at(C, y, k, tt)) if jit else (S[k], T[k])
        z = C.xor(C.xor(Sk, Tk), carry) if carry is not None else C.xor(Sk, Tk)
        nt = C.p(f'~{theta[k]["w"]}', theta[k]['t'])
        lt = C.xor_pub(C.hpc2(C.xor_pub(z, nt), C.xor_pub(lt, theta[k])), theta[k])
        carry = C.hpc2(Sk, Tk) if carry is None else C.maj(Sk, Tk, carry)
    Sm, Tm = S[m], T[m]                  # boundary bit: T_m is also needed early (OR term of bit m + 1), so reuse it
    e_m = C.xor(C.xor(Sm, Tm), carry)
    early = [C.xor(C.xor(S[k], T[k]), C.or_(S[k - 1], T[k - 1])) for k in range(m + 1, n)]
    while len(early) > 1:
        nxt = [C.or_(early[i], early[i + 1]) for i in range(0, len(early) - 1, 2)]
        if len(early) % 2: nxt.append(early[-1])
        early = nxt
    top_zero = C.hpc2(C.not_(e_m), C.not_(early[0]))
    return C.hpc2(top_zero, lt)


def kernel_bos(C, y, ths, jit, w=12):
    """[s < th] XOR-combined over the five public thresholds ths (14-bit), s = y0 + y1 + y2 (12-bit shares):
    one ripple carry chain (CSA + carries) feeding five fused ripple comparators (one HPC2 per bit and threshold)."""
    t0 = y[0][0]['t']; n = 14
    S, T = early_st(C, y, w, jit, w + 1)                               # T_k = maj(y[k-1]), k = 1..12
    lts = [C.and_pub(C.not_(S[0]), th[0]) for th in ths]
    carry = None
    for k in range(1, n):
        tt = t0 + 2 if carry is None else carry['t']
        if k < w:
            Sk, Tk = (S_at(C, y, k, tt), T_at(C, y, k, tt)) if jit else (S[k], T[k])
            z = C.xor(C.xor(Sk, Tk), carry) if carry is not None else C.xor(Sk, Tk)
            nc = C.hpc2(Sk, Tk) if carry is None else C.maj(Sk, Tk, carry)
        elif k == w:                                                # S_12 = 0
            Tk = T_at(C, y, k, tt) if jit else T[k]
            z = C.xor(Tk, carry); nc = C.hpc2(Tk, carry)
        else:                                                       # bit 13 = carry out of bit 12
            z = carry; nc = None
        for j, th in enumerate(ths):
            nt = C.p(f'~{th[k]["w"]}', th[k]['t'])
            lts[j] = C.xor_pub(C.hpc2(C.xor_pub(z, nt), C.xor_pub(lts[j], th[k])), th[k])
        carry = nc
    out = lts[0]
    for lt in lts[1:]: out = C.xor(out, lt)
    return out


def build(name):
    fam, o = parse(name)
    C = G.Ckt(); P = int(o['p'])
    if fam == 'pams':
        K = 14; M, S = G.floor_mult(K); width = K
        y_regs = (f'''  wire [47:0] m0 = {{36'b0, x0r}} * 48'd{M}, m1 = {{36'b0, x1r}} * 48'd{M}, m2 = {{36'b0, x2r}} * 48'd{M};
  wire [13:0] s0 = m0 >> {S}, s1 = m1 >> {S}, s2 = m2 >> {S};
''' + ('''  // extra share-wise pipeline stage after the multiplier (variant p)
  reg [13:0] s0p, s1p, s2p, lowp, thp;
  always @(posedge clk) begin s0p <= s0; s1p <= s1; s2p <= s2; lowp <= lowr; thp <= thr; end
  reg [13:0] y0, y1, y2, th2;
  always @(posedge clk) begin y0 <= s0p - lowp + 14'd2; y1 <= s1p; y2 <= s2p; th2 <= thp; end
''' if P else '''  reg [13:0] y0, y1, y2, th2;
  always @(posedge clk) begin y0 <= s0 - lowr + 14'd2; y1 <= s1; y2 <= s2; th2 <= thr; end
'''))
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
{y_regs}'''
        t0 = 3 + P
        y = [[C.m([f'y0[{k}]', None, None], t0) for k in range(width)], [C.m([None, f'y1[{k}]', None], t0) for k in range(width)],
             [C.m([None, None, f'y2[{k}]'], t0) for k in range(width)]]
        theta = [C.p(f'th2[{k}]', t0) for k in range(width)]
        b = kernel_pams_split(C, y, theta, o['j'])
    elif fam in ('base', 'hoc'):
        t = 13 if fam == 'base' else 14; A = 1 if fam == 'base' else 0
        W = 11 + t; M, S = G.floor_mult(W)
        if fam == 'base':
            off = "((({13'b0, c0}) << 1) - 24'd1) * 24'd4096 - 24'd1"           # frozen text, (2c - 1) 2^12 - A
        else:
            off = f"((({{{W - 11}'b0, c0}}) << 1) - {W}'d1) * {W}'d{1 << (t - 1)}"  # (2c - 1) 2^13, A = 0
        y_regs = (f'''  wire [{W + 35}:0] m0 = {{{W + 24}'b0, x0r}} * {W + 36}'d{M}, m1 = {{{W + 24}'b0, x1r}} * {W + 36}'d{M}, m2 = {{{W + 24}'b0, x2r}} * {W + 36}'d{M};
  wire [{W - 1}:0] f0 = m0 >> {S}, f1 = m1 >> {S}, f2 = m2 >> {S};
''' + (f'''  // extra share-wise pipeline stage after the multiplier (variant p)
  reg [{W - 1}:0] fq0, fq1, fq2, offp, enp; reg [2:0] shp;
  always @(posedge clk) begin fq0 <= f0; fq1 <= f1; fq2 <= f2; offp <= offr; enp <= enr; shp <= shr; end
  wire [{W - 1}:0] s0 = fq0 >> shp, s1 = fq1 >> shp, s2 = fq2 >> shp;
  reg [{W - 1}:0] y0, y1, y2, en2;
  always @(posedge clk) begin y0 <= s0 - offp; y1 <= s1; y2 <= s2; en2 <= enp; end
''' if P else f'''  wire [{W - 1}:0] s0 = f0 >> shr, s1 = f1 >> shr, s2 = f2 >> shr;
  reg [{W - 1}:0] y0, y1, y2, en2;
  always @(posedge clk) begin y0 <= s0 - offr; y1 <= s1; y2 <= s2; en2 <= enr; end
'''))
        front = f'''
  // stage 1: public offset (2c - 1) 2^{t - 1} - {A} and region enables; mode shift 11 - d
  reg [{W - 1}:0] offr; reg [{W - 1}:0] enr; reg [2:0] shr; reg [11:0] x0r, x1r, x2r;
  always @(posedge clk) begin
    offr <= {off};
    enr <= (({W}'d1 << (5'd{t} + d0)) - {W}'d1) & ~{W}'h{(1 << t) - 1:x};
    shr <= 4'd11 - d0; x0r <= x0q; x1r <= x1q; x2r <= x2q;
  end
  // stage 2: share-wise modulus switch floor(x_i 2^({t}+d) / q) = ((x_i * {M}) >> {S}) >> (11 - d); share 0 offset
{y_regs}'''
        t0 = 3 + P
        y = [[C.m([f'y0[{k}]', None, None], t0) for k in range(W)], [C.m([None, f'y1[{k}]', None], t0) for k in range(W)],
             [C.m([None, None, f'y2[{k}]'], t0) for k in range(W)]]
        en = [C.p(f'en2[{k}]', t0) for k in range(W)]
        b = kernel_simple(C, y, en, W, t, o['j'], o['bk'])
    else:   # bos
        assert not P, 'bos has no multiplier stage to pipeline'
        front = f'''
  // stage 1: public interval start a_c = ceil((2c - 1) q / 2^(d+1)) mod q and width W_c = a_(c+1) - a_c mod q
  wire [3:0] sh = d0 + 4'd1;
  wire [11:0] cm = (12'd1 << d0) - 12'd1;
  wire [23:0] num_c = ({{12'b0, c0, 1'b0}} - 24'd1) * 24'd{Q}, num_n = ({{12'b0, c0, 1'b0}} + 24'd1) * 24'd{Q};
  wire [11:0] wrap = 12'd{Q} - (12'd{Q} >> sh);                       // a_0 = a_(2^d) = q - floor(q / 2^(d+1))
  wire [11:0] ac = (c0 == 11'd0) ? wrap : (num_c + (24'd1 << sh) - 24'd1) >> sh;
  wire [11:0] an = ({{1'b0, c0}} == cm) ? wrap : (num_n + (24'd1 << sh) - 24'd1) >> sh;
  wire [11:0] wc = (an >= ac) ? an - ac : an + 12'd{Q} - ac;
  reg [11:0] acr, wr; reg [11:0] x0r, x1r, x2r;
  always @(posedge clk) begin acr <= ac; wr <= wc; x0r <= x0q; x1r <= x1q; x2r <= x2q; end
  // stage 2: share 0 shifted share-locally to the interval start: x0' = (x0 - a_c) mod q; thresholds W, q + W, 2q + W
  reg [11:0] y0, y1, y2; reg [13:0] tw0, tw1, tw2;
  always @(posedge clk) begin
    y0 <= (x0r >= acr) ? x0r - acr : x0r + 12'd{Q} - acr; y1 <= x1r; y2 <= x2r;
    tw0 <= {{2'b0, wr}}; tw1 <= {{2'b0, wr}} + 14'd{Q}; tw2 <= {{2'b0, wr}} + 14'd{2 * Q};
  end
'''
        t0 = 3
        y = [[C.m([f'y0[{k}]', None, None], t0) for k in range(12)], [C.m([None, f'y1[{k}]', None], t0) for k in range(12)],
             [C.m([None, None, f'y2[{k}]'], t0) for k in range(12)]]
        const = lambda v: [C.p("1'b1" if v >> k & 1 else "1'b0", t0) for k in range(14)]
        ths = [[C.p(f'tw0[{k}]', t0) for k in range(14)], const(Q), [C.p(f'tw1[{k}]', t0) for k in range(14)],
               const(2 * Q), [C.p(f'tw2[{k}]', t0) for k in range(14)]]
        b = kernel_bos(C, y, ths, o['j'])
    return emit(name, C, b, front)


def emit(design, C, b, front):
    """Lane wrapper: verbatim copy of the tail of gen.build (accumulator, control pipeline, ports)."""
    lat = b['t']; G0 = C.gadgets
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
{G.HPC2}
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
    info = dict(design=design, gadgets=C.gadgets, kernel_gadgets=G0, rnd_bits=R, latency=lat, ffs_model=C.ffs)
    return v, info


def check_offsets():
    """Simple / HOCompress exactness for every x and every floor-sum error e in {0, 1, 2} (superset of the reachable
    errors): t = 13 needs A = 1 (frozen base), t = 14 admits A = 0 (HOCompress rounding offset)."""
    comp = lambda x, d: ((x << (d + 1)) + Q) // (2 * Q) % (1 << d)
    for t, A in ((13, 1), (14, 0)):
        for d in (4, 5, 10, 11):
            for x in range(Q):
                v = (x << (d + t)) // Q
                assert all(((v - e + A + (1 << (t - 1))) >> t) % (1 << d) == comp(x, d) for e in (0, 1, 2)), (t, A, d, x)


def check_bos_windows():
    """[compress_d(x) = c] == [(x - a_c) mod q < W_c] for all d, c, x, with a_c, W_c as computed in the RTL."""
    comp = lambda x, d: ((x << (d + 1)) + Q) // (2 * Q) % (1 << d)
    for d in (4, 5, 10, 11):
        sh = d + 1; wrap = Q - (Q >> sh)
        a = lambda c: wrap if c in (0, 1 << d) else (((2 * c - 1) * Q) + (1 << sh) - 1) >> sh
        for c in range(1 << d):
            W = (a(c + 1) - a(c)) % Q
            assert all((comp(x, d) == c) == ((x - a(c)) % Q < W) for x in range(Q)), (d, c)


if __name__ == '__main__':
    check_offsets(); check_bos_windows()
    out = CM.parent / 'rtl'; out.mkdir(exist_ok=True)
    for name in sys.argv[1:]:
        if name in ('base', 'pams'):                    # frozen generator, redirected output; must equal rtl/<name>.v
            G.build(name); same = (out / f'{name}.v').read_bytes() == (MV / 'rtl' / f'{name}.v').read_bytes()
            print(f'{name}: frozen generator re-emitted, identical to rtl/{name}.v: {same}'); assert same; continue
        v, info = build(name)
        (out / f'{name}.v').write_text(v)
        if name in ('base_x', 'pams_x'):                # regression: this generator reproduces the frozen design
            ref = (MV / 'rtl' / f'{name[:-2]}.v').read_text().replace(f'{name[:-2]}_lane', f'{name}_lane').replace(f'gen.py ({name[:-2]})', f'gen.py ({name})')
            print(f'{name}: identical to rtl/{name[:-2]}.v up to the module name: {v == ref}'); assert v == ref
        print(info)
