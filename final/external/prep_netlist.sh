#!/usr/bin/env bash
# P&R netlist preparation (identical for every design; same as ORFS synthesis does): constants -> tie cells
# (LOGIC1_X1 / LOGIC0_X1), assign statements -> BUF_X1, so that OpenROAD sees no constant/power-typed signal nets.
# usage: prep_netlist.sh IN_MAPPED.v OUT.v [TOP=ntt_mlkem]
set -eu
H=$(cd "$(dirname "$0")" && pwd); LIB=$H/../../current/lib/NangateOpenCellLibrary_typical.lib
IN=$(realpath "$1"); OUTV=$(realpath -m "$2"); TOP=${3:-ntt_mlkem}
yosys -q -p "read_liberty -lib $LIB; read_verilog $IN; hierarchy -top $TOP; hilomap -singleton -hicell LOGIC1_X1 Z -locell LOGIC0_X1 Z; setundef -zero; insbuf -buf BUF_X1 A Z; opt_clean; stat -liberty $LIB; write_verilog -noattr -noexpr -nohex -nodec $OUTV" | grep -i "chip area" || true
