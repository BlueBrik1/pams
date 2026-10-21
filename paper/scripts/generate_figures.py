#!/usr/bin/env python3
"""Generate every data-derived figure of the PAMS paper from the frozen research artifacts (read-only).

Sources (all under phase2/masked_verification/):
  final/runs/pnr_stats.json            seeded P&R campaign (Phase XIV), every run
  competitors/runs/cbench.json         synthesis, 5 mappings per design (Phase XIII)
  final/data/gadget_breakdown.csv      gadget counts per kernel part (MATHEMATICS.md sec. 6)
  final/runs/pnr_<d>_T1.2_s1/          final.def + timing.rpt of the reference routed runs
  competitors/runs/syn_pams_jqr_p0/    mapped.json (Yosys) for the gate-level extracts
Outputs: paper/figures/{results,physical,gates,mathematics}/*.pdf|png, paper/data/*.tex (numbers used in the text)

usage: python3 -I generate_figures.py [results] [physical] [gates] [math] [layout]   (no argument: all)
'layout' renders the routed layouts with OpenROAD (headless save_image); it needs the ORFS image."""
import csv, json, math, os, re, statistics as st, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D

PAPER = Path(__file__).resolve().parents[1]; MV = PAPER.parent; FIG = PAPER / 'figures'
PST = json.loads((MV / 'final/runs/pnr_stats.json').read_text())
CB = json.loads((MV / 'competitors/runs/cbench.json').read_text())
NAME = {'pams_jqr': 'PAMS (pams_jqr)', 'base_jq': 'Simple baseline (base_jq)'}
COL = {'pams_jqr': '#1f5fa8', 'base_jq': '#c0392b'}
TGT = [2.0, 1.2, 1.1]
plt.rcParams.update({'font.family': 'serif', 'font.size': 8, 'axes.titlesize': 8, 'axes.labelsize': 8,
                     'legend.fontsize': 7, 'xtick.labelsize': 7, 'ytick.labelsize': 7, 'pdf.fonttype': 42,
                     'axes.spines.top': False, 'axes.spines.right': False})
W1 = 3.4     # single column width (in)


def runs(d, T=None, valid=None):
    out = [r for r in PST['runs'].values() if r['design'] == d and (T is None or abs(r['target'] - T) < 1e-9)]
    return [r for r in out if valid is None or r['valid'] == valid]


def save(fig, sub, name):
    p = FIG / sub; p.mkdir(parents=True, exist_ok=True)
    fig.savefig(p / f'{name}.pdf', bbox_inches='tight'); plt.close(fig); print('wrote', p / f'{name}.pdf')


# ------------------------------------------------------------------------------------------------ results
def fig_area():
    fig, ax = plt.subplots(figsize=(W1, 2.1))
    cats = ['synthesis\n(5 mappings)'] + [f'routed\n{T:.1f} ns' for T in TGT]
    w = 0.38
    for k, d in enumerate(('base_jq', 'pams_jqr')):
        med, lo, hi = [CB[d]['area_med']], [CB[d]['area_min']], [CB[d]['area_max']]
        for T in TGT:
            v = [r['cell'] for r in runs(d, T, True)]
            med.append(st.median(v)); lo.append(min(v)); hi.append(max(v))
        x = [i + (k - 0.5) * w for i in range(len(cats))]
        ax.bar(x, med, w, color=COL[d], label=NAME[d], yerr=[[m - l for m, l in zip(med, lo)], [h - m for m, h in zip(med, hi)]],
               capsize=2, error_kw={'lw': 0.6})
        for xi, m in zip(x, med): ax.text(xi, m + 300, f'{m / 1000:.1f}k', ha='center', va='bottom', fontsize=6)
    nb = len(runs('base_jq', 1.1, True))
    ax.text(3 - w / 2, 2000, f'n={nb}', ha='center', color='white', fontsize=6)
    ax.set_xticks(range(len(cats))); ax.set_xticklabels(cats); ax.set_ylabel('standard-cell area (µm²)'); ax.set_ylim(0, 27000)
    ax.legend(loc='upper center', ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.13))
    save(fig, 'results', 'fig_area')


