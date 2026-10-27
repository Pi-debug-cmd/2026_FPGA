"""PS-20261025-20 v10: frozen v1 output with three-frame temporal smoothing."""
import argparse
import json
from pathlib import Path
import shutil
import time
import numpy as np

import remote_ps_c_hubert_fargan as experiment

experiment.DEFAULT_OUTPUT = experiment.GENERATED / "remote_ps_c_hubert_fargan_v10"
experiment.CANDIDATE = "Remote-PS-C_HuBERT_BiGRU_FARGAN_v10_temporal_smooth3"
V1_OUTPUT = experiment.GENERATED / "remote_ps_c_hubert_fargan_v1"


def infer(args):
    started = time.monotonic()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ("mapper.pt", "statistics.npz"):
        shutil.copyfile(V1_OUTPUT / name, args.output / name)
    experiment.infer(args)
    stats = dict(np.load(args.output / "statistics.npz"))
    raw = np.fromfile(args.output / "fixed_male4.features.f32", dtype="<f4").reshape(-1, 20)
    features = raw.copy()
    padded = np.pad(features, ((1, 1), (0, 0)), mode="edge")
    features = (padded[:-2] + padded[1:-1] + padded[2:]) / 3.0
    features = np.clip(features, stats["low"], stats["high"]).astype("<f4")
    features.tofile(args.output / "fixed_male4.features.f32")
    summary = experiment.synthesize(args.native, args.output / "fixed_male4.features.f32", args.output / "fixed_male4.wav")
    source = experiment.ROOT / "人物音频资料/男声/标准录音 4.wav"
    summary.update({"task": "PS-20261025-20", "candidate": experiment.CANDIDATE,
                    "source_sha256": experiment.sha256(source), "source_samples": len(experiment.read16(source)),
                    "frames": len(features), "inference_seconds": time.monotonic() - started,
                    "rtf_host_full_chain": (time.monotonic() - started) / (len(experiment.read16(source)) / 16000),
                    "mapper_sha256": experiment.sha256(args.output / "mapper.pt"),
                    "native_sha256": experiment.sha256(args.native), "temporal_window": 3,
                    "male5_used": False, "target_track9_used": False, "played": False, "board_touched": False})
    experiment.save_json(args.output / "inference.json", summary)
    experiment.save_json(args.output / "evaluation_manifest.json", {
        "inputs": [{"role": "source", "path": source.relative_to(experiment.ROOT).as_posix()}],
        "outputs": [{"candidate": experiment.CANDIDATE,
                     "path": (args.output / "fixed_male4.wav").relative_to(experiment.ROOT).as_posix()}]})
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("infer",))
    parser.add_argument("--assets", type=Path, default=experiment.GENERATED / "remote_ps_c_assets")
    parser.add_argument("--output", type=Path, default=experiment.DEFAULT_OUTPUT)
    parser.add_argument("--native", type=Path, default=experiment.GENERATED / "remote_ps_c_native/fargan_probe_host.exe")
    args = parser.parse_args()
    args.assets, args.output, args.native = args.assets.resolve(), args.output.resolve(), args.native.resolve()
    infer(args)


if __name__ == "__main__":
    main()
