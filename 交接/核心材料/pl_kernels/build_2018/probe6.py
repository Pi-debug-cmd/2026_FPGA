import json
from pathlib import Path
bd=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
d=json.loads(bd.read_text(encoding="utf-8"))["design"]
print("=== ALL nets (scalar) ===")
for name,net in d["nets"].items():
    print(f"{name}: {net.get('ports')}")
print()
print("=== ALL interface_nets ===")
for name,net in d["interface_nets"].items():
    print(f"{name}: {net.get('interface_ports')}")