def fig_die():
    fig, ax = plt.subplots(figsize=(W1, 1.9)); ax.set_aspect('equal'); ax.axis('off')
    x0 = 0
    for d in ('base_jq', 'pams_jqr'):
        r = runs(d, 2.0, True)[0]; side = math.sqrt(r['die'])
        ax.add_patch(Rectangle((x0, 0), side, side, fill=False, ec=COL[d], lw=1.2))
        core = math.sqrt(r['cell'] / 0.5)        # floorplan: utilization 0.5 of the (synthesized + tie) area
        ax.text(x0 + side / 2, side / 2, f"{NAME[d].split(' (')[0]}\ndie {side:.1f} × {side:.1f} µm\n= {r['die']:,.0f} µm²\n"
                f"routed cells {st.median(v['cell'] for v in runs(d, 2.0, True)):,.0f} µm²", ha='center', va='center', fontsize=5.8)
        x0 += side + 25
    ax.set_xlim(-5, x0); ax.set_ylim(-5, 215)
    save(fig, 'results', 'fig_die')


def fig_timing():
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.2), sharey=True)
    for ax, T in zip(axs, TGT):
        for k, d in enumerate(('pams_jqr', 'base_jq')):
            rs = sorted(runs(d, T), key=lambda r: r['seed'])
            for r in rs:
                xx = k + (r['seed'] - 4) * 0.05
                if r['valid']:
                    ax.plot(xx, r['period'], 'o', ms=4, color=COL[d])
                elif r['period'] is not None:
                    ax.plot(xx, r['period'], 'o', ms=4, mfc='none', mec=COL[d])
                else:
                    ax.plot(xx, ax.get_ylim()[1] if False else 1.28, 'x', ms=5, color=COL[d])
            v = [r['period'] for r in rs if r['valid']]
            if len(v) > 1: ax.hlines(st.median(v), k - 0.22, k + 0.22, color=COL[d], lw=0.8)
            nv = sum(r['valid'] for r in rs)
            ax.text(k, 1.035, f'{nv}/{len(rs)} valid', ha='center', fontsize=6.5, color=COL[d])
        if T < 2: ax.axhline(T, color='grey', ls=':', lw=0.8); ax.text(1.45, T, 'target', fontsize=6, color='grey', va='bottom', ha='right')
        ax.set_xticks([0, 1]); ax.set_xticklabels(['PAMS', 'baseline']); ax.set_xlim(-0.5, 1.5); ax.set_title(f'target {T:.1f} ns')
    axs[0].set_ylabel('achieved period (ns)'); axs[0].set_ylim(1.02, 1.30)
    axs[2].text(1, 1.268, 'TIMEOUT\n(90 min)', ha='center', fontsize=5.5, color=COL['base_jq'])
    fig.legend(handles=[Line2D([], [], marker='o', ls='', color='k', ms=4, label='valid run (0 DRC, hold met, RCX)'),
                        Line2D([], [], marker='o', ls='', mfc='none', mec='k', ms=4, label='finished, DRC violations (invalid)'),
                        Line2D([], [], marker='x', ls='', color='k', ms=5, label='stopped at 90-min limit'),
                        Line2D([], [], color='k', lw=0.8, label='median of valid runs')],
               loc='upper center', ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.08))
    save(fig, 'results', 'fig_timing')


