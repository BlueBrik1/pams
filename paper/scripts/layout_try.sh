cd ~/lwe_agent_handoff/phase2
export QT_QPA_PLATFORM=offscreen RUN=$HOME/lwe_agent_handoff/phase2/masked_verification/final/runs/pnr_pams_jqr_T2.0_s1 IMG=/tmp/pams_try.png RES=0.1
timeout 300 bash orfs_run.sh openroad -no_init -exit $HOME/lwe_agent_handoff/phase2/masked_verification/paper/scripts/layout_image.tcl 2>&1 | tail -8
ls -la /tmp/pams_try.png
