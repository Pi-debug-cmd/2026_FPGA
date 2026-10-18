import json
from pathlib import Path
BD=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
ps=json.loads(BD.read_text(encoding="utf-8"))["design"]["components"]["processing_system7_0"]["parameters"]
for k,v in ps.items():
    val=v["value"] if isinstance(v,dict) else v
    if any(c in val for c in ["[","]","$","\\","{","}","\""]):
        print(repr(k), "=", repr(val))
