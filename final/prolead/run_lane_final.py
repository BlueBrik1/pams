#!/usr/bin/env python3
"""Phase XII lane harness (validation/prolead/run_lane.py, imported read-only) pointed at the final netlists:
competitors/runs/syn_<design>_p0/mapped.json, outputs in final/prolead/lane/<tag>/. Same fixture (tb_gen, copied),
same PROLEAD build, library, probe placement, end-cycle rule (n + latency + 5) and output check.
usage: run_lane_final.py DESIGN VARIANT ORDER CYCLES SIMS [N]      DESIGN: pams_jqr | base_jq"""
import json, os, re, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); MV = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(MV, 'validation', 'prolead'))
import run_lane as L  # noqa: E402

L.HERE = HERE                                    # outputs + tb_gen fixture (copied byte-identically into ./lane/)
L.LANE.update({'pams_jqr': ('pams_jqr_lane', 120, 31), 'base_jq': ('base_jq_lane', 171, 33)})   # module, rnd bits, cdec latency


def lane_json(design):
    """run_lane.lane_json with the competitors/ path: same JSON-versus-mapped.v cell-multiset check"""
    w = os.path.join(MV, 'competitors', 'runs', f'syn_{design}_p0')
    J = json.load(open(os.path.join(w, 'mapped.json'))); v = open(os.path.join(w, 'mapped.v')).read()
    for mod in (L.LANE[design][0], 'hpc2'):
        body = re.search(rf'^module {mod}\(.*?^endmodule', v, re.S | re.M).group(0)
        assert sorted(re.findall(r'^  (\S+) \S+ \(', body, re.M)) == sorted(c['type'] for c in J['modules'][mod]['cells'].values()), mod
    return J


L.lane_json = lane_json
if __name__ == '__main__':
    L.main()
