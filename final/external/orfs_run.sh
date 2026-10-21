#!/usr/bin/env bash
# Run a tool from the unpacked ORFS image (get_orfs.py) natively in WSL: the image's own dynamic loader and
# libraries (the real loader file: lib64/ld-linux-x86-64.so.2 is an absolute symlink to the HOST loader), no chroot/sudo/Docker. usage: orfs_run.sh openroad|yosys|sta [args...]
R=$(cd "$(dirname "$0")" && pwd)/ext/tools/orfs_rootfs
T=$1; shift
case $T in
  openroad) B=$R/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad ;;
  sta)      B=$R/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/sta ;;
  yosys)    B=$R/OpenROAD-flow-scripts/tools/install/yosys/bin/yosys ;;
  *) echo "unknown tool $T"; exit 2 ;;
esac
LP=$R/lib/x86_64-linux-gnu:$R/usr/lib/x86_64-linux-gnu:$R/usr/local/lib:$R/usr/lib:$R/lib
for d in $R/OpenROAD-flow-scripts/tools/install/*/lib $R/usr/lib/x86_64-linux-gnu/*/; do [ -d "$d" ] && LP=$LP:$d; done
export TCL_LIBRARY=$(ls -d $R/usr/share/tcltk/tcl8.* 2>/dev/null | head -1)
export ORFS_PLATFORMS=$R/OpenROAD-flow-scripts/flow/platforms
exec $R/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 --library-path "$LP" "$B" "$@"
