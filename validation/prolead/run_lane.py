#!/usr/bin/env python3
"""PROLEAD v3.1.0 on a complete frozen lane netlist (runs/syn_<design>_p0/mapped.v, lane + hpc2 modules verbatim).

Fixture: tb_gen (lane/tb_gen.v, synthesized to Nangate45 here) turns the unshared group value into a registered
arithmetic 3-sharing mod q from fresh uniform words; its signals (tb_*) are excluded from probe placement.
One simulation = one ciphertext of N coefficients streamed one per cycle (pipeline full), fixed vs random x,
fresh rnd every cycle, public c/mode/first/last identical in both groups. The run ends at dvalid = 1, where the
masked decision must equal 1 for the fixed group (all coefficients match) -- PROLEAD checks this.

usage: run_lane.py DESIGN VARIANT ORDER CYCLES SIMS [N]
  DESIGN  pams | base;   VARIANT  frozen | NC_<name> (see NC below);   CYCLES  e.g. 30-33,61-65
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import run_gadget as G  # noqa: E402
import jnet  # noqa: E402

Q = 3329
LIB = '/home/slee5/lwe_agent_handoff/current/lib/NangateOpenCellLibrary_typical.lib'
LANE = {'pams': ('pams_lane', 120, 29), 'base': ('base_lane', 171, 31)}   # module, rnd width, cdec latency
MODE = {4: 0, 5: 1, 10: 2, 11: 3}


def vb(v, w): return f"{w}'b{v:0{w}b}"      # PROLEAD accepts binary/hex literals only


def compress(x, d): return ((x << (d + 1)) + Q) // (2 * Q) % (1 << d)


def fixed_coeffs(n):
    """Boundary-heavy fixed inputs: interval starts/ends and the wrap at 0 / q-1; first half d=11, second half d=5."""
    out = []
    for k in range(n):
        d = 11 if k < n // 2 else 5
        starts = [x for x in range(Q) if compress(x, d) != compress((x - 1) % Q, d)]
        s = starts[(37 * k + 11) % len(starts)]
        x = [s, (s - 1) % Q, 0, Q - 1, (s + 1) % Q][k % 5]
        out.append((x, d, compress(x, d)))
    return out


def tb_gen_netlist():
    j = os.path.join(HERE, 'lane', 'tb_gen_mapped.json')
    if not os.path.exists(j):
        ys = f"read_verilog {HERE}/lane/tb_gen.v; synth -top tb_gen -flatten; dfflibmap -liberty {LIB}; "              f"abc -liberty {LIB}; opt_clean; write_json {j}"
        subprocess.run(['yosys', '-q', '-p', ys], check=True)
    return jnet.emit(json.load(open(j)), 'tb_gen')[0]


def lane_json(design):
    J = json.load(open(os.path.join(RES, 'runs', f'syn_{design}_p0', 'mapped.json')))
    # mapped.json and mapped.v come from the same Yosys run; confirm cell-type multisets agree before using JSON
    v = open(os.path.join(RES, 'runs', f'syn_{design}_p0', 'mapped.v')).read()
    for mod in (LANE[design][0], 'hpc2'):
        body = re.search(rf'^module {mod}\(.*?^endmodule', v, re.S | re.M).group(0)
        vt = sorted(re.findall(r'^  (\S+) \S+ \(', body, re.M))
        assert vt == sorted(c['type'] for c in J['modules'][mod]['cells'].values()), mod
    return J


NC = jnet.NC


def build(design, variant, n):
    mod, w, lat = LANE[design]
    J = lane_json(design)
    if variant != 'frozen': J = NC[variant](J, mod, design)
    lane, info = jnet.emit(J, mod); hpc2, _ = jnet.emit(J, 'hpc2')
    extra = 'nc_leak' if 'nc_leak' in J['modules'][mod]['ports'] else ''
    ports = 'clk, tb_x, tb_r1, tb_r2, c, mode, vin, first, last, rnd, cdec, cvalid, dec, dvalid' + (f', {extra}' if extra else '')
    top = f"""module tb_top({ports});
  input clk; input [11:0] tb_x; input [31:0] tb_r1; input [31:0] tb_r2; input [10:0] c; input [1:0] mode;
  input vin; input first; input last; input [{w - 1}:0] rnd;
  output [2:0] cdec; output cvalid; output [2:0] dec; output dvalid;{f' output {extra};' if extra else ''}
  wire [11:0] x0; wire [11:0] x1; wire [11:0] x2;
  tb_gen tb_g ( .clk(clk), .tb_x(tb_x), .tb_r1(tb_r1), .tb_r2(tb_r2), .tb_x0(x0), .tb_x1(x1), .tb_x2(x2) );
  {mod} lane ( .clk(clk), .x0(x0), .x1(x1), .x2(x2), .c(c), .mode(mode), .vin(vin), .first(first), .last(last),
    .rnd(rnd), .cdec(cdec), .cvalid(cvalid), .dec(dec), .dvalid(dvalid){f', .{extra}({extra})' if extra else ''} );
