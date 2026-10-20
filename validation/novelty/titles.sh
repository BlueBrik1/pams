L=~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot/usr/lib/x86_64-linux-gnu; B=~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot/usr/bin
for f in $(find ~/lwe_agent_handoff/phase2/ext/papers -name "*.pdf"); do printf "%s :: " "$(basename $f)"; LD_LIBRARY_PATH=$L $B/pdftotext -l 1 "$f" - 2>/dev/null | tr -s '\n ' ' ' | cut -c1-150; echo; done
