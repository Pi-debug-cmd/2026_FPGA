# =====================================================================
# Stage 1: create project, IP repos, BD, PS7 with extracted config.
# =====================================================================
set build_dir "D:/g_build"
set proj_dir  "$build_dir/proj"
set ip_repo_vendor "D:/Tools_FPGA/workspace/voice_conversion_zynq7020/vendor_base_2022_2/ip_repo"
set ip_repo_gemm   "D:/g_ip"
set ps_cfg_file    "D:/Tools_FPGA/workspace/voice_conversion_zynq7020/pl_kernels/build_2018/ps7_config.tcl"

file delete -force $proj_dir
file mkdir $proj_dir
create_project voice7020 $proj_dir -part xc7z020clg400-2 -force
set_property ip_repo_paths [list $ip_repo_vendor $ip_repo_gemm] [current_project]
update_ip_catalog

create_bd_design zynq
source $ps_cfg_file

set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
set_property -dict $ps_cfg $ps

# Apply PS7 block automation (enables GP/HP AXI clocks per the config)
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 -config {make_wrapper {0} } [get_bd_cells ps7]

save_bd_design
puts STAGE1_DONE
exit
