import json
from pathlib import Path
bd=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
d=json.loads(bd.read_text(encoding="utf-8"))["design"]
audio=d["components"]["audio"]
print("=== external interface_ports ===")
for n,p in audio["interface_ports"].items():
    print(n, p.get("vlnv"), p.get("mode"))
print("=== external ports ===")
for n,p in audio["ports"].items():
    print(n, p.get("vlnv"))
print("=== internal interface_nets ===")
for n,net in audio["interface_nets"].items():
    print(n, net.get("interface_ports"))
print("=== internal nets ===")
for n,net in audio["nets"].items():
    print(n, net.get("ports"))
