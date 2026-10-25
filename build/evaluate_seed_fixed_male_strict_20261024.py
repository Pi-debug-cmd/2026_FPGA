"""Evaluate strict Fixed-Male Seed-VC outputs without using locked target Track 9."""
from __future__ import annotations

import argparse
from math import gcd
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
GATES = {"identity": 0.45, "identity_p10": 0.35, "leakage": 0.10, "utmos": 2.30, "cer": 0.15}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def normalise_text(text: str, convert_script: bool = True) -> str:
    drop = set("，。、！？；：\"“”‘’（）《》 \t\n,.!?;:'()")
    cleaned = "".join(character for character in text if character not in drop).lower()
    if convert_script:
        from opencc import OpenCC

        cleaned = OpenCC("t2s").convert(cleaned)
    return cleaned


def cer(reference: str, hypothesis: str, convert_script: bool = True) -> dict:
    ref = normalise_text(reference, convert_script=convert_script)
    hyp = normalise_text(hypothesis, convert_script=convert_script)
    if not ref:
        return {"reference_chars": 0, "hypothesis_chars": len(hyp), "distance": 0, "cer": None}
    previous = list(range(len(hyp) + 1))
    for row, reference_character in enumerate(ref, 1):
        current = [row]
        for column, hypothesis_character in enumerate(hyp, 1):
            current.append(
                min(
                    previous[column] + 1,
                    current[column - 1] + 1,
                    previous[column - 1] + (reference_character != hypothesis_character),
                )
            )
        previous = current
    return {
        "reference_chars": len(ref),
        "hypothesis_chars": len(hyp),
        "distance": previous[-1],
        "cer": previous[-1] / len(ref),
    }


