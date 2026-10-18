# =====================================================================
# Minimal constraints for Wildfire ZYNQ7020: audio + PS I2C0/I2C1.
# =====================================================================

# ---- audio (WM8960 I2S) ----
set_property IOSTANDARD LVCMOS33 [get_ports MCLK]
set_property PACKAGE_PIN H17 [get_ports MCLK]
set_property IOSTANDARD LVCMOS33 [get_ports ADCLRC]
set_property PACKAGE_PIN K19 [get_ports ADCLRC]
set_property IOSTANDARD LVCMOS33 [get_ports DACLRC]
set_property PACKAGE_PIN J19 [get_ports DACLRC]
set_property IOSTANDARD LVCMOS33 [get_ports {BCLK[0]}]
set_property PACKAGE_PIN J18 [get_ports {BCLK[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports DACDAT]
set_property PACKAGE_PIN H16 [get_ports DACDAT]
set_property IOSTANDARD LVCMOS33 [get_ports ADCDAT]
set_property PACKAGE_PIN H18 [get_ports ADCDAT]

# ---- PS I2C0 (codec WM8960 @0x1a) ----
set_property IOSTANDARD LVCMOS33 [get_ports IIC_0_0_scl_io]
set_property PACKAGE_PIN N17 [get_ports IIC_0_0_scl_io]
set_property IOSTANDARD LVCMOS33 [get_ports IIC_0_0_sda_io]
set_property PACKAGE_PIN P18 [get_ports IIC_0_0_sda_io]

# ---- PS I2C1 ----
set_property IOSTANDARD LVCMOS33 [get_ports IIC_1_0_scl_io]
set_property PACKAGE_PIN P20 [get_ports IIC_1_0_scl_io]
set_property IOSTANDARD LVCMOS33 [get_ports IIC_1_0_sda_io]
set_property PACKAGE_PIN N20 [get_ports IIC_1_0_sda_io]
