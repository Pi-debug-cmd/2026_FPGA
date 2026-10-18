"""Derive a separate configurable board design; preserve the tested fixed design."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
s = (root / 'build/create_audio_pitch_dma.tcl').read_text(encoding='utf-8')
def replace(old, new):
    global s
    if s.count(old) != 1:
        raise ValueError(f'Base design changed: {old}')
    s = s.replace(old, new)

replace('set root [file normalize [file join [file dirname [info script]] ..]]',
        f'set root {{{root.as_posix()}}}')
replace('set tag audio_pitch_dma\n', 'set tag audio_pitch_dma_control\n')
replace('set ratio [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 ratio]\nset_property -dict [list CONFIG.CONST_WIDTH {18} CONFIG.CONST_VAL {86856}] $ratio',
'''set control [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 pitch_control]
set_property -dict [list CONFIG.C_IS_DUAL {1} CONFIG.C_ALL_OUTPUTS {1} CONFIG.C_ALL_OUTPUTS_2 {1} CONFIG.C_GPIO_WIDTH {18} CONFIG.C_GPIO2_WIDTH {1} CONFIG.C_DOUT_DEFAULT {0x00015348} CONFIG.C_DOUT_DEFAULT_2 {0x00000000}] $control
set reset_gate [create_bd_cell -type ip -vlnv xilinx.com:ip:util_vector_logic:2.0 pitch_reset_gate]
set_property -dict [list CONFIG.C_OPERATION {and} CONFIG.C_SIZE {1}] $reset_gate''')
replace('CONFIG.NUM_MI {6}', 'CONFIG.NUM_MI {7}')
replace('connect_bd_net [get_bd_pins ratio/dout] [get_bd_pins pitch/ratio_q16]',
'''connect_bd_net [get_bd_pins pitch_control/gpio_io_o] [get_bd_pins pitch/ratio_q16]
connect_bd_net [get_bd_pins pitch_control/gpio2_io_o] [get_bd_pins pitch_reset_gate/Op2]
connect_bd_net [get_bd_pins crst/peripheral_aresetn] [get_bd_pins pitch_reset_gate/Op1]
connect_bd_net [get_bd_pins pitch_reset_gate/Res] [get_bd_pins pitch/aresetn]
connect_bd_intf_net [get_bd_intf_pins ctrl_ic/M06_AXI] [get_bd_intf_pins pitch_control/S_AXI]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins pitch_control/s_axi_aclk]
connect_bd_net [get_bd_pins crst/peripheral_aresetn] [get_bd_pins pitch_control/s_axi_aresetn]''')
replace('[get_bd_pins pitch/aresetn] [get_bd_pins pitch_dma/axi_resetn]', '[get_bd_pins pitch_dma/axi_resetn]')
if s.count('foreach m {M00 M01 M02 M03 M04 M05}') != 2:
    raise ValueError('Interconnect clock/reset structure changed')
s = s.replace('foreach m {M00 M01 M02 M03 M04 M05}', 'foreach m {M00 M01 M02 M03 M04 M05 M06}')
replace('# ---------------- addresses ----------------', '''# ---------------- addresses ----------------
assign_bd_address -offset 0x41200000 -range 0x00010000 -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs pitch_control/S_AXI/Reg]''')
out = root / 'build/generated/create_audio_pitch_control.tcl'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(s, encoding='utf-8', newline='\n')
print(out)
