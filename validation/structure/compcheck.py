#!/usr/bin/env python3
"""Preconditions of trivial PINI composition (Cassiers & Standaert, TIFS 2020; HPC, Cassiers et al., TC 2021)
checked mechanically on a netlist. The gadget itself is verified separately (SILVER, PROLEAD); here every HPC2
instance is a black box with ports a[i], b[i], r[k], c[i].

  G  (routed netlists) every gadget instance equals the reference gadget cell-by-cell and pin-by-pin, after
     collapsing buffers inserted by P&R and ignoring drive strength; this also recovers its port nets
  D  outside the gadgets no net depends on two share domains (domain i = cone of x_i or of a gadget's c[i])
  R  each fresh random bit reaches nothing but the r-port of exactly one gadget; 3 distinct bits per gadget
  P  gadget input a[i] / b[i] depends only on domain i and public data
  O  lane output share i (cdec[i], dec[i]) is domain i
usage: compcheck.py mapped.json TOP                 (hierarchical Yosys netlist; gadget ports exact)
       compcheck.py final.v TOP --ref mapped.v       (flattened OpenROAD netlist; gadget cells named <inst>/<cell>)
"""
import collections, json, re, sys

OUT_PINS = {'Z', 'ZN', 'Q', 'QN'}
BUF = re.compile(r'^(BUF|CLKBUF)_X\d+$')
DOMAIN_IN = {'x0': 0, 'x1': 1, 'x2': 2}
base = lambda t: re.sub(r'_X\d+$', '', t)


def load_json(path, top):
    """flatten one level: lane cells + hpc2 instances (cells prefixed inst/); exact gadget port maps"""
    J = json.load(open(path)); m = J['modules'][top]; h = J['modules']['hpc2']
    net = lambda b, pre='': (f'{pre}n{b}' if isinstance(b, int) else f'const{b}')
    ports = {p: (d['direction'], [net(b) for b in d['bits']]) for p, d in m['ports'].items()}
    cells, gports = {}, {}
    for cn, c in m['cells'].items():
        if c['type'] != 'hpc2':
            cells[cn] = (c['type'], {p: net(bs[0]) for p, bs in c['connections'].items()}); continue
        pmap = {b: net(c['connections'][p][i]) for p, d in h['ports'].items() for i, b in enumerate(d['bits'])}
        gports[cn] = {p: [net(b) for b in c['connections'][p]] for p in 'abrc'}
        for hn, hc in h['cells'].items():
            cells[f'{cn}/{hn}'] = (hc['type'], {p: pmap.get(bs[0], net(bs[0], f'{cn}/')) for p, bs in hc['connections'].items()})
    return cells, ports, gports


def load_verilog(path, top):
    text = re.search(rf'module {re.escape(top)}\s*\(.*?\);(.*?)endmodule', re.sub(r'//[^\n]*', '', open(path).read()), re.S).group(1)
    ports = {}
    for d, w, names in re.findall(r'\b(input|output)\s+(?:wire\s+)?(\[\d+:\d+\])?\s*([^;]+);', text):
        for n in [x.strip() for x in names.split(',')]:
            if w:
                h, l = map(int, w[1:-1].split(':'))
                ports[n] = (d, [f'{n}[{i}]' for i in range(min(h, l), max(h, l) + 1)])
            else: ports[n] = (d, [n])
    cells = {}
    for t, n, pins in re.findall(r'\n\s*([A-Z][A-Z0-9_]*)\s+(\\\S+|[\w$]+)\s*\((.*?)\);', text, re.S):
        if t.startswith(('FILLCELL', 'TAPCELL')): continue
        pm = {p: v.strip().lstrip('\\').strip() for p, v in re.findall(r'\.(\w+)\s*\(\s*([^()]*?)\s*\)', pins)}
        cells[n.lstrip('\\')] = (t, {p: v for p, v in pm.items() if v})
    for a, b in re.findall(r'assign\s+(\S+)\s*=\s*(\S+);', text):
        cells[f'assign_{a}'] = ('BUF_X1', {'A': b.lstrip('\\'), 'Z': a.lstrip('\\')})
    return cells, ports


class Net:
    def __init__(self, cells):
        self.cells = cells; self.drv = {}; self.rd = collections.defaultdict(list)
        for cn, (t, pm) in cells.items():
            for p, n in pm.items():
                (self.drv.__setitem__(n, (cn, p)) if p in OUT_PINS else self.rd[n].append((cn, p)))

    def src(self, n):            # through buffer chains back to the real driver net; tie cells are constants
        while n in self.drv and BUF.match(self.cells[self.drv[n][0]][0]): n = self.cells[self.drv[n][0]][1]['A']
        t = self.cells[self.drv[n][0]][0] if n in self.drv else ''
        return 'const0' if t.startswith('LOGIC0') else 'const1' if t.startswith('LOGIC1') else n

    def sinks(self, n):          # real (non-buffer) readers, through buffer chains
        out, todo = [], [n]
        while todo:
            m = todo.pop()
            for c, p in self.rd.get(m, []):
                t, pm = self.cells[c]
                if BUF.match(t): todo.append(next(v for q, v in pm.items() if q in OUT_PINS))
                else: out.append((c, p))
        return out


