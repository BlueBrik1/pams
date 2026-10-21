#!/usr/bin/env python3
"""Phase II butterfly bench: ML-KEM (q=3329) CT/GS butterfly units.

Interface of every candidate (phase2/rtl/<name>.v, or gen:<arch>[-k=v..] from gen2.py):
  module dut(input clk, rst_n, gs, input [11:0] u, v, w, output [11:0] uo, vo);
  // latency: L   (cycles from inputs to outputs; one butterfly per cycle; outputs canonical 0..q-1)
CT (gs=0):  uo = u + v*w,  vo = u - v*w            (mod q)   -- ML-KEM NTT layer, FIPS 203 Alg. 9
GS (gs=1):  uo = (u+v)/2,  vo = (u-v)*w/2          (mod q)   -- Adams Bridge INTT with per-layer 1/2
Inputs canonical (0..q-1). The reference model below is independent integer Python.

Flow per design: streaming RTL sim (corners + random, both modes, mode switches with flush, reset
mid-stream) -> Yosys/ABC (identical script to Phase I) under 5 neutral perturbations -> gate-level sim
of every mapping -> OpenSTA (Phase I SDC + min clock period). Rows appended to phase2/results.csv.
usage: python3 bfbench.py --designs abr_bf gen:... [--jobs 3] [--tag ID] [--perturb 5]
"""
from __future__ import annotations
import argparse, csv, datetime, hashlib, json, random, re, statistics, subprocess, sys, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parent
LIB = ROOT.parent/'current'/'lib'/'NangateOpenCellLibrary_typical.lib'
STA = str(Path.home()/'.local/bin/sta')
RUNS, CSV = ROOT/'runs', ROOT/'results.csv'
Q, INV2 = 3329, 1665
BENIGN = (r"unsupported expression 'SE\*SI\+D\*!SE'", r'multi-output gates', r'network is combinational',
          r'Replacing memory .* with list of registers')
FIELDS = ('tag flow twiddle ts design family status reason latency area area_min area_max ff cells tclk tclk_min tclk_max '
          'worst in2reg reg2reg reg2out in2out crit_start crit_end rtl_vectors gate_vectors unexpected_warnings '
          'maps src_sha256 lib_sha256 tools seconds').split()

