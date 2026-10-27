"""PS-20261025-20: frozen v1 label/dynamics audit; no training or locked audio."""
import json
from pathlib import Path
import subprocess
import time

import remote_ps_c_hubert_fargan as v1
import numpy as np
import torch


ROOT = v1.ROOT
CORPUS = v1.GENERATED / "remote_ps_c_assets/paired_corpus_v1/paired_hubert_fargan_corpus_v1"
MODEL = v1.GENERATED / "remote_ps_c_hubert_fargan_v1"
OUT = v1.GENERATED / "remote_ps_c_diagnostic_v1"
NATIVE = v1.GENERATED / "remote_ps_c_native/fargan_probe_host.exe"
REPORT = ROOT / "report/ps_20261025_20_feature_diagnostic_20261026.json"


def correlation(x, y):
    x = np.asarray(x, dtype=np.float64) - np.mean(x)
    y = np.asarray(y, dtype=np.float64) - np.mean(y)
    denominator = np.linalg.norm(x) * np.linalg.norm(y)
    return float(x @ y / denominator) if denominator > 1e-12 else None


def energy_lag(source, teacher):
    """Positive lag means teacher is later; equal source support for all lags."""
    count = min(len(source), len(teacher)) // 160
    x, y = [np.log(np.maximum((z[:count*160].reshape(count, 160).astype(np.float64)**2)
                              .mean(axis=1), 1e-8)) for z in (source, teacher)]
    lags = range(-30, 31)
    scores = [correlation(x[30:count-30], y[30+lag:count-30+lag]) for lag in lags]
    if any(score is None for score in scores):
        return {"zero_lag_correlation": None, "best_lag_ms": None,
                "best_correlation": None, "gain": None}
    best = int(np.argmax(scores))
    return {"zero_lag_correlation": scores[30], "best_lag_ms": (best-30)*10,
            "best_correlation": scores[best], "gain": scores[best]-scores[30]}


