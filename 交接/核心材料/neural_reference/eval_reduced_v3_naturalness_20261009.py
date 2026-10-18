"""UTMOS diagnostic for reduced student candidates on the same held-out clips."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import torch
import soundfile as sf

BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference"; BUD=BASE/"board_budget_20261005"
assets=json.loads((NR/"cross_evaluators/manifest.json").read_text(encoding="utf-8"))
asset=next(a for a in assets if a["evaluator"].startswith("UTMOS"))
assert hashlib.sha256(Path(asset["weight"]["path"]).read_bytes()).hexdigest()==asset["weight"]["sha256"]
sys.path.insert(0,asset["source_directory"])
from speechmos.utmos22.strong.model import UTMOS22Strong
torch.set_num_threads(4)
model=UTMOS22Strong()
model.load_state_dict(torch.load(asset["weight"]["path"],map_location="cpu",weights_only=True))
model=model.to("cuda").eval()
manifest=json.loads((BUD/"full_train_corpus_16k/manifest.json").read_text(encoding="utf-8"))
dirs={
 "deployed_v2":BUD/"reduced_student_v3_id16_2s/screen",
 "v3_id16_step800":BUD/"reduced_student_v3_id16_2s/screen",
 "v3_id24_step800":BUD/"reduced_student_v3_id24_2s/screen"
}
rows=[]
for e in manifest["validation"][:4]:
    for kind,d in dirs.items():
        path=d/(e["stem"]+"_"+kind+".wav")
        x,sr=sf.read(path,dtype="float32")
        assert sr==16000
        x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8)
        with torch.inference_mode():
            score=float(model(torch.tensor(x,device="cuda")[None],16000).item())
        row=dict(stem=e["stem"],kind=kind,predicted_naturalness=score,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
summary={k:float(np.mean([r["predicted_naturalness"] for r in rows if r["kind"]==k])) for k in dirs}
print("SUMMARY",json.dumps(summary,ensure_ascii=False),flush=True)
out=BUD/"reduced_student_v3_id16_2s/naturalness_screen.json"
out.write_text(json.dumps(dict(rows=rows,summary=summary,limitations=["UTMOS is an uncalibrated predictor for this Mandarin conversion task, not a listener verdict.","Same audio normalization applied to each candidate."]),ensure_ascii=False,indent=2),encoding="utf-8")
