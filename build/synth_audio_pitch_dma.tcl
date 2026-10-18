# Continue the isolated A-disk board design; no programming commands.
set root [file normalize [file join [file dirname [info script]] ..]]
set out [file join $root build generated audio_pitch_dma]
open_project [file join $out voice7020.xpr]
open_bd_design [get_files zynq.bd]
# First construction predated the live I2C IRQ audit. Match the current builder.
set pin [get_bd_pins xlc/In2]
disconnect_bd_net [get_bd_nets -of_objects $pin] $pin
connect_bd_net [get_bd_pins axi_iic/iic2intc_irpt] $pin
# Preserve occupied VTC/UART interrupt positions; new DMA uses free bits 12/13.
foreach {oldbit newbit signal} {0 12 mm2s_introut 1 13 s2mm_introut} {
    foreach bit [list $oldbit $newbit] {
        set pin [get_bd_pins xlc/In$bit]
        disconnect_bd_net [get_bd_nets -of_objects $pin] $pin
    }
    connect_bd_net [get_bd_pins irqzero/dout] [get_bd_pins xlc/In$oldbit]
    connect_bd_net [get_bd_pins pitch_dma/$signal] [get_bd_pins xlc/In$newbit]
}
validate_bd_design
save_bd_design
set_property GENERATE_SYNTH_CHECKPOINT true [get_files zynq.bd]
generate_target all [get_files zynq.bd]
create_ip_run [get_files zynq.bd]
update_compile_order -fileset sources_1
reset_run synth_1
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis failed: inspect run log"}
open_run synth_1
report_utilization -file [file join $root report audio_pitch_dma_utilization.txt]
report_timing_summary -file [file join $root report audio_pitch_dma_synth_timing.txt]
report_drc -file [file join $root report audio_pitch_dma_synth_drc.txt]
puts AUDIO_PITCH_DMA_SYNTHESIZED
exit
