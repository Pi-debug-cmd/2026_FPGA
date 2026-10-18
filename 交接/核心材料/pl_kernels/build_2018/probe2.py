import json
from pathlib import Path
bd=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
d=json.loads(bd.read_text(encoding="utf-8"))["design"]
def show(comps, prefix=""):
    for name,c in comps.items():
        v=c.get("vlnv","(hierarchy)")
        print(f"{prefix}{name}: {v}")
        if "components" in c:
            show(c["components"], prefix+"  ")
show(d["components"])
