"""PS-20261025-20 v20: output-feature framewise adversarial weight 0.60.

Only auxiliary train rows fit the mapper/statistics/PCA. Auxiliary validation
selects a checkpoint. Fixed-Male 4 is the development screen; male 5 and target
Track 9 are never opened. This is a noncausal PC ceiling, not a deployment model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from math import gcd
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "build/generated"
for key, suffix in {"TEMP": "tmp", "TMP": "tmp", "HF_HOME": "hf", "TORCH_HOME": "torch",
                    "XDG_CACHE_HOME": "xdg", "PIP_CACHE_DIR": "pip"}.items():
    directory = GENERATED / "remote_ps_c_cache" / suffix
    directory.mkdir(parents=True, exist_ok=True)
    os.environ[key] = str(directory)
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")

import numpy as np
from scipy.signal import resample_poly
import soundfile as sf
import torch
from torch import nn
from transformers import HubertModel

torch.set_num_threads(4)
HUBERT_SHA = "cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5"
MANIFEST_SHA = "8e88db6e2777a331c874cfd3da948f9b86b0571acde17efbb384787ed9410e58"
CONFIG = {"seed": 20261026, "pca_dim": 96, "hidden": 192, "layers": 2,
          "bidirectional": True, "crop_frames": 192, "batch": 8,
          "steps": 2000, "check_every": 100, "patience_checks": 8,
          "learning_rate": 0.001, "delta_weight": 0.25,
          "speaker_adv_weight": 0.60, "speaker_classes": 20,
          "speaker_adv_mode": "framewise"}
DEFAULT_OUTPUT = GENERATED / "remote_ps_c_hubert_fargan_v20"
CANDIDATE = "Remote-PS-C_HuBERT_BiGRU_FARGAN_v20_output_framewise_adv060"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hubert(assets: Path) -> HubertModel:
    directory = assets / "hubert_base/hubert_base"
    if sha256(directory / "pytorch_model.bin") != HUBERT_SHA:
        raise ValueError("HuBERT SHA mismatch")
    return HubertModel.from_pretrained(directory, local_files_only=True).float().eval()


def read16(path: Path) -> np.ndarray:
    signal, rate = sf.read(path, dtype="float32", always_2d=True)
    signal = signal.mean(axis=1)
    divisor = gcd(rate, 16000)
    if rate != 16000:
        signal = resample_poly(signal, 16000 // divisor, rate // divisor)
    if not len(signal) or not np.isfinite(signal).all():
        raise ValueError(f"invalid audio: {path}")
    return signal.astype(np.float32)


def content_at_frames(model: HubertModel, signal: np.ndarray, frames: int) -> np.ndarray:
    with torch.inference_mode():
        features = model(torch.from_numpy(signal)[None], output_hidden_states=True).hidden_states[9][0].numpy()
    # HuBERT convolution: stride 320 samples, receptive field 400 samples.
    # Match each FARGAN 10 ms frame by physical time, not utterance-length warping.
    source_time = (np.arange(len(features)) * 320 + 199.5) / 16000
    frame_time = (np.arange(frames) * 160 + 79.5) / 16000
    result = np.stack([np.interp(frame_time, source_time, features[:, column])
                       for column in range(768)], axis=1).astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("nonfinite HuBERT content")
    return result


def cache(args) -> None:
    started = time.monotonic()
    corpus = args.assets / "paired_corpus_v1/paired_hubert_fargan_corpus_v1"
    path = corpus / "portable_manifest.json"
    if sha256(path) != MANIFEST_SHA:
        raise ValueError("paired corpus manifest SHA mismatch")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not manifest["complete"] or manifest["target_track9_used"]:
        raise ValueError("invalid corpus declaration")
    model = hubert(args.assets)
    records = []
    for index, row in enumerate(manifest["rows"], 1):
        files = row["assets"]
        for asset in files.values():
            if sha256(corpus / asset["path"]) != asset["sha256"]:
                raise ValueError(f"corpus checksum: {row['stem']}")
        signal = np.fromfile(corpus / files["source_pcm"]["path"], dtype="<f4")
        if files["source_pcm"]["samples_or_frames"] != files["teacher_pcm"]["samples_or_frames"]:
            raise ValueError("unequal source/teacher PCM durations require alignment review")
        target = np.fromfile(corpus / files["teacher_features"]["path"], dtype="<f4").reshape(-1, 20)
        frames = min(len(signal) // 160, len(target))
        target = target[:frames]
        destination = args.output / "cache" / (row["stem"] + ".npz")
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = content_at_frames(model, signal, frames)
        np.savez_compressed(destination, content=content.astype(np.float16), target=target)
        records.append({"stem": row["stem"], "speaker": row["speaker"], "split": row["split"],
                        "frames": frames, "discarded_teacher_tail_frames": files["teacher_features"]["samples_or_frames"] - frames,
                        "source_samples": len(signal), "cache": destination.name,
                        "cache_sha256": sha256(destination), "assets": files})
        if index == 1 or index % 10 == 0:
            print(json.dumps({"cached": index, "total": len(manifest["rows"]),
                              "elapsed_seconds": round(time.monotonic() - started, 1)}), flush=True)
    speakers = {split: sorted({r["speaker"] for r in records if r["split"] == split})
                for split in ("train", "validation")}
    assert not set(speakers["train"]) & set(speakers["validation"])
    save_json(args.output / "cache_manifest.json", {
        "task": "PS-20261025-20", "corpus_manifest_sha256": MANIFEST_SHA,
        "hubert_sha256": HUBERT_SHA, "hubert_layer": 9, "hubert_waveform_normalization": "none (shared reference convention)",
        "alignment": "HuBERT RF center (320*i+199.5)/16000 interpolated at FARGAN (160*j+79.5)/16000; edge replication; no time warp",
        "tail_rule": "min(floor(source_samples/160), teacher_feature_frames)",
        "speakers": speakers, "counts": manifest["counts"], "records": records,
        "fixed_male_used": False, "target_track9_used": False,
        "elapsed_seconds": time.monotonic() - started})


class GradientReversal(torch.autograd.Function):
    @staticmethod
    def forward(context, value, weight):
        context.weight = weight
        return value

    @staticmethod
    def backward(context, gradient):
        return -context.weight * gradient, None


def gradient_reversal(value, weight):
    return GradientReversal.apply(value, weight)


class Mapper(nn.Module):
    def __init__(self):
        super().__init__()
        self.input = nn.Sequential(nn.Linear(CONFIG["pca_dim"], CONFIG["hidden"]), nn.ReLU())
        self.gru = nn.GRU(CONFIG["hidden"], CONFIG["hidden"], CONFIG["layers"],
                          batch_first=True, bidirectional=CONFIG["bidirectional"])
        self.output = nn.Linear(CONFIG["hidden"] * 2, 20)
        self.speaker = nn.Linear(20, CONFIG["speaker_classes"])

    def forward(self, x, return_speaker=False):
        hidden = self.gru(self.input(x))[0]
        prediction = self.output(hidden)
        if not return_speaker:
            return prediction
        framewise = gradient_reversal(prediction, CONFIG["speaker_adv_weight"])
        return prediction, self.speaker(framewise)


def loss_value(prediction, target):
    reconstruction = nn.functional.smooth_l1_loss(prediction, target)
    delta = nn.functional.smooth_l1_loss(prediction[:, 1:] - prediction[:, :-1],
                                        target[:, 1:] - target[:, :-1])
    return reconstruction + CONFIG["delta_weight"] * delta


def train(args) -> None:
    started = time.monotonic()
    torch.manual_seed(CONFIG["seed"])
    rng = np.random.default_rng(CONFIG["seed"])
    cache_root = args.cache_root or args.output
    manifest = json.loads((cache_root / "cache_manifest.json").read_text(encoding="utf-8"))
    data = {split: [] for split in ("train", "validation")}
    speaker_names = sorted({row["speaker"] for row in manifest["records"] if row["split"] == "train"})
    if len(speaker_names) != CONFIG["speaker_classes"]:
        raise ValueError("unexpected training speaker count")
    speaker_to_index = {name: index for index, name in enumerate(speaker_names)}
    for row in manifest["records"]:
        path = cache_root / "cache" / row["cache"]
        if sha256(path) != row["cache_sha256"]:
            raise ValueError("cache SHA mismatch")
        with np.load(path) as item:
            x, y = item["content"].astype(np.float32), item["target"].astype(np.float32)
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("nonfinite cache")
        data[row["split"]].append((x, y, speaker_to_index.get(row["speaker"], -1)))
    train_x = np.concatenate([x for x, y, _ in data["train"]])
    mean = train_x.mean(axis=0)
    centered = train_x - mean
    eigenvalues, eigenvectors = np.linalg.eigh(centered.T @ centered / (len(centered) - 1))
    projection = eigenvectors[:, -CONFIG["pca_dim"]:][:, ::-1].copy()
    x_std = np.maximum((centered @ projection).std(axis=0), 0.01)
    train_y = np.concatenate([y for x, y, _ in data["train"]])
    y_mean, y_std = train_y.mean(axis=0), np.maximum(train_y.std(axis=0), 0.05)
    low, high = np.percentile(train_y, [0.1, 99.9], axis=0).astype(np.float32)
    statistics = {"mean": mean, "projection": projection, "x_std": x_std,
                  "y_mean": y_mean, "y_std": y_std, "low": low, "high": high}
    np.savez(args.output / "statistics.npz", **statistics)
    for split in data:
        data[split] = [(torch.from_numpy(((x - mean) @ projection / x_std).astype(np.float32)),
                        torch.from_numpy(((y - y_mean) / y_std).astype(np.float32)), speaker)
                       for x, y, speaker in data[split]]
    model = Mapper()
    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG["learning_rate"], weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, CONFIG["steps"])
    history, best_loss, best_step = [], float("inf"), 0
    crop = CONFIG["crop_frames"]
    for step in range(1, CONFIG["steps"] + 1):
        batch_x, batch_y, batch_speaker = [], [], []
        for index in rng.integers(len(data["train"]), size=CONFIG["batch"]):
            x, y, speaker = data["train"][index]
            start = int(rng.integers(max(1, len(x) - crop + 1)))
            count = min(crop, len(x))
            batch_x.append(nn.functional.pad(x[start:start+count], (0, 0, 0, crop-count)))
            batch_y.append(nn.functional.pad(y[start:start+count], (0, 0, 0, crop-count)))
            batch_speaker.append(speaker)
        model.train()
        prediction, speaker_logits = model(torch.stack(batch_x), return_speaker=True)
        reconstruction = loss_value(prediction, torch.stack(batch_y))
        labels = torch.tensor(batch_speaker, dtype=torch.long)[:, None].expand(-1, speaker_logits.shape[1])
        speaker_loss = nn.functional.cross_entropy(speaker_logits.reshape(-1, CONFIG["speaker_classes"]), labels.reshape(-1))
        loss = reconstruction + speaker_loss
        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        scheduler.step()
        if step == 1 or step % CONFIG["check_every"] == 0:
            model.eval()
            with torch.inference_mode():
                validation = float(np.mean([float(loss_value(model(x[None]), y[None]))
                                             for x, y, _ in data["validation"]]))
            record = {"step": step, "train_loss": float(loss.detach()), "validation_loss": validation,
                      "elapsed_seconds": time.monotonic() - started}
            history.append(record)
            print(json.dumps(record), flush=True)
            if validation < best_loss:
                best_loss, best_step = validation, step
                torch.save({"state_dict": model.state_dict(), "config": CONFIG,
                            "cache_manifest_sha256": sha256(cache_root / "cache_manifest.json"),
                            "step": step}, args.output / "mapper.pt")
            if step - best_step >= CONFIG["patience_checks"] * CONFIG["check_every"]:
                break
    save_json(args.output / "training.json", {
        "task": "PS-20261025-20", "config": CONFIG, "history": history,
        "best_step": best_step, "best_validation_loss": best_loss,
        "pca_explained_variance_ratio": float(eigenvalues[-CONFIG["pca_dim"]:].sum() / eigenvalues.sum()),
        "train_frames": len(train_y), "train_pairs": len(data["train"]), "validation_pairs": len(data["validation"]),
        "fit_scope": "declared auxiliary train only; no Fixed-Male or target Track WAVs",
         "speaker_adversarial": {"classes": speaker_names, "weight": CONFIG["speaker_adv_weight"],
                                  "mode": CONFIG["speaker_adv_mode"],
                                 "training_only": True, "validation_selection_excludes_classifier_loss": True},
        "parameters": sum(p.numel() for p in model.parameters()),
        "mapper_sha256": sha256(args.output / "mapper.pt"), "statistics_sha256": sha256(args.output / "statistics.npz"),
        "noncausal": True, "future_context": "bidirectional GRU and full-utterance HuBERT",
        "elapsed_seconds": time.monotonic() - started, "board_touched": False, "played": False})


def synthesize(exe: Path, feature_path: Path, output: Path) -> dict:
    subprocess.run([str(exe.resolve()), "--synthesis", str(feature_path.resolve()),
                    str(output.with_suffix(".pcm").resolve()), str(output.with_suffix(".synthesis.json").resolve())], check=True)
    pcm = np.fromfile(output.with_suffix(".pcm"), dtype="<i2")
    expected = feature_path.stat().st_size // 80 * 160
    if len(pcm) != expected or not np.any(pcm):
        raise ValueError("invalid FARGAN output")
    sf.write(output, pcm, 16000, subtype="PCM_16")
    signal = pcm.astype(np.float64) / 32768
    return {"samples": len(pcm), "peak": float(abs(signal).max()),
            "rms": float(np.sqrt(np.mean(signal ** 2))), "sha256": sha256(output),
            "clipping_fraction": float(np.mean(abs(signal) >= 32767 / 32768))}


def infer(args) -> None:
    started = time.monotonic()
    # Explicit allowlist: the first screen cannot accidentally open locked audio.
    source = ROOT / "人物音频资料/男声/标准录音 4.wav"
    signal = read16(source)
    frames = len(signal) // 160
    content = content_at_frames(hubert(args.assets), signal, frames)
    stats = dict(np.load(args.output / "statistics.npz"))
    checkpoint = torch.load(args.output / "mapper.pt", map_location="cpu", weights_only=True)
    if checkpoint["config"] != CONFIG:
        raise ValueError("mapper configuration mismatch")
    model = Mapper().eval()
    model.load_state_dict(checkpoint["state_dict"])
    x = ((content - stats["mean"]) @ stats["projection"]) / stats["x_std"]
    with torch.inference_mode():
        prediction = model(torch.from_numpy(x.astype(np.float32))[None])[0].numpy()
    features = np.clip(prediction * stats["y_std"] + stats["y_mean"], stats["low"], stats["high"])
    feature_path = args.output / "fixed_male4.features.f32"
    features.astype("<f4").tofile(feature_path)
    output = args.output / "fixed_male4.wav"
    summary = synthesize(args.native, feature_path, output)
    summary.update({"task": "PS-20261025-20", "source_sha256": sha256(source),
                    "source_samples": len(signal), "frames": frames,
                    "inference_seconds": time.monotonic() - started,
                    "rtf_host_full_chain": (time.monotonic() - started) / (len(signal) / 16000),
                    "mapper_sha256": sha256(args.output / "mapper.pt"), "native_sha256": sha256(args.native),
                    "male5_used": False, "target_track9_used": False, "played": False, "board_touched": False})
    save_json(args.output / "inference.json", summary)
    save_json(args.output / "evaluation_manifest.json", {
        "inputs": [{"role": "source", "path": source.relative_to(ROOT).as_posix()}],
        "outputs": [{"candidate": CANDIDATE,
                     "path": output.relative_to(ROOT).as_posix()}]})
    print(json.dumps(summary, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("cache", "train", "infer"))
    parser.add_argument("--assets", type=Path, default=GENERATED / "remote_ps_c_assets")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-root", type=Path, help="reuse a SHA-verified cache for training")
    parser.add_argument("--native", type=Path, default=GENERATED / "remote_ps_c_native/fargan_probe_host.exe")
    args = parser.parse_args()
    args.assets = args.assets.resolve()
    args.output = args.output.resolve()
    args.native = args.native.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    {"cache": cache, "train": train, "infer": infer}[args.stage](args)


if __name__ == "__main__":
    main()