def sh(cmd, log=None, timeout=900, cwd=None):
    p = subprocess.run([str(c) for c in cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout, cwd=cwd)
    if log: Path(log).write_text(p.stdout)
    if p.returncode: raise RuntimeError(f'{Path(str(cmd[0])).name} failed rc={p.returncode}; see {log}\n' + p.stdout[-800:])
    return p.stdout

def sha(paths):
    h = hashlib.sha256()
    for f in paths: h.update(Path(f).name.encode()); h.update(Path(f).read_bytes())
    return h.hexdigest()

ENC = {'plain': lambda w: w, 'mont16': lambda w: w * 65536 % Q, 'k2red': lambda w: w * pow(169, -1, Q) % Q}
def ref(gs, u, v, w):
    if gs: return ((u + v) * INV2) % Q, ((u - v) * w * INV2) % Q
    t = v * w; return (u + t) % Q, (u - t) % Q

def sources(design, work):
    if design.startswith('gen:'):
        sys.path.insert(0, str(ROOT)); import gen2
        f = gen2.build(design, work); txt = f.read_text()
    else:
        f = ROOT/'rtl'/f'{design}.v'; txt = f.read_text()
    deps = [ (ROOT/'rtl'/d).resolve() for d in re.findall(r'//\s*requires:\s*(\S+)', txt)]
    lat = int(re.search(r'//\s*latency:\s*(\d+)', txt).group(1))
    tw = re.search(r'//\s*twiddle:\s*(\S+)', txt); tw = tw.group(1) if tw else 'plain'
    fam = re.search(r'//\s*family:\s*(\S+)', txt).group(1)
    return deps + [f], lat, fam, tw

def stimulus(seed, n_rand):
    """Cycle list of (rst_n, gs, u, v, w, check_flag) ; expected outputs computed with latency L later."""
    r = random.Random(seed); cyc = [(0, 0, 0, 0, 0)] * 3
    edge = [0, 1, 2, Q//2, Q//2+1, Q-2, Q-1]
    for gs in (0, 1, 0, 1):
        for u in edge:
            for v in edge:
                for w in (0, 1, 17, Q-1, 1729, 2285):    # 17 = root of unity, 1729/2285 typical zetas
                    cyc.append((1, gs, u, v, w))
        cyc += [(1, gs, r.randrange(Q), r.randrange(Q), r.randrange(Q)) for _ in range(n_rand)]
    # reset in the middle of a stream
    cyc += [(1, 0, r.randrange(Q), r.randrange(Q), r.randrange(Q)) for _ in range(5)] + [(0, 0, 1, 2, 3)] * 2
    cyc += [(1, 1, r.randrange(Q), r.randrange(Q), r.randrange(Q)) for _ in range(200)]
    return cyc

def testbench(vecfile, n, L):
    return f'''`timescale 1ns/1ps
module tb;
reg clk=0; always #5 clk=~clk;
reg rst_n=0, gs=0; reg [11:0] u=0, v=0, w=0; wire [11:0] uo, vo;
reg [63:0] mem [0:{n-1}]; reg [63:0] e; integer k, bad=0, checked=0;
dut uut(.clk(clk),.rst_n(rst_n),.gs(gs),.u(u),.v(v),.w(w),.uo(uo),.vo(vo));
initial begin
  $readmemh("{vecfile}", mem);
  for (k=0; k<{n}; k=k+1) begin
    @(negedge clk);
    e = mem[k];             // {{chk, exp_uo, exp_vo, rst_n, gs, u, v, w}}
    if (e[62] && ({{uo,vo}} !== e[61:38])) begin bad=bad+1; if (bad<5) $display("MISMATCH k=%0d got %0d %0d exp %0d %0d", k, uo, vo, e[61:50], e[49:38]); end
    if (e[62]) checked=checked+1;
    rst_n=e[37]; gs=e[36]; u=e[35:24]; v=e[23:12]; w=e[11:0];
  end
  if (bad) begin $display("FAIL mismatches=%0d", bad); $fatal(1); end
  $display("PASS vectors=%0d", checked); $finish;
end
endmodule
'''

def write_vectors(path, seed, n_rand, L, tw='plain'):
    cyc = stimulus(seed, n_rand); lines = []
    cyc = cyc + [(1, cyc[-1][1], 0, 0, 0)] * (L + 1)          # drain with the last mode held
    for k in range(len(cyc)):
        # at negedge k (before applying cyc[k]) outputs reflect the inputs applied at negedge k-L
        src = k - max(L, 1)
        chk = 0; eu = ev = 0
        # checked only if src is out of reset, no reset since, and the mode was constant over the
        # pipeline window (the engine changes mode only on a drained pipeline)
        if 0 <= src and all(cyc[j][0] and cyc[j][1] == cyc[src][1] for j in range(src, k)):
            chk = 1; eu, ev = ref(*cyc[src][1:])
        rst, gs, u, v, w = cyc[k]
        w = ENC[tw](w)              # twiddle encoding of the design (stored that way in the ROM)
        val = (chk << 62) | (eu << 50) | (ev << 38) | (rst << 37) | (gs << 36) | (u << 24) | (v << 12) | w
        lines.append(f'{val:016x}')
    path.write_text('\n'.join(lines) + '\n')
    return len(lines)

def simulate(files, work, label, L, seeds, n_rand, tw='plain'):
    total = 0
    for s in seeds:
        vec = work/f'{label}_vec{s}.hex'; n = write_vectors(vec, s, n_rand, L, tw)
        tb = work/f'{label}_tb{s}.v'; tb.write_text(testbench(vec, n, L))
        exe = work/f'{label}_{s}.vvp'
        sh(['iverilog', '-g2012', '-s', 'tb', '-o', exe, *files, tb], work/f'{label}_compile{s}.log')
        out = sh(['vvp', '-n', exe], work/f'{label}_sim{s}.log')
        total += int(re.search(r'PASS vectors=(\d+)', out).group(1)); exe.unlink()
    return total

FLOW = 'A'      # A: Phase I script (abc -liberty). B: + -constr (BUF_X1 drive, 5 fF load) -D 500: buffer/upsize/dnsize
def synth(files, work, top='dut'):
    v = work/'mapped.v'
    (work/'abc.constr').write_text('set_driving_cell BUF_X1\nset_load 5.0\n')
    # flow C = flow B mapped onto the library minus the OpenROAD-flow-scripts nangate45 DONT_USE cells (P&R inputs;
    # AOI211_X1 / OAI211_X1 have pin-access problems). Yosys 0.33 has no -dont_use, hence a pruned liberty copy.
    ml = Path(__file__).resolve().parent/'pnr'/'NangateOpenCellLibrary_typical_dontuse.lib' if FLOW == 'C' else LIB
    abc = f'abc -liberty {ml}' if FLOW == 'A' else f"abc -liberty {ml} -constr {work/'abc.constr'} -D 500"
    inc = ' '.join(sorted({f'-I{Path(f).resolve().parent}' for f in files}))   # `include files next to sources
    script = f'''read_verilog -sv {inc} {' '.join(map(str, files))}
synth -top {top} -flatten -noabc
dfflibmap -liberty {ml}
{abc}
clean
stat -liberty {LIB}
write_verilog -noattr -noexpr {v}
write_json {work/'mapped.json'}
'''
    (work/'synth.ys').write_text(script)
    out = sh(['yosys', '-Q', '-T', '-s', work/'synth.ys'], work/'yosys.log', timeout=3600)
    area = float(re.findall(r'Chip area for (?:top )?module.*?:\s*([0-9.]+)', out)[-1])
    warns = [l for l in out.splitlines() if re.search('warning', l, re.I) and not any(re.search(b, l) for b in BENIGN)]
    types = [c['type'] for c in json.loads((work/'mapped.json').read_text())['modules'][top]['cells'].values()]
    gl = work/'gate.v'
    sh(['yosys', '-q', '-p', f'read_liberty -ignore_miss_func {LIB}; read_verilog {v}; hierarchy -top {top}; flatten; opt_clean; write_verilog -noattr {gl}'], work/'gate_export.log')
    return dict(area=area, ff=sum('DFF' in t for t in types), cells=len(types), unexpected_warnings=len(warns)), v, gl

GROUPS = {'in2reg': '-from [all_inputs] -to [all_registers -data_pins]',
          'reg2reg': '-from [all_registers -clock_pins] -to [all_registers -data_pins]',
          'reg2out': '-from [all_registers -clock_pins] -to [all_outputs]',
          'in2out': '-from [all_inputs] -to [all_outputs]'}

def sta(mapped, work, top='dut'):
    tcl = f'''read_liberty {{{LIB}}}
read_verilog {{{mapped}}}
link_design {top}
create_clock -name benchclk -period 1000 [get_ports clk]
set_input_delay 0 -clock benchclk [delete_from_list [all_inputs] [get_ports clk]]
set_output_delay 0 -clock benchclk [all_outputs]
set_input_transition 0.05 [delete_from_list [all_inputs] [get_ports clk]]
set_load 0.005 [all_outputs]
puts "BEGIN_setup"
check_setup -verbose
puts "END_setup"
puts "BEGIN_all"
report_checks -path_delay max -digits 6
puts "END_all"
'''
    for g, a in GROUPS.items(): tcl += f'puts "BEGIN_{g}"\nreport_checks {a} -path_delay max -digits 6\nputs "END_{g}"\n'
    (work/'sta.tcl').write_text(tcl)
    out = sh([STA, '-no_init', '-no_splash', '-exit', work/'sta.tcl'], work/'sta.log')
    if re.search(r'^\s*(Error|ERROR)', out, re.M): raise RuntimeError('STA error')
    sec = lambda g: re.search(rf'BEGIN_{g}\n(.*?)END_{g}', out, re.S).group(1)
    arr = lambda t: [float(x) for x in re.findall(r'^\s*([\d.]+)\s+data arrival time', t, re.M)]
    r = {g: (max(arr(sec(g))) if arr(sec(g)) else 0.0) for g in GROUPS}
    # min period: data paths only (the default worst-slack path can be an async-reset recovery check)
    sl = {g: min([float(s) for s in re.findall(r'^\s*(-?[\d.]+)\s+slack', sec(g), re.M)] or [1e9]) for g in GROUPS}
    cg = min(sl, key=sl.get); slack = sl[cg]
    a = sec(cg)
    r.update(worst=max(r.values()), tclk=round(1000 - slack, 6), crit_group=cg,          # min period incl. setup, I/O at clock edge
             crit_start=re.search(r'Startpoint:\s*(\S+)', a).group(1), crit_end=re.search(r'Endpoint:\s*(\S+)', a).group(1),
             unconstrained=sec('setup').strip()[:200])
    return r

def run_one(design, tag, tools, perturb, n_rand):
    work = RUNS/(design.replace(':', '_') + ('' if FLOW == 'A' else '__' + FLOW)); work.mkdir(parents=True, exist_ok=True)
    row = dict.fromkeys(FIELDS, ''); t0 = time.monotonic()
    row.update(tag=tag, flow=FLOW, ts=datetime.datetime.now().isoformat(timespec='seconds'), design=design, status='FAIL', tools=tools)
    try:
        files, L, fam, tw = sources(design, work)
        row.update(family=fam, latency=L, twiddle=tw, src_sha256=sha(files + [Path(__file__)]), lib_sha256=sha([LIB]))
        row['rtl_vectors'] = simulate(files, work, 'rtl', L, (1, 2), n_rand, tw)
        maps, gv, warn, unc = [], 0, 0, ''
        for k in range(perturb):
            pw = work/f'p{k}'; pw.mkdir(exist_ok=True)
            pad = pw/'pad.v'; pad.write_text(''.join(f'module __pad{i}(input [3:0] x, output [3:0] y); assign y = x + {i}; endmodule\n' for i in range(3*k)))
            m, mapped, gl = synth(([pad] if k else []) + files, pw)
            gv += simulate([gl], pw, 'gate', L, (1,) if k else (1, 2), n_rand if k == 0 else n_rand // 4, tw)
            m.update(sta(mapped, pw)); maps.append(m); warn += m['unexpected_warnings']; unc = unc or m['unconstrained']
        med = lambda key: statistics.median(m[key] for m in maps)
        for key in ('area', 'ff', 'cells', 'tclk', 'worst', 'in2reg', 'reg2reg', 'reg2out', 'in2out'): row[key] = round(med(key), 6)
        row.update(area_min=min(m['area'] for m in maps), area_max=max(m['area'] for m in maps),
                   tclk_min=min(m['tclk'] for m in maps), tclk_max=max(m['tclk'] for m in maps),
                   crit_start=maps[0]['crit_start'], crit_end=maps[0]['crit_end'], gate_vectors=gv,
                   unexpected_warnings=warn, maps=len(maps))
        row['status'] = 'PASS' if not warn and not unc else 'SUSPECT'
        if row['status'] != 'PASS': row['reason'] = f'warnings={warn} setup="{unc}"'
    except Exception as ex:
        row['reason'] = str(ex).splitlines()[0][:300]
    row['seconds'] = round(time.monotonic() - t0, 1)
    (work/'row.json').write_text(json.dumps({**row, 'per_map': locals().get('maps', [])}, indent=1))
    return row

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--designs', nargs='+', required=True)
    p.add_argument('--jobs', type=int, default=3); p.add_argument('--tag', default='')
    p.add_argument('--perturb', type=int, default=5); p.add_argument('--rand', type=int, default=20000)
    p.add_argument('--flow', choices=['A', 'B', 'C'], default='A')
    a = p.parse_args(); assert 1 <= a.jobs <= 3
    global FLOW; FLOW = a.flow
    tools = f"{sh(['yosys','-V']).strip()}; {sh(['iverilog','-V']).splitlines()[0]}; OpenSTA {sh([STA,'-version']).strip()}"
    with ThreadPoolExecutor(a.jobs) as pool:
        rows = list(pool.map(lambda d: run_one(d, a.tag, tools, a.perturb, a.rand), a.designs))
    new = not CSV.exists()
    with CSV.open('a', newline='') as f:
        w = csv.DictWriter(f, FIELDS); new and w.writeheader(); w.writerows(rows)
    for r in rows:
        print(f"{r['status']:7} {r['design']:38} L={r['latency']} area={r['area']} [{r['area_min']}..{r['area_max']}] ff={r['ff']} "
              f"tclk={r['tclk']} [{r['tclk_min']}..{r['tclk_max']}] i2r={r['in2reg']} r2r={r['reg2reg']} r2o={r['reg2out']} "
              f"vec={r['rtl_vectors']}/{r['gate_vectors']} {r['reason']}")

if __name__ == '__main__':
    main()
