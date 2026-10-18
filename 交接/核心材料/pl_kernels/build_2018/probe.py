import json
from pathlib import Path
bd=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
d=json.loads(bd.read_text(encoding="utf-8"))
def walk(o,p="",depth=0):
    if depth>3: return
    if isinstance(o,dict):
        for k,v in o.items():
            if k in ("components","connections","addressing"):
                print(p+"/"+k, type(v).__name__, (len(v) if hasattr(v,'__len__') else ''))
            walk(v,p+"/"+k,depth+1)
walk(d)
print("top keys:", list(d.keys()))
