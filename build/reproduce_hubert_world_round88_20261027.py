"""Reproduce Round88-91 crop/PCA/anchor experiments with external assets."""
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
    parser.add_argument("--experiment-round", type=int, choices=(88, 89, 90, 91), default=88)
    parser.add_argument("--cer-normalizer", choices=("identity", "opencc"),
                        help="Default: historical identity for 88/89, OpenCC 0.1.7 for 90+")
    args = parser.parse_args()
    root = args.asset_root.resolve()
    generated = root / "build/generated"
    output = generated / f"hubert_world_round{args.experiment_round}_20261027"
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
            if (args.experiment_round == 89
                    and name == "train_paired_hubert_world_gru_round26_20261025.py"):
                assert text.count("CROP = 128") == 1
                text = text.replace("CROP = 128", "CROP = 192")
            if (args.experiment_round == 90 and name in (
                    "train_hubert_world_teacher_round20_20261025.py",
                    "train_hubert_world_causal_gru_round23_20261025.py")):
                assert text.count("PCA_DIM = 96") == 1
                text = text.replace("PCA_DIM = 96", "PCA_DIM = 192")
            if (args.experiment_round == 91
                    and name == "train_paired_hubert_world_gru_round26_20261025.py"):
                assert text.count("ANCHOR_PROBABILITY = 0.25") == 1
                text = text.replace("ANCHOR_PROBABILITY = 0.25", "ANCHOR_PROBABILITY = 0.50")
            if name.startswith("apply_world_temporal"):
                text = text.replace('sys.path.insert(0, str(ROOT / "build"))',
                                    'sys.path.insert(0, str(Path(__file__).resolve().parent))')
            (runtime / name).write_text(text, encoding="utf-8", newline="\n")
        return

    if args.stage == "evaluate":
        normalizer = args.cer_normalizer or ("opencc" if args.experiment_round >= 90 else "identity")
        if normalizer == "identity":
            # Historical comparability only: no Chinese script conversion.
            shim = types.ModuleType("opencc")
            class IdentityOpenCC:
                def __init__(self, config: str) -> None:
                    pass

                def convert(self, text: str) -> str:
                    return text
            shim.OpenCC = IdentityOpenCC
            sys.modules["opencc"] = shim
        else:
            sys.path.insert(0, str(generated / "eval_opencc_deps_20261027"))
            from opencc import OpenCC
            assert OpenCC("t2s").convert("骷髏") == "骷髅"
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
                       "--experiment-round", str(args.experiment_round), "--source-relative",
                       "人物音频资料/男声/标准录音 4.wav"]
    sys.path.insert(0, str(runtime))
    sys.argv = [str(script), "--asset-root", str(root), *options]
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
