"""One-time prep: resample train/validation pairs and target anchors to 16k mono."""
import json, hashlib
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from math import gcd

BASE = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020")
B2026 = BASE / "board_budget_20261005"
OUT = B2026 / "full_train_corpus_16k"
(OUT / "src").mkdir(parents=True, exist_ok=True)
(OUT / "tch").mkdir(parents=True, exist_ok=True)

def read16(path):
    x, sr = sf.read(path, dtype="float32")
    x = x.mean(axis=1) if x.ndim == 2 else x
    if sr != 16000:
        g = gcd(sr, 16000)
        x = resample_poly(x, 16000//g, sr//g).astype("float32")
    return x

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def pairs(manifest):
    doc = json.loads(Path(manifest).read_text(encoding="utf-8"))
    assert doc["complete"]
    return doc["files"]

def emit(rows, split_tag):
    entries = []
    for r in rows:
        stem = Path(r["filename"]).stem
        x = read16(r["path"])
        y = read16(r["teacher_path"])
        # align teacher to source length (teacher is CV3, <=100ms difference)
        if len(y) < len(x):
            y = np.pad(y, (0, len(x)-len(y)))
        else:
            y = y[:len(x)]
        sp = OUT/"src"/(stem+".f32"); tp = OUT/"tch"/(stem+".f32")
        sp.write_bytes(x.astype("<f4").tobytes())
        tp.write_bytes(y.astype("<f4").tobytes())
        entries.append(dict(stem=stem, speaker=r["speaker"], split=split_tag,
                            src=str(sp), tch=str(tp), n=len(x),
                            src_sha=sha(sp), tch_sha=sha(tp),
                            text=r.get("text","")))
    return entries

train_rows = pairs(B2026/"student_corpus_expanded"/"paired_manifest.json")
val_rows = pairs(B2026/"student_corpus"/"paired_manifest.json")
train = emit(train_rows, "train")
val = emit([r for r in val_rows if r["split"]=="validation"], "validation")

# target anchors Track5-8 (16k)
(OUT/"anchor").mkdir(exist_ok=True)
anchors=[]
for i in range(5,9):
    p = Path(r"D:\总进度\目标人物语音")/("Track "+str(i)+".wav")
    x = read16(p); ap = OUT/"anchor"/("track"+str(i)+".f32")
    ap.write_bytes(x.astype("<f4").tobytes())
    anchors.append(dict(track=i, path=str(ap), n=len(x), sha=sha(ap)))

manifest = dict(complete=True, train=train, validation=val, anchors=anchors,
                train_pairs=len(train), val_pairs=len(val),
                target_track9_used=False, sr=16000)
(OUT/"manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print("PREP_DONE train", len(train), "val", len(val), "anchors", len(anchors), flush=True)
