set root [file normalize [file join [file dirname [info script]] ..]]
open_project [file join $root build generated audio_pitch_dma_control voice7020.xpr]
open_run impl_1
report_bus_skew -file [file join $root report audio_pitch_control_bus_skew.txt]
exit