def fig_gadgets():
    rows = list(csv.reader(open(MV / 'final/data/gadget_breakdown.csv')))[1:]
    parts = [r for r in rows if r[0] not in ('total', 'random bits per cycle')]
    fig, ax = plt.subplots(figsize=(W1, 1.9))
    colors = ['#4c72b0', '#55a868', '#c44e52', '#8172b2', '#ccb974', '#64b5cd']
    for k, (lab, key) in enumerate((('PAMS', 1), ('baseline', 2))):
        left = 0
        for (name, *_), c, r in zip(parts, colors, parts):
            v = int(r[key])
            if v:
                ax.barh(k, v, left=left, color=c, edgecolor='white', lw=0.5)
                if v >= 3: ax.text(left + v / 2, k, str(v), ha='center', va='center', fontsize=6.5, color='white')
            left += v
        ax.text(left + 0.8, k, f'{left} HPC2', va='center', fontsize=7)
    ax.set_yticks([0, 1]); ax.set_yticklabels(['PAMS', 'baseline']); ax.set_xlim(0, 66); ax.set_xlabel('HPC2 gadgets per lane')
    ax.legend(handles=[Patch(color=c, label=f'{p[0]} ({p[1]} / {p[2]})') for c, p in zip(colors, parts)], ncol=2, frameon=False, loc='upper center',
              bbox_to_anchor=(0.45, 1.42), fontsize=6.3)
    save(fig, 'results', 'fig_gadgets')


def fig_random():
    fig, ax = plt.subplots(figsize=(W1, 1.5))
    for k, d in enumerate(('pams_jqr', 'base_jq')):
        v = CB[d]['rnd_bits']; ax.barh(k, v, color=COL[d]); ax.text(v + 2, k, f'{v} bits/cycle  ({CB[d]["gadgets"]} gadgets × 3)', va='center', fontsize=7)
    ax.set_yticks([0, 1]); ax.set_yticklabels(['PAMS', 'baseline']); ax.set_xlim(0, 260); ax.set_xlabel('fresh random bits per cycle (lane input rnd)')
    save(fig, 'results', 'fig_random')


def fig_adp():
    fig, ax = plt.subplots(figsize=(W1, 2.4))
    mk = {2.0: 'o', 1.2: 's', 1.1: '^'}
    for d in ('pams_jqr', 'base_jq'):
        for T in TGT:
            for r in runs(d, T):
                if r['period'] is None: continue
                ax.plot(r['period'], r['cell'], mk[T], ms=3.5, color=COL[d], mfc=COL[d] if r['valid'] else 'none')
        ax.plot(CB[d]['tclk_med'], CB[d]['area_med'], '*', ms=7, color=COL[d], mec='k', mew=0.4)
    for adp in (20000, 22000, 24000, 26000, 28000):
        xs = [1.02 + i * 0.005 for i in range(50)]; ax.plot(xs, [adp / x for x in xs], color='0.8', lw=0.5, zorder=0)
        ax.text(1.265, adp / 1.265, f'{adp / 1000:.0f}k', fontsize=5.5, color='0.55', va='center')
    ax.set_xlim(1.02, 1.28); ax.set_ylim(16500, 24500); ax.set_xlabel('achieved period (ns)'); ax.set_ylabel('cell area (µm²)')
    hs = [Line2D([], [], marker=mk[T], ls='', color='k', ms=3.5, label=f'routed, target {T:.1f} ns') for T in TGT]
    hs += [Line2D([], [], marker='*', ls='', color='k', ms=6, label='synthesis (median)'),
           Line2D([], [], marker='o', ls='', mfc='none', mec='k', ms=3.5, label='invalid (DRC)'),
           Patch(color=COL['pams_jqr'], label='PAMS'), Patch(color=COL['base_jq'], label='baseline'),
           Line2D([], [], color='0.8', lw=0.5, label='iso area×delay (µm²·ns)')]
    ax.legend(handles=hs, fontsize=5.8, frameon=False, loc='upper center', ncol=3, bbox_to_anchor=(0.5, -0.2))
    save(fig, 'results', 'fig_adp')


