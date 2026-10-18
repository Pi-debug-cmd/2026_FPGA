set proj_dir D:/g_build/concat_probe
file delete -force $proj_dir
file mkdir $proj_dir
create_project cp $proj_dir -part xc7z020clg400-2
create_bd_design z
set xlc [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconcat:2.1 irq_concat]
puts "PINS_AFTER_CREATE: [get_bd_pins -of $xlc -quiet]"
set_property -dict [list CONFIG.NUM_PORTS {16}] $xlc
puts "PINS_AFTER_SETPROP: [get_bd_pins -of $xlc -quiet]"
save_bd_design
puts "PINS_AFTER_SAVE: [get_bd_pins -of $xlc -quiet]"
regenerate_bd_layout
puts "PINS_AFTER_REGEN: [get_bd_pins -of $xlc -quiet]"
validate_bd_design
puts "PINS_AFTER_VALIDATE: [get_bd_pins -of $xlc -quiet]"
exit
