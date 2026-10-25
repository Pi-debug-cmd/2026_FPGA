"""Train the frozen Round-20 HuBERT-to-WORLD target-speaker oracle.

This is an offline ceiling experiment.  It trains only on target Tracks 5-8,
evaluates Track 9 exactly once after training, and never accesses audio I/O or
the board.  Large features, checkpoints, and reconstructed audio are written
under build/generated and therefore stay outside Git.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
DEPENDENCY_ROOT = Path(os.environ.get("FPGA_ASSET_ROOT", ROOT))
DEPENDENCIES = ("llvc_cpu_deps", "seed_audio_deps", "seed_cpu_deps", "world_deps")
for dependency in reversed(DEPENDENCIES):
    sys.path.insert(0, str(DEPENDENCY_ROOT / "build" / "generated" / dependency))

import numpy as np  # noqa: E402
import pyworld  # noqa: E402
from scipy.fft import dct, idct  # noqa: E402
from scipy.signal import medfilt, resample_poly  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from torch import nn  # noqa: E402
from transformers import HubertModel  # noqa: E402


SEED = 20261025
SAMPLE_RATE = 16000
FRAME_PERIOD_MS = 5.0
HUBERT_LAYER = 9
PCA_DIM = 96
CONTEXT = 2
SP_DIM = 60
AP_DIM = 12
OUTPUT_DIM = SP_DIM + 3 + AP_DIM  # spectrum, log-F0, VUV logit, energy, AP
STEPS = 2500
BATCH = 1024
HIDDEN = 384


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_16k(path: Path) -> np.ndarray:
    signal, rate = sf.read(path, dtype="float32", always_2d=True)
    mono = signal.mean(axis=1)
    if rate != SAMPLE_RATE:
        divisor = int(np.gcd(rate, SAMPLE_RATE))
        mono = resample_poly(mono, SAMPLE_RATE // divisor, rate // divisor)
    peak = float(np.max(np.abs(mono))) if len(mono) else 0.0
    if not len(mono) or not np.isfinite(mono).all() or peak == 0.0:
        raise ValueError(f"invalid audio: {path}")
    return np.ascontiguousarray(mono.astype(np.float64))


def extract_hubert(model: HubertModel, signal: np.ndarray) -> np.ndarray:
    waveform = torch.from_numpy(signal.astype(np.float32))[None]
    with torch.inference_mode():
        output = model(waveform, output_hidden_states=True)
    features = output.hidden_states[HUBERT_LAYER][0].float().cpu().numpy()
    if features.ndim != 2 or features.shape[1] != 768 or not np.isfinite(features).all():
        raise ValueError(f"invalid HuBERT feature shape: {features.shape}")
    return features.astype(np.float32)


def continuous_log_f0(f0: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    voiced = f0 > 0.0
    log_f0 = np.zeros_like(f0)
    if voiced.any():
        indices = np.arange(len(f0))
        log_f0[:] = np.interp(indices, indices[voiced], np.log(f0[voiced]))
    return log_f0, voiced.astype(np.float64)


def analyze_world(signal: np.ndarray) -> dict[str, np.ndarray]:
    f0, times = pyworld.harvest(signal, SAMPLE_RATE, frame_period=FRAME_PERIOD_MS,
                                f0_floor=55.0, f0_ceil=500.0)
    f0 = pyworld.stonemask(signal, f0, times, SAMPLE_RATE)
    spectrum = pyworld.cheaptrick(signal, f0, times, SAMPLE_RATE, fft_size=1024)
    aperiodicity = pyworld.d4c(signal, f0, times, SAMPLE_RATE, fft_size=1024)
    log_f0, voiced = continuous_log_f0(f0)
    log_spectrum = np.log(np.maximum(spectrum, 1e-8))
    energy = log_spectrum.mean(axis=1, keepdims=True)
    centered_spectrum = log_spectrum - energy
    sp_code = dct(centered_spectrum, type=2, axis=1, norm="ortho")[:, :SP_DIM]
    ap = np.clip(aperiodicity, 1e-5, 1.0 - 1e-5)
    ap_logit = np.log(ap / (1.0 - ap))
    ap_code = dct(ap_logit, type=2, axis=1, norm="ortho")[:, :AP_DIM]
    output = np.concatenate((sp_code, log_f0[:, None], voiced[:, None], energy, ap_code), axis=1)
    return {"times": times, "f0": f0, "spectrum": spectrum,
            "aperiodicity": aperiodicity, "output": output.astype(np.float32)}


def pca_fit(features: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    pooled = np.concatenate(features).astype(np.float64)
    mean = pooled.mean(axis=0)
    centered = pooled - mean
    covariance = centered.T @ centered / max(1, len(centered) - 1)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1][:PCA_DIM]
    projection = eigenvectors[:, order]
    signs = np.sign(projection[np.argmax(np.abs(projection), axis=0), np.arange(PCA_DIM)])
    projection *= np.where(signs == 0.0, 1.0, signs)
    return mean.astype(np.float32), projection.astype(np.float32)


def context_features(features: np.ndarray) -> np.ndarray:
    padded = np.pad(features, ((CONTEXT, CONTEXT), (0, 0)), mode="edge")
    return np.concatenate([padded[index:index + len(features)]
                           for index in range(2 * CONTEXT + 1)], axis=1)


def align_content(features: np.ndarray, mean: np.ndarray, projection: np.ndarray,
                  world_frames: int) -> np.ndarray:
    reduced = (features - mean) @ projection
    reduced = context_features(reduced)
    source_position = np.linspace(0.0, 1.0, len(reduced), dtype=np.float64)
    target_position = np.linspace(0.0, 1.0, world_frames, dtype=np.float64)
    aligned = np.stack([np.interp(target_position, source_position, reduced[:, column])
                        for column in range(reduced.shape[1])], axis=1)
    return aligned.astype(np.float32)


class Mapper(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        dimension = PCA_DIM * (2 * CONTEXT + 1)
        self.net = nn.Sequential(
            nn.Linear(dimension, HIDDEN), nn.GELU(),
            nn.Linear(HIDDEN, HIDDEN), nn.GELU(),
            nn.Linear(HIDDEN, OUTPUT_DIM),
        )

    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return self.net(value)


def synthesize(prediction: np.ndarray, statistics: dict[str, np.ndarray]) -> tuple[np.ndarray, dict]:
    sp_code = prediction[:, :SP_DIM]
    log_f0 = prediction[:, SP_DIM]
    voiced_score = prediction[:, SP_DIM + 1]
    energy = prediction[:, SP_DIM + 2:SP_DIM + 3]
    ap_code = prediction[:, SP_DIM + 3:]

    full_sp = np.zeros((len(prediction), 513), dtype=np.float64)
    full_sp[:, :SP_DIM] = sp_code
    log_spectrum = idct(full_sp, type=2, axis=1, norm="ortho") + energy
    log_spectrum = np.clip(log_spectrum, statistics["log_sp_lo"], statistics["log_sp_hi"])
    spectrum = np.exp(log_spectrum)

    voiced_probability = 1.0 / (1.0 + np.exp(-np.clip(voiced_score, -20.0, 20.0)))
    voiced = medfilt((voiced_probability >= 0.5).astype(np.float64), kernel_size=5) > 0.5
    log_f0 = medfilt(np.clip(log_f0, statistics["log_f0_lo"],
                             statistics["log_f0_hi"]), kernel_size=5)
    f0 = np.where(voiced, np.exp(log_f0), 0.0)

    full_ap = np.zeros((len(prediction), 513), dtype=np.float64)
    full_ap[:, :AP_DIM] = ap_code
    ap_logit = idct(full_ap, type=2, axis=1, norm="ortho")
    aperiodicity = 1.0 / (1.0 + np.exp(-np.clip(ap_logit, -15.0, 15.0)))
    aperiodicity = np.clip(aperiodicity, 0.001, 0.999999)
    signal = pyworld.synthesize(np.ascontiguousarray(f0, dtype=np.float64),
                                np.ascontiguousarray(spectrum, dtype=np.float64),
                                np.ascontiguousarray(aperiodicity, dtype=np.float64), SAMPLE_RATE,
                                frame_period=FRAME_PERIOD_MS)
    peak = float(np.max(np.abs(signal)))
    if peak > 0.98:
        signal *= 0.98 / peak
    return signal.astype(np.float32), {
        "voiced_fraction": float(voiced.mean()), "f0_voiced_median_hz":
        float(np.median(f0[voiced])) if voiced.any() else None,
        "peak_before_limit": peak,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/hubert_world_round20_20261025")
    parser.add_argument("--steps", type=int, default=STEPS)
    args = parser.parse_args()
    started = time.monotonic()
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    args.output.mkdir(parents=True, exist_ok=True)

    target_dir = args.asset_root / "人物音频资料/女声"
    paths = {number: target_dir / f"Track {number}.wav" for number in range(5, 10)}
    hubert_dir = args.asset_root / "交接/核心材料/neural_reference/RVC/assets/hubert_base"
    weight = hubert_dir / "pytorch_model.bin"
    expected = "cc8c20f4b90a520757260197a3ff2505705a7adbd20ad9eeaa4e1a9b38442ef5"
    if sha256(weight) != expected:
        raise ValueError("HuBERT checkpoint SHA-256 mismatch")
    model = HubertModel.from_pretrained(hubert_dir, local_files_only=True).float().eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)

    train_numbers = (5, 6, 7, 8)
    rows = {}
    for number in train_numbers:
        path = paths[number]
        signal = read_16k(path)
        content = extract_hubert(model, signal)
        world = analyze_world(signal)
        rows[number] = {"path": path, "signal": signal, "content": content, "world": world}
        print(json.dumps({"track": number, "samples": len(signal),
                          "hubert_frames": len(content), "world_frames": len(world["output"])},
                         ensure_ascii=False), flush=True)
    mean, projection = pca_fit([rows[number]["content"] for number in train_numbers])
    for row in rows.values():
        row["input"] = align_content(row["content"], mean, projection,
                                      len(row["world"]["output"]))

    train_x = np.concatenate([rows[number]["input"] for number in train_numbers])
    train_y = np.concatenate([rows[number]["world"]["output"] for number in train_numbers])
    y_mean = train_y.mean(axis=0)
    y_std = np.maximum(train_y.std(axis=0), 0.05)
    train_z = (train_y - y_mean) / y_std
    clip_lo = np.percentile(train_y, 0.1, axis=0)
    clip_hi = np.percentile(train_y, 99.9, axis=0)
    voiced_train = train_y[:, SP_DIM + 1] > 0.5
    log_f0_train = train_y[voiced_train, SP_DIM]
    log_sp_train = np.log(np.maximum(np.concatenate(
        [rows[number]["world"]["spectrum"] for number in train_numbers]), 1e-8))
    synthesis_stats = {
        "log_f0_lo": float(np.percentile(log_f0_train, 0.5)),
        "log_f0_hi": float(np.percentile(log_f0_train, 99.5)),
        "log_sp_lo": float(np.percentile(log_sp_train, 0.05)),
        "log_sp_hi": float(np.percentile(log_sp_train, 99.95)),
    }

    mapper = Mapper()
    optimizer = torch.optim.AdamW(mapper.parameters(), lr=1.0e-3, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, args.steps)
    rng = np.random.default_rng(SEED)
    history = []
    for step in range(1, args.steps + 1):
        indices = rng.integers(0, len(train_x), size=BATCH)
        x = torch.from_numpy(train_x[indices])
        target = torch.from_numpy(train_z[indices])
        prediction = mapper(x)
        weight_vector = torch.ones(OUTPUT_DIM)
        weight_vector[SP_DIM:SP_DIM + 3] = torch.tensor([2.0, 1.5, 1.0])
        loss = torch.mean(torch.nn.functional.smooth_l1_loss(
            prediction, target, reduction="none") * weight_vector)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(mapper.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        if step == 1 or step % 100 == 0:
            record = {"step": step, "loss": float(loss.detach()),
                      "learning_rate": optimizer.param_groups[0]["lr"]}
            history.append(record)
            print(json.dumps(record), flush=True)

    checkpoint = args.output / "hubert_world_teacher.pt"
    torch.save({"format": "hubert_world_teacher_round20_v1", "seed": SEED,
                "model": mapper.state_dict(), "pca_mean": mean, "pca_projection": projection,
                "output_mean": y_mean, "output_std": y_std, "clip_lo": clip_lo,
                "clip_hi": clip_hi, "synthesis_stats": synthesis_stats}, checkpoint)

    # Track 9 is first decoded here, after the fixed training loop is complete.
    heldout_signal = read_16k(paths[9])
    heldout_content = extract_hubert(model, heldout_signal)
    heldout_world = analyze_world(heldout_signal)
    heldout = {"path": paths[9], "signal": heldout_signal,
               "content": heldout_content, "world": heldout_world}
    heldout["input"] = align_content(heldout_content, mean, projection,
                                      len(heldout_world["output"]))
    del model
    print(json.dumps({"track": 9, "samples": len(heldout_signal),
                      "hubert_frames": len(heldout_content),
                      "world_frames": len(heldout_world["output"])}, ensure_ascii=False),
          flush=True)
    with torch.inference_mode():
        predicted_z = mapper(torch.from_numpy(heldout["input"])).numpy()
    predicted = predicted_z * y_std + y_mean
    predicted = np.clip(predicted, clip_lo, clip_hi)
    vuv_probability = predicted[:, SP_DIM + 1].copy()
    # The mapper regresses VUV as a probability-like value.  WORLD synthesis
    # expects the field consumed below to have a zero decision boundary, so
    # convert p=0.5 to logit zero instead of feeding clipped [0, 1] values
    # (which would incorrectly mark every frame voiced).
    predicted[:, SP_DIM + 1] = (vuv_probability - 0.5) * 8.0
    reconstructed, synthesis = synthesize(predicted, synthesis_stats)
    wav_path = args.output / "track9_hubert_world_reconstruction.wav"
    sf.write(wav_path, reconstructed, SAMPLE_RATE, subtype="PCM_16")
    truth = heldout["world"]["output"]
    mae = np.mean(np.abs(predicted - truth), axis=0)
    vuv_mae = float(np.mean(np.abs(vuv_probability - truth[:, SP_DIM + 1])))
    summary = {
        "task": "PS-20261021-10", "round": 20,
        "kind": "frozen_hubert_to_world_target_speaker_oracle",
        "seed": SEED, "steps": args.steps, "train_tracks": list(train_numbers),
        "heldout_track": 9, "track9_first_used_after_training": True,
        "source_audio_used_for_training": False, "source_spectrum_skip": False,
        "hubert": {"layer": HUBERT_LAYER, "pca_dim": PCA_DIM,
                   "checkpoint_sha256": expected, "deployed_to_board": False},
        "world": {"sample_rate": SAMPLE_RATE, "frame_period_ms": FRAME_PERIOD_MS,
                  "fft_size": 1024, "spectrum_dct_dim": SP_DIM,
                  "aperiodicity_dct_dim": AP_DIM},
        "model_parameters": sum(parameter.numel() for parameter in mapper.parameters()),
        "training_frames": len(train_x), "heldout_frames": len(truth),
        "heldout_mae": {"spectrum_dct_mean": float(mae[:SP_DIM].mean()),
                         "log_f0": float(mae[SP_DIM]),
                         "vuv_probability": vuv_mae,
                         "energy": float(mae[SP_DIM + 2]),
                         "aperiodicity_dct_mean": float(mae[SP_DIM + 3:].mean())},
        "synthesis": synthesis,
        "input_sha256": {str(number): sha256(paths[number]) for number in paths},
        "checkpoint_sha256": sha256(checkpoint), "reconstruction_sha256": sha256(wav_path),
        "history": history, "elapsed_seconds": time.monotonic() - started,
        "objective_gate_evaluated": False,
        "notes": ["Track 9 was excluded from PCA, normalization, clipping bounds, and training.",
                  "HuBERT and the non-causal teacher mapper are PC-only quality-ceiling components."]
    }
    summary_path = args.output / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
