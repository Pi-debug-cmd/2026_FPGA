# Dump a fresh PS7's default CONFIG properties as base64-encoded lines.
set out "D:/Tools_FPGA/workspace/voice_conversion_zynq7020/pl_kernels/build_2018/ps7_defaults.b64"
create_project pdef D:/g_def -part xc7z020clg400-2 -force
create_bd_design d
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
set fh [open $out w]
foreach p [lsort [list_property $ps]] {
    if {[string range $p 0 6] eq "CONFIG."} {
        if {[catch {set val [get_property $p $ps]}]} continue
        set b64 [b64encode [encoding convertto utf-8 $val]]
        puts $fh "$p\t$b64"
    }
}
close $fh
close_bd_design [current_bd_design]
puts DEFAULTS_DUMPED
exit
