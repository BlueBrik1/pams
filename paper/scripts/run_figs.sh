cd ~/lwe_agent_handoff/phase2/masked_verification/paper/scripts
python3 -I generate_figures.py "$@" 2>&1 | tail -25
