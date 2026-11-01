# Regenerate both xfft instances with the final (unscaled, 24-bit) config and
# dump the instantiation templates so the RTL port widths are authoritative.
set root [file normalize [file join [file dirname [info script]] ..]]
source [file join $root tcl ip_fft.tcl]
set logf [open [file join $root report xfft_ports.txt] w]
proc P {s} { global logf; puts $s; puts $logf $s; flush $logf }

create_project -force iponly [file join $root build iponly] -part xc7z020clg400-2
make_fft_ips

foreach n {fft_fwd fft_inv} {
    set veo [file join $root build iponly iponly.srcs sources_1 ip $n $n.veo]
    P "===== $n ====="
    if {[file exists $veo]} {
        P [read [open $veo r]]
    } else {
        P "MISSING $veo"
        foreach f [glob -nocomplain -directory [file join $root build iponly] -types f *.veo] { P "found $f" }
    }
    P "---- CONFIG ----"
    foreach p [list_property [get_ips $n]] {
        if {[string match CONFIG.* $p]} { P "  $p = [get_property $p [get_ips $n]]" }
    }
}
close $logf
P "IP_PORTS_DONE"
