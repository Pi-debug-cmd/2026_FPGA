"""Four-metric evaluator for the fixed male->female pair.

Metrics
  identity  : WeSpeaker CN-Celeb ResNet34 cosine to the FEMALE centroid
  leakage   : WeSpeaker cosine to the MALE centroid (lower is better)
  utmos     : UTMOS22-Strong predicted naturalness (1..5)
  cer       : character error rate of whisper-small transcription vs the
              male source transcription (content preservation)

Every metric is computed on the same 16 kHz mono window. Nothing here plays or
records audio.

The evaluator weights are the same files the old project used, referenced in
place (read-only) from D:\Tools_FPGA.
"""
from __future__ import annotations

import functools
import json
import os
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parents[1]
# Evaluator weights live inside the project now; the legacy workspace under
# D:\Tools_FPGA is only a fallback. Override with FVC_ASSETS if needed.
_ASSETS = Path(os.environ.get("FVC_ASSETS", str(ROOT / "assets" / "evaluator_assets")))
_LEGACY = Path(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\neural_reference")
if not (_ASSETS / "cross_evaluators").exists():
    CROSS = _LEGACY / "cross_evaluators"
    HF_HUB = _LEGACY / "cache" / "hf" / "hub"
else:
    CROSS = _ASSETS / "cross_evaluators"
    HF_HUB = _ASSETS / "hf" / "hub"
SPEECHMOS = CROSS / "SpeechMOS-ed25eacbfa42b99156c36ebec67a733b5dbb9b79"
WESPEAKER = CROSS / "cnceleb_resnet34_LM.onnx"
UTMOS_W = CROSS / "utmos22_strong_step7459_v1.pt"

SR = 16000


def _require(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def load16(path: Path, start: float = 0.0, seconds: float | None = None) -> np.ndarray:
    x, sr = sf.read(str(path), dtype="float64", always_2d=False)
    if x.ndim == 2:
        x = x.mean(axis=1)
    if sr != SR:
        from math import gcd
        from scipy.signal import resample_poly
        g = gcd(int(sr), SR)
        x = resample_poly(x, SR // g, int(sr) // g)
    if start:
        x = x[int(round(start * SR)):]
    if seconds is not None:
        x = x[: int(round(seconds * SR))]
    return np.ascontiguousarray(x, dtype=np.float64)


def chunks(x: np.ndarray, win: int = 96000, hop: int = 96000):
    for s in range(0, len(x), hop):
        c = x[s:s + win]
        if len(c) >= 24000 and float(np.sqrt(np.mean(c * c))) >= 1e-3:
            yield s, c


class Evaluator:
    def __init__(self) -> None:
        import onnxruntime as ort
        import torchaudio

        self._torchaudio = torchaudio
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        opts.inter_op_num_threads = 1
        self.spk = ort.InferenceSession(
            str(_require(WESPEAKER)), sess_options=opts, providers=["CPUExecutionProvider"])

        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ["HF_HUB_CACHE"] = str(HF_HUB)
        os.environ["HF_HOME"] = str(HF_HUB.parent)

        sys.path.insert(0, str(SPEECHMOS))
        from speechmos.utmos22.strong.model import UTMOS22Strong
        m = UTMOS22Strong()
        m.load_state_dict(torch.load(str(_require(UTMOS_W)), map_location="cpu", weights_only=True))
        self.utmos = m.eval()

        self._whisper = None
        self._centroids: dict[str, np.ndarray] = {}

    # ---- speaker ---------------------------------------------------------
    def embed_clip(self, clip: np.ndarray) -> np.ndarray:
        ta = self._torchaudio
        rms = float(np.sqrt(np.mean(clip * clip)))
        norm = clip * 0.04 / max(rms, 1e-8)
        feat = ta.compliance.kaldi.fbank(
            torch.from_numpy(norm * 32768).unsqueeze(0).float(),
            num_mel_bins=80, frame_length=25, frame_shift=10, sample_frequency=SR,
            window_type="hamming", dither=0.0)
        feat = (feat - feat.mean(dim=0)).unsqueeze(0).numpy().astype("float32")
        v = self.spk.run(None, {"feats": feat})[0][0].astype(np.float64)
        return v / max(float(np.linalg.norm(v)), 1e-9)

    def embed(self, x: np.ndarray) -> np.ndarray:
        vecs = [self.embed_clip(c) for _, c in chunks(x)]
        if not vecs:
            raise ValueError("no usable speech chunks")
        v = np.mean(vecs, axis=0)
        return v / max(float(np.linalg.norm(v)), 1e-9)

    def centroid(self, wavs: list[Path]) -> np.ndarray:
        key = "|".join(str(w) for w in wavs)
        if key not in self._centroids:
            v = np.mean([self.embed(load16(w)) for w in wavs], axis=0)
            self._centroids[key] = v / max(float(np.linalg.norm(v)), 1e-9)
        return self._centroids[key]

    # ---- naturalness -----------------------------------------------------
    def utmos_score(self, x: np.ndarray) -> float:
        vals = []
        for _, c in chunks(x):
            t = torch.from_numpy(c.astype(np.float32)).unsqueeze(0)
            with torch.no_grad():
                vals.extend(self.utmos(t, SR).cpu().numpy().reshape(-1).tolist())
        return float(np.mean(vals)) if vals else float("nan")

    # ---- content ---------------------------------------------------------
    def transcribe(self, x: np.ndarray) -> str:
        if self._whisper is None:
            from transformers import WhisperForConditionalGeneration, WhisperProcessor
            snap = sorted((HF_HUB / "models--openai--whisper-small" / "snapshots").glob("*"))[0]
            name = str(snap)
            self._processor = WhisperProcessor.from_pretrained(name, local_files_only=True)
            self._whisper = WhisperForConditionalGeneration.from_pretrained(
                name, local_files_only=True).eval()
        if len(x) < 1600:
            return ""
        feats = self._processor(x.astype(np.float32), sampling_rate=SR,
                                return_tensors="pt").input_features
        with torch.no_grad():
            ids = self._whisper.generate(feats, language="zh", task="transcribe",
                                         max_new_tokens=225)
        return self._processor.batch_decode(ids, skip_special_tokens=True)[0].strip()


def cer(ref: str, hyp: str) -> float:
    """Character error rate with a plain Levenshtein distance."""
    r = [c for c in ref if not c.isspace()]
    h = [c for c in hyp if not c.isspace()]
    if not r:
        return float("nan")
    prev = list(range(len(h) + 1))
    for i, rc in enumerate(r, 1):
        cur = [i] + [0] * len(h)
        for j, hc in enumerate(h, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (rc != hc))
        prev = cur
    return prev[-1] / len(r)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("wav", nargs="+", type=Path)
    ap.add_argument("--label", nargs="*", default=None)
    ap.add_argument("--ref-text", default=None, help="reference transcription (male source)")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((ROOT / "data/pair16k/manifest.json").read_text(encoding="utf-8"))
    female_train = [ROOT / e["wav"] for e in man["files"]
                    if e["speaker"] == "female" and e["split"] == "train"]
    male_train = [ROOT / e["wav"] for e in man["files"]
                  if e["speaker"] == "male" and e["split"] == "train"]

    ev = Evaluator()
    fcent = ev.centroid(female_train)
    mcent = ev.centroid(male_train)

    out = []
    labels = args.label or [str(p.stem) for p in args.wav]
    for label, path in zip(labels, args.wav):
        x = load16(path)
        v = ev.embed(x)
        rec = {
            "label": label,
            "wav": str(path),
            "seconds": round(len(x) / SR, 2),
            "identity_female": round(float(v @ fcent), 4),
            "leakage_male": round(float(v @ mcent), 4),
            "utmos": round(ev.utmos_score(x), 4),
        }
        if args.ref_text:
            hyp = ev.transcribe(x)
            rec["transcript"] = hyp
            rec["cer"] = round(cer(args.ref_text, hyp), 4)
        out.append(rec)
        print(json.dumps(rec, ensure_ascii=False))

    if args.json:
        args.json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