def summarize(values):
    x = np.asarray([v for v in values if v is not None], dtype=np.float64)
    return {"count": len(x), "mean": float(x.mean()), "median": float(np.median(x)),
            "p90": float(np.percentile(x, 90)), "max": float(x.max())} if len(x) else {"count": 0}


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    assert v1.sha256(CORPUS / "portable_manifest.json") == v1.MANIFEST_SHA
    assert v1.sha256(NATIVE) == "0e5eb4d457741820564d4397e0b69f8dd58b25c896259bb66d8e84fb88a3dc14"
    assert v1.sha256(MODEL / "mapper.pt") == "ea545fda2b64b7242e710b4a799dfdd45034a958ff987ffd529a189abae26f68"
    assert v1.sha256(MODEL / "statistics.npz") == "fc95aab77f18e7ea2308dacb524292a48d5ba9517bbdcb431341338f759584d8"
    manifest = json.loads((CORPUS / "portable_manifest.json").read_text(encoding="utf-8"))
    assert manifest["complete"] and not manifest["target_track9_used"]
    assert manifest["counts"] == {"train": 192, "validation": 8} and len(manifest["rows"]) == 200
    cache = json.loads((MODEL / "cache_manifest.json").read_text(encoding="utf-8"))
    assert cache["corpus_manifest_sha256"] == v1.MANIFEST_SHA
    assert cache["hubert_sha256"] == v1.HUBERT_SHA and cache["hubert_layer"] == 9
    cached = {r["stem"]: r for r in cache["records"]}
    assert set(cached) == {r["stem"] for r in manifest["rows"]}
    stats = dict(np.load(MODEL / "statistics.npz"))
    checkpoint = torch.load(MODEL / "mapper.pt", weights_only=True, map_location="cpu")
    assert checkpoint["config"] == v1.CONFIG
    model = v1.Mapper().eval()
    model.load_state_dict(checkpoint["state_dict"])
    records, predictions, truths = [], [], []
    prediction_deltas, truth_deltas = [], []
    checked = 0
    for index, row in enumerate(manifest["rows"], 1):
        for asset in row["assets"].values():
            path = CORPUS / asset["path"]
            assert path.stat().st_size == asset["bytes"] and v1.sha256(path) == asset["sha256"]
            checked += 1
        pcm = {role: np.fromfile(CORPUS / row["assets"][role+"_pcm"]["path"], dtype="<f4")
               for role in ("source", "teacher")}
        assert len(pcm["source"]) == len(pcm["teacher"])
        record = {"stem": row["stem"], "speaker": row["speaker"], "split": row["split"],
                  "energy_lag": energy_lag(pcm["source"], pcm["teacher"]), "feature_reextraction": {}}
        for role in ("source", "teacher"):
            prefix = OUT / (row["stem"]+"_"+role)
            np.clip(np.rint(pcm[role]*32768), -32768, 32767).astype("<i2").tofile(prefix.with_suffix(".pcm"))
            subprocess.run([str(NATIVE), "--features", str(prefix.with_suffix(".pcm")),
                            str(prefix.with_suffix(".f32")), str(prefix.with_suffix(".json"))], check=True)
            actual = np.fromfile(prefix.with_suffix(".f32"), dtype="<f4").reshape(-1, 20)
            supplied = np.fromfile(CORPUS / row["assets"][role+"_features"]["path"], dtype="<f4").reshape(-1, 20)
            frames = min(len(actual), len(supplied))
            assert frames > 60 and np.isfinite(actual).all() and np.isfinite(supplied).all()
            difference = np.abs(actual[:frames]-supplied[:frames])
            maximum = np.unravel_index(np.argmax(difference), difference.shape)
            record["feature_reextraction"][role] = {
                "actual_frames": len(actual), "supplied_frames": len(supplied), "common_frames": frames,
                "mae": float(difference.mean()), "max_abs_error": float(difference.max()),
                "max_error_frame": int(maximum[0]), "max_error_dimension": int(maximum[1]),
                "fraction_abs_error_over_0_01": float(np.mean(difference > 0.01)),
                "per_dimension_mae": difference.mean(axis=0).tolist()}
        cache_row = cached[row["stem"]]
        assert cache_row["split"] == row["split"]
        path = MODEL / "cache" / cache_row["cache"]
        assert v1.sha256(path) == cache_row["cache_sha256"]
        with np.load(path) as item:
            y = item["target"].astype(np.float32)
            supplied = np.fromfile(CORPUS / row["assets"]["teacher_features"]["path"], dtype="<f4").reshape(-1, 20)
            assert np.array_equal(y, supplied[:len(y)])
            if row["split"] == "validation":
                x = item["content"].astype(np.float32)
                x = ((x-stats["mean"]) @ stats["projection"]) / stats["x_std"]
                with torch.inference_mode():
                    normalized = model(torch.from_numpy(x.astype(np.float32))[None])[0].numpy()
                raw = normalized*stats["y_std"]+stats["y_mean"]
                prediction = np.clip(raw, stats["low"], stats["high"])
                record["prediction"] = {"frames": len(y),
                    "normalized_mae": float(np.abs((prediction-y)/stats["y_std"]).mean()),
                    "clipped_fraction": float(np.mean(prediction != raw))}
                predictions.append(prediction)
                truths.append(y)
                prediction_deltas.append(np.diff(prediction, axis=0))
                truth_deltas.append(np.diff(y, axis=0))
        records.append(record)
        if index == 1 or index % 25 == 0:
            print(json.dumps({"checked_pairs": index, "elapsed_seconds": time.monotonic()-started}), flush=True)
    p, y = np.concatenate(predictions), np.concatenate(truths)
    dp, dy = np.concatenate(prediction_deltas), np.concatenate(truth_deltas)
    baseline = np.broadcast_to(stats["y_mean"], y.shape)
    dimensions = []
    for j in range(20):
        mse = float(np.mean((p[:, j]-y[:, j])**2))
        baseline_mse = float(np.mean((baseline[:, j]-y[:, j])**2))
        dimensions.append({"index": j, "mae": float(np.abs(p[:, j]-y[:, j]).mean()),
            "normalized_mae": float(np.abs((p[:, j]-y[:, j])/stats["y_std"][j]).mean()),
            "mse": mse, "train_mean_mse": baseline_mse, "mse_ratio_to_train_mean": mse/baseline_mse,
            "correlation": correlation(p[:, j], y[:, j]),
            "prediction_std": float(p[:, j].std()), "teacher_std": float(y[:, j].std()),
            "std_ratio": float(p[:, j].std()/y[:, j].std()),
            "prediction_delta_rms": float(np.sqrt(np.mean(dp[:, j]**2))),
            "teacher_delta_rms": float(np.sqrt(np.mean(dy[:, j]**2))),
            "delta_rms_ratio": float(np.sqrt(np.mean(dp[:, j]**2)/np.mean(dy[:, j]**2)))})
    report = {"task": "PS-20261025-20", "date": "2026-10-26", "role": "Remote-PS-C",
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "round": "frozen_v1_feature_diagnostic", "training_performed": False,
        "corpus_manifest_sha256": v1.MANIFEST_SHA, "native_sha256": v1.sha256(NATIVE),
        "mapper_sha256": v1.sha256(MODEL / "mapper.pt"), "statistics_sha256": v1.sha256(MODEL / "statistics.npz"),
        "cache_manifest_sha256": v1.sha256(MODEL / "cache_manifest.json"),
        "checkpoint_original_cache_manifest_sha256": checkpoint["cache_manifest_sha256"],
        "script_sha256": v1.sha256(Path(__file__)), "asset_hash_checks": checked,
        "cache_target_exact_matches": len(records), "pairs": len(records),
        "validation_pairs": len(predictions), "validation_frames": len(y),
        "reextraction": {role: {key: summarize([r["feature_reextraction"][role][key] for r in records])
                                 for key in ("mae", "max_abs_error", "fraction_abs_error_over_0_01")} for role in ("source", "teacher")},
        "energy_lag": {"method": "natural log of 10 ms PCM mean-square energy, floor 1e-8; fixed source support excluding 30 edge frames; teacher offsets -30..30 frames; positive=teacher later; no data shifted",
            "zero_lag": summarize([r["energy_lag"]["zero_lag_correlation"] for r in records]),
            "absolute_best_lag_ms": summarize([abs(r["energy_lag"]["best_lag_ms"]) for r in records if r["energy_lag"]["best_lag_ms"] is not None]),
            "gain": summarize([r["energy_lag"]["gain"] for r in records])},
        "validation_dynamics": {"aggregation": "frame-weighted; deltas within each utterance only; no cross-boundary differences",
            "normalized_mae": float(np.abs((p-y)/stats["y_std"]).mean()),
            "train_mean_normalized_mae": float(np.abs((baseline-y)/stats["y_std"]).mean()),
            "normalized_mse": float(np.mean(((p-y)/stats["y_std"])**2)),
            "train_mean_normalized_mse": float(np.mean(((baseline-y)/stats["y_std"])**2)),
            "dimensions": dimensions}, "records": records,
        "limitations": ["Energy correlation cannot establish phoneme alignment or causality of CER/leakage failures.",
            "Current native source/build differs from historical feature producer; reextraction is not historical bit parity.",
            "Auxiliary validation already selected v1 checkpoint; this is not an independent quality acceptance test.",
            "No five-gate evaluation repeated, no new candidate, no model weight/statistic modified."],
        "fixed_male_audio_read": False, "target_track_audio_read": False,
        "played": False, "board_touched": False, "quality_status": "REJECTED (unchanged v1)",
        "elapsed_seconds": time.monotonic()-started}
    v1.save_json(REPORT, report)
    print(json.dumps({k: report[k] for k in ("pairs", "asset_hash_checks", "validation_frames", "reextraction", "energy_lag", "elapsed_seconds")}, indent=2))


if __name__ == "__main__":
    main()
