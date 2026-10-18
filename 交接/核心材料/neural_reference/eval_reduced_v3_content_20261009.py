"""Independent Whisper-small content screen; diagnostic, never human pronunciation approval."""
from pathlib import Path
import sys,json,re,hashlib
import numpy as np
import torch
import soundfile as sf
from transformers import WhisperProcessor,WhisperForConditionalGeneration
from opencc import OpenCC

BASE=Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
NR=BASE/"neural_reference";BUD=BASE/"board_budget_20261005"
MODEL=NR/"cache/hf/hub/models--openai--whisper-small/snapshots/973afd24965f72e36ca33b3055d56a652f456b4d"
OUT=BUD/"reduced_student_v3_id24_2s"/"content_screen"
OUT.mkdir(exist_ok=True)
MAN=json.loads((BUD/"full_train_corpus_16k/manifest.json").read_text(encoding="utf-8"))
screen=BUD/"reduced_student_v3_id24_2s"/"screen"
torch.set_num_threads(4)
processor=WhisperProcessor.from_pretrained(str(MODEL),local_files_only=True)
model=WhisperForConditionalGeneration.from_pretrained(str(MODEL),local_files_only=True,torch_dtype=torch.float16).to("cuda").eval()
model.generation_config.forced_decoder_ids=None
cc=OpenCC("t2s")
def canon(s):
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]","",cc.convert(s)).lower()
def edits(a,b):
    old=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        new=[i]
        for j,cb in enumerate(b,1):
            new.append(min(new[-1]+1,old[j]+1,old[j-1]+(ca!=cb)))
        old=new
    return old[-1]
def transcribe(wave):
    inp=processor(np.asarray(wave,dtype="float32"),sampling_rate=16000,return_tensors="pt",return_attention_mask=True)
    with torch.inference_mode():
        ids=model.generate(inp.input_features.to("cuda",dtype=torch.float16),attention_mask=inp.attention_mask.to("cuda"),language="zh",task="transcribe",num_beams=5,max_new_tokens=180)
    return processor.batch_decode(ids,skip_special_tokens=True)[0].strip()
rows=[]
for e in MAN["validation"][:4]:
    stem=e["stem"];expected=e["text"]
    paths={
      "source":e["src"],
      "teacher":e["tch"],
      "deployed_v2":str(screen/(stem+"_deployed_v2.wav")),
      "v3_id24_step800":str(screen/(stem+"_v3_id24_step800.wav"))
    }
    for kind,path in paths.items():
        if path.endswith(".f32"): wave=np.fromfile(path,dtype="<f4")
        else: wave,sr=sf.read(path,dtype="float32"); assert sr==16000
        got=transcribe(wave)
        row=dict(stem=stem,kind=kind,expected=expected,recognized=got,character_edits=edits(canon(expected),canon(got)),reference_chars=len(canon(expected)),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
        rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
fixed="我的校园很美，走近大门就能看见宽阔的操场。"
for kind,path in {
  "deployed_v2":screen/"fixed_deployed_v2.wav",
  "v3_id24_step800":screen/"fixed_v3_id24_step800.wav"
}.items():
    wave,sr=sf.read(path,dtype="float32");assert sr==16000
    got=transcribe(wave)
    row=dict(stem="fixed_campus",kind=kind,expected=fixed,recognized=got,character_edits=edits(canon(fixed),canon(got)),reference_chars=len(canon(fixed)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
summary={}
for kind in sorted(set(r["kind"] for r in rows)):
    rs=[r for r in rows if r["kind"]==kind and r["stem"]!="fixed_campus"]
    summary[kind]=dict(edits=sum(r["character_edits"] for r in rs),chars=sum(r["reference_chars"] for r in rs))
print("SUMMARY",json.dumps(summary,ensure_ascii=False),flush=True)
(OUT/"report.json").write_text(json.dumps(dict(rows=rows,summary=summary,limitations=["ASR is an independent content diagnostic, not human pronunciation or naturalness acceptance.","The four validation speakers have been used for repeated development screening."]),ensure_ascii=False,indent=2),encoding="utf-8")
