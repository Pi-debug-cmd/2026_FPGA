# 2018.3 implementation + bitstream + XSA export (never programs hardware).
set root D:/g_build/pl_20261025
set out [file join $root build generated audio_pitch_dma]
open_project [file join $out voice7020.xpr]
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis not complete"}
set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true [get_runs impl_1]
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
report_utilization -file [file join $root report impl_utilization.txt]
report_utilization -hierarchical -file [file join $root report impl_utilization_hier.txt]
report_timing_summary -file [file join $root report impl_timing.txt]
report_bus_skew -file [file join $root report impl_bus_skew.txt]
report_drc -file [file join $root report impl_drc.txt]
report_clock_utilization -file [file join $root report impl_clock_utilization.txt]
# export hardware platform for the 2018.3 flow (.xsa; .hdf fallback)
if {[catch {
  write_hw_platform -fixed -include_bit -force -file [file join $root audio_pitch.xsa]
} msg]} {
  puts "write_hw_platform note: $msg"
  catch {write_sysdef -hwdef [file join $root audio_pitch.hwdef] -bitfile [get_property DIRECTORY [get_runs impl_1]]/zynq_wrapper.bit -file [file join $root audio_pitch.sysdef]}
}
puts AUDIO_PITCH_DMA_BITSTREAM_BUILT_2018_3
exit
