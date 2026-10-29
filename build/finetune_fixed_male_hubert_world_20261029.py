"""Fine-tune the frozen HuBERT/WORLD student on verified fixed-male teacher pairs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "build"))
import train_hubert_world_teacher_round20_20261025 as base  # noqa: E402
import train_paired_hubert_world_gru_round26_20261025 as paired  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-manifest", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--experiment-round", required=True, type=int)
    parser.add_argument("--steps", required=True, type=int)
    parser.add_argument("--learning-rate", required=True, type=float)
    parser.add_argument("--roles", nargs="+", default=["train1", "train2", "train3"])
    parser.add_argument("--trainable", choices=("all", "output", "gru_output"), default="all")
    parser.add_argument("--weight-decay", type=float, default=1e-5)
    args = parser.parse_args()
    if args.steps < 1 or not np.isfinite(args.learning_rate) or args.learning_rate <= 0:
        raise ValueError("steps and learning rate must be positive")
    if len(set(args.roles)) != len(args.roles) or not set(args.roles) <= {"train1", "train2", "train3"}:
        raise ValueError("roles must be a unique subset of train1/train2/train3")
    manifest = json.loads(args.cache_manifest.read_text(encoding="utf-8"))
    if not manifest["complete"] or manifest["recording4_used"] or manifest["recording5_used"]:
        raise ValueError("invalid fixed-male cache manifest")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    if checkpoint["format"] != "paired_hubert_world_causal_gru_round37_variance_matching_v1":
        raise ValueError("fine-tuning requires the Round37-compatible student format")
    torch.manual_seed(20261029)
    np.random.seed(20261029)
    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    model = paired.ProsodyCausalWorldGRU()
    model.load_state_dict(checkpoint["model"])
    if args.trainable == "output":
        for name, parameter in model.named_parameters():
            parameter.requires_grad_(name.startswith("output."))
    elif args.trainable == "gru_output":
        for name, parameter in model.named_parameters():
            parameter.requires_grad_(name.startswith("gru.") or name.startswith("output."))
    trainable_parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(trainable_parameters, lr=args.learning_rate,
                                  weight_decay=args.weight_decay)
    rows = {row["role"]: row for row in manifest["rows"]}
    pairs = []
    raw_targets = []
    for role in args.roles:
        data = np.load(rows[role]["cache_path"])
        content = data["content"].astype(np.float32)
        target = data["target"].astype(np.float32)
        prosody = data["source_prosody"].astype(np.float32)
        x = (((content - checkpoint["pca_mean"]) @ checkpoint["pca_projection"]
              - checkpoint["x_mean"]) / checkpoint["x_std"]).astype(np.float32)
        x = np.concatenate((x, ((prosody - checkpoint["prosody_mean"])
                                / checkpoint["prosody_std"]).astype(np.float32)), axis=1)
        z = ((target - checkpoint["y_mean"]) / checkpoint["y_std"]).astype(np.float32)
        z[:, paired.VUV_INDEX] = target[:, paired.VUV_INDEX]
        if len(x) != len(z) or len(x) < 128 or not np.isfinite(x).all() or not np.isfinite(z).all():
            raise ValueError(f"invalid prepared pair: {role}")
        pairs.append((role, x, z))
        raw_targets.append(target)
    pooled = np.concatenate(raw_targets)
    voiced_fraction = float(np.mean(pooled[:, paired.VUV_INDEX] > 0.5))
    positive_weight = torch.tensor((1.0 - voiced_fraction) / max(voiced_fraction, 1e-4))

    def evaluate() -> dict:
        model.eval()
        totals = []
        with torch.inference_mode():
            for _, x, z in pairs:
                prediction = model(torch.from_numpy(x[None]))
                _, metrics = paired.loss_terms(
                    prediction, torch.from_numpy(z[None]), torch.from_numpy(z[None, :, paired.VUV_INDEX]),
                    positive_weight, True, False, True, False, False, False, 1.20)
                totals.append(metrics)
        return {key: float(np.mean([row[key] for row in totals])) for key in totals[0]}

    initial = evaluate()
    rng = np.random.default_rng(20261029)
    started = time.monotonic()
    history = []
    model.train()
    for step in range(1, args.steps + 1):
        batch_x, batch_y = [], []
        for _ in range(8):
            _, x, z = pairs[int(rng.integers(len(pairs)))]
            start = int(rng.integers(len(x) - 128 + 1))
            batch_x.append(x[start:start + 128])
            batch_y.append(z[start:start + 128])
        x = torch.from_numpy(np.stack(batch_x))
        target = torch.from_numpy(np.stack(batch_y))
        prediction = model(x)
        loss, metrics = paired.loss_terms(prediction, target, target[..., paired.VUV_INDEX],
                                          positive_weight, True, False, True, False,
                                          False, False, 1.20)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable_parameters, 1.0)
        optimizer.step()
        if step == 1 or step % 100 == 0 or step == args.steps:
            history.append({"step": step, "train": metrics})
            print(json.dumps(history[-1]), flush=True)
    final = evaluate()
    args.output.mkdir(parents=True, exist_ok=True)
    output_checkpoint = args.output / "paired_causal_gru.pt"
    result = dict(checkpoint)
    result["model"] = model.state_dict()
    result["fixed_male_finetune"] = {
        "experiment_round": args.experiment_round, "roles": args.roles,
        "steps": args.steps, "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay, "trainable": args.trainable,
        "initial": initial, "final": final, "history": history,
        "cache_manifest_sha256": base.sha256(args.cache_manifest),
        "base_checkpoint_sha256": base.sha256(args.checkpoint),
        "recording4_used": False, "recording5_used": False, "target_track9_used": False,
    }
    torch.save(result, output_checkpoint)
    summary = {"task": "PS-20261021-10", "round": args.experiment_round,
               "kind": "fixed_male_teacher_finetune", **result["fixed_male_finetune"],
               "checkpoint_sha256": base.sha256(output_checkpoint),
               "trainable_parameters": sum(p.numel() for p in trainable_parameters),
               "elapsed_seconds": time.monotonic() - started, "played": False,
               "board_touched": False}
    (args.output / "finetune_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