endmodule
"""
    return tb_gen_netlist() + '\n' + hpc2 + '\n' + lane + '\n' + top


def config(design, n, order, cycles, sims, variate):
    w = LANE[design][1]
    fx = fixed_coeffs(n)
    bits = ''.join(format(x, '012b') for x, _, _ in reversed(fx))
    bad = int(os.environ.get('BADC', '-1'))
    pub = lambda k: [{'name': 'c[10:0]', 'value': vb(fx[k][2] ^ (k == bad), 11)}, {'name': 'mode[1:0]', 'value': vb(MODE[fx[k][1]], 2)},
                     {'name': 'vin', 'value': "1'b1"}, {'name': 'first', 'value': f"1'b{int(k == 0)}"},
                     {'name': 'last', 'value': f"1'b{int(k == n - 1)}"}]
    # idle cycles carry x = 0 with c = 1 (no match), so the accumulated decision drops to 0 right after dvalid and
    # PROLEAD's output check pins the end cycle; BADC=k makes the fixed group's coefficient k mismatch (self-test)
    idle = [{'name': 'c[10:0]', 'value': vb(1, 11)}, {'name': 'mode[1:0]', 'value': vb(0, 2)}, {'name': 'vin', 'value': "1'b0"},
            {'name': 'first', 'value': "1'b0"}, {'name': 'last', 'value': "1'b0"}]
    seq = []
    for t in range(n + 1):        # public inputs trail tb_x by one cycle (tb_gen registers the shares)
        sig = [{'name': 'tb_x[11:0]', 'value': f'group_in0[{12 * t + 11}:{12 * t}]' if t < n else vb(0, 12)}]
        sig += pub(t - 1) if t >= 1 else idle
        seq.append({'signals': sig})
    seq.append({'signals': idle})
    return {
        'performance': {'max_number_of_threads': 'all', 'minimize_probing_sets': os.environ.get('MINIMIZE', 'trivial'),
                        'compact_distributions': True, 'number_of_probing_sets_per_step': 2000000},
        'simulation': {
            'groups': [f"{12 * n}'b" + '$' * (12 * n), f"{12 * n}'b{bits}"],
            'always_random_inputs': [f'rnd[{w - 1}:0]', 'tb_r1[31:0]', 'tb_r2[31:0]'],
            'input_sequence': seq,
            # dvalid of the last coefficient (lane input cycle n) is visible n + latency + 4 cycles in; PROLEAD's
            # signal-based end_condition is rejected by its own schema validator in v3.1.0, so the count is fixed
            'number_of_clock_cycles': n + LANE[design][2] + int(os.environ.get('END_OFFSET', '5')),
            'output_shares': ['dec[0]', 'dec[1]', 'dec[2]'],
            'expected_output': ["1'b$", "1'b$" if os.environ.get('NO_OUTPUT_CHECK') else "1'b1"],
            'number_of_simulations': sims, 'number_of_simulations_per_step': min(sims, 1 << 18)},
        'hardware': {'clock_signal_name': 'clk'},
        'side_channel_analysis': {
            'order': order, 'transitional_leakage': True, 'relaxed_model': False, 'variate': variate,
            'clock_cycles': cycles.split(','),
            # flip-flop D-pin nets (pd_*, see jnet.py) and lane outputs; tb_* fixture signals excluded
            'probe_placement': {'include': {'signals': os.environ.get('PROBES', '(.*pd_.*)|(.*dec.*)|(.*nc_leak.*)|(x[012]\[.*)'),
                                            'paths': '(?!)'},
                                'exclude': {'signals': '(.*tb_.*)', 'paths': '(?!)'}}},
    }, fx


def main():
    design, variant, order, cycles, sims = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
    n = int(sys.argv[6]) if len(sys.argv) > 6 else 32
    variate = os.environ.get('VARIATE', 'univariate')
    tag = f'{design}_{variant}_o{order}_{cycles.replace(",", "+")}_{sims}'
    d = os.path.join(HERE, 'lane', tag); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    open(os.path.join(d, 'design.v'), 'w').write(build(design, variant, n))
    cfg, fx = config(design, n, order, cycles, sims, variate)
    json.dump(cfg, open(os.path.join(d, 'config.json'), 'w'), indent=1)
    cmd = [f'{G.PROLEAD}/release/PROLEAD', '-l', G.LIBRARY, '-n', 'NANG45', '-d', 'design.v', '-m', 'tb_top',
           '-c', 'config.json', '-r', 'result']
    p = subprocess.run(cmd, cwd=d, env=dict(os.environ, LD_LIBRARY_PATH=G.LIBS), capture_output=True, text=True)
    out = re.sub(r'\x1b\[[0-9;]*m', '', p.stdout + p.stderr)
    open(os.path.join(d, 'prolead.log'), 'w').write(' '.join(cmd) + '\n\n' + out)
    r = {'design': design, 'variant': variant, 'order': order, 'cycles': cycles, 'simulations': sims, 'n': n,
         'variate': variate, 'fixed_coefficients': fx, 'returncode': p.returncode,
         'edit': NC[variant].__doc__ if variant in NC else None, **G.summarize(out)}
    json.dump(r, open(os.path.join(d, 'result.json'), 'w'), indent=1)
    print(tag, json.dumps({k: r[k] for k in ('returncode', 'probing_sets', 'simulations_done', 'max_minus_log10_p',
                                              'leakage_detected', 'top_probing_set')}))


if __name__ == '__main__':
    main()
