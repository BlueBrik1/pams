# Publication manifest (PAMS research freeze)

**Freeze:**
- Git repository: `phase2/masked_verification/` (remote `origin` = https://github.com/BlueBrik1/res.git, not pushed by this phase).
- **Freeze tag: `pams-publication-freeze-v1`**.
- Content commit: see §6; the tag points to the commit that records it.

## 1. Canonical circuits
| role | path | SHA-256 |
|---|---|---|
| **PAMS (publication)** | `final/rtl/pams_jqr.v` | `804fd73a263baacb371033015171519213d84cfa817dee9ba6ae2b3760ba0e7f` |
| **strongest baseline** | `final/rtl/base_jq.v` | `e573286a2b1b4ead019699538be21b454bab359fdaeb4f62e273d137458f6533` |
| copies of the above (Phase XIII origin, identical) | `competitors/rtl/pams_jqr.v`, `competitors/rtl/base_jq.v` | same |
| P&R input netlist, PAMS (flow C) | `final/netlists/pnr_in_pams_jqr_mapped.v` (= `competitors/runs/pnrsyn_pams_jqr/mapped.v`) | `e918ebcf1f671913bde510dd6a92df27a5bb0c88dcfe7216de6aef0bee7632f7` |
| P&R input netlist, baseline (flow C) | `final/netlists/pnr_in_base_jq_mapped.v` (= `competitors/runs/pnrsyn_base_jq/mapped.v`) | `5e2ec0cafa71e9f32f04750a22370df284fc2a1ba56f1f939b57016d5158dc65` |
| historical PAMS (Phase XI, frozen) | `rtl/pams.v` | `fe8c346a216bb3bc8d23885bfd6e3288ee528ea15c3ace9f47b2050a42aa5038` |
| historical baseline (Phase XI, frozen) | `rtl/base.v` | `4401fd6df1e39de94db9693a956ffa9b467871b81f5bfa0da8278156cc000d0c` |

**Reference routed implementations** (seed 1, 2.0 ns, utilization 50 %; not committed because of size, regenerable bit-identically):

| file | SHA-256 |
|---|---|
| `final/runs/pnr_pams_jqr_T2.0_s1/final.def` | `7aaa0d45e2a123d22746e88fd1b14ec411ed3d1a0943a20b42f87489c812119f` |
| `final/runs/pnr_pams_jqr_T2.0_s1/final.v` | `ea37ad6dce04c420a81b371b70bebbe41e21f377b5bc7a3d96ff1fca959e745d` |
| `final/runs/pnr_base_jq_T2.0_s1/final.def` | `fc68817d4a2221419c5ab6c4cde42474ff09fdbe3de3d78cc75e7c75ce914a23` |
| `final/runs/pnr_base_jq_T2.0_s1/final.v` | `fa12848de734ce654b69c410dbfa78b8de01a58cb52e677c9cbd77c439f929b9` |

## 2. Final reports (all refer to the circuits above)
FINAL_RESEARCH_VERDICT.md (authoritative), FINAL_BENCHMARKS.md, FINAL_SECURITY_STATUS.md, FINAL_NOVELTY_STATEMENT.md, FINAL_MATHEMATICAL_SPECIFICATION.md, FINAL_DESIGN_SPECIFICATION.md, FINAL_REPRODUCIBILITY.md, PAPER_EVIDENCE_INDEX.md, this file.

## 3. Evidence files (committed)
| evidence | files |
|---|---|
| seeded P&R campaign | `final/runs/pnr_stats.json`, `final/runs/pnr_stats.md`, `final/runs/pnr_*_T*_s*/{metrics.txt,timing.rpt,openroad.log,power.rpt,drc.rpt,TIMEOUT.txt}`, `final/runs/campaign1.log`, `final/runs/watchdog.log` |
| functional verification | `final/runs/fsim_*.log`, `final/runs/fsim_routed.log`, `final/runs/pnr_*_T2.0_s1/{fsim_routed,sim_routed}.log` |
| security checks | `final/runs/gadget_identity.json`, `final/runs/control_final.json`, `final/runs/routed_check_final.jsonl` |
| focused PROLEAD | `final/prolead/lane/*/{config.json,prolead.log,result.json}`, `final/prolead/lane_table.json`, `final/prolead/campaign_final*.log` |
| fairness timing analysis | `final/runs/pubpaths_{base_jq,pams_jqr}.txt` |
| figure data | `final/data/*.csv` |
| scripts | `final/tools/` (pnr_final.tcl, run_pnr_final.sh, pnr_campaign.sh, campaign1.sh, watchdog.sh, routed_check_final.sh), `final/models/` (fsim.py, fsim_all.sh, fsim_routed.sh, gadget_identity.py, control_final.py, pubpaths.py, placediff.py, pnr_stats.py, export_data.py), `final/prolead/` (run_lane_final.py, campaign_final*.sh, lane_table.py) |
| earlier phases (unchanged) | Phase XI (top level: `rtl/`, `models/`, `runs/`, `*.md`); Phase XII (`validation/`); Phase XIII (`competitors/`) |

## 4. External dependencies (not in the repository)
| dependency | location | identifier |
|---|---|---|
| synthesis / STA flow | `phase2/bfbench.py` (copy: `final/external/bfbench.py`) | sha256 `d16cf68ff319da0793be53b0f8b3ae2c60a38afa41d882fbb0d09dda0d38ffbe` |
| OpenROAD runner | `phase2/orfs_run.sh` (copy: `final/external/orfs_run.sh`) | sha256 `8f49a0b0b5f061cb6ca4a801c68defc40c1c535eae4c27534470fc85bbe660ba` |
| P&R netlist preparation | `phase2/pnr/prep_netlist.sh` (copy: `final/external/prep_netlist.sh`) | sha256 `198538d747047d5b673d8e11cd9d0955027ca3c3aa7a2609e91d94d70e751334` |
| Nangate45 liberty (synthesis) | `current/lib/NangateOpenCellLibrary_typical.lib` | sha256 `8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1` (not redistributed here) |
| don't-use-pruned liberty (flow C) | `phase2/pnr/NangateOpenCellLibrary_typical_dontuse.lib` | sha256 `d40bd28432308969df5ccaa35de390fd50d5ade956cb5c370d40f6b63226d3be` |
| OpenROAD + Nangate45 platform | ORFS image 26Q3-705-gecb3cfdeb, unpacked at `phase2/ext/tools/orfs_rootfs/` | image tag |
| Yosys / Icarus / OpenSTA | Yosys 0.33 (git 2584903a060), Icarus Verilog 12.0, OpenSTA 3.1.0 | — |
| SILVER | built by `validation/tools/build_silver.sh` into `phase2/ext/tools/sca/` | Sylvan 5e9da97 |
| PROLEAD | `phase2/ext/tools/sca/prolead-3.1.0` | v3.1.0, commit 91338e02 |

**Not distributed:** the full-text papers used in the reviews (`refs/*.txt` is git-ignored; `phase2/ext/priorart/papers/` is outside the repository). They are copyrighted and are cited only.

## 5. History preservation
- The Phase XI, XII and XIII artifacts are unchanged by this phase.
- `git diff` of `rtl/ models/ runs/ validation/ competitors/` against the Phase XIII commit `cf634d7` is empty; this was checked before the freeze commit.
- The only pre-existing working-copy difference is `tools/tmp.sh`. It is an uncommitted state predating Phase XII, restored there byte-exactly, and is not part of any commit.

## 6. Commits
| phase | commit |
|---|---|
| initial import (Phase XI) | `966d54a` |
| Phase XII | `979ea56`, `7089b57` |
| Phase XIII | `1046b60`, `3b69463`, `cf634d7` |
| Phase XIV content | <!-- CONTENT_COMMIT --> |
| freeze (this manifest; tagged `pams-publication-freeze-v1`) | the commit following the content commit |
