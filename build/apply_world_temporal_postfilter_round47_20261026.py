"""Apply the frozen Round-46 gain to Round-37 Track-9 reconstruction."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import audit_source_prosody_round32_20261025 as prosody_audit  # noqa: E402
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import train_paired_hubert_world_gru_round26_20261025 as paired  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


VUV_INDEX = paired.VUV_INDEX
NON_F0 = (slice(0, base.SP_DIM),
          slice(base.SP_DIM + 2, base.SP_DIM + 3),
          slice(base.SP_DIM + 3, base.OUTPUT_DIM))


def interpolate(values: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(values), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, values[:, column])
                     for column in range(values.shape[1])], axis=1).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--generated-root", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--gain", type=float, default=1.4)
    parser.add_argument("--gains", nargs="+", type=float)
    parser.add_argument("--source-detail-alphas", nargs="+", type=float)
    parser.add_argument("--source-detail-cutoffs", nargs="+", type=int)
    parser.add_argument("--source-residual-alphas", nargs="+", type=float)
    parser.add_argument("--source-residual-cutoff", type=int, default=8)
    parser.add_argument("--source-vuv-alphas", nargs="+", type=float)
    parser.add_argument("--experiment-round", type=int, default=47)
    parser.add_argument("--source-relative", default="人物音频资料/女声/Track 9.wav")
    parser.add_argument("--candidate-label")
    args = parser.parse_args()
    gains = tuple(args.gains) if args.gains else (args.gain,)
    if any(gain < 1.0 for gain in gains) or len(set(gains)) != len(gains):
        raise ValueError("postfilter gains must be unique and at least 1.0")
    if args.source_detail_alphas and (source_detail_invalid := any(
            alpha < 0.0 or alpha > 1.0 for alpha in args.source_detail_alphas)):
        raise ValueError(f"source detail alphas must be in [0, 1]: {source_detail_invalid}")
    if args.source_detail_cutoffs and (not args.source_detail_alphas
                                       or len(args.source_detail_alphas) != 1
                                       or any(cutoff < 1 or cutoff >= base.SP_DIM
                                              for cutoff in args.source_detail_cutoffs)):
        raise ValueError("cutoff sweep requires one alpha and cutoffs within spectrum DCT")
    if args.source_residual_alphas and (any(alpha < 0.0 or alpha > 1.0
                                             for alpha in args.source_residual_alphas)
                                        or args.source_residual_cutoff < 1
                                        or args.source_residual_cutoff >= base.SP_DIM):
        raise ValueError("source residual settings are outside the supported range")
    if args.source_vuv_alphas and (any(alpha < 0.0 or alpha > 1.0
                                        for alpha in args.source_vuv_alphas)
                                   or len(set(args.source_vuv_alphas)) != len(args.source_vuv_alphas)):
        raise ValueError("source VUV alphas must be unique and in [0, 1]")
    args.output.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(4)
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if checkpoint["format"] != "paired_hubert_world_causal_gru_round37_variance_matching_v1":
        raise ValueError("Round47 requires the frozen Round37 checkpoint")
    model = paired.ProsodyCausalWorldGRU().eval()
    model.load_state_dict(checkpoint["model"])

    hubert_dir = args.asset_root / "交接/核心材料/neural_reference/RVC/assets/hubert_base"
    hubert = base.HubertModel.from_pretrained(hubert_dir, local_files_only=True).float().eval()
    source_is_track9 = args.source_relative == "人物音频资料/女声/Track 9.wav"
    source_signal = base.read_16k(args.asset_root / args.source_relative)
    source_content = base.extract_hubert(hubert, source_signal)
    source_world = base.analyze_world(source_signal)
    source_x = (((source_content - checkpoint["pca_mean"]) @ checkpoint["pca_projection"]
                 - checkpoint["x_mean"]) / checkpoint["x_std"]).astype(np.float32)
    source_prosody = prosody_audit.resample_rows(
        prosody_audit.source_prosody(source_signal), len(source_content))
    source_x = np.concatenate((source_x, ((source_prosody - checkpoint["prosody_mean"])
                              / checkpoint["prosody_std"]).astype(np.float32)), axis=1)
    with torch.inference_mode():
        raw = model(torch.from_numpy(source_x[None]))[0].numpy()
    continuous = raw * checkpoint["y_std"] + checkpoint["y_mean"]
    probability = 1.0 / (1.0 + np.exp(-np.clip(raw[:, VUV_INDEX], -20.0, 20.0)))

    anchor_targets = []
    anchor_worlds = []
    for number in (5, 6, 7, 8):
        signal = base.read_16k(args.asset_root / f"人物音频资料/女声/Track {number}.wav")
        content = base.extract_hubert(hubert, signal)
        world = base.analyze_world(signal)
        anchor_worlds.append(world)
        anchor_targets.append(interpolate(world["output"], len(content)))
    del hubert
    anchor_y = np.concatenate(anchor_targets)
    clip_lo = np.percentile(anchor_y, 0.1, axis=0)
    clip_hi = np.percentile(anchor_y, 99.9, axis=0)
    voiced = anchor_y[:, VUV_INDEX] > 0.5
    log_sp = np.log(np.maximum(np.concatenate(
        [row["spectrum"] for row in anchor_worlds]), 1e-8))
    stats = {"log_f0_lo": float(np.percentile(anchor_y[voiced, base.SP_DIM], 0.5)),
             "log_f0_hi": float(np.percentile(anchor_y[voiced, base.SP_DIM], 99.5)),
             "log_sp_lo": float(np.percentile(log_sp, 0.05)),
             "log_sp_hi": float(np.percentile(log_sp, 99.95))}

    outputs = []
    label = args.candidate_label or f"round{args.experiment_round}_non_f0_gain{str(args.gain).replace('.', '_')}"
    if args.source_vuv_alphas:
        variants = tuple((f"round{args.experiment_round}_source_vuv{str(alpha).replace('.', '_')}",
                          args.gain, 0.0, 20, 0.0, alpha) for alpha in args.source_vuv_alphas)
    elif args.source_residual_alphas:
        variants = tuple((f"round{args.experiment_round}_source_residual{str(alpha).replace('.', '_')}",
                          args.gain, 0.0, 20, alpha, 0.0) for alpha in args.source_residual_alphas)
    elif args.source_detail_cutoffs:
        alpha = args.source_detail_alphas[0]
        variants = tuple((f"round{args.experiment_round}_source_cutoff{cutoff}",
                          args.gain, alpha, cutoff, 0.0, 0.0) for cutoff in args.source_detail_cutoffs)
    elif args.source_detail_alphas:
        variants = tuple((f"round{args.experiment_round}_source_detail{str(alpha).replace('.', '_')}",
                          args.gain, alpha, 20, 0.0, 0.0) for alpha in args.source_detail_alphas)
    elif args.gains:
        variants = tuple((f"round{args.experiment_round}_fixed_male_gain{str(gain).replace('.', '_')}",
                          gain, 0.0, 20, 0.0, 0.0) for gain in gains)
    else:
        variants = (("round37_baseline", 1.0, 0.0, 20, 0.0, 0.0),
                    (label, args.gain, 0.0, 20, 0.0, 0.0)) if source_is_track9 else ((label, args.gain, 0.0, 20, 0.0, 0.0),)
    for (name, gain, source_detail_alpha, source_detail_cutoff,
         source_residual_alpha, source_vuv_alpha) in variants:
        filtered = continuous.copy()
        if gain != 1.0:
            for group in NON_F0:
                center = np.mean(filtered[:, group], axis=0, keepdims=True)
                filtered[:, group] = center + gain * (filtered[:, group] - center)
        features5 = interpolate(filtered, len(source_world["output"]))
        features5 = np.clip(features5, clip_lo, clip_hi)
        if source_detail_alpha:
            region = slice(source_detail_cutoff, base.SP_DIM)
            features5[:, region] = (
                (1.0 - source_detail_alpha) * features5[:, region]
                + source_detail_alpha * source_world["output"][:, region])
            features5 = np.clip(features5, clip_lo, clip_hi)
        if source_residual_alpha:
            region = slice(args.source_residual_cutoff, base.SP_DIM)
            source_block = source_world["output"][:, region]
            source_residual = source_block - np.mean(source_block, axis=0, keepdims=True)
            features5[:, region] += source_residual_alpha * source_residual
            features5 = np.clip(features5, clip_lo, clip_hi)
        predicted_vuv = interpolate(probability[:, None], len(features5))[:, 0]
        source_vuv = source_world["output"][:, VUV_INDEX]
        blended_vuv = (1.0 - source_vuv_alpha) * predicted_vuv + source_vuv_alpha * source_vuv
        features5[:, VUV_INDEX] = (blended_vuv - 0.5) * 8.0
        waveform, synthesis = base.synthesize(features5, stats)
        path = args.output / f"{name}.wav"
        base.sf.write(path, waveform, base.SAMPLE_RATE, subtype="PCM_16")
        outputs.append({"candidate": name,
                        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": base.sha256(path), "gain": gain,
                        "source_detail_alpha": source_detail_alpha,
                        "source_detail_cutoff": source_detail_cutoff,
                        "source_residual_alpha": source_residual_alpha,
                        "source_residual_cutoff": args.source_residual_cutoff,
                        "source_vuv_alpha": source_vuv_alpha,
                        "synthesis": synthesis})

    baseline_bit_identical = None
    if source_is_track9:
        frozen = args.generated_root / "hubert_world_round37_20261025/track9_paired_causal_gru_variance_matching.wav"
        baseline_bit_identical = outputs[0]["sha256"] == base.sha256(frozen)
        if not baseline_bit_identical:
            raise ValueError("Round37 baseline is not bit-identical")
    manifest = {"inputs": [{"role": "source", "path": args.source_relative}],
                "outputs": [{"candidate": row["candidate"], "path": row["path"]}
                            for row in outputs]}
    (args.output / "strict_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"task": "PS-20261021-10", "round": args.experiment_round,
               "kind": "frozen_non_f0_gain_track9_regression",
               "gain": args.gain if not args.gains else None, "gains": list(gains),
               "source_detail_alphas": args.source_detail_alphas,
               "source_detail_cutoffs": args.source_detail_cutoffs,
               "source_residual_alphas": args.source_residual_alphas,
               "source_residual_cutoff": args.source_residual_cutoff,
               "source_vuv_alphas": args.source_vuv_alphas,
               "checkpoint_sha256": base.sha256(args.checkpoint),
               "baseline_bit_identical": baseline_bit_identical, "outputs": outputs,
               "source_relative": args.source_relative,
               "track9_used_after_freeze": source_is_track9,
               "track9_used_for_selection": False,
               "fixed_male_used": not source_is_track9, "played": False,
               "board_touched": False, "board_powered": False}
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
