"""Extract PS7 config and audio subsystem from the 2022.2 BD JSON, emit TCL."""
import json
from pathlib import Path

BD = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\vendor_base_2022_2\zynq7020.srcs\sources_1\bd\zynq\zynq.bd")
OUT = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\pl_kernels\build_2018")
OUT.mkdir(parents=True, exist_ok=True)

design = json.loads(BD.read_text(encoding="utf-8"))["design"]
comps = design["components"]

import json, re
from pathlib import Path

# ---- PS7 ---- (braces avoid all TCL substitution; values have no braces)
# Exclude auto-derived parameters (the IP recomputes them).
DERIVED = [r"^PCW_MIO_TREE_", r"^PCW_ACT_", r"BASEADDR$", r"HIGHADDR$",
           r"^PCW_UIPARAM_DDR_CLOCK_", r"^PCW_UIPARAM_DDR_CLOCK_STOP_EN"]
ps = comps["processing_system7_0"]["parameters"]
items = []
for k, v in ps.items():
    if any(re.search(p, k) for p in DERIVED):
        continue
    val = v["value"] if isinstance(v, dict) else v
    assert "{" not in val and "}" not in val, (k, val)
    items.append(f"CONFIG.{k} {{{val}}}")
tcl = "set ps_cfg [list \\\n  " + " \\\n  ".join(items) + " \\\n]\n"
(OUT/"ps7_config.tcl").write_text(tcl, encoding="utf-8")
print("PS7 settable params:", len(items))

# ---- audio hierarchy internal components ----
audio_comps = comps["audio"]["components"]
audio_info = {}
for name, c in audio_comps.items():
    v = c.get("vlnv", "")
    cfg = {k: (vv["value"] if isinstance(vv, dict) else vv) for k, vv in c.get("parameters", {}).items()}
    audio_info[name] = dict(vlnv=v, config=cfg)
# also top-level axi_iic
iic = comps["axi_iic_0"]
audio_info["axi_iic_0"] = dict(vlnv=iic["vlnv"],
    config={k:(vv["value"] if isinstance(vv,dict) else vv) for k,vv in iic.get("parameters",{}).items()})
(OUT/"audio_info.json").write_text(json.dumps(audio_info, indent=2, ensure_ascii=False), encoding="utf-8")
print("audio IPs:", list(audio_info.keys()))
