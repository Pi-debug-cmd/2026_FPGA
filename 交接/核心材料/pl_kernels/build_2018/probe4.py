import json
from pathlib import Path
bd=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
d=json.loads(bd.read_text(encoding="utf-8"))["design"]
print("=== interface_nets (AXI/interface level) ===")
for name,net in d["interface_nets"].items():
    ports=net.get("ports",[])
    print(f"{name}: {ports}")
