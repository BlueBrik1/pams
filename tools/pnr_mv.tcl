# Phase V: matched place-and-route of an engine netlist with OpenROAD (ORFS image 26Q3-705-gecb3cfdeb), Nangate45.
# Same script, constraints and knobs for every design. Inputs (env): NETLIST TOP PERIOD OUT UTIL DENS THREADS
# Output: $OUT/metrics.txt (key value lines), $OUT/final.def, $OUT/final.v, reports.
set P $::env(ORFS_PLATFORMS)/nangate45
set OUT $::env(OUT); file mkdir $OUT
set PERIOD $::env(PERIOD); set UTIL $::env(UTIL); set DENS $::env(DENS); set THREADS $::env(THREADS)
set_thread_count $THREADS
set ::env(TAP_CELL_NAME) TAPCELL_X1   ;# used by the platform's tapcell.tcl (ORFS config.mk value)
proc metric {k v} { global OUT; set f [open $OUT/metrics.txt a]; puts $f "$k $v"; close $f; puts "METRIC $k $v" }
file delete -force $OUT/metrics.txt

read_lef $P/lef/NangateOpenCellLibrary.tech.lef
read_lef $P/lef/NangateOpenCellLibrary.macro.mod.lef
read_liberty $P/lib/NangateOpenCellLibrary_typical.lib
read_verilog $::env(NETLIST)
link_design $::env(TOP)

# constraints: identical to the synthesis STA (I/O at the clock edge), plus a real clock period for the optimizers
create_clock -name clk -period $PERIOD [get_ports clk]
set ins [delete_from_list [all_inputs] [get_ports clk]]
set_input_delay 0 -clock clk $ins
set_output_delay 0 -clock clk [all_outputs]
set_input_transition 0.05 $ins
set_load 0.005 [all_outputs]
set_dont_use {TAPCELL_X1 FILLCELL_X1 AOI211_X1 OAI211_X1}
metric synth_cell_area [sta::format_area [rsz::design_area] 3]

initialize_floorplan -utilization $UTIL -aspect_ratio 1.0 -core_space 2.0 -site FreePDK45_38x28_10R_NP_162NW_34O
source $P/make_tracks.tcl
remove_buffers
place_pins -hor_layers metal5 -ver_layers metal6 -random_seed 1
source $P/tapcell.tcl
source $P/grid_strategy-M1-M4-M7.tcl
pdngen
source $P/setRC.tcl

global_placement -density $DENS -skip_io
place_pins -hor_layers metal5 -ver_layers metal6
global_placement -density $DENS -timing_driven
estimate_parasitics -placement
repair_design
repair_tie_fanout LOGIC0_X1/Z
repair_tie_fanout LOGIC1_X1/Z
detailed_placement
clock_tree_synthesis -root_buf BUF_X4 -buf_list {BUF_X4 BUF_X8} -sink_clustering_enable
set_propagated_clock [all_clocks]
estimate_parasitics -placement
repair_clock_nets
detailed_placement
repair_timing -setup -skip_pin_swap
repair_timing -hold -max_buffer_percent 60
detailed_placement
check_placement -verbose

set_routing_layers -signal metal2-metal10 -clock metal4-metal10
set_global_routing_layer_adjustment metal2-metal10 0.5
global_route -guide_file $OUT/route.guide -congestion_iterations 50 -congestion_report_file $OUT/congestion.rpt
estimate_parasitics -global_routing
repair_timing -setup -skip_pin_swap
detailed_route -output_drc $OUT/drc.rpt -verbose 1 -droute_end_iter 64
filler_placement {FILLCELL_X32 FILLCELL_X16 FILLCELL_X8 FILLCELL_X4 FILLCELL_X2 FILLCELL_X1}

# post-route timing on extracted parasitics
define_process_corner -ext_model_index 0 X
if {[catch {extract_parasitics -ext_model_file $P/rcx_patterns.rules} err]} {
  # RCX refuses nets with remaining routing shorts; fall back to global-route estimates and say so in the metrics
  puts "RCX failed: $err"; estimate_parasitics -global_routing; metric parasitics estimated_global_route
} else {
  write_spef $OUT/final.spef; read_spef $OUT/final.spef; metric parasitics rcx_extracted
}

proc group_slack {from to} {
  set p [find_timing_paths -from $from -to $to -path_delay max -group_path_count 1]
  if {[llength $p] == 0} { return 1e9 }
  return [get_property [lindex $p 0] slack]
}
set regs_ck [all_registers -clock_pins]; set regs_d [all_registers -data_pins]
set s_in2reg  [group_slack $ins $regs_d]
set s_reg2reg [group_slack $regs_ck $regs_d]
set s_reg2out [group_slack $regs_ck [all_outputs]]
set s_in2out  [group_slack $ins [all_outputs]]
set smin [expr min($s_in2reg, $s_reg2reg, $s_reg2out, $s_in2out)]
foreach {k v} [list in2reg $s_in2reg reg2reg $s_reg2reg reg2out $s_reg2out in2out $s_in2out] { metric slack_$k $v }
metric period_target $PERIOD
metric period_achieved [expr $PERIOD - $smin]
metric hold_wns [sta::worst_slack -min]
metric cell_area [sta::format_area [rsz::design_area] 3]
set db [ord::get_db]; set blk [[$db getChip] getBlock]
set core [$blk getCoreArea]; set die [$blk getDieArea]
metric core_area_um2 [expr ([$core dx] / 2000.0) * ([$core dy] / 2000.0)]
metric die_area_um2 [expr ([$die dx] / 2000.0) * ([$die dy] / 2000.0)]
set ninst 0; set nbuf 0
foreach i [$blk getInsts] { incr ninst; set m [[$i getMaster] getName]; if {[string match BUF_* $m] || [string match CLKBUF_* $m]} { incr nbuf } }
metric instances $ninst
metric buffers $nbuf
# wirelength / vias: parsed from TritonRoute's summary in openroad.log by run_pnr.sh
set drc 0
if {[file exists $OUT/drc.rpt]} { set f [open $OUT/drc.rpt]; foreach l [split [read $f] "\n"] { if {[string match "violation type*" $l]} { incr drc } }; close $f }
metric drc_violations $drc
set_power_activity -input -activity 0.1   ;# vectorless estimate (same default for every design); parsed by run_pnr.sh
report_power > $OUT/power.rpt
report_checks -path_delay max -group_path_count 3 -digits 4 > $OUT/timing.rpt
write_def $OUT/final.def
write_verilog $OUT/final.v
metric done 1
exit
