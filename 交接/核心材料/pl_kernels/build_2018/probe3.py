import json
from pathlib import Path
bd=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
d=json.loads(bd.read_text(encoding="utf-8"))["design"]
print("design keys:", list(d.keys()))
for k,v in d.items():
    if k not in ("components",):
        print(k, type(v).__name__, len(v) if hasattr(v,'__len__') else '')
