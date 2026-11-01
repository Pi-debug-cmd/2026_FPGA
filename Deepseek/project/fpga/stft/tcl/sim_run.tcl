# Re-run the (already elaborated) simulation in batch mode without waveform
# recording; the WDB writer was the bottleneck, not the RTL.
set root [file normalize [file join [file dirname [info script]] ..]]
open_project [file join $root build sim sim.xpr]
set fs [get_filesets sim_1]
set_property xsim.simulate.wdb none $fs
set_property xsim.simulate.runtime all $fs
launch_simulation
puts "SIM_BATCH_DONE"
