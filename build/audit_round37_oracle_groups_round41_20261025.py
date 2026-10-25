"""Attribute Round-37 Track-9 naturalness loss with non-deployable WORLD group oracles."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import audit_source_prosody_round32_20261025 as prosody_audit  # noqa: E402
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import train_paired_hubert_world_gru_round26_20261025 as train  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


def interpolate(values: np.ndarray, frames: int) -> np.ndarray:
    source = np.linspace(0.0, 1.0, len(values), dtype=np.float64)
    target = np.linspace(0.0, 1.0, frames, dtype=np.float64)
    return np.stack([np.interp(target, source, values[:, column])
                     for column in range(values.shape[1])], axis=1).astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True, type=Path)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split-f0-vuv", action="store_true",
                        help="Round 42: isolate log-F0 and VUV from the joint oracle")
    args = parser.parse_args()
    args.checkpoint = args.checkpoint.resolve()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    torch.set_num_threads(4)

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    expected_format = "paired_hubert_world_causal_gru_round37_variance_matching_v1"
    if checkpoint["format"] != expected_format or not checkpoint["source_prosody"]:
        raise ValueError("not the frozen Round-37 source-prosody checkpoint")
    model = train.ProsodyCausalWorldGRU().eval()
    model.load_state_dict(checkpoint["model"])

    signal9 = base.read_16k(args.asset_root / "人物音频资料/女声/Track 9.wav")
    hubert_dir = args.asset_root / "交接/核心材料/neural_reference/RVC/assets/hubert_base"
    hubert = base.HubertModel.from_pretrained(hubert_dir, local_files_only=True).float().eval()
    content9 = base.extract_hubert(hubert, signal9)
    world9 = base.analyze_world(signal9)
    x9 = (((content9 - checkpoint["pca_mean"]) @ checkpoint["pca_projection"]
           - checkpoint["x_mean"]) / checkpoint["x_std"]).astype(np.float32)
    prosody9 = prosody_audit.resample_rows(prosody_audit.source_prosody(signal9), len(content9))
    x9 = np.concatenate((x9, ((prosody9 - checkpoint["prosody_mean"])
                              / checkpoint["prosody_std"]).astype(np.float32)), axis=1)
    with torch.inference_mode():
        raw = model(torch.from_numpy(x9[None]))[0].numpy()
    continuous = raw * checkpoint["y_std"] + checkpoint["y_mean"]
    probability = 1.0 / (1.0 + np.exp(-np.clip(raw[:, train.VUV_INDEX], -20.0, 20.0)))
    prediction = interpolate(continuous, len(world9["output"]))
    probability = interpolate(probability[:, None], len(prediction))[:, 0]

    anchor_worlds = []
    anchor_targets = []
    for number in (5, 6, 7, 8):
        signal = base.read_16k(args.asset_root / f"人物音频资料/女声/Track {number}.wav")
        content = base.extract_hubert(hubert, signal)
        world = base.analyze_world(signal)
        anchor_worlds.append(world)
        anchor_targets.append(interpolate(world["output"], len(content)))
    del hubert
    anchor_y = np.concatenate(anchor_targets)
    prediction = np.clip(prediction, np.percentile(anchor_y, 0.1, axis=0),
                         np.percentile(anchor_y, 99.9, axis=0))
    prediction[:, train.VUV_INDEX] = (probability - 0.5) * 8.0
    truth = world9["output"].copy()
    truth[:, train.VUV_INDEX] = (truth[:, train.VUV_INDEX] - 0.5) * 8.0

    voiced = anchor_y[:, train.VUV_INDEX] > 0.5
    log_sp = np.log(np.maximum(np.concatenate(
        [row["spectrum"] for row in anchor_worlds]), 1e-8))
    stats = {"log_f0_lo": float(np.percentile(anchor_y[voiced, base.SP_DIM], 0.5)),
             "log_f0_hi": float(np.percentile(anchor_y[voiced, base.SP_DIM], 99.5)),
             "log_sp_lo": float(np.percentile(log_sp, 0.05)),
             "log_sp_hi": float(np.percentile(log_sp, 99.95))}

    groups = ({"round37_baseline": (),
               "oracle_log_f0": (slice(base.SP_DIM, base.SP_DIM + 1),),
               "oracle_vuv": (slice(base.SP_DIM + 1, base.SP_DIM + 2),),
               "oracle_f0_vuv": (slice(base.SP_DIM, base.SP_DIM + 2),)}
              if args.split_f0_vuv else
              {"round37_baseline": (),
               "oracle_spectrum": (slice(0, base.SP_DIM),),
               "oracle_f0_vuv": (slice(base.SP_DIM, base.SP_DIM + 2),),
               "oracle_energy": (slice(base.SP_DIM + 2, base.SP_DIM + 3),),
               "oracle_aperiodicity": (slice(base.SP_DIM + 3, base.OUTPUT_DIM),),
               "oracle_all": (slice(0, base.OUTPUT_DIM),)})
    outputs = []
    for name, slices in groups.items():
        parameters = prediction.copy()
        for group in slices:
            parameters[:, group] = truth[:, group]
        signal, synthesis = base.synthesize(parameters, stats)
        path = args.output / f"track9_{name}.wav"
        base.sf.write(path, signal, base.SAMPLE_RATE, subtype="PCM_16")
        outputs.append({"candidate": name,
                        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": base.sha256(path), "synthesis": synthesis})

    frozen_sha = base.sha256(ROOT / "build/generated/hubert_world_round37_20261025"
                             / "track9_paired_causal_gru_variance_matching.wav")
    if outputs[0]["sha256"] != frozen_sha:
        raise ValueError("Round-37 baseline reconstruction is not bit-identical")
    manifest = {"inputs": [{"role": "source", "path": "人物音频资料/女声/Track 9.wav"}],
                "outputs": [{"candidate": row["candidate"], "path": row["path"]}
                            for row in outputs]}
    (args.output / "strict_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"task": "PS-20261021-10", "round": 42 if args.split_f0_vuv else 41,
               "kind": ("round37_f0_vuv_split_oracle"
                        if args.split_f0_vuv else "round37_world_group_oracle_attribution"),
               "checkpoint_sha256": base.sha256(args.checkpoint),
               "baseline_bit_identical": True, "outputs": outputs,
               "oracle_non_deployable": True, "played": False,
               "board_touched": False, "board_powered": False}
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
