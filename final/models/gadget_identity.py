#!/usr/bin/env python3
"""Are the mapped HPC2 gadgets of the final netlists byte-identical to the variants SILVER verified in Phase XII?
Uses validation/silver/run_silver.gadget() (the same extraction) on every final synthesis / P&R-input netlist and
compares the sha256 with validation/silver/results.json. Writes final/runs/gadget_identity.json."""
import json, sys
from pathlib import Path
sys.dont_write_bytecode = True
MV = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MV / 'validation' / 'silver'))
import run_silver as RS  # noqa: E402  (import only defines functions; main() is not run)

ver = {v['sha256_of_mapped_module']: tag for tag, v in json.load(open(MV / 'validation' / 'silver' / 'results.json'))['runs'].items()
       if 'sha256_of_mapped_module' in v}
res = {}
for d in ('pams_jqr', 'base_jq', 'pams_jpr', 'base_jp'):
    for run in [f'syn_{d}_p{k}' for k in range(5)] + [f'pnrsyn_{d}']:
        f = MV / 'competitors' / 'runs' / run
        _, h = RS.gadget(f)
        res[run] = dict(sha256=h, silver_verified_variant=ver.get(h))
(MV / 'final' / 'runs' / 'gadget_identity.json').write_text(json.dumps(dict(verified_variants=ver, netlists=res), indent=1))
for k, v in res.items(): print(k, v['silver_verified_variant'] or f"NEW VARIANT {v['sha256'][:16]}")
print('all identical to a SILVER-verified variant:', all(v['silver_verified_variant'] for v in res.values()))
