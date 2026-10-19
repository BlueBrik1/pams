#!/usr/bin/env python3
"""Matched synthesis benchmark of the generated lanes.
Flow: phase2 flow B (Yosys + ABC on Nangate45 typical, BUF_X1 drive, 5 fF load), OpenSTA data-path groups.
Mappings: 5 per design, identical for both designs:
- ABC -D 500 with 0 / 3 / 6 dummy pad modules (the Phase VIII perturbation);
- ABC -D 400 and -D 650.
Every mapping gets a gate-level functional re-check (sim.py on the exported gate netlist) and the structural
share-domain check (domaincheck.py on the mapped JSON).
Results: masked_verification/runs/bench.json (merged per design).
usage: python3 -I bench.py [designs...]"""
import json, statistics, subprocess, sys, time
from pathlib import Path
H = Path(__file__).resolve().parent; P2 = H.parents[1]; sys.path.insert(0, str(P2))
import bfbench as B
B.FLOW = 'B'
MAPS = ((0, 500), (1, 500), (2, 500), (3, 400), (4, 650))

def synth_D(files, work, top, D):
    """bfbench.synth (flow B), with the ABC delay target D as the only change."""
    text = Path(B.__file__).read_text()
    body = text[text.index('def synth(files, work, top='):text.index('GROUPS = {')]
    assert body.count('-D 500') == 1
    ns = dict(B.__dict__); exec(compile(body.replace('-D 500', f'-D {D}'), 'synth_D', 'exec'), ns)
    return ns['synth'](files, work, top)

def run(d):
    subprocess.run([sys.executable, '-I', str(H / 'gen.py'), d], check=True)
    rtl = H.parents[0] / 'rtl' / f'{d}.v'; maps = []
    for k, D in MAPS:
        w = H.parents[0] / 'runs' / f'syn_{d}_p{k}'; w.mkdir(parents=True, exist_ok=True); t0 = time.monotonic()
        pad = w / 'pad.v'
        pad.write_text(''.join(f'module __pad{i}(input [3:0] x, output [3:0] y); assign y = x + {i}; endmodule\n' for i in range(3 * k if k < 3 else 0)))
        m, mapped, gl = synth_D(([pad] if k in (1, 2) else []) + [rtl], w, f'{d}_lane', D)
        m.update(B.sta(mapped, w, top=f'{d}_lane'))
        g = subprocess.run([sys.executable, '-I', str(H / 'sim.py'), d, '1500', str(10 + k), str(gl)], capture_output=True, text=True)
        dc = subprocess.run([sys.executable, '-I', str(H / 'domaincheck.py'), str(w / 'mapped.json'), f'{d}_lane'], capture_output=True, text=True)
        maps.append(dict(k=k, D=D, area=m['area'], ff=m['ff'], cells=m['cells'], tclk=m['tclk'], crit_group=m['crit_group'],
                         crit_start=m['crit_start'], crit_end=m['crit_end'], warnings=m['unexpected_warnings'],
                         gate_pass=g.returncode == 0, gate_check=(g.stdout.strip().splitlines() or [g.stderr[-200:]])[-1],
                         domain_pass=dc.returncode == 0, domain_check=dc.stdout.strip().splitlines()[0] if dc.stdout.strip() else dc.stderr[-200:],
                         seconds=round(time.monotonic() - t0)))
        print(d, maps[-1], flush=True)
    med = lambda key: statistics.median(x[key] for x in maps)
    return dict(maps=maps, area_med=med('area'), area_min=min(x['area'] for x in maps), area_max=max(x['area'] for x in maps),
                tclk_med=med('tclk'), tclk_min=min(x['tclk'] for x in maps), tclk_max=max(x['tclk'] for x in maps), ff_med=med('ff'),
                all_gate_pass=all(x['gate_pass'] for x in maps), all_domain_pass=all(x['domain_pass'] for x in maps))

if __name__ == '__main__':
    out = H.parents[0] / 'runs' / 'bench.json'
    res = json.loads(out.read_text()) if out.exists() else {}
    for d in sys.argv[1:] or ['base', 'pams']:
        res[d] = run(d); out.write_text(json.dumps(res, indent=1))
    for d, r in res.items():
        print(f'{d}: area {r["area_med"]:.0f} [{r["area_min"]:.0f}, {r["area_max"]:.0f}] um2, tclk {r["tclk_med"]:.3f} '
              f'[{r["tclk_min"]:.3f}, {r["tclk_max"]:.3f}] ns, FF {r["ff_med"]}, gate {r["all_gate_pass"]}, domains {r["all_domain_pass"]}')
