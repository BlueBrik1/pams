import json, sys
J = json.load(open(sys.argv[1])); M = J['modules'][sys.argv[2]]
names = {}
for n, net in M['netnames'].items():
    for i, b in enumerate(net['bits']):
        if isinstance(b, int): names.setdefault(b, f'{n}[{i}]')
OUTPINS = {'Z', 'ZN', 'Q', 'QN', 'CO', 'S'}
drv = {}
for cn, c in M['cells'].items():
    for pn, bs in c['connections'].items():
        isout = (J['modules'][c['type']]['ports'][pn]['direction'] == 'output') if c['type'] in J['modules'] else pn in OUTPINS
        if isout:
            for b in bs: drv[b] = (cn, c['type'])
# find nets named x0/x1/x2 cone mixing: show a few cells that read two different x-port cones directly
for cn, c in list(M['cells'].items()):
    if c['type'] in ('BUF_X1', 'BUF_X4', 'CLKBUF_X3'):
        ins = [b for pn, bs in c['connections'].items() if pn == 'A' for b in bs]
        print(cn[-30:], c['type'], 'input net', [names.get(b, b) for b in ins], 'driver', [drv.get(b) for b in ins]); break
# provenance: walk back from shr[2] through drivers, printing types and the input pins seen
seen = set(); stack = [M['netnames']['shr']['bits'][2]]; depth = 0
while stack and depth < 12:
    b = stack.pop(); depth += 1
    if b in seen or b not in drv: continue
    seen.add(b); cn, ty = drv[b]; c = M['cells'][cn]
    print('net', names.get(b), '<-', ty, {pn: [names.get(x, x) for x in bs] for pn, bs in c['connections'].items()})
    for pn, bs in c['connections'].items():
        isout = (J['modules'][c['type']]['ports'][pn]['direction'] == 'output') if c['type'] in J['modules'] else pn in OUTPINS
        if not isout: stack.extend(x for x in bs if isinstance(x, int))
