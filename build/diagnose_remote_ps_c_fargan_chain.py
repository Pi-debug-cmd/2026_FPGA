"""PS-20261025-20: frozen auxiliary-validation teacher/vocoder/mapper audit.

Descriptive ASR and speaker diagnostics only: no training, candidate selection,
Fixed-Male audio, locked Track9, playback, or five-gate acceptance decision.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

import remote_ps_c_hubert_fargan as base
from evaluate_seed_fixed_male_strict_20261024 import cer
import numpy as np
import onnxruntime as ort
import soundfile as sf
import torch
import torchaudio
from transformers import WhisperForConditionalGeneration, WhisperProcessor

ROOT = base.ROOT
ASSETS = base.GENERATED / "remote_ps_c_assets"
CORPUS = ASSETS / "paired_corpus_v1/paired_hubert_fargan_corpus_v1"
CACHE = base.GENERATED / "remote_ps_c_hubert_fargan_v1"
NATIVE = base.GENERATED / "remote_ps_c_native/fargan_probe_host.exe"
OUT = base.GENERATED / "remote_ps_c_chain_diagnostic_20261027"
REPORT = ROOT / "report/ps_20261025_20_chain_diagnostic_20261027.json"
CONDITIONS = ("source", "teacher_pcm", "teacher_features_oracle", "v1", "v2")
MODEL_SHAS = {
    "v1": "ea545fda2b64b7242e710b4a799dfdd45034a958ff987ffd529a189abae26f68",
    "v2": "610f592539fd51420409ca413e04232f3cd20da57f885957d050c6157569791c",
}
STATISTICS_SHA = "fc95aab77f18e7ea2308dacb524292a48d5ba9517bbdcb431341338f759584d8"


def chunks(signal):
    # Match the established speaker evaluator's 6 s / 1.5 s tail / RMS rule.
    for start in range(0, len(signal), 96000):
        clip = signal[start:start + 96000]
        if len(clip) >= 24000 and float(np.sqrt(np.mean(clip * clip))) >= 1e-3:
            yield clip


def unit(vector):
    vector = np.asarray(vector, dtype=np.float64)
    norm = np.linalg.norm(vector)
    if not np.isfinite(vector).all() or norm < 1e-9:
        raise ValueError("invalid speaker vector")
    return vector / norm


class Evaluator:
    def __init__(self, snapshot):
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(ASSETS / "wespeaker/cnceleb_resnet34_LM.onnx"), sess_options=options,
            providers=["CPUExecutionProvider"])
        self.processor = WhisperProcessor.from_pretrained(snapshot, local_files_only=True)
        self.whisper = WhisperForConditionalGeneration.from_pretrained(
            snapshot, local_files_only=True).eval()

    def vectors(self, signal):
        vectors, lengths = [], []
        for clip in chunks(signal):
            normalized = clip * 0.04 / max(float(np.sqrt(np.mean(clip * clip))), 1e-8)
            features = torchaudio.compliance.kaldi.fbank(
                torch.from_numpy(normalized * 32768).unsqueeze(0).float(),
                num_mel_bins=80, frame_length=25, frame_shift=10,
                sample_frequency=16000, window_type="hamming", dither=0.0)
            features = (features - features.mean(dim=0)).unsqueeze(0).numpy().astype("float32")
            vectors.append(unit(self.session.run(None, {"feats": features})[0][0]))
            lengths.append(len(clip))
        if not vectors:
            raise ValueError("no valid speaker window")
        return np.stack(vectors), lengths

    def transcribe(self, signal):
        inputs = self.processor(signal.astype("float32"), sampling_rate=16000,
                                return_tensors="pt")
        with torch.inference_mode():
            ids = self.whisper.generate(inputs.input_features, language="zh",
                                        task="transcribe", max_new_tokens=256)
        return self.processor.batch_decode(ids, skip_special_tokens=True)[0].strip()


def fingerprint(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
            "sha256": base.sha256(path)}


def describe(values):
    array = np.asarray(values, dtype=np.float64)
    if not len(array) or not np.isfinite(array).all():
        raise ValueError("invalid diagnostic values")
    return {"mean": float(array.mean()), "median": float(np.median(array)),
            "min": float(array.min()), "max": float(array.max())}


def main():
    started = time.monotonic()
    if REPORT.exists() or OUT.exists():
        raise FileExistsError("diagnostic already exists; retain original evidence")
    OUT.mkdir(parents=True)
    denied = []

    def guard(event, args):
        if event != "open" or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = os.fsdecode(args[0]).replace("\\", "/").casefold()
        if ("/人物音频资料/男声/" in path and path.endswith(".wav")) or path.endswith("/track 9.wav"):
            denied.append(path)
            raise PermissionError("Fixed-Male and Track9 audio are outside this audit")

    sys.addaudithook(guard)
    manifest_path = CORPUS / "portable_manifest.json"
    assert base.sha256(manifest_path) == base.MANIFEST_SHA
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["complete"] and not manifest["target_track9_used"]
    rows = [row for row in manifest["rows"] if row["split"] == "validation"]
    assert len(rows) == 8
    speakers = sorted({row["speaker"] for row in rows})
    assert len(speakers) == 2
    assert all(sum(row["speaker"] == speaker for row in rows) == 4 for speaker in speakers)
    assert not set(speakers) & {r["speaker"] for r in manifest["rows"] if r["split"] == "train"}
    assert base.sha256(NATIVE) == "0e5eb4d457741820564d4397e0b69f8dd58b25c896259bb66d8e84fb88a3dc14"
    cache_manifest = CACHE / "cache_manifest.json"
    cache_sha = base.sha256(cache_manifest)
    assert cache_sha == "d305aab590730054f873a2cda25e0e1afb05b887bb3f9104d95047a7b72461ca"
    cached = {r["stem"]: r for r in json.loads(cache_manifest.read_text(encoding="utf-8"))["records"]}
    models, stats, artifacts = {}, {}, [fingerprint(manifest_path), fingerprint(cache_manifest), fingerprint(NATIVE)]
    for name in ("v1", "v2"):
        directory = base.GENERATED / ("remote_ps_c_hubert_fargan_" + name)
        model_path, stats_path = directory / "mapper.pt", directory / "statistics.npz"
        assert base.sha256(model_path) == MODEL_SHAS[name]
        assert base.sha256(stats_path) == STATISTICS_SHA
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
        config = {**base.CONFIG, "delta_weight": 0.25 if name == "v1" else 1.0}
        assert checkpoint["config"] == config and checkpoint["step"] == 400
        assert checkpoint["cache_manifest_sha256"] == cache_sha
        models[name] = base.Mapper().eval()
        models[name].load_state_dict(checkpoint["state_dict"])
        with np.load(stats_path) as item:
            stats[name] = dict(item)
        artifacts += [fingerprint(model_path), fingerprint(stats_path)]

    os.environ["HF_HUB_CACHE"] = str(ASSETS / "hf_home/hub")
    snapshots = sorted((ASSETS / "hf_home/hub/models--openai--whisper-small/snapshots").iterdir())
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    artifacts += [fingerprint(p) for p in sorted(snapshot.rglob("*")) if p.is_file()]
    artifacts.append(fingerprint(ASSETS / "wespeaker/cnceleb_resnet34_LM.onnx"))
    evaluator = Evaluator(str(snapshot))
    target_paths = [ROOT / "人物音频资料/女声" / f"Track {i}.wav" for i in range(5, 9)]
    target_vectors = []
    for path in target_paths:
        vectors, lengths = evaluator.vectors(base.read16(path).astype(np.float64))
        target_vectors.append(unit(np.average(vectors, axis=0, weights=lengths)))
        artifacts.append(fingerprint(path))
    target_profile = unit(np.mean(target_vectors, axis=0))

    prepared, source_vectors = {}, {}
    for row in rows:
        stem = row["stem"]
        record = cached[stem]
        assert record["speaker"] == row["speaker"] and record["split"] == "validation"
        for asset in row["assets"].values():
            path = CORPUS / asset["path"]
            assert path.stat().st_size == asset["bytes"] and base.sha256(path) == asset["sha256"]
            artifacts.append(fingerprint(path))
        cache_path = CACHE / "cache" / record["cache"]
        assert base.sha256(cache_path) == record["cache_sha256"]
        artifacts.append(fingerprint(cache_path))
        with np.load(cache_path) as item:
            content = item["content"].astype(np.float32)
            target = item["target"].copy()
        frames, samples = len(target), len(target) * 160
        teacher = np.fromfile(CORPUS / row["assets"]["teacher_features"]["path"], dtype="<f4").reshape(-1, 20)
        assert np.array_equal(target, teacher[:frames])
        signals, wav_info = {}, {}
        for role in ("source", "teacher"):
            values = np.fromfile(CORPUS / row["assets"][role + "_pcm"]["path"], dtype="<f4")
            assert len(values) == record["source_samples"] and len(values) >= samples
            pcm = np.clip(np.rint(values[:samples] * 32768), -32768, 32767).astype("<i2")
            name = "source" if role == "source" else "teacher_pcm"
            path = OUT / (stem + "_" + name + ".wav")
            sf.write(path, pcm, 16000, subtype="PCM_16")
            signals[name] = pcm.astype(np.float64) / 32768
            wav_info[name] = fingerprint(path)
        vectors, lengths = evaluator.vectors(signals["source"])
        source_vectors[stem] = unit(np.average(vectors, axis=0, weights=lengths))
        prepared[stem] = {"signals": signals, "wav_info": wav_info, "frames": frames,
                          "content": content, "target": target, "source_samples": record["source_samples"]}

    records = []
    for row in rows:
        stem, speaker = row["stem"], row["speaker"]
        item = prepared[stem]
        other_stems = [r["stem"] for r in rows if r["speaker"] == speaker and r["stem"] != stem]
        assert len(other_stems) == 3
        source_profile = unit(np.mean([source_vectors[s] for s in other_stems], axis=0))
        feature_errors = {}
        for name in ("teacher_features_oracle", "v1", "v2"):
            features = item["target"]
            if name != "teacher_features_oracle":
                st = stats[name]
                content = (item["content"] - st["mean"]) @ st["projection"] / st["x_std"]
                with torch.inference_mode():
                    prediction = models[name](torch.from_numpy(content.astype(np.float32))[None])[0].numpy()
                raw = prediction * st["y_std"] + st["y_mean"]
                features = np.clip(raw, st["low"], st["high"])
                feature_errors[name] = {
                    "normalized_mae": float(np.abs((features - item["target"]) / st["y_std"]).mean()),
                    "clipped_fraction": float(np.mean(raw != features))}
            feature_path = OUT / (stem + "_" + name + ".features.f32")
            features.astype("<f4").tofile(feature_path)
            wav_path = OUT / (stem + "_" + name + ".wav")
            synthesis = base.synthesize(NATIVE, feature_path, wav_path)
            values, rate = sf.read(wav_path, dtype="float64")
            assert rate == 16000 and len(values) == item["frames"] * 160 and np.isfinite(values).all()
            item["signals"][name] = values
            item["wav_info"][name] = {**fingerprint(wav_path), **synthesis,
                                      "features": fingerprint(feature_path)}
        source_asr = evaluator.transcribe(item["signals"]["source"])
        results = {}
        for name in CONDITIONS:
            signal = item["signals"][name]
            text = source_asr if name == "source" else evaluator.transcribe(signal)
            vectors, lengths = evaluator.vectors(signal)
            aggregate = unit(np.average(vectors, axis=0, weights=lengths))
            identity = vectors @ target_profile
            leakages = vectors @ source_profile
            results[name] = {
                "asr": text, "cer_vs_source_asr": cer(source_asr, text),
                "cer_vs_manifest_text": cer(row["text"], text),
                "target_identity_mean": float(identity.mean()),
                "target_identity_p10": float(np.percentile(identity, 10)),
                "source_similarity_window_mean": float(leakages.mean()),
                "source_similarity_aggregate": float(aggregate @ source_profile),
                "source_similarity_strict": max(float(leakages.mean()), float(aggregate @ source_profile)),
                "source_similarity_by_chunk": leakages.tolist(),
                "target_identity_by_chunk": identity.tolist(),
                "samples": len(signal), "peak": float(abs(signal).max()),
                "clipping_fraction": float(np.mean(abs(signal) >= 32767 / 32768)),
                "output": item["wav_info"][name]}
            print(json.dumps({"stem": stem, "condition": name,
                              "cer_source": results[name]["cer_vs_source_asr"]["cer"],
                              "cer_text": results[name]["cer_vs_manifest_text"]["cer"],
                              "source_similarity": results[name]["source_similarity_strict"]}), flush=True)
        record = {"stem": stem, "speaker": speaker, "split": "validation", "manifest_text": row["text"],
                  "frames": item["frames"], "original_samples": item["source_samples"],
                  "source_profile_other_stems": other_stems,
                  "source_profile_sha256_f64": __import__("hashlib").sha256(source_profile.tobytes()).hexdigest(),
                  "feature_errors": feature_errors, "conditions": results}
        records.append(record)
        base.save_json(OUT / (stem + "_record.json"), record)

    summaries = {}
    for name in CONDITIONS:
        conditions = [r["conditions"][name] for r in records]
        summary = {key: describe([r[key] for r in conditions]) for key in (
            "target_identity_mean", "target_identity_p10", "source_similarity_strict")}
        for key in ("cer_vs_source_asr", "cer_vs_manifest_text"):
            chars = sum(r[key]["reference_chars"] for r in conditions)
            distance = sum(r[key]["distance"] for r in conditions)
            assert chars > 0 and all(r[key]["reference_chars"] > 0 for r in conditions)
            summary[key] = {"reference_chars": chars, "distance": distance,
                            "micro": distance / chars,
                            "per_utterance": describe([r[key]["cer"] for r in conditions])}
        summaries[name] = summary
    for name in MODEL_SHAS:
        directory = base.GENERATED / ("remote_ps_c_hubert_fargan_" + name)
        assert base.sha256(directory / "mapper.pt") == MODEL_SHAS[name]
        assert base.sha256(directory / "statistics.npz") == STATISTICS_SHA
    assert not denied and base.sha256(cache_manifest) == cache_sha
    report = {
        "task": "PS-20261025-20", "date": "2026-10-27", "role": "Remote-PS-C",
        "round": "frozen_auxiliary_validation_chain_diagnostic", "status": "DIAGNOSTIC_COMPLETE",
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "script_sha256": base.sha256(Path(__file__)), "corpus_manifest_sha256": base.MANIFEST_SHA,
        "validation_pairs": len(rows), "speakers": speakers, "validation_frames": sum(r["frames"] for r in records),
        "conditions": list(CONDITIONS), "summaries": summaries, "records": records,
        "input_artifacts": artifacts,
        "protocol": {
            "duration": "All five conditions truncated to cached teacher prefix frames * 160 samples; no time warp or search.",
            "pcm": "source/teacher float32 rounded/clipped to PCM16; all evaluated signals mono16k PCM16",
            "mapper": "frozen step400 checkpoints; original float16 cached HuBERT content, PCA/statistics and clipping",
            "source_profile": "leave-one-utterance-out mean of normalized same-speaker source aggregates (3 other auxiliary validation utterances)",
            "target_profile": "equal-weight normalized per-file centroid of Track5-8, existing speaker windows",
            "speaker_windows": "6s nonoverlap; tail >=1.5s; RMS>=0.001; RMS0.04 fbank80 Hamming CMN, no VAD",
            "source_similarity": "max(mean window cosine, normalized duration-weighted aggregate cosine); descriptive, not the Fixed-Male profile",
            "asr": "offline Whisper-small language zh task transcribe max_new_tokens256; existing forced_decoder_ids/attention-mask settings unchanged",
            "cer": "existing evaluator cer() punctuation/case/OpenCC t2s; separately source-ASR and declared manifest text references; micro=sum edits/sum reference chars",
            "utmos": "not evaluated in this diagnostic; no quality-gate acceptance or selection"},
        "environment": {"python": sys.version, "torch": torch.__version__, "onnxruntime": ort.__version__,
                        "threads": torch.get_num_threads(), "runtime": sys.executable},
        "training_performed": False, "model_or_statistics_modified": False,
        "fixed_male_audio_read": False, "target_track9_read": False,
        "python_guard_denied_accesses": denied, "played": False, "board_touched": False,
        "quality_status": "v1/v2 REJECTED unchanged; not WAIT_LOCAL_TEST",
        "limitations": [
            "Auxiliary validation selected the existing checkpoints; this is not an independent acceptance set or Fixed-Male result.",
            "Two speakers and short utterances do not establish generalization; source-profile protocol differs from fixed-male gates.",
            "Whisper transcript errors and source-ASR reference errors can confound CER; manifest text is declared corpus metadata, not newly human-verified audio transcription.",
            "Teacher PCM and supplied feature oracle use historical paired assets; native build is not historical bit parity.",
            "Only one stage is replaced in each adjacent comparison, but numeric metric differences do not prove the cause of Fixed-Male failures.",
            "Python file-open guard does not trace operating-system-wide or native-child access.",
            "No new weights, hyperparameter sweep, locked-set evaluation, playback, human listening, ARM, PL or real-time result."],
        "elapsed_seconds": time.monotonic() - started}
    base.save_json(REPORT, report)
    print("SUMMARY", json.dumps(summaries, ensure_ascii=False), flush=True)
    print("REPORT", str(REPORT), "SECONDS", report["elapsed_seconds"], flush=True)


if __name__ == "__main__":
    main()
