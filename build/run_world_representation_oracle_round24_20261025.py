"""WORLD representation oracle for the exposed target Track 9 (Round 24)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import numpy as np  # noqa: E402
from scipy.fft import dct, idct  # noqa: E402


VARIANTS = ((60, 12), (120, 24), (180, 48))


def limit(signal: np.ndarray) -> tuple[np.ndarray, float]:
    peak = float(np.max(np.abs(signal)))
    if peak > 0.98:
        signal = signal * (0.98 / peak)
    return signal.astype(np.float32), peak


def reconstruct(spectrum: np.ndarray, aperiodicity: np.ndarray,
                sp_dim: int, ap_dim: int) -> tuple[np.ndarray, np.ndarray, dict]:
    log_spectrum = np.log(np.maximum(spectrum, 1e-8))
    energy = log_spectrum.mean(axis=1, keepdims=True)
    centered = log_spectrum - energy
    sp_code = dct(centered, type=2, axis=1, norm="ortho")[:, :sp_dim]
    sp_full = np.zeros_like(log_spectrum)
    sp_full[:, :sp_dim] = sp_code
    decoded_log_spectrum = idct(sp_full, type=2, axis=1, norm="ortho") + energy
    decoded_spectrum = np.exp(decoded_log_spectrum)

    clipped_ap = np.clip(aperiodicity, 1e-5, 1.0 - 1e-5)
    ap_logit = np.log(clipped_ap / (1.0 - clipped_ap))
    ap_code = dct(ap_logit, type=2, axis=1, norm="ortho")[:, :ap_dim]
    ap_full = np.zeros_like(ap_logit)
    ap_full[:, :ap_dim] = ap_code
    decoded_logit = idct(ap_full, type=2, axis=1, norm="ortho")
    decoded_ap = 1.0 / (1.0 + np.exp(-np.clip(decoded_logit, -15.0, 15.0)))
    decoded_ap = np.clip(decoded_ap, 0.001, 0.999999)
    diagnostics = {
        "sp_dim": sp_dim, "ap_dim": ap_dim,
        "log_spectrum_mae": float(np.mean(np.abs(decoded_log_spectrum - log_spectrum))),
        "aperiodicity_mae": float(np.mean(np.abs(decoded_ap - aperiodicity))),
    }
    return decoded_spectrum, decoded_ap, diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/generated/world_representation_round24_20261025")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.asset_root / "人物音频资料/女声/Track 9.wav"
    signal = base.read_16k(source)
    world = base.analyze_world(signal)
    f0 = np.ascontiguousarray(world["f0"], dtype=np.float64)
    spectrum = np.ascontiguousarray(world["spectrum"], dtype=np.float64)
    aperiodicity = np.ascontiguousarray(world["aperiodicity"], dtype=np.float64)

    outputs = []
    full = base.pyworld.synthesize(f0, spectrum, aperiodicity, base.SAMPLE_RATE,
                                   frame_period=base.FRAME_PERIOD_MS)
    full, full_peak = limit(full)
    full_path = args.output / "track9_full_world.wav"
    base.sf.write(full_path, full, base.SAMPLE_RATE, subtype="PCM_16")
    outputs.append({"candidate": "track9_full_world",
                    "path": "build/generated/world_representation_round24_20261025/track9_full_world.wav",
                    "sha256": base.sha256(full_path), "peak_before_limit": full_peak,
                    "representation": "full 513-bin SP + full 513-bin AP"})

    for sp_dim, ap_dim in VARIANTS:
        decoded_sp, decoded_ap, diagnostics = reconstruct(spectrum, aperiodicity, sp_dim, ap_dim)
        audio = base.pyworld.synthesize(
            f0, np.ascontiguousarray(decoded_sp, dtype=np.float64),
            np.ascontiguousarray(decoded_ap, dtype=np.float64), base.SAMPLE_RATE,
            frame_period=base.FRAME_PERIOD_MS)
        audio, peak = limit(audio)
        name = f"track9_sp{sp_dim}_ap{ap_dim}"
        path = args.output / f"{name}.wav"
        base.sf.write(path, audio, base.SAMPLE_RATE, subtype="PCM_16")
        outputs.append({"candidate": name,
                        "path": f"build/generated/world_representation_round24_20261025/{name}.wav",
                        "sha256": base.sha256(path), "peak_before_limit": peak,
                        **diagnostics})

    summary = {"task": "PS-20261021-10", "round": 24,
               "kind": "world_representation_oracle", "source": str(source),
               "source_sha256": base.sha256(source), "track9_already_exposed": True,
               "same_track_true_f0_vuv_energy": True, "hubert_used": False,
               "mapper_used": False, "outputs": outputs,
               "played": False, "board_touched": False}
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {"kind": "world_representation_oracle",
                "inputs": [{"role": "source", "path": "人物音频资料/女声/Track 9.wav"}],
                "outputs": [{"candidate": row["candidate"], "path": row["path"]}
                            for row in outputs]}
    (args.output / "strict_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
