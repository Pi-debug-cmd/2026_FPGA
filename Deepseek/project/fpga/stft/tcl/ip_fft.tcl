# Shared IP factory: two 1024-point xfft 9.1 instances, fixed point, UNSCALED
# (no scale-schedule word to get wrong; every scaling factor is explicit in RTL)
#   fft_fwd : 24-bit in -> 40-bit out   (a[n] = x[n] in int16 units)
#   fft_inv : 32-bit in -> 48-bit out   (Y[k], 6 fractional bits)
proc make_fft_ips {} {
    foreach n {fft_fwd fft_inv} {
        if {[llength [get_ips -quiet $n]] == 0} {
            create_ip -name xfft -vendor xilinx.com -library ip -version 9.1 \
                -module_name $n
        }
    }
    set base [list \
        CONFIG.transform_length {1024} \
        CONFIG.implementation_options {pipelined_streaming_io} \
        CONFIG.data_format {fixed_point} \
        CONFIG.phase_factor_width {24} \
        CONFIG.scaling_options {unscaled} \
        CONFIG.rounding_modes {convergent_rounding} \
        CONFIG.output_ordering {natural_order} \
        CONFIG.ovflo {false} \
        CONFIG.aclken {false} \
        CONFIG.aresetn {true} \
        CONFIG.xk_index {false} \
        CONFIG.target_clock_frequency {100} ]
    set_property -dict [concat $base [list CONFIG.input_width {24}]] [get_ips fft_fwd]
    set_property -dict [concat $base [list CONFIG.input_width {32}]] [get_ips fft_inv]
    foreach n {fft_fwd fft_inv} {
        generate_target {instantiation_template synthesis simulation} [get_ips $n]
    }
}
