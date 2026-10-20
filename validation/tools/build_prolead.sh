# Build PROLEAD v3.1.0 (latest release) against the user-local sysroot from deps.sh
set -e -o pipefail
T=~/lwe_agent_handoff/phase2/ext/tools/sca; R=$T/sysroot; L=$R/usr/lib/x86_64-linux-gnu
cd $T; [ -d prolead-3.1.0 ] || git -C PROLEAD worktree add -f ../prolead-3.1.0 v3.1.0 >/dev/null 2>&1
cd prolead-3.1.0; git checkout -q Makefile
INC="-I$R/usr/include -I$R/usr/include/python3.12 -I$R/usr/include/x86_64-linux-gnu/python3.12 -I$R/usr/include/flint -I$R/usr/include/x86_64-linux-gnu"
sed -i "s|^INCLUDE_PYTHON3=.*|INCLUDE_PYTHON3=$INC|; s|^LINK_PYTHON3=.*|LINK_PYTHON3=-L$L -Wl,-rpath,$L -lpython3.12|; s|-lboost_python310|-lboost_python312 -L$L -Wl,-rpath,$L|" Makefile
make release -j16 > build.log 2>&1 || { grep -E " error|Error " build.log | head -20; exit 1; }
ls -la release/ 2>/dev/null | head; f=$(ls release/PROLEAD* release/prolead* 2>/dev/null | head -1); echo "binary: $f"; LD_LIBRARY_PATH=$L $f --help 2>&1 | head -30
