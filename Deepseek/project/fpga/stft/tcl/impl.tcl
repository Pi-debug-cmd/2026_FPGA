# 2018.3 implementation, bitstream and .hdf export for the stft_dma design.
set root [file normalize [file join [file dirname [info script]] ..]]
set out [file join $root build generated stft_dma]
open_project [file join $out voice7020.xpr]
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis not complete"}
set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true [get_runs impl_1]
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
report_utilization -file [file join $root report impl_utilization.txt]
report_utilization -hierarchical -file [file join $root report impl_utilization_hier.txt]
report_timing_summary -file [file join $root report impl_timing.txt]
report_bus_skew -file [file join $root report impl_bus_skew.txt]
report_drc -file [file join $root report impl_drc.txt]
report_clock_utilization -file [file join $root report impl_clock_utilization.txt]
set bitdir [file join $root build generated stft_dma voice7020.runs impl_1]
file copy -force [file join $bitdir zynq_wrapper.bit] [file join $root bitstream stft_dma.bit]
file copy -force [file join $bitdir zynq_wrapper.bin] [file join $root bitstream stft_dma.bin]
if {[catch {
  write_hw_platform -fixed -include_bit -force -file [file join $root bitstream stft_dma.xsa]
} msg]} {
  puts "write_hw_platform note: $msg"
  catch {write_hwdef -force -file [file join $root bitstream stft_dma.hwdef]}
}
puts STFT_DMA_BITSTREAM_BUILT
exit