def main() -> None:
    args = parse_args()
    asset_root = args.asset_root.resolve()
    external_generated = asset_root / "build" / "generated"
    sys.path.insert(0, str(ROOT / "build" / "generated" / "seed_eval_deps"))
    eval_deps = external_generated / "eval_deps_20261016"
    speechmos_root = next((external_generated / "eval_sources_20261016").glob("SpeechMOS-*"))
    for extra in (
        eval_deps,
        external_generated / "world_deps",
        external_generated / "llvc_cpu_deps",
        external_generated / "seed_audio_deps",
        external_generated / "seed_cpu_deps",
        speechmos_root,
    ):
        sys.path.insert(0, str(extra))

    hf_cache = asset_root / "交接" / "核心材料" / "neural_reference" / "cache" / "hf" / "hub"
    whisper_snapshot = next((hf_cache / "models--openai--whisper-small" / "snapshots").glob("*"))
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_CACHE"] = str(hf_cache)
    os.environ["HF_HOME"] = str(hf_cache.parent)

    import numpy as np
    import onnxruntime as ort
    from scipy.signal import resample_poly
    import soundfile as sf
    import torch
    import torchaudio
    from speechmos.utmos22.strong.model import UTMOS22Strong

    torch.set_num_threads(4)

    def load16(path: Path):
        signal, rate = sf.read(str(path), dtype="float64", always_2d=False)
        if signal.ndim == 2:
            signal = signal.mean(axis=1)
        if rate != 16000:
            factor = gcd(int(rate), 16000)
            signal = resample_poly(signal, 16000 // factor, int(rate) // factor)
        return np.ascontiguousarray(signal, dtype=np.float64)

    def chunks(signal):
        for start in range(0, len(signal), 96000):
            clip = signal[start : start + 96000]
            if len(clip) >= 24000 and float(np.sqrt(np.mean(clip * clip))) >= 1e-3:
                yield start, clip

    cross = asset_root / "交接" / "核心材料" / "neural_reference" / "cross_evaluators"
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(cross / "cnceleb_resnet34_LM.onnx"),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    naturalness_model = UTMOS22Strong()
    naturalness_model.load_state_dict(
        torch.load(cross / "utmos22_strong_step7459_v1.pt", map_location="cpu", weights_only=True)
    )
    naturalness_model.eval()

    def embedding(clip):
        normalized = clip * 0.04 / max(float(np.sqrt(np.mean(clip * clip))), 1e-8)
        features = torchaudio.compliance.kaldi.fbank(
            torch.from_numpy(normalized * 32768).unsqueeze(0).float(),
            num_mel_bins=80,
            frame_length=25,
            frame_shift=10,
            sample_frequency=16000,
            window_type="hamming",
            dither=0.0,
        )
        features = (features - features.mean(dim=0)).unsqueeze(0).numpy().astype("float32")
        vector = session.run(None, {"feats": features})[0][0].astype("float64")
        return vector / max(float(np.linalg.norm(vector)), 1e-9)

    def chunk_embeddings(signal):
        records = []
        for start, clip in chunks(signal):
            records.append((start, len(clip), embedding(clip)))
        if not records:
            raise RuntimeError("No valid speaker segments")
        return records

    def centroid(paths):
        per_file = []
        for path in paths:
            records = chunk_embeddings(load16(path))
            vector = np.average(
                np.stack([item[2] for item in records]),
                axis=0,
                weights=[item[1] for item in records],
            )
            per_file.append(vector / np.linalg.norm(vector))
        center = np.stack(per_file).mean(axis=0)
        return center / np.linalg.norm(center)

    def utmos(clip):
        normalized = clip * 0.04 / max(float(np.sqrt(np.mean(clip * clip))), 1e-8)
        with torch.inference_mode():
            score = float(naturalness_model(torch.from_numpy(normalized).unsqueeze(0).float(), 16000).item())
        if not np.isfinite(score):
            raise RuntimeError("Non-finite UTMOS")
        return score

    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    processor = WhisperProcessor.from_pretrained(str(whisper_snapshot), local_files_only=True)
    whisper = WhisperForConditionalGeneration.from_pretrained(str(whisper_snapshot), local_files_only=True).eval()

    def transcribe(signal):
        inputs = processor(signal.astype("float32"), sampling_rate=16000, return_tensors="pt")
        with torch.inference_mode():
            ids = whisper.generate(inputs.input_features, language="zh", task="transcribe", max_new_tokens=256)
        return processor.batch_decode(ids, skip_special_tokens=True)[0].strip()

    source_profile = centroid(
        [ROOT / "人物音频资料" / "男声" / f"标准录音 {number}.wav" for number in range(1, 4)]
    )
    target_profile = centroid(
        [ROOT / "人物音频资料" / "女声" / f"Track {number}.wav" for number in range(5, 9)]
    )

    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_item = next(item for item in manifest["inputs"] if item["role"] == "source")
    source_path = ROOT / source_item["path"]
    source_audio = load16(source_path)
    source_text = transcribe(source_audio)
    rows = []
    for output in manifest["outputs"]:
        candidate_audio = load16(ROOT / output["path"])
        records = chunk_embeddings(candidate_audio)
        identities = [float(item[2] @ target_profile) for item in records]
        leakages = [float(item[2] @ source_profile) for item in records]
        aggregate = np.average(
            np.stack([item[2] for item in records]),
            axis=0,
            weights=[item[1] for item in records],
        )
        aggregate /= np.linalg.norm(aggregate)
        leakage_window_mean = float(np.mean(leakages))
        leakage_aggregate = float(aggregate @ source_profile)
        naturalness = [utmos(clip) for _, clip in chunks(candidate_audio)]
        candidate_text = transcribe(candidate_audio)
        content = cer(source_text, candidate_text)
        raw_content = cer(source_text, candidate_text, convert_script=False)
        metrics = {
            "identity": float(np.mean(identities)),
            "identity_p10": float(np.percentile(identities, 10)),
            "leakage": max(leakage_window_mean, leakage_aggregate),
            "leakage_window_mean": leakage_window_mean,
            "leakage_aggregate": leakage_aggregate,
            "utmos": float(np.mean(naturalness)),
            "cer": content["cer"],
        }
        passed = {
            "identity": metrics["identity"] >= GATES["identity"],
            "identity_p10": metrics["identity_p10"] >= GATES["identity_p10"],
            "leakage": metrics["leakage"] <= GATES["leakage"],
            "utmos": metrics["utmos"] >= GATES["utmos"],
            "cer": metrics["cer"] is not None and metrics["cer"] <= GATES["cer"],
        }
        ratios = [
            metrics["identity"] / GATES["identity"],
            metrics["identity_p10"] / GATES["identity_p10"],
            GATES["leakage"] / max(metrics["leakage"], 1e-6),
            metrics["utmos"] / GATES["utmos"],
            GATES["cer"] / max(metrics["cer"], 1e-6),
        ]
        rows.append(
            {
                **output,
                "metrics": metrics,
                "passed": passed,
                "all_gates_pass": all(passed.values()),
                "selection_score": {"minimum_gate_ratio": min(ratios), "mean_gate_ratio": float(np.mean(ratios))},
                "identity_by_chunk": identities,
                "leakage_by_chunk": leakages,
                "utmos_by_chunk": naturalness,
                "source_asr": source_text,
                "candidate_asr": candidate_text,
                "cer_detail": content,
                "cer_without_script_normalization": raw_content,
            }
        )
        print(
            output["candidate"],
            " ".join(f"{key}={value:.4f}" for key, value in metrics.items()),
            f"pass={all(passed.values())}",
            flush=True,
        )

    rows.sort(
        key=lambda item: (
            item["all_gates_pass"],
            item["selection_score"]["minimum_gate_ratio"],
            item["selection_score"]["mean_gate_ratio"],
        ),
        reverse=True,
    )
    report = {
        "kind": "strict_fixed_male_seed_vc_evaluation",
        "protocol": {
            "source_profile": [f"人物音频资料/男声/标准录音 {number}.wav" for number in range(1, 4)],
            "evaluated_source": source_item["path"],
            "target_profile": [f"人物音频资料/女声/Track {number}.wav" for number in range(5, 9)],
            "target_track9_used": False,
            "speaker_and_utmos_windows": "non-overlapping 6 s; tail >=1.5 s; RMS >=0.001",
            "leakage": "maximum of arithmetic mean of per-window cosines and whole-file length-weighted aggregate-vector cosine",
            "cer": "offline Whisper-small candidate transcript versus source transcript; punctuation removed and OpenCC 0.1.7 t2s-normalized",
        },
        "gates": GATES,
        "selected": rows[0]["candidate"],
        "rows": rows,
        "played": False,
        "board_touched": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SELECTED {rows[0]['candidate']}")
    print(f"REPORT {args.output}")


if __name__ == "__main__":
    main()