def fig_routing():
    fig, ax = plt.subplots(figsize=(W1, 1.9))
    cats = []; w = 0.38
    for i, T in enumerate(TGT):
        for k, d in enumerate(('pams_jqr', 'base_jq')):
            rs = runs(d, T); v = sum(r['valid'] for r in rs); drc = sum(r['done'] and not r['valid'] for r in rs); to = sum(not r['done'] for r in rs)
            x = i + (k - 0.5) * w
            ax.bar(x, v, w, color=COL[d]); ax.bar(x, drc, w, bottom=v, color=COL[d], alpha=0.35, hatch='///', ec='white')
            ax.bar(x, to, w, bottom=v + drc, color='0.75', hatch='xx', ec='white')
            ax.text(x, 7.15, f'{v}/7', ha='center', fontsize=6.5, color=COL[d])
    ax.set_xticks(range(3)); ax.set_xticklabels([f'{T:.1f} ns' for T in TGT]); ax.set_ylim(0, 8.6); ax.set_ylabel('P&R runs (seeds 1–7)')
    ax.legend(handles=[Patch(color=COL['pams_jqr'], label='PAMS valid'), Patch(color=COL['base_jq'], label='baseline valid'),
                       Patch(fc='0.85', hatch='///', label='finished with DRC violations'), Patch(fc='0.75', hatch='xx', label='stopped at 90-min limit')],
              fontsize=5.8, frameon=False, ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.32))
    save(fig, 'results', 'fig_routing')


# ------------------------------------------------------------------------------------------------ physical
LEF = Path.home() / 'lwe_agent_handoff/phase2/ext/tools/orfs_rootfs/OpenROAD-flow-scripts/flow/platforms/nangate45/lef/NangateOpenCellLibrary.macro.mod.lef'


def lef_sizes():
    t = LEF.read_text(); out = {}
    for m in re.finditer(r'MACRO (\S+)(.*?)END \1', t, re.S):
        s = re.search(r'SIZE ([\d.]+) BY ([\d.]+)', m.group(2))
        if s: out[m.group(1)] = (float(s.group(1)), float(s.group(2)))
    return out


def read_def(path):
    d = path.read_text(); u = int(re.search(r'UNITS DISTANCE MICRONS (\d+)', d).group(1))
    die = [int(v) / u for v in re.search(r'DIEAREA \( (\d+) (\d+) \) \( (\d+) (\d+) \)', d).groups()]
    comps = d[d.index('\nCOMPONENTS'):d.index('END COMPONENTS')]
    cells = [(m.group(1), m.group(2), int(m.group(3)) / u, int(m.group(4)) / u)
             for m in re.finditer(r'-\s+(\S+)\s+(\S+)\s+[^;]*?\+\s+(?:PLACED|FIXED)\s+\(\s*(-?\d+)\s+(-?\d+)\s*\)', comps)]
    return die, cells


def crit_path(run):
    t = (run / 'timing.rpt').read_text().split('Startpoint:')[1]
    pts = re.findall(r'^\s+([\d.]+)\s+([\d.]+)\s+[v^]\s+(\S+)/(\S+)\s+\((\S+)\)', t, re.M)
    slack = float(re.search(r'(-?[\d.]+)\s+slack', t).group(1))
    return [(inst, pin, float(tm), cell) for dl, tm, inst, pin, cell in pts], slack


def classify(name, master):
    if master.startswith(('FILLCELL', 'TAPCELL')): return None
    if master.startswith(('BUF', 'CLKBUF')): return 'buffer'
    if master.startswith('INV') and name.startswith('clk'): return 'buffer'
    if '/' in name: return 'gadget'
    if master.startswith('DFF'): return 'ff'
    return 'logic'


CLS = {'gadget': ('#2b6cb0', 'HPC2 gadget cells (incl. 30 FFs each)'), 'ff': ('#38a169', 'flip-flops outside gadgets (pipeline / alignment)'),
       'logic': ('#dd6b20', 'other combinational logic (share-wise front end, XOR network, public logic)'), 'buffer': ('#a0aec0', 'buffers (CTS, hold, repair)')}


