"""Audit A-disk PS settings and prepare an isolated 2018.3 audio/DMA design."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
vendor = Path(sys.argv[1])
handoff = ROOT / '交接/核心材料/pl_kernels/build_2018'
inputs = ROOT / 'board/vendor_inputs'
inputs.mkdir(parents=True, exist_ok=True)
bd_path = vendor / 'zynq7020.srcs/sources_1/bd/zynq/zynq.bd'
bd = json.loads(bd_path.read_text(encoding='utf-8'))['design']
assert bd['design_info']['device'] == 'xc7z020clg400-2'
parameters = {k: v['value'] for k, v in bd['components']['processing_system7_0']['parameters'].items()}
cfg_path = handoff / 'ps7_config.tcl'
cfg = cfg_path.read_text(encoding='utf-8')
old = dict(re.findall(r'CONFIG\.(\w+)\s+\{([^}]*)\}', cfg))
differences = {k: [v, parameters.get(k)] for k, v in old.items() if parameters.get(k) != v}
assert not differences, differences
(inputs / 'ps7_config.tcl').write_bytes(cfg_path.read_bytes())
shutil.copyfile(handoff / 'my_iobuf.v', inputs / 'my_iobuf.v')
ip_source = vendor / 'ip_repo/axi_dynclk'
ip_dest = inputs / 'ip_repo/axi_dynclk'
for source in ip_source.rglob('*'):
    if source.is_file():
        target = ip_dest / source.relative_to(ip_source)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise ValueError(f'Existing vendor IP differs: {target}')
        shutil.copyfile(source, target)

# Use only A-disk constraints for the exposed audio and I2C ports.
xdc_path = vendor / 'zynq7020.srcs/constrs_1/new/zynq.xdc'
raw = xdc_path.read_bytes()
try:
    xdc = raw.decode('utf-8')
except UnicodeDecodeError:
    xdc = raw.decode('gb18030')
ports = ['ADCLRC', 'DACLRC', 'DACDAT', 'BCLK', 'ADCDAT', 'MCLK',
         'I2C1_scl_io', 'I2C1_sda_io', 'I2C2_scl_io', 'I2C2_sda_io', 'I2C3_scl_io', 'I2C3_sda_io']
lines = []
for line in xdc.splitlines():
    if 'set_property' not in line or 'get_ports' not in line:
        continue
    if any(re.search(r'\b' + re.escape(port) + r'\b', line) for port in ports):
        lines.append(line.replace('{BCLK[0]}', 'BCLK'))
assert len(lines) == len(ports) * 2, lines
(inputs / 'audio_i2c.xdc').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')

# Adapt the reviewed legacy wiring, never execute its deletion or absolute paths.
s = (handoff / 'build_all.tcl').read_text(encoding='utf-8')
start = s.index('# ---------------- PS7')
s = s[start:]
s = s.replace('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/pl_kernels/build_2018/ps7_config.tcl', '[file join $root board vendor_inputs ps7_config.tcl]')
s = s.replace('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/pl_kernels/build_2018/my_iobuf.v', '[file join $root board vendor_inputs my_iobuf.v]')
s = s.replace('set_property -dict $ps_cfg $ps', 'set_property -dict $ps_cfg $ps\nset_property -dict [list CONFIG.PCW_USE_S_AXI_HP2 {0} CONFIG.PCW_USE_S_AXI_HP3 {0}] $ps')
s = s.replace('set gemm [create_bd_cell -type ip -vlnv local.user:hls:gemm_s8:1.1 gemm]', '''set dma [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_dma:7.1 pitch_dma]
set_property -dict [list CONFIG.c_include_sg {0} CONFIG.c_m_axis_mm2s_tdata_width {32} CONFIG.c_sg_length_width {23}] $dma
create_bd_cell -type module -reference axis_pitch_shift pitch
set ratio [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 ratio]
set_property -dict [list CONFIG.CONST_WIDTH {18} CONFIG.CONST_VAL {86856}] $ratio''')
a = s.index('# Three independent'); b = s.index('# interrupt concat', a)
s = s[:a] + '''set pic [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 pitch_dma_mem]
set_property -dict [list CONFIG.NUM_SI {2} CONFIG.NUM_MI {1}] $pic

''' + s[b:]
s = s.replace('gemm/s_axi_control', 'pitch_dma/S_AXI_LITE')
a = s.index('# gemm HP interconnects:'); b = s.index('# ---------------- clocks', a)
s = s[:a] + '''# Independent PCM16 stream; never insert it directly into the I2S stream.
connect_bd_intf_net [get_bd_intf_pins pitch_dma/M_AXI_MM2S] [get_bd_intf_pins pitch_dma_mem/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins pitch_dma/M_AXI_S2MM] [get_bd_intf_pins pitch_dma_mem/S01_AXI]
connect_bd_intf_net [get_bd_intf_pins pitch_dma_mem/M00_AXI] [get_bd_intf_pins ps7/S_AXI_HP1]
connect_bd_intf_net [get_bd_intf_pins pitch_dma/M_AXIS_MM2S] [get_bd_intf_pins pitch/s_axis]
connect_bd_intf_net [get_bd_intf_pins pitch/m_axis] [get_bd_intf_pins pitch_dma/S_AXIS_S2MM]
connect_bd_net [get_bd_pins ratio/dout] [get_bd_pins pitch/ratio_q16]

''' + s[b:]
s = s.replace('[get_bd_pins ps7/S_AXI_HP2_ACLK] [get_bd_pins ps7/S_AXI_HP3_ACLK]', '')
for suffix in ['ACLK', 'ARESETN']:
    s = s.replace(f'[get_bd_pins weights_ic/{suffix}] [get_bd_pins input_ic/{suffix}] [get_bd_pins output_ic/{suffix}]', f'[get_bd_pins pitch_dma_mem/{suffix}] [get_bd_pins pitch_dma_mem/S01_{suffix}]')
s = s.replace('foreach ic {weights_ic input_ic output_ic}', 'foreach ic {pitch_dma_mem}')
s = s.replace('[get_bd_pins gemm/ap_clk]', '[get_bd_pins pitch/aclk] [get_bd_pins pitch_dma/s_axi_lite_aclk] [get_bd_pins pitch_dma/m_axi_mm2s_aclk] [get_bd_pins pitch_dma/m_axi_s2mm_aclk]')
s = s.replace('[get_bd_pins gemm/ap_rst_n]', '[get_bd_pins pitch/aresetn] [get_bd_pins pitch_dma/axi_resetn]')
s = s.replace('foreach i {0 1 2 7 8 9 10 11 12 13 14 15}', 'connect_bd_net [get_bd_pins pitch_dma/mm2s_introut] [get_bd_pins xlc/In12]\nconnect_bd_net [get_bd_pins pitch_dma/s2mm_introut] [get_bd_pins xlc/In13]\nconnect_bd_net [get_bd_pins axi_iic/iic2intc_irpt] [get_bd_pins xlc/In2]\nforeach i {0 1 7 8 9 10 11 14 15}')
s = s.replace('route_i2c I2C0 IIC_0_0', 'route_i2c I2C0 I2C1').replace('route_i2c I2C1 IIC_1_0', 'route_i2c I2C1 I2C2')
s = s.replace('# Leave the PL axi_iic IIC interface unconnected (codec is on PS IIC0 EMIO).', '# Expose all A-disk I2C pins; codec is on PS I2C0 EMIO, not PL axi_iic.')
s = s.replace('puts "EXT_IIC_PORTS: [get_bd_ports IIC_*_io]"', 'make_bd_intf_pins_external [get_bd_intf_pins axi_iic/IIC]\nset_property name I2C3 [get_bd_intf_ports IIC_0]')
s = s.replace('0x43D00000', '0x40400000').replace('pitch_dma/S_AXI_LITE/reg0', 'pitch_dma/S_AXI_LITE/Reg')
s = '\n'.join(line for line in s.splitlines() if not ('assign_bd_address' in line and 'gemm/' in line))
s = s.replace('save_bd_design\nvalidate_bd_design\nputs BUILD_ALL_DONE\nexit', '''foreach master {M_AXI_MM2S M_AXI_S2MM} {
  assign_bd_address -offset 0x00000000 -range 0x40000000 -target_address_space [get_bd_addr_spaces pitch_dma/$master] [get_bd_addr_segs ps7/S_AXI_HP1/HP1_DDR_LOWOCM]
}
save_bd_design
validate_bd_design
save_bd_design
add_files -norecurse [make_wrapper -files [get_files zynq.bd] -top]
add_files -fileset constrs_1 [file join $root board vendor_inputs audio_i2c.xdc]
set_property top zynq_wrapper [current_fileset]
puts AUDIO_PITCH_DMA_VALIDATED
exit''')
assert 'D:/' not in s and 'gemm/' not in s
header = '''# Audio wiring adapted from reviewed handoff; PS and pins audited against A disk.
set root [file normalize [file join [file dirname [info script]] ..]]
set tag audio_pitch_dma
if {[llength $argv] == 1} {set tag [lindex $argv 0]}
if {[llength $argv] > 1 || ![regexp {^audio_pitch_dma(_[a-zA-Z0-9]+)?$} $tag]} {error "Invalid output tag"}
set out [file join $root build generated $tag]
if {[file exists [file join $out voice7020.xpr]]} {error "Output project exists; preserve it"}
create_project voice7020 $out -part xc7z020clg400-2
set_property ip_repo_paths [list [file join $root board vendor_inputs ip_repo]] [current_project]
update_ip_catalog
add_files [list [file join $root src rtl pcm_delay_ram.v] [file join $root src rtl axis_pitch_shift.v]]
update_compile_order -fileset sources_1
create_bd_design zynq
'''
(ROOT / 'build/create_audio_pitch_dma.tcl').write_text(header + s + '\n', encoding='utf-8', newline='\n')
record = {'part': bd['design_info']['device'], 'user_decision': 'Use A disk as hardware authority', 'matched_ps_parameters': len(old), 'differences': differences, 'vendor_bd': str(bd_path), 'vendor_bd_sha256': hashlib.sha256(bd_path.read_bytes()).hexdigest(), 'vendor_xdc_sha256': hashlib.sha256(raw).hexdigest(), 'selected_constraints': len(lines)}
(ROOT / 'report/vendor_audio_audit.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Prepared {len(old)} matching PS parameters and {len(lines)} A-disk constraints')
