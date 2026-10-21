# Workstation-only placement/routing/bitstream generation; never programs hardware.
set root [file normalize [file join [file dirname [info script]] ..]]
open_project [file join $root build generated audio_pitch_dma_2026 voice7020.xpr]
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis not complete"}
set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true [get_runs impl_1]
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
report_utilization -file [file join $root report audio_pitch_dma_2026_impl_utilization.txt]
report_timing_summary -file [file join $root report audio_pitch_dma_2026_impl_timing.txt]
report_bus_skew -file [file join $root report audio_pitch_dma_2026_impl_bus_skew.txt]
report_drc -file [file join $root report audio_pitch_dma_2026_impl_drc.txt]
puts AUDIO_PITCH_DMA_BITSTREAM_BUILT