def fig_placement():
    sz = lef_sizes(); fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.6))
    stats = {}
    for ax, d in zip(axs, ('pams_jqr', 'base_jq')):
        run = MV / f'final/runs/pnr_{d}_T1.2_s1'; die, cells = read_def(run / 'final.def'); pos = {}
        cnt = {k: [0, 0.0] for k in CLS}
        order = {'logic': 0, 'ff': 1, 'gadget': 2, 'buffer': 3}         # buffers drawn last (on top)
        cells = sorted(cells, key=lambda t: order.get(classify(t[0], t[1]), -1))
        for name, master, x, y in cells:
            k = classify(name, master); w, h = sz.get(master, (0.19, 1.4)); pos[name] = (x + w / 2, y + h / 2)
            if k is None: continue
            cnt[k][0] += 1; cnt[k][1] += w * h
            ax.add_patch(Rectangle((x, y), w, h, color=CLS[k][0], lw=0))
        path, slack = crit_path(run)
        pts = [pos[i] for i, *_ in path if i in pos]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], '-', color='k', lw=0.9); ax.plot(*pts[0], 'o', color='k', ms=3); ax.plot(*pts[-1], 's', color='k', ms=3)
        ax.add_patch(Rectangle((0, 0), die[2], die[3], fill=False, ec='k', lw=0.6))
        ax.set_xlim(0, 210); ax.set_ylim(0, 210); ax.set_aspect('equal'); ax.set_xlabel('x (µm)')
        ax.set_title(f"{NAME[d]}\ndie {die[2]:.1f} × {die[3]:.1f} µm; worst path data delay {path[-1][2] - path[0][2]:.3f} ns", fontsize=7)
        stats[d] = {k: v for k, v in cnt.items()}
    axs[0].set_ylabel('y (µm)')
    fig.legend(handles=[Patch(color=c, label=l) for c, l in CLS.values()] + [Line2D([], [], color='k', lw=0.9, label='worst setup path: ● start register, ■ end register')],
               loc='lower center', ncol=3, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, -0.06))
    save(fig, 'physical', 'fig_placement')
    (PAPER / 'data' / 'placement_classes.json').write_text(json.dumps(stats, indent=1))


def fig_critpath():
    fig, axs = plt.subplots(2, 1, figsize=(7.0, 4.2), sharex=False)
    info = {}
    for ax, d in zip(axs, ('pams_jqr', 'base_jq')):
        run = MV / f'final/runs/pnr_{d}_T1.2_s1'; path, slack = crit_path(run)
        fv = (run / 'final.v').read_text()
        def qnet(inst):
            m = re.search(rf'DFF_X\d\s+{re.escape(inst)}\s*\((.*?)\);', fv, re.S)
            q = re.search(r'\.Q\(([^)]+)\)', m.group(1)) if m else None
            return q.group(1).strip() if q else inst
        t0 = path[0][2]
        for i, (inst, pin, tm, cell) in enumerate(path):
            ax.bar(i, tm - (path[i - 1][2] if i else 0), bottom=(path[i - 1][2] if i else 0), color=COL[d], width=0.8)
        ax.step(range(len(path)), [p[2] for p in path], where='mid', color='k', lw=0.5)
        start, end = qnet(path[0][0]), path[-1][0]
        endq = qnet(end)
        ax.set_ylabel('arrival (ns)')
        ax.set_title(f"{NAME[d]}, target 1.2 ns, seed 1:  launch {path[0][0]} (Q = {start})  →  capture {end} (Q = {endq})\n"
                     f"data arrival {path[-1][2]:.3f} ns = clock latency {t0:.3f} ns + data path {path[-1][2] - t0:.3f} ns;  setup slack {slack:+.4f} ns",
                     fontsize=6.3, loc='left')
        ax.set_xticks(range(len(path))); ax.set_xticklabels([c.replace('_X', ' x') for *_, c in path], rotation=90, fontsize=5)
        info[d] = dict(start=path[0][0], start_q=start, end=end, end_q=endq, arrival=path[-1][2], clock_latency=t0, slack=slack, cells=len(path) - 2)
    fig.subplots_adjust(hspace=1.05)
    save(fig, 'physical', 'fig_critpath')
    (PAPER / 'data' / 'critpath.json').write_text(json.dumps(info, indent=1))


