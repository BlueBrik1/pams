#!/bin/bash
# render PDF pages to PNG for visual inspection (poppler from the Phase XII user-local sysroot)
# usage: preview.sh FILE.pdf OUTPREFIX [first [last]] [dpi]
R=~/lwe_agent_handoff/phase2/ext/tools/sca/sysroot
export LD_LIBRARY_PATH=$R/usr/lib/x86_64-linux-gnu:$R/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
$R/usr/bin/pdftoppm -png -r ${5:-110} -f ${3:-1} -l ${4:-${3:-1}} "$1" "$2"
