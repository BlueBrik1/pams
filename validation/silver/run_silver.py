#!/usr/bin/env python3
"""SILVER (Knichel, Sasdrich, Moradi, ASIACRYPT 2020) on the HPC2 gadget exactly as mapped in the frozen Phase XI
netlists, plus negative controls derived from the same mapped netlist by one minimal edit each.

The gadget text is copied verbatim from runs/syn_<d>_p<k>/mapped.v; the only changes are SILVER port annotations
and removal of three dead `assign rXY = r[i]` lines (unused aliases; SILVER's parser has no assign support).
Frozen files are only read. Output: validation/silver/results.json and one log per run.
"""
import hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.abspath(os.path.join(HERE, '..', '..'))
SILVER = os.path.expanduser('~/lwe_agent_handoff/phase2/ext/tools/sca/SILVER')
LIBS = os.path.expanduser('~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot/usr/lib/x86_64-linux-gnu')
ANN = {'clk': 'clock', 'a': '0_[2:0]', 'b': '1_[2:0]', 'r': 'refresh', 'c': '0_[2:0]'}


def gadget(run):
    s = open(os.path.join(RES, 'runs', run, 'mapped.v')).read()
    m = re.search(r'^module hpc2\(.*?^endmodule', s, re.S | re.M).group(0)
    return m, hashlib.sha256(m.encode()).hexdigest()


def annotate(m):
    m = clean(m)
    for port, a in ANN.items():
        m, n = re.subn(rf'^(\s*)((?:input|output)\s+(?:\[2:0\]\s+)?{port};)', rf'\1(* SILVER="{a}" *) \2', m, flags=re.M)
        assert n == 1, port
    return m


def clean(m):
    m = re.sub(r'^\s*assign r(01|02|12) = r\[\d\];\n', '', m, flags=re.M)
    assert 'assign' not in m, 'unexpected assign in mapped gadget'
    # Yosys repeats each port as a wire declaration; SILVER's parser treats the duplicate as a new undriven net
    m = re.sub(r'^\s*wire\s+(?:\[2:0\]\s+)?(?:a|b|c|r|clk|r01|r02|r12);\n', '', m, flags=re.M)
    return m


# negative controls: one minimal edit of the mapped gadget each (applied to the annotated text)
def nc_unregistered_refresh(m):
    # classic HPC/DOM glitch flaw: the cross product uses b_j ^ r_ij straight from the XOR, not from the rbr register
    m2, n = re.subn(r'\.A2\(rbr\[(\d)\]\)', r'.A2(_001_[\1])', m)
    assert n == 6; return m2

def nc_mask_reuse(m):
    # r12 replaced by r01 everywhere (3 shares need 3 independent bits; reuse is a known second-order flaw)
    m2, n = re.subn(r'\br\[2\]', 'r[0]', m)
    assert n == 3; return m2

def nc_recombine(m):
    # an output share is recombined with another domain: c[0] = c0 ^ c1 (exposes a*b to a probe on c[0] plus c[2])
    m2, n = re.subn(r'\.ZN\(c\[0\]\)', '.ZN(_c0_)', m)
    assert n == 1
    m2 = m2.replace(');\n', ');\n  wire _c0_;\n', 1)          # SILVER wants declarations before use
    m2 = m2.replace('endmodule', '  XOR2_X1 _nc_ (  .A(_c0_),  .B(c[1]),  .Z(c[0])  );\nendmodule')
    return m2


def run(name, text):
    d = os.path.join(HERE, 'work'); os.makedirs(d, exist_ok=True)
    v = os.path.join(d, f'{name}.v'); open(v, 'w').write(text)
    cmd = ['./bin/verify', '--verilog=1', '--verilog-libfile=cell/Library.txt', '--verilog-libname=NANG45',
           f'--verilog-design_file={v}', '--verilog-module_name=hpc2', f'--insfile={d}/{name}.nl', '--verbose=1',
           '--cores=8']
    env = dict(os.environ, LD_LIBRARY_PATH=f'{SILVER}/lib:{LIBS}')
    p = subprocess.run(cmd, cwd=SILVER, env=env, capture_output=True, text=True, timeout=3600)
    out = re.sub(r'\x1b\[[0-9;]*m', '', p.stdout + p.stderr)
    open(os.path.join(HERE, f'{name}.log'), 'w').write(' '.join(cmd) + '\n\n' + out)
    res = {}
    for line in out.splitlines():
        mm = re.search(r'(probing|NI|SNI|PINI)\.(standard|robust)\s+\(d \S+ (\d+)\) -- (PASS|FAIL)\.(?:\s*>> Probes: (.*))?', line)
        # SILVER prints the largest secure order on PASS and the first failing order on FAIL
        if mm:
            secure = int(mm[3]) if mm[4] == 'PASS' else int(mm[3]) - 1
            res[f'{mm[1]}.{mm[2]}'] = {'secure_up_to_order': secure, 'second_order': 'PASS' if secure >= 2 else 'FAIL',
                                       'witness_probes': (mm[5] or '').strip()}
        mm = re.search(r'uniformity\s+-- (PASS|FAIL)', line)
        if mm: res['uniformity'] = {'second_order': mm[1]}
    gates = re.search(r'Parse: (\d+) gate', out)
    return {'returncode': p.returncode, 'gates': int(gates[1]) if gates else None, 'checks': res}


def main():
    out = {'tool': 'SILVER', 'commit': subprocess.run(['git', '-C', SILVER, 'log', '-1', '--format=%H %ci'],
           capture_output=True, text=True).stdout.strip(), 'runs': {}}
    variants = {}
    for d in ('pams', 'base', 'pams_r'):
        for k in range(5):
            m, h = gadget(f'syn_{d}_p{k}')
            variants.setdefault(h, {'text': m, 'used_in': []})['used_in'].append(f'syn_{d}_p{k}')
    for i, (h, v) in enumerate(sorted(variants.items(), key=lambda x: -len(x[1]['used_in']))):
        a = annotate(v['text']); tag = f'hpc2_mapped_v{i}'
        out['runs'][tag] = {'sha256_of_mapped_module': h, 'used_in': v['used_in'], **run(tag, a)}
        if i == 0:
            for nc in (nc_unregistered_refresh, nc_mask_reuse, nc_recombine):
                t = f'NC_{nc.__name__[3:]}'
                out['runs'][t] = {'derived_from': tag, 'edit': nc.__doc__ or nc.__code__.co_consts[0], **run(t, nc(a))}
    json.dump(out, open(os.path.join(HERE, 'results.json'), 'w'), indent=1)
    for k, r in out['runs'].items():
        print(k, r['gates'], ' '.join(f"{c}={v['second_order']}" for c, v in r['checks'].items()))


if __name__ == '__main__':
    main()