def layout_images():
    """OpenROAD GUI renderer, headless; the same um/pixel for both designs (equal scale)."""
    for d in ('pams_jqr', 'base_jq'):
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', RUN=str(MV / f'final/runs/pnr_{d}_T1.2_s1'),
                   IMG=str(FIG / 'physical' / f'layout_{d}.png'), RES='0.1')
        subprocess.run(['bash', str(MV.parents[0] / 'orfs_run.sh'), 'openroad', '-no_init', '-exit', str(PAPER / 'scripts' / 'layout_image.tcl')],
                       env=env, check=True, capture_output=True, cwd=str(MV.parents[0]))
        from PIL import Image
        im = Image.open(env['IMG']); print('layout', d, im.size)
        im.resize((im.size[0] // 2, im.size[1] // 2), Image.LANCZOS).save(FIG / 'physical' / f'layout_{d}_half.png')   # 0.2 um/px, equal scale


# ------------------------------------------------------------------------------------------------ gates
def dot_hpc2():
    """the real mapped hpc2 module (Yosys JSON of competitors/runs/syn_pams_jqr_p0) as a Graphviz netlist"""
    J = json.loads((MV / 'competitors/runs/syn_pams_jqr_p0/mapped.json').read_text()); m = J['modules']['hpc2']
    netname = {}
    for n, v in m['netnames'].items():
        for i, b in enumerate(v['bits']):
            if isinstance(b, int) and (b not in netname or not n.startswith('$')): netname[b] = n if len(v['bits']) == 1 else f'{n}[{i}]'
    drv, sinks = {}, {}
    for p, v in m['ports'].items():
        for i, b in enumerate(v['bits']):
            (drv if v['direction'] == 'input' else sinks).setdefault(b, []).append(f'P_{p}{i}')
    OUTP = {'Z', 'ZN', 'Q', 'QN'}
    for cn, c in m['cells'].items():
        for p, bs in c['connections'].items():
            for b in bs:
                if not isinstance(b, int): continue
                (drv if p in OUTP else sinks).setdefault(b, []).append((cn, p))
    # final review: wider spacing with spline routing keeps every edge off every node (ortho merged edges into shared corridors)
    L = ['digraph hpc2 {', 'rankdir=LR; splines=true; nodesep=0.35; ranksep=0.7; node [fontname="Helvetica", fontsize=9, shape=box, style="rounded,filled", fillcolor="#f2f2f2", height=0.25];',
         'edge [arrowsize=0.4, penwidth=0.6];']
    for p, v in m['ports'].items():
        if p == 'clk': continue
        for i in range(len(v['bits'])):
            L.append(f'P_{p}{i} [label="{p}[{i}]", shape=ellipse, fillcolor="{"#d6eaf8" if v["direction"] == "input" else "#fdebd0"}"];')
    for cn, c in m['cells'].items():
        t = c['type']; q = c['connections'].get('Q', [None])[0]
        lab = f'{t}\\n{netname.get(q, "")}' if t.startswith('DFF') else t
        col = '#d5f5e3' if t.startswith('DFF') else '#fcf3cf'
        L.append(f'"{cn}" [label="{lab}", fillcolor="{col}"];')
    for b, ds in drv.items():
        for s in sinks.get(b, []):
            for dd in ds:
                if s and isinstance(s, tuple) and s[1] == 'CK': continue
                src = dd if isinstance(dd, str) else f'"{dd[0]}"'; dst = s if isinstance(s, str) else f'"{s[0]}"'
                if src == 'P_clk0': continue
                L.append(f'{src} -> {dst};')
    L.append('}')
    (FIG / 'gates').mkdir(parents=True, exist_ok=True)
    f = FIG / 'gates' / 'hpc2_mapped.dot'; f.write_text('\n'.join(L))
    subprocess.run(['dot', '-Tpdf', str(f), '-o', str(FIG / 'gates' / 'hpc2_mapped.pdf')], check=True)
    types = {}
    for c in m['cells'].values(): types[c['type']] = types.get(c['type'], 0) + 1
    (PAPER / 'data' / 'hpc2_mapped_cells.json').write_text(json.dumps(types, indent=1)); print('hpc2 mapped cells', types)


def dot_slice(gadgets=('ug111', 'ug128', 'ug134'), depth=3):
    """top-level mapped cells around three real gadget instances of bit 1 (CSA majority T_1, comparator lt_2,
    carry c_2): every cell in the fan-in of their a/b pins up to `depth` levels (stopping at flip-flops / ports)."""
    J = json.loads((MV / 'competitors/runs/syn_pams_jqr_p0/mapped.json').read_text()); m = J['modules']['pams_jqr_lane']
    netname = {}
    for n, v in m['netnames'].items():
        for i, b in enumerate(v['bits']):
            if isinstance(b, int) and (b not in netname or (netname[b].startswith('$') and not n.startswith('$'))):
                netname[b] = n if len(v['bits']) == 1 else f'{n}[{i}]'
    OUTP = {'Z', 'ZN', 'Q', 'QN', 'c'}
    drv = {}
    for cn, c in m['cells'].items():
        for p, bs in c['connections'].items():
            if p in OUTP or (c['type'] == 'hpc2' and p == 'c'):
                for b in bs:
                    if isinstance(b, int): drv[b] = (cn, p)
    keep, edges, frontier = set(gadgets), set(), [(g, 0) for g in gadgets]
    while frontier:
        cn, lvl = frontier.pop(); c = m['cells'][cn]
        ins = [(p, b) for p, bs in c['connections'].items() for b in bs if isinstance(b, int) and p not in OUTP and p not in ('CK', 'clk', 'r')]
        for p, b in ins:
            src = drv.get(b)
            if src is None: edges.add((f'IN:{netname.get(b, b)}', cn, p)); continue
            edges.add((src[0], cn, p))
            if src[0] not in keep:
                keep.add(src[0])
                if lvl + 1 < depth and not m['cells'][src[0]]['type'].startswith('DFF') and m['cells'][src[0]]['type'] != 'hpc2':
                    frontier.append((src[0], lvl + 1))
    # final review: pin names are encoded by line style instead of edge labels, which piled up where edges converge
    L = ['digraph slice {', 'rankdir=LR; splines=true; nodesep=0.35; ranksep=0.7; node [fontname="Helvetica", fontsize=8, shape=box, style="rounded,filled", height=0.22];',
         'edge [arrowsize=0.35, penwidth=0.5, fontsize=6, fontname="Helvetica"];']
    for cn in keep:
        c = m['cells'][cn]; t = c['type']
        if t == 'hpc2':
            L.append(f'"{cn}" [label="HPC2 instance {cn}\\n(a[2:0], b[2:0], r[2:0] -> c[2:0])", fillcolor="#aed6f1", shape=box3d, height=0.6];')
        elif t.startswith('DFF'):
            q = netname.get(c['connections']['Q'][0], '') if 'Q' in c['connections'] else ''
            L.append(f'"{cn}" [label="{t}\\nQ = {q}", fillcolor="#d5f5e3"];')
        else:
            z = [b for p, bs in c['connections'].items() if p in OUTP for b in bs]
            nn = netname.get(z[0], '') if z else ''
            nn = '(ABC-internal net)' if nn.startswith('$') else nn
            L.append(f'"{cn}" [label="{t}\\n{nn}", fillcolor="#fcf3cf"];')
    sty = lambda p: 'dashed' if p.lower() == 'b' else 'solid'        # gadget pin a / cell pin A solid, b / B dashed
    for s, dname, p in sorted(edges):
        if s.startswith('IN:'):
            L.append(f'"{s}" [label="{s[3:]}", shape=ellipse, fillcolor="#eeeeee"];')
        assert p.lower() in ('a', 'b'), p
        L.append(f'"{s}" -> "{dname}" [style={sty(p)}];')
    L.append('}')
    f = FIG / 'gates' / 'slice_bit1.dot'; f.write_text('\n'.join(L))
    subprocess.run(['dot', '-Tpdf', str(f), '-o', str(FIG / 'gates' / 'slice_bit1.pdf')], check=True)
    print('slice cells', len(keep))


# ------------------------------------------------------------------------------------------------ math
def fig_math():
    """F_14 on both sides of the d = 4, c = 0 interval (it wraps through q-1 -> 0): Z versus x for j = 0, 1, 2 and Theta."""
    sys.path.insert(0, str(MV / 'models')); import pams as P
    Q, K, d, c = 3329, 14, 4, 0
    F = lambda v: (v << K) // Q; lo = P.low_formula(c, d, K); hi = P.low_formula(c + 1, d, K); th = (hi - lo - 1) % (1 << K)
    a = P.starts(d)
    xs = list(range(a[c] - 6, a[c] + 4)) + list(range(a[c + 1] - 4, a[c + 1] + 6))
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 2.1), sharey=False)
    for ax, seg in zip(axs, (list(range(a[c] - 6, a[c] + 5)), list(range(a[c + 1] - 5, a[c + 1] + 6)))):
        for j, mk in zip((0, 1, 2), ('o', 's', '^')):
            zs = [((F(x % Q) - j - lo + 2) % (1 << K)) for x in seg]
            zz = [z if z < 8192 else z - (1 << K) for z in zs]
            ax.plot(seg, zz, mk, ms=3, mfc='none' if j else None, label=f'j = {j}', color=['#1f5fa8', '#2e8b57', '#b8860b'][j])
        ax.axhline(th, color='#c0392b', lw=0.8); ax.axhline(0, color='0.5', lw=0.5); ax.axhline(th - 1, color='#c0392b', lw=0.4, ls=':')
        for x in seg:
            if P.compress(x % Q, d) == c: ax.axvspan(x - 0.5, x + 0.5, color='#d6eaf8', lw=0, zorder=0)
        ax.set_xlabel('x (canonical value)')
    axs[0].set_ylabel('Z (signed representative mod 2¹⁴)'); axs[0].set_ylim(-32, 28); axs[1].set_ylim(th - 30, th + 30)
    axs[0].text(a[c] + 0.7, -27, 'members: 0 ≤ Z ≤ Θ−1', fontsize=6)
    axs[0].text(a[c] - 6.2, 20, 'non-members: shown as Z < 0,\ni.e. Z ≥ 2¹⁴ − 32 (wrapped)', fontsize=6)
    axs[1].text(a[c + 1] + 0.6, th - 26, 'non-members: Z ≥ Θ+1', fontsize=6)
    axs[0].set_title(f'interval start a_0 = {a[c]} (x = 3224 → 3225)', fontsize=7)
    axs[1].set_title(f'interval end a_1 = {a[c + 1]} (x = 104 → 105), Θ_0 = {th}', fontsize=7)
    axs[0].text(a[c] + 3.5, 2, 'Z = 0', color='0.4', fontsize=6)
    axs[1].legend(frameon=False, fontsize=6, loc='upper left')
    save(fig, 'mathematics', 'fig_switch_boundaries')
    (PAPER / 'data' / 'math_fig.json').write_text(json.dumps(dict(d=d, c=c, a_c=a[c], a_c1=a[c + 1], Low=lo, Low_next=hi, Theta=th)))


if __name__ == '__main__':
    parts = sys.argv[1:] or ['results', 'physical', 'gates', 'math']
    (PAPER / 'data').mkdir(exist_ok=True)
    if 'results' in parts:
        for f in (fig_area, fig_die, fig_timing, fig_gadgets, fig_random, fig_adp, fig_routing): f()
    if 'physical' in parts: fig_placement(); fig_critpath()
    if 'layout' in parts: layout_images()
    if 'gates' in parts: dot_hpc2(); dot_slice()
    if 'math' in parts: fig_math()
