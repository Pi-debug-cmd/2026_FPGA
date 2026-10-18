import json
from pathlib import Path
BD=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
ps=json.loads(BD.read_text(encoding="utf-8"))["design"]["components"]["processing_system7_0"]["parameters"]
# show full structure of a few params
for k in ["PCW_MIO_TREE_SIGNALS","PCW_I2C0_BASEADDR","PCW_ACT_APU_PERIPHERAL_FREQMHZ","PCW_UART0_PERIPHERAL_ENABLE"]:
    print(k, json.dumps(ps.get(k), indent=1))
