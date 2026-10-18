open_project pointwise_s8_packed_hls
set_top pointwise_s8
add_files pointwise_s8_packed.cpp
add_files -tb test_pointwise_s8.cpp
open_solution solution1
set_part {xc7z020clg400-2}
create_clock -period 10 -name default
csim_design
csynth_design
cosim_design -rtl verilog -tool xsim
exit
