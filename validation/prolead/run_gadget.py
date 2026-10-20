#!/usr/bin/env python3
"""PROLEAD v3.1.0 (Müller & Moradi, TCHES 2022) on the mapped HPC2 gadget: 2nd order, glitch + transition robust
probing, multivariate (probes may sit in different cycles), four back-to-back invocations (pipelined use), fixed vs
random inputs, fresh uniform r every cycle. Same gadget text and negative-control edits as validation/silver.
Usage: run_gadget.py [simulations]   Writes validation/prolead/gadget/<run>/ and gadget_results.json.
"""
import json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'silver'))
import run_silver as S  # noqa: E402  (gadget extraction + negative controls)

PROLEAD = os.path.expanduser('~/lwe_agent_handoff/phase2/ext/tools/sca/prolead-3.1.0')
LIBS = os.path.expanduser('~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot/usr/lib/x86_64-linux-gnu')
LIBRARY = os.path.join(HERE, 'library.json')
FIXED = [(1, 1), (0, 1), (1, 0), (1, 1)]           # fixed-group (a, b) per invocation; last one gives c = 1


def config(sims, check=True):
    seq = []
    for k in range(4):
        seq.append({'signals': [{'name': f'{p}[{s}]', 'value': f'group_in{s}[{2 * k + (p == "b")}]'}
                                for s in range(3) for p in ('a', 'b')]})
    seq.append({'signals': [{'name': f'{p}[{s}]', 'value': "1'b0"} for s in range(3) for p in ('a', 'b')]})
    fixed = ''.join(f'{b}{a}' for a, b in reversed(FIXED))  # bit 2k = a_k, bit 2k+1 = b_k
    return {
        'performance': {'max_number_of_threads': 'all', 'minimize_probing_sets': 'aggressive', 'compact_distributions': True},
        'simulation': {
            'groups': ["8'b$$$$$$$$", f"8'b{fixed}"],
            'always_random_inputs': ['r[0]', 'r[1]', 'r[2]'],
            'input_sequence': seq,
            'number_of_clock_cycles': 6,           # invocation k enters at cycle k, leaves 2 cycles later
            'output_shares': ['c[0]', 'c[1]', 'c[2]'],
            'expected_output': ["1'b$", "1'b1" if check else "1'b$"],   # functional check off for NCs that change c
            'number_of_simulations': sims, 'number_of_simulations_per_step': min(sims, 1 << 20)},
        'hardware': {'clock_signal_name': 'clk'},
        'side_channel_analysis': {'order': 2, 'transitional_leakage': True, 'relaxed_model': False,
                                  'variate': 'multivariate', 'distance': 6, 'clock_cycles': ['1-6']},
    }


def run(name, text, sims, check=True):
    d = os.path.join(HERE, 'gadget', name); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    open(os.path.join(d, 'design.v'), 'w').write(text)
    json.dump(config(sims, check), open(os.path.join(d, 'config.json'), 'w'), indent=1)
    cmd = [f'{PROLEAD}/release/PROLEAD', '-l', LIBRARY, '-n', 'NANG45', '-d', 'design.v', '-m', 'hpc2',
           '-c', 'config.json', '-r', 'result']
    p = subprocess.run(cmd, cwd=d, env=dict(os.environ, LD_LIBRARY_PATH=LIBS), capture_output=True, text=True,
                       timeout=6 * 3600)
    out = re.sub(r'\x1b\[[0-9;]*m', '', p.stdout + p.stderr)
    open(os.path.join(d, 'prolead.log'), 'w').write(' '.join(cmd) + '\n\n' + out)
    return {'returncode': p.returncode, **summarize(out)}


def summarize(out):
    """Final verdict line and the strongest probing set from PROLEAD's last report table."""
    r = {'leakage_detected': None, 'max_minus_log10_p': None, 'top_probing_set': None, 'probing_sets': None,
         'simulations_done': None}
    m = re.findall(r'(\d+) probing sets remain!', out)
    if m: r['probing_sets'] = int(m[-1])
    # status rows: | elapsed | ram | processed sims | probing set | -log10(p) | OKAY/LEAKAGE |
    rows = re.findall(r'^\|\s*[\d.]+s\s*\|\s*[\d.]+[GMK]B\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*([\d.]+|inf)\s*\|\s*(\w+)\s*\|',
                      out, re.M)
    if rows:
        sims, top, p, status = rows[-1]
        r.update(simulations_done=int(sims), top_probing_set=top, max_minus_log10_p=float(p),
                 leakage_detected=status != 'OKAY', status=status,
                 first_leak_at_simulations=next((int(x[0]) for x in rows if x[3] != 'OKAY'), None))
    r['tail'] = out.strip().splitlines()[-6:]
    return r


def main():
    sims = int(sys.argv[1]) if len(sys.argv) > 1 else 1 << 22
    variants = {}
    for dsg in ('pams', 'base', 'pams_r'):
        for k in range(5):
            m, h = S.gadget(f'syn_{dsg}_p{k}')
            variants.setdefault(h, {'text': m, 'used_in': []})['used_in'].append(f'syn_{dsg}_p{k}')
    res = {'tool': 'PROLEAD v3.1.0', 'simulations': sims, 'config': config(sims), 'runs': {}}
    for i, (h, v) in enumerate(sorted(variants.items(), key=lambda x: -len(x[1]['used_in']))):
        t = S.clean(v['text']); tag = f'hpc2_mapped_v{i}'
        res['runs'][tag] = {'sha256_of_mapped_module': h, 'used_in': v['used_in'], **run(tag, t, sims)}
        if i == 0:
            for nc in (S.nc_unregistered_refresh, S.nc_mask_reuse, S.nc_recombine):
                n = f'NC_{nc.__name__[3:]}'
                chk = nc is S.nc_mask_reuse                    # the other two edits change the gadget's function
                res['runs'][n] = {'derived_from': tag, 'output_check': chk, **run(n, nc(t), sims, chk)}
        print(tag, json.dumps({k: res['runs'][tag][k] for k in ('leakage_detected', 'max_minus_log10_p')}), flush=True)
    json.dump(res, open(os.path.join(HERE, 'gadget_results.json'), 'w'), indent=1)
    for k, r in res['runs'].items():
        print(f"{k:28s} leak={r['leakage_detected']} max-log10p={r['max_minus_log10_p']} top={r['top_probing_set']}")


if __name__ == '__main__':
    main()
