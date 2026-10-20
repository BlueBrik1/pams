"""Bit-level structural Verilog from a Yosys JSON netlist (runs/syn_*/mapped.json), for PROLEAD's netlist reader.

mapped.json and mapped.v are written by the same Phase XI Yosys run from the same design state (cell types and
counts are checked identical in run_lane.py). Emission keeps every cell and pin connection; nets that Yosys aliased
with `assign` become a single wire; bits driven only by 'x' are dropped after checking that no cell reads them.
"""
import copy, re

CONST = {'0': "1'b0", '1': "1'b1"}


def _san(s):
    s = re.sub(r'[^A-Za-z0-9_]', '_', s.lstrip('\\$'))
    return s if re.match(r'[A-Za-z_]', s) else 'n' + s


def emit(J, name):
    m = J['modules'][name]
    names, used = {}, set()
    port_bits = {}
    for p, d in m['ports'].items():
        for i, b in enumerate(d['bits']):
            if isinstance(b, int): port_bits.setdefault(b, []).append((p, i, len(d['bits'])))
    for b, lst in port_bits.items():          # a port bit is named after its first port
        p, i, w = lst[0]; names[b] = f'{p}[{i}]' if w > 1 or p in ('rnd',) else p
    # nets feeding a flip-flop D pin get the prefix pd_: under the robust probing model every other wire's extended
    # probe is a subset of a pd_ net's (or an output port's), so probe placement can be restricted to these
    dpin = {b for c in m['cells'].values() if c['type'].startswith('DFF') for b in c['connections'].get('D', [])}
    dpin |= {b for c in m['cells'].values() if c['type'] == 'hpc2' for p in 'abr' for b in c['connections'][p]}  # ra/rb/rr
    cand = sorted(m['netnames'].items(), key=lambda kv: (kv[1].get('hide_name', 0), len(kv[0])))
    for n, d in cand:
        for i, b in enumerate(d['bits']):
            if isinstance(b, int) and b not in names:
                base = ('pd_' if b in dpin else '') + _san(n) + (f'_{i}' if len(d['bits']) > 1 else '')
                while base in used: base += '_'
                used.add(base); names[b] = base
    for c in m['cells'].values():             # bits added by a negative-control edit have no netname yet
        for bs in c['connections'].values():
            for b in bs:
                if isinstance(b, int) and b not in names: names[b] = f'nc_n{b}'
    read = {b for c in m['cells'].values() for p, bs in c['connections'].items()
            if c.get('port_directions', {}).get(p, 'input') != 'output' for b in bs}
    expr = lambda bs: (lambda xs: xs[0] if len(xs) == 1 else '{ ' + ', '.join(reversed(xs)) + ' }')(
        [CONST[b] if b in CONST else names[b] for b in bs])

    out = [f"module {name}({', '.join(m['ports'])});"]
    for p, d in m['ports'].items():
        w = len(d['bits'])
        out.append(f"  {d['direction']} {f'[{w - 1}:0] ' if w > 1 or p == 'rnd' else ''}{p};")
    for b, n in sorted(names.items()):
        if b not in port_bits: out.append(f'  wire {n};')
    for cn, c in sorted(m['cells'].items()):
        conns = []
        for p, bs in c['connections'].items():
            if any(b == 'x' for b in bs):
                assert c['port_directions'].get(p) == 'output', (cn, p)
                continue
            conns.append(f'.{p}({expr(bs)})')
        out.append(f"  {c['type']} {_san(cn)} ( {', '.join(conns)} );")
    for b, lst in port_bits.items():          # a bit shared by two ports, e.g. output = input
        for p, i, w in lst[1:]:
            out.append(f"  assign {p}[{i}] = {names[b]};" if w > 1 else f'  assign {p} = {names[b]};')
    for p, d in m['ports'].items():           # constant-driven output bits
        for i, b in enumerate(d['bits']):
            if b in CONST and d['direction'] == 'output':
                assert True
                out.append(f"  assign {p}{f'[{i}]' if len(d['bits']) > 1 else ''} = {CONST[b]};")
    dropped = [n for n, d in m['netnames'].items() for b in d['bits'] if b == 'x']
    assert not any(b == 'x' for b in read), 'x drives a cell input'
    out.append('endmodule')
    return '\n'.join(out) + '\n', {'cells': len(m['cells']), 'x_netname_bits_dropped': len(dropped)}


# ---- negative controls on the lane, as minimal edits of the JSON netlist ----
def _new_bit(m):
    m.setdefault('_next', max(b for c in m['cells'].values() for bs in c['connections'].values()
                              for b in bs if isinstance(b, int)) + 1000)
    m['_next'] += 1
    return m['_next']


def _xor(m, name, a, b, z):
    m['cells'][name] = {'type': 'XOR2_X1', 'port_directions': {'A': 'input', 'B': 'input', 'Z': 'output'},
                        'connections': {'A': [a], 'B': [b], 'Z': [z]}}


def nc_exposed_decision(J, mod, design):
    """unmasked per-coefficient decision on an extra output: XOR of the three cdec shares (first-order leak)"""
    J = copy.deepcopy(J); m = J['modules'][mod]; s = m['ports']['cdec']['bits']
    t, z = _new_bit(m), _new_bit(m)
    _xor(m, 'nc_x1', s[0], s[1], t); _xor(m, 'nc_x2', t, s[2], z)
    m['ports']['nc_leak'] = {'direction': 'output', 'bits': [z]}
    return J


def nc_partial_recombination(J, mod, design):
    """two decision shares recombined on an extra output (second-order leak together with a probe on the third)"""
    J = copy.deepcopy(J); m = J['modules'][mod]; s = m['ports']['cdec']['bits']
    z = _new_bit(m); _xor(m, 'nc_x1', s[0], s[1], z)
    m['ports']['nc_leak'] = {'direction': 'output', 'bits': [z]}
    return J


def nc_mask_reuse(J, mod, design):
    """the gadget producing cdec gets r01 also as r12 (randomness reuse inside one lane gadget)"""
    J = copy.deepcopy(J); m = J['modules'][mod]
    g = {'pams': 'ug2250', 'base': 'ug2317'}[design]
    r = m['cells'][g]['connections']['r']
    m['cells'][g]['connections']['r'] = [r[0], r[1], r[0]]
    return J


NC = {f'NC_{f.__name__[3:]}': f for f in (nc_exposed_decision, nc_partial_recombination, nc_mask_reuse)}
