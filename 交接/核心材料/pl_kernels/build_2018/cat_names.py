import json,re
from pathlib import Path
BD=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
ps=json.loads(BD.read_text(encoding="utf-8"))["design"]["components"]["processing_system7_0"]["parameters"]
names=list(ps.keys())
derived_patterns=[r"^PCW_MIO_TREE_", r"^PCW_ACT_", r"BASEADDR$", r"HIGHADDR$", r"_GRP$", r"VALIDATION", r"^PCW_.*_CLOCK_", r"^PCW_TPMU_", r"^PCW_SSP_", r"^PCW_PCAP_"]
def der(n):
    return any(re.search(p,n) for p in derived_patterns)
d=[n for n in names if der(n)]
s=[n for n in names if not der(n)]
print("derived-ish:",len(d)); print("settable-ish:",len(s))
Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\pl_kernels\build_2018\ps7_settable_names.txt").write_text("\n".join(s),encoding="utf-8")
# print the derived ones to verify
for n in d: print("D",n)