def match_gadgets(N, ref_cells):
    """G: cell-by-cell match of every <inst>/ group against the reference hpc2 module; returns port nets"""
    gname = lambda c: c.split('/')[0] if '/' in c else None
    groups = collections.defaultdict(dict)
    for c, v in N.cells.items():
        if gname(c) and not BUF.match(v[0]) and not v[0].startswith('LOGIC'): groups[gname(c)][c.split('/', 1)[1]] = v
    ref_cells = {c: v for c, v in ref_cells.items() if not c.startswith('assign_')}   # dead `assign rXY = r[k]`
    rdrv = {n: (c, p) for c, (t, pm) in ref_cells.items() for p, n in pm.items() if p in OUT_PINS}
    gports, bad = {}, []
    for g, own in sorted(groups.items()):
        pn, err = {}, []
        if set(own) != set(ref_cells): err.append(('cell set differs', sorted(set(own) ^ set(ref_cells))[:4]))
        for rc, (rt, rpm) in ref_cells.items():
            if rc not in own: continue
            t, pm = own[rc]
            if base(t) != base(rt): err.append((rc, 'type', t, rt)); continue
            for p, rn in rpm.items():
                if p == 'CK': continue
                fn = pm.get(p)
                if p in OUT_PINS:
                    if re.match(r'c\[\d\]$', rn): pn[rn] = fn
                    continue
                fs = N.src(fn)
                if re.match(r'[abr]\[\d\]$', rn):
                    if pn.setdefault(rn, fs) != fs: err.append((rc, p, 'port net inconsistent', rn))
                else:
                    want = rdrv.get(rn)
                    got = N.drv.get(fs)
                    if want is None or got is None or got != (f'{g}/{want[0]}', want[1]): err.append((rc, p, rn, got))
        if err: bad.append((g, err[:3]))
        gports[g] = {k: [pn.get(f'{k}[{i}]') for i in range(3)] for k in 'abrc'}
    return gports, bad


def check(cells, ports, gports):
    N = Net(cells)
    gname = lambda c: c.split('/')[0] if '/' in c else None
    dom = {}
    for p, (d, nets) in ports.items():
        if d != 'input': continue
        for i, n in enumerate(nets):
            dom[n] = frozenset({DOMAIN_IN[p]}) if p in DOMAIN_IN else frozenset({f'R{i}'}) if p == 'rnd' else frozenset()
    for g, gp in gports.items():
        for i, n in enumerate(gp['c']): dom[n] = frozenset({i})
    sys.setrecursionlimit(1000000)
    internal_leaks = []

    def get(n):
        if n in dom: return dom[n] if dom[n] is not None else frozenset()
        if n.startswith('const') or "'" in n: return frozenset()
        d = N.drv.get(n)
        if d is None: return frozenset()
        c, p = d
        if gname(c): internal_leaks.append((n, c)); return frozenset()
        t, pm = cells[c]
        if t.startswith('LOGIC'): dom[n] = frozenset(); return dom[n]
        dom[n] = None                                         # cycle guard
        ins = [pm['D']] if t.startswith('DFF') else [m for q, m in pm.items() if q not in OUT_PINS and q != 'CK']
        v = frozenset().union(*[get(m) for m in ins]); dom[n] = v; return v

    mixed, rand_in_logic = [], []
    for c, (t, pm) in cells.items():
        if gname(c): continue
        for p, n in pm.items():
            if p in OUT_PINS:
                v = get(n); sh = {x for x in v if isinstance(x, int)}
                if len(sh) > 1: mixed.append((c, t, sorted(sh)))
                if any(isinstance(x, str) for x in v) and not BUF.match(t): rand_in_logic.append((c, t))
    res = {'gadgets': len(gports), 'cells_outside_gadgets': sum(1 for c in cells if not gname(c))}
    res['D_cross_domain_cells'] = (len(mixed), mixed[:5])
    res['D_gadget_internal_nets_read_outside'] = (len(internal_leaks), internal_leaks[:5])
    # R
    rnets = ports.get('rnd', ('input', []))[1]
    owner, viol = {}, []
    for g, gp in gports.items():
        if len(set(gp['r'])) != 3 or None in gp['r']: viol.append((g, 'r not 3 distinct bits', gp['r']))
        for k, n in enumerate(gp['r']):
            if n not in rnets: viol.append((g, f'r[{k}] not a fresh rnd input', n))
            elif n in owner: viol.append((g, f'r[{k}] shared with', owner[n], n))
            else: owner[n] = g
    for n in rnets:
        for c, p in N.sinks(n):
            if gname(c) != owner.get(n): viol.append(('rnd bit read outside its gadget', n, c))
    res['R_randomness_violations'] = (len(viol) + len(rand_in_logic), viol[:5] + rand_in_logic[:5])
    res['R_unused_rnd_bits'] = [n for n in rnets if n not in owner]
    # P
    pv = []
    for g, gp in gports.items():
        for port in 'ab':
            for i, n in enumerate(gp[port]):
                v = get(N.src(n)) if n else frozenset({'?'})
                if any(x != i for x in v): pv.append((g, f'{port}[{i}]', sorted(v, key=str)))
    res['P_gadget_input_domain_violations'] = (len(pv), pv[:5])
    # O
    ov = [(p, i, sorted(get(N.src(n)), key=str)) for p in ('cdec', 'dec') for i, n in enumerate(ports[p][1])
          if get(N.src(n)) != frozenset({i})]
    res['O_output_domain_violations'] = (len(ov), ov)
    res['PASS'] = all(v[0] == 0 for k, v in res.items() if isinstance(v, tuple))
    return res


if __name__ == '__main__':
    path, top = sys.argv[1], sys.argv[2]
    if path.endswith('.json'):
        cells, ports, gports = load_json(path, top); res = check(cells, ports, gports)
    else:
        cells, ports = load_verilog(path, top)
        ref, _ = load_verilog(sys.argv[sys.argv.index('--ref') + 1], 'hpc2')
        gports, bad = match_gadgets(Net(cells), ref)
        res = check(cells, ports, gports)
        res['G_gadget_mismatches'] = (len(bad), bad[:3]); res['G_reference_cells'] = len(ref)
        res['PASS'] = res['PASS'] and not bad
    print(json.dumps(res, default=str))
