#!/usr/bin/env python3
"""Matched synthesis benchmark of the Phase XIII competitors: the frozen Phase XI procedure (models/bench.py) with
the inputs and outputs redirected to competitors/. Same flow B (Yosys 0.33 + ABC, Nangate45 typical, BUF_X1 drive,
5 fF load, HPC2 keep_hierarchy), same five mappings (ABC -D 500 with 0/3/6 pad modules, -D 400, -D 650), same
OpenSTA data-path groups, same gate-level functional re-check (models/sim.py) and share-domain check
(models/domaincheck.py), plus the Phase XII composition-precondition check (validation/structure/compcheck.py).
RTL check first: models/sim.py on the RTL with 6000 boundary-heavy coefficients (all d, wraparound, ciphertexts).
usage: python3 -I cbench.py [--maps 0,1,2,3,4] DESIGN [DESIGN ...]    results merged into competitors/runs/cbench.json"""
import json, re, statistics, subprocess, sys, time
from pathlib import Path
CM = Path(__file__).resolve().parent; C = CM.parent; MV = C.parent
sys.path.insert(0, str(MV / 'models'))
import bench  # noqa: E402  (frozen; imports bfbench with FLOW = 'B')
import sim    # noqa: E402
B = bench.B
sim.H = CM                       # sim reads <H.parents[0]>/rtl/<design>.v -> competitors/rtl
PY = sys.executable


def rtl_facts(d):
    v = (C / 'rtl' / f'{d}.v').read_text()
    return dict(gadgets=len(re.findall(r'^\s*hpc2 u', v, re.M)), rnd_bits=int(re.search(r'input wire \[(\d+):0\] rnd', v).group(1)) + 1,
                decision_latency=int(re.search(r'per-coefficient decision \(stage (\d+)\)', v).group(1)))


def run(d, maps):
    f = rtl_facts(d)
    ok = sim.run(d, 6000, 7)
    res = dict(**f, rtl_pass=ok, maps=[])
    if not ok: return res
    for k, D in [m for m in bench.MAPS if m[0] in maps]:
        w = C / 'runs' / f'syn_{d}_p{k}'; w.mkdir(parents=True, exist_ok=True); t0 = time.monotonic()
        pad = w / 'pad.v'
        pad.write_text(''.join(f'module __pad{i}(input [3:0] x, output [3:0] y); assign y = x + {i}; endmodule\n' for i in range(3 * k if k < 3 else 0)))
        m, mapped, gl = bench.synth_D(([pad] if k in (1, 2) else []) + [C / 'rtl' / f'{d}.v'], w, f'{d}_lane', D)
        m.update(B.sta(mapped, w, top=f'{d}_lane'))
        g = subprocess.run([PY, '-I', '-c', f'import sys; sys.path.insert(0, {str(CM)!r}); import cbench; '
                            f'sys.exit(0 if cbench.sim.run({d!r}, 1500, {10 + k}, {str(gl)!r}) else 1)'], capture_output=True, text=True)
        dc = subprocess.run([PY, '-I', str(MV / 'models' / 'domaincheck.py'), str(w / 'mapped.json'), f'{d}_lane'], capture_output=True, text=True)
        cc = subprocess.run([PY, '-I', str(MV / 'validation' / 'structure' / 'compcheck.py'), str(w / 'mapped.json'), f'{d}_lane'], capture_output=True, text=True)
        ccj = json.loads(cc.stdout) if cc.returncode == 0 and cc.stdout.strip().startswith('{') else {'PASS': False, 'err': cc.stderr[-300:]}
        res['maps'].append(dict(k=k, D=D, area=m['area'], ff=m['ff'], cells=m['cells'], tclk=m['tclk'], crit_group=m['crit_group'],
                                crit_start=m['crit_start'], crit_end=m['crit_end'], warnings=m['unexpected_warnings'],
                                gate_pass=g.returncode == 0, gate_check=(g.stdout.strip().splitlines() or [g.stderr[-200:]])[-1],
                                domain_pass=dc.returncode == 0, domain_check=(dc.stdout.strip().splitlines() or [dc.stderr[-200:]])[0],
                                compcheck_pass=bool(ccj.get('PASS')), seconds=round(time.monotonic() - t0)))
        print(d, res['maps'][-1], flush=True)
    ms = res['maps']; med = lambda key: statistics.median(x[key] for x in ms)
    res.update(area_med=med('area'), area_min=min(x['area'] for x in ms), area_max=max(x['area'] for x in ms),
               tclk_med=med('tclk'), tclk_min=min(x['tclk'] for x in ms), tclk_max=max(x['tclk'] for x in ms),
               ff_med=med('ff'), cells_med=med('cells'), comb_cells_med=med('cells') - med('ff'),
               all_gate_pass=all(x['gate_pass'] for x in ms), all_domain_pass=all(x['domain_pass'] for x in ms),
               all_compcheck_pass=all(x['compcheck_pass'] for x in ms))
    return res


if __name__ == '__main__':
    a = sys.argv[1:]; maps = (0, 1, 2, 3, 4)
    if a and a[0] == '--maps': maps = tuple(int(x) for x in a[1].split(',')); a = a[2:]
    out = C / 'runs' / 'cbench.json'; out.parent.mkdir(exist_ok=True)
    for d in a:
        r = run(d, maps)
        res = json.loads(out.read_text()) if out.exists() else {}      # re-read: merge-safe between sequential calls
        res[d] = r; out.write_text(json.dumps(res, indent=1))
        if r.get('maps'):
            print(f'{d}: area {r["area_med"]:.0f} [{r["area_min"]:.0f}, {r["area_max"]:.0f}] tclk {r["tclk_med"]:.3f} '
                  f'[{r["tclk_min"]:.3f}, {r["tclk_max"]:.3f}] FF {r["ff_med"]} gadgets {r["gadgets"]} rnd {r["rnd_bits"]} '
                  f'lat {r["decision_latency"]} gate {r["all_gate_pass"]} dom {r["all_domain_pass"]} comp {r["all_compcheck_pass"]}', flush=True)
        else:
            print(f'{d}: RTL check FAILED', flush=True)
