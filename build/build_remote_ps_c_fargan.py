"""Build the existing FARGAN probe for the local Windows CPU only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "d3c6c54fefb4f31162710bb47880d11b93e8d23993553a6590017749893351d2"
MODEL_SHA = "a5177ec6fb7d15058e99e57029746100121f68e4890b1467d4094aa336b6013e"


def sha256(path: Path) -> str:
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--gcc", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    assets, out, gcc = args.assets.resolve(), args.output.resolve(), args.gcc.resolve()
    out.mkdir(parents=True, exist_ok=True)
    archive = assets / "opus_fargan_main_20261026.zip"
    models = assets / "opus_data-a5177ec6.tar.gz"
    if sha256(archive) != SOURCE_SHA or sha256(models) != MODEL_SHA:
        raise ValueError("Opus source/model archive SHA mismatch")
    # Extract only the source and model files used by this build, into generated/.
    source = out / "opus-main"
    with zipfile.ZipFile(archive) as bundle:
        for name in bundle.namelist():
            if name.startswith(("opus-main/dnn/", "opus-main/celt/", "opus-main/include/")):
                target = (out / name).resolve()
                if not target.is_relative_to(out):
                    raise ValueError("unsafe source path")
                bundle.extract(name, out)
    data_names = ["fargan_data.c", "fargan_data.h", "pitchdnn_data.c",
                  "pitchdnn_data.h", "plc_data.h", "dred_rdovae_constants.h"]
    with tarfile.open(models) as bundle:
        for name in data_names:
            data = bundle.extractfile("dnn/" + name)
            if data is None:
                raise ValueError(name)
            (source / "dnn" / name).write_bytes(data.read())
    probe = ROOT / "交接/核心材料/board_support/native_llvc_20261005/fargan_probe.c"
    # Keep Unicode repository paths away from older Windows compiler subprocesses.
    shutil.copyfile(probe, out / "fargan_probe.c")
    compat = probe.with_name("fargan_mingw_compat.h")
    shutil.copyfile(compat, out / compat.name)
    sources = ["dnn/" + name + ".c" for name in (
        "burg", "freq", "fargan", "fargan_data", "lpcnet_enc", "lpcnet_tables",
        "nnet", "nnet_default", "parse_lpcnet_weights", "pitchdnn", "pitchdnn_data")]
    sources += ["celt/" + name + ".c" for name in ("kiss_fft", "pitch", "celt_lpc", "mathops")]
    exe = out / "fargan_probe_host.exe"
    command = [str(gcc), "-O3", "-std=gnu99", "-DOPUS_BUILD", "-DUSE_ALLOCA",
               "-include", str(out / compat.name),
               "-ffunction-sections", "-fdata-sections", "-Wl,--gc-sections",
               "-I" + str(source), "-I" + str(source / "include"), "-I" + str(source / "celt"),
               "-I" + str(source / "dnn"), str(out / "fargan_probe.c")]
    command += [str(source / name) for name in sources]
    command += ["-lm", "-o", str(exe)]
    environment = dict(os.environ)
    environment["PATH"] = str(gcc.parent) + os.pathsep + environment.get("PATH", "")
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    (out / "compiler.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        print(result.stderr)
        raise SystemExit(result.returncode)
    report = {"task": "PS-20261025-20", "source_archive_sha256": SOURCE_SHA,
              "source_is_exact_historical_archive": False, "model_archive_sha256": MODEL_SHA,
              "compiler": subprocess.check_output([str(gcc), "--version"], env=environment, text=True).splitlines()[0],
              "command": command, "probe_sha256": sha256(probe),
              "compat_sha256": sha256(compat), "exe_sha256": sha256(exe),
              "compiled_sources": {name: sha256(source / name) for name in sources},
              "host_only": True, "board_touched": False, "played": False}
    if args.smoke:
        corpus = assets / "paired_corpus_v1/paired_hubert_fargan_corpus_v1"
        manifest = json.loads((corpus / "portable_manifest.json").read_text(encoding="utf-8"))
        smoke = []
        for row in manifest["rows"][:2]:
            stem = out / row["stem"]
            signal = np.fromfile(corpus / row["assets"]["teacher_pcm"]["path"], dtype="<f4")
            np.rint(np.clip(signal, -1, 32767 / 32768) * 32768).astype("<i2").tofile(stem.with_suffix(".pcm"))
            subprocess.run([str(exe), "--features", str(stem.with_suffix(".pcm")),
                            str(stem.with_suffix(".f32")), str(stem.with_suffix(".analysis.json"))], check=True, env=environment)
            actual = np.fromfile(stem.with_suffix(".f32"), dtype="<f4").reshape(-1, 20)
            expected = np.fromfile(corpus / row["assets"]["teacher_features"]["path"], dtype="<f4").reshape(-1, 20)
            n = min(len(actual), len(expected))
            subprocess.run([str(exe), "--synthesis", str(stem.with_suffix(".f32")),
                            str(stem.with_suffix(".out.pcm")), str(stem.with_suffix(".synthesis.json"))], check=True, env=environment)
            pcm = np.fromfile(stem.with_suffix(".out.pcm"), dtype="<i2").astype(np.float64) / 32768
            if len(pcm) != len(actual) * 160 or not np.isfinite(actual).all() or not np.any(pcm):
                raise ValueError("invalid native smoke output")
            smoke.append({"stem": row["stem"], "frames": len(actual), "delivered_frames": len(expected),
                          "feature_mae": float(abs(actual[:n] - expected[:n]).mean()),
                          "feature_max_difference": float(abs(actual[:n] - expected[:n]).max()),
                          "output_samples": len(pcm), "output_peak": float(abs(pcm).max()),
                          "output_rms": float(np.sqrt(np.mean(pcm ** 2))),
                          "analysis": json.loads(stem.with_suffix(".analysis.json").read_text()),
                          "synthesis": json.loads(stem.with_suffix(".synthesis.json").read_text())})
        report["smoke"] = smoke
    (out / "build_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
