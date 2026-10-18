set proj_dir D:/g_build/iic_probe
file delete -force $proj_dir
file mkdir $proj_dir
create_project iprobe $proj_dir -part xc7z020clg400-2
create_bd_design z
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
source D:/Tools_FPGA/workspace/voice_conversion_zynq7020/pl_kernels/build_2018/ps7_config.tcl
set_property -dict $ps_cfg $ps
puts "INTF_IIC: [get_bd_intf_pins */IIC*]"
puts "PINS_IIC: [get_bd_pins */IIC*]"
exit
