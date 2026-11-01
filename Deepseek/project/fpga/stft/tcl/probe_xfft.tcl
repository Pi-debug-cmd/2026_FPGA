# Probe the 2018.3 xfft IP: available versions, configurable properties, port
# widths of the two instances we need (forward scaled 16->24, inverse unscaled
# 24->35).  Writes report/xfft_probe.txt and the instantiation templates.
set root [file normalize [file join [file dirname [info script]] ..]]
set logf [open [file join $root report xfft_probe.txt] w]

proc P {s} { global logf; puts $s; puts $logf $s; flush $logf }

create_project -force probe [file join $root build probe] -part xc7z020clg400-2

P "== xfft ipdefs =="
foreach d [get_ipdefs -all *xfft*] { P $d }

proc mk {name dict} {
    global root logf
    create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 -module_name $name
    set_property -dict $dict [get_ips $name]
    generate_target {instantiation_template synthesis} [get_ips $name]
    P "== $name properties =="
    foreach p [list_property [get_ips $name]] {
        if {[string match CONFIG.* $p]} { P "  $p = [get_property $p [get_ips $name]]" }
    }
}

mk fft_fwd [list \
    CONFIG.transform_length {1024} \
    CONFIG.implementation_options {pipelined_streaming_io} \
    CONFIG.data_format {fixed_point} \
    CONFIG.input_width {16} \
    CONFIG.phase_factor_width {24} \
    CONFIG.scaling_options {scaled} \
    CONFIG.rounding_modes {convergent_rounding} \
    CONFIG.output_ordering {natural_order} \
    CONFIG.ovflo {false} \
    CONFIG.aclken {false} \
    CONFIG.aresetn {false} \
]

mk fft_inv [list \
    CONFIG.transform_length {1024} \
    CONFIG.implementation_options {pipelined_streaming_io} \
    CONFIG.data_format {fixed_point} \
    CONFIG.input_width {24} \
    CONFIG.phase_factor_width {24} \
    CONFIG.scaling_options {unscaled} \
    CONFIG.rounding_modes {convergent_rounding} \
    CONFIG.output_ordering {natural_order} \
    CONFIG.ovflo {false} \
    CONFIG.aclken {false} \
    CONFIG.aresetn {false} \
]

foreach n {fft_fwd fft_inv} {
    set veo [file join $root build probe probe.srcs sources ip $n $n.veo]
    P "== $n .veo =="
    if {[file exists $veo]} { P [read [open $veo r]] } else { P "MISSING $veo" }
}
close $logf
P "PROBE_DONE"
