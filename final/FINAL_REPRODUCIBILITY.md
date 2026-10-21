# Reproducing the final results

All commands run in WSL2 Ubuntu 24.04.4 LTS (Python 3.12.3, gcc 13.3.0), as an ordinary user, from `~/lwe_agent_handoff/phase2/masked_verification` unless stated. Python is always run with `-I`. Times are for a 16-thread machine.

## 1. Tools and versions
| tool | version / source | used for |
|---|---|---|
| Python | 3.12 (system) | generators, checks, harnesses |
| Yosys | 0.33 (git sha1 2584903a060), system package | synthesis (flow B / C), gate-level export |
| Icarus Verilog | 12.0 (stable) | RTL and gate-level simulation |
| OpenSTA | 3.1.0, `~/.local/bin/sta` | synthesis STA |
| OpenROAD | ORFS image 26Q3-705-gecb3cfdeb, unpacked at `phase2/ext/tools/orfs_rootfs`, run through `phase2/orfs_run.sh` (version string reported as "unknown" by the binary) | P&R, RCX |
| Nangate45 | `current/lib/NangateOpenCellLibrary_typical.lib` (synthesis); ORFS platform `nangate45` (P&R: LEF, liberty, `rcx_patterns.rules`) | library |
| SILVER | built by `validation/tools/build_silver.sh` (Sylvan 5e9da97) into `phase2/ext/tools/sca/` | gadget proof (Phase XII) |
| PROLEAD | v3.1.0 (commit 91338e0), built by `validation/tools/build_prolead.sh` into `phase2/ext/tools/sca/prolead-3.1.0`, user-local sysroot (`validation/tools/deps.sh`) | leakage detection |

**External, not in the repository:**
- `phase2/bfbench.py`: the synthesis and STA flow used by all benchmarks;
- `phase2/orfs_run.sh`, `phase2/pnr/prep_netlist.sh`, the ORFS root filesystem;
- `current/lib/` (Nangate45 liberty);
- the SILVER and PROLEAD builds and their sysroot.

Their paths are listed in PUBLICATION_MANIFEST.md. The P&R script itself (`final/tools/pnr_final.tcl`) is in the repository.

## 2. Mathematics (exhaustive)
```
cd validation/math && gcc -O3 -fopenmp lemma.c -o lemma && for K in 14 13 24; do ./lemma $K; done   # integer-error lemma over all 3329^3 triples (see run_lemma.sh)
python3 -I validation/math/audit.py                                     # checks A-G -> audit_results.json
python3 -I -c "import sys; sys.path.insert(0,'competitors/models'); import cgen; cgen.check_offsets(); cgen.check_bos_windows(); print('ok')"
```

## 3. RTL generation (deterministic; identity checks included)
```
cd competitors/models && python3 -I cgen.py base pams base_x pams_x pams_jqr base_jq pams_jpr base_jp
# prints "identical to rtl/base.v / rtl/pams.v: True" for the frozen re-emission and the regression designs
sha256sum ../rtl/pams_jqr.v ../rtl/base_jq.v      # must equal PUBLICATION_MANIFEST.md
```

## 4. Functional verification
```
bash final/models/fsim_all.sh          # systematic (39,112 coefficients): RTL of pams_jqr, base_jq, pams, base; gate-level syn p0 + P&R input
bash final/models/fsim_routed.sh pnr_pams_jqr_T2.0_s1 pnr_base_jq_T2.0_s1    # routed netlists: systematic + random (frozen sim.py)
python3 -I competitors/models/cbench.py pams_jqr base_jq      # 6,001-coefficient RTL check + 5 mappings x 1,500 gate-level (+ synthesis)
```

## 5. Security checks
```
python3 -I final/models/gadget_identity.py      # gadget sha256 versus the SILVER-verified variants
python3 -I final/models/control_final.py        # cvalid / dvalid data independence
bash final/tools/routed_check_final.sh          # compcheck D/R/P/O/G on every routed run
python3 -I validation/silver/run_silver.py      # (Phase XII) SILVER on the gadget variants + negative controls
bash final/prolead/campaign_final.sh            # focused lane PROLEAD on pams_jqr (~1 h): self-test, order 1, NC, order 2
bash final/prolead/campaign_final2.sh; bash final/prolead/campaign_final3.sh    # confirmations of the two flagged maxima (4.2 M simulations each)
python3 -I final/prolead/lane_table.py          # probing-set counts and null maxima -> final/prolead/lane_table.json
```

## 6. Synthesis (Phase XIII matched benchmark, 5 mappings)
```
cd competitors/models && python3 -I cbench.py pams_jqr base_jq pams_jpr base_jp pams base   # -> competitors/runs/cbench.json
python3 -I tables.py > ../runs/tables.md
python3 -I final/models/pubpaths.py base_jq offr enr shr offrq enrq shrq offp enp shp en2 mh0 ml0 fq0 y0   # stage timing
python3 -I final/models/pubpaths.py pams_jqr qcr qnr e0r c0r lowrq thrq lowp thp th2 mh0 ml0 s0p y0
```

## 7. Place and route (Phase XIV seeded campaign)
- **Inputs:** `competitors/runs/pnrsyn_{pams_jqr,base_jq}/mapped.v`, the flow-C netlists from `competitors/models/pnr_c.sh <d> synth-only`. Their hashes are in PUBLICATION_MANIFEST.md.
- **Commands:**
  ```
  bash final/tools/campaign1.sh             # seeds 1-7 x targets 2.0 / 1.2 / 1.1 ns x 2 designs, UTIL 50, DENS 0.6, 3 concurrent
  bash final/tools/watchdog.sh &            # 90-min wall-clock limit per run (TIMEOUT.txt in the run directory)
  python3 -I final/models/pnr_stats.py      # -> final/runs/pnr_stats.json + tables
  python3 -I final/models/placediff.py final/runs/pnr_pams_jqr_T2.0_s1 final/runs/pnr_pams_jqr_T2.0_s2   # seed independence
  ```
- **Determinism:** the same seed reproduces a run bit-identically. Seed 1 at 2.0 ns reproduces the Phase XIII u50 run's `final.def` exactly (sha256 7aaa0d45…).

## 8. Final tables
`final/runs/pnr_stats.json`, `competitors/runs/cbench.json` and `final/runs/*.json` are the sources of every number in FINAL_BENCHMARKS.md and FINAL_RESEARCH_VERDICT.md.
