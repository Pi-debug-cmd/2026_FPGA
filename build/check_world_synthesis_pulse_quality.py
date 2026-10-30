"""Real-WORLD CPU vs synthesis-pulse C-model regression."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import wave
from math import gcd

import numpy as np
from scipy.signal import resample_poly


def prepare_input(source: Path, seconds: int) -> tuple[bytes, dict]:
    with wave.open(str(source), "rb") as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        width = wav.getsampwidth()
        raw = wav.readframes(rate * seconds)
    if width == 3:
        packed = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        signed = packed[:, 0] | packed[:, 1] << 8 | packed[:, 2] << 16
        samples = ((signed ^ 0x800000) - 0x800000).astype(float) / 8388608
    elif width == 2:
        samples = np.frombuffer(raw, dtype="<i2").astype(float) / 32768
    else:
        raise ValueError(f"{source}: require PCM16 or PCM24")
    samples = samples.reshape(-1, channels).mean(axis=1)
    factor = gcd(rate, 16000)
    samples = resample_poly(samples, 16000 // factor, rate // factor)
    samples = samples[: seconds * 16000]
    if len(samples) != seconds * 16000:
        raise ValueError(f"{source}: shorter than {seconds} seconds")
    pcm = np.clip(np.rint(samples * 32768), -32768, 32767).astype("<i2").tobytes()
    return pcm, {"rate": rate, "channels": channels, "sample_width": width}


def json_logs(stderr: bytes) -> list[dict]:
    return [json.loads(line) for line in stderr.decode(errors="replace").splitlines()
            if line.startswith("{")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=5)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    result = {
        "exe_sha256": hashlib.sha256(args.exe.read_bytes()).hexdigest(),
        "thresholds": {"snr_db_min": 75.0, "max_pcm16_error_max": 3,
                       "clipped_samples_max": 0, "model_calls_min": 1},
        "cases": [],
    }
    all_passed = True
    for case_index, source in enumerate(args.source, 1):
        case_dir = args.out / f"case{case_index}"
        case_dir.mkdir(exist_ok=True)
        pcm, metadata = prepare_input(source, args.seconds)
        (case_dir / "input.raw").write_bytes(pcm)
        case = {
            "source": str(source),
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "input_sha256": hashlib.sha256(pcm).hexdigest(),
            "preprocessing": "first N seconds, channel mean, scipy resample_poly to 16k, round/clip PCM16",
            "seconds": args.seconds,
            **metadata,
            "runs": {},
        }
        outputs = {}
        for mode, enabled in (("cpu", "0"), ("model", "1")):
            env = os.environ.copy()
            env["WORLD_EXP"] = "cpu"
            env["WORLD_AP_MINPHASE_STRIDE"] = "1"
            env["WORLD_AP_FALLBACK_RATIO"] = "8"
            env["WORLD_SYNTH_PULSE_MODEL"] = enabled
            run = subprocess.run(
                [str(args.exe.resolve()), str(args.seconds), "pcm16", "0", "39322"],
                input=pcm, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, timeout=120, check=False)
            (case_dir / f"{mode}.raw").write_bytes(run.stdout)
            (case_dir / f"{mode}.log").write_bytes(run.stderr)
            if run.returncode != 0:
                raise RuntimeError(run.stderr.decode(errors="replace"))
            output = np.frombuffer(run.stdout, dtype="<i2").astype(np.float64)
            outputs[mode] = output
            case["runs"][mode] = {
                "exit": run.returncode,
                "sha256": hashlib.sha256(run.stdout).hexdigest(),
                "samples": len(output),
                "clipped_samples": int(np.count_nonzero((output <= -32768) | (output >= 32767))),
                "logs": json_logs(run.stderr),
            }
        cpu, model = outputs["cpu"], outputs["model"]
        if len(cpu) != len(model) or len(cpu) != args.seconds * 16000:
            raise ValueError("unexpected output length")
        difference = cpu - model
        error_power = float(np.dot(difference, difference))
        signal_power = float(np.dot(cpu, cpu))
        telemetry = [entry for entry in case["runs"]["model"]["logs"]
                     if entry.get("kind") == "world_synthesis_pulse_model"]
        calls = telemetry[-1]["calls"] if telemetry else 0
        fallbacks = telemetry[-1]["cpu_fallbacks"] if telemetry else 0
        comparison = {
            "snr_db": float(10 * np.log10(signal_power / max(1.0, error_power))),
            "max_pcm16_error": int(np.max(np.abs(difference))),
            "rms_pcm16_error": float(np.sqrt(np.mean(difference ** 2))),
            "model_calls": calls,
            "cpu_fallbacks": fallbacks,
        }
        comparison["passed"] = (
            comparison["snr_db"] >= 75.0 and
            comparison["max_pcm16_error"] <= 3 and
            case["runs"]["cpu"]["clipped_samples"] == 0 and
            case["runs"]["model"]["clipped_samples"] == 0 and calls >= 1)
        case["comparison"] = comparison
        result["cases"].append(case)
        all_passed &= comparison["passed"]
        print(json.dumps({"case": case_index, **comparison}, ensure_ascii=False))
    result["passed"] = all_passed
    (args.out / "quality.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not all_passed:
        raise SystemExit("Synthesis pulse model regression failed")


if __name__ == "__main__":
    main()
