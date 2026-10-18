import json
from pathlib import Path
bd=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
d=json.loads(bd.read_text(encoding="utf-8"))["design"]
print("=== interface_net audio_M00_AXI ===")
print(json.dumps(d["interface_nets"]["audio_M00_AXI"], indent=2))
print("=== first net ===")
k=list(d["nets"].keys())[0]
print(k, json.dumps(d["nets"][k], indent=2))
