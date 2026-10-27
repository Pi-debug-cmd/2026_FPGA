"""Reproduce Round88 with external assets and the historical compatibility runtime."""
from __future__ import annotations

import argparse
from pathlib import Path
import runpy
import sys
import types


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "train", "candidate", "evaluate"))
    parser.add_argument("--asset-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.asset_root.resolve()
    generated = root / "build/generated"
    output = generated / "hubert_world_round88_20261027"
    runtime = output / "runtime/build"
    source = Path(__file__).resolve().parent
    if args.stage == "prepare":
        runtime.mkdir(parents=True, exist_ok=True)
        for name in (
            "train_hubert_world_teacher_round20_20261025.py",
            "train_hubert_world_causal_gru_round23_20261025.py",
            "audit_source_prosody_round32_20261025.py",
            "train_paired_hubert_world_gru_round26_20261025.py",
            "apply_world_temporal_postfilter_round47_20261026.py",
            "evaluate_seed_fixed_male_strict_20261024.py",
        ):
            text = (source / name).read_text(encoding="utf-8")
            text = text.replace("ROOT = Path(__file__).resolve().parents[1]",
                                f"ROOT = Path({str(root)!r})")
            if name.startswith("apply_world_temporal"):
                text = text.replace('sys.path.insert(0, str(ROOT / "build"))',
                                    'sys.path.insert(0, str(Path(__file__).resolve().parent))')
            (runtime / name).write_text(text, encoding="utf-8", newline="\n")
        return

    if args.stage == "evaluate":
        # Historical comparability only: this performs no Chinese script conversion.
        shim = types.ModuleType("opencc")
        class IdentityOpenCC:
            def __init__(self, config: str) -> None:
                pass

            def convert(self, text: str) -> str:
                return text
        shim.OpenCC = IdentityOpenCC
        sys.modules["opencc"] = shim
        script = runtime / "evaluate_seed_fixed_male_strict_20261024.py"
        options = ["--manifest", str(output / "candidates/strict_manifest.json"),
                   "--output", str(output / "strict_evaluation.json")]
    else:
        # Import the interpreter's torch before adding the cached dependency paths,
        # matching the original Round88 invocation. No NMS operation is executed.
        import torch
        for dependency in reversed(("llvc_cpu_deps", "seed_audio_deps",
                                    "seed_cpu_deps", "world_deps")):
            sys.path.insert(0, str(generated / dependency))
        nms_schema = torch.library.Library("torchvision", "DEF")
        nms_schema.define("nms(Tensor boxes, Tensor scores, float iou_threshold) -> Tensor")
        if args.stage == "train":
            script = runtime / "train_paired_hubert_world_gru_round26_20261025.py"
            options = ["--output", str(output), "--multiscale-dynamics",
                       "--multiscale-weight", "1.20", "--source-prosody",
                       "--variance-matching", "--skip-locked-target-regression"]
        else:
            script = runtime / "apply_world_temporal_postfilter_round47_20261026.py"
            options = ["--generated-root", str(generated), "--checkpoint",
                       str(output / "paired_causal_gru.pt"), "--output",
                       str(output / "candidates"), "--gain", "1.6",
                       "--experiment-round", "88", "--source-relative",
                       "人物音频资料/男声/标准录音 4.wav"]
    sys.path.insert(0, str(runtime))
    sys.argv = [str(script), "--asset-root", str(root), *options]
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
