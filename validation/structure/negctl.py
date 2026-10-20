#!/usr/bin/env python3
"""Negative controls for compcheck.py: the lane NC edits used with PROLEAD (validation/prolead/jnet.py) applied to
the frozen syn_pams_p0 / syn_base_p0 netlists, plus Phase XI's deliberately leaky lane (runs/negctl_leak).
Each must FAIL. Also confirms that the gadget module used by P&R (pnrsyn_*) is byte-identical to a SILVER-verified one."""
import hashlib, json, os, re, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'prolead'))
import compcheck as C, jnet  # noqa: E402

out = {}
for d, mod in (('pams', 'pams_lane'), ('base', 'base_lane')):
    J = json.load(open(f'{RES}/runs/syn_{d}_p0/mapped.json'))
    for name, f in jnet.NC.items():
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as t: json.dump(f(J, mod, d), t)
        r = C.check(*C.load_json(t.name, mod)); os.unlink(t.name)
        out[f'{d}:{name}'] = {'PASS': r['PASS'], **{k: v[0] for k, v in r.items() if isinstance(v, tuple)}}
r = C.check(*C.load_json(f'{RES}/runs/negctl_leak/mapped.json', 'pams_leak_lane'))
out['phaseXI_negctl_leak'] = {'PASS': r['PASS'], **{k: v[0] for k, v in r.items() if isinstance(v, tuple)}}
ver = json.load(open(f'{RES}/validation/silver/results.json'))['runs']
verified = {v['sha256_of_mapped_module'] for k, v in ver.items() if k.startswith('hpc2_mapped')}
for d in ('pams', 'base'):
    s = open(f'{RES}/runs/pnrsyn_{d}/mapped.v').read()
    h = hashlib.sha256(re.search(r'^module hpc2\(.*?^endmodule', s, re.S | re.M).group(0).encode()).hexdigest()
    out[f'pnrsyn_{d}_gadget_is_SILVER_verified_variant'] = h in verified
json.dump(out, open(os.path.join(HERE, 'negctl_results.json'), 'w'), indent=1)
print(json.dumps(out, indent=1))
