"""Compact on-board C reference vectors and expected SHA256 values."""

import hashlib
import json
from pathlib import Path

import numpy as np

from src.reference.pitch_shift_fixed import FixedPitchShifter, ratio_to_q16


def main():
    output = Path("build/generated/ps_reference")
    output.mkdir(parents=True, exist_ok=True)
    samples = np.random.default_rng(77).integers(-32768, 32768, 4096, dtype=np.int16)
    samples[:16] = np.resize([-32768, -1, 0, 1, 32767], 16)
    raw = samples.astype("<i2").tobytes()
    (output / "input.raw").write_bytes(raw)
    expected = []
    for ratio in (0.5, 0.8, 1.0, 1.25, 1.5, 2.0):
        q16 = ratio_to_q16(ratio)
        result = FixedPitchShifter(q16).process(samples).astype("<i2").tobytes()
        expected.append({"ratio_q16": q16, "samples": len(samples),
                         "bytes": len(result), "sha256": hashlib.sha256(result).hexdigest()})
    record = {"input_sha256": hashlib.sha256(raw).hexdigest(), "expected": expected}
    # Native hardware words contain unsigned lower 24 bits in 32-bit containers.
    # Deliberately different right channel verifies that only the left mic is used.
    left24 = samples.astype(np.int32) * 256 + 127
    native = np.empty((len(samples), 2), dtype="<u4")
    native[:, 0] = left24 & 0xffffff
    native[:, 1] = 123456
    (output / "native_input.raw").write_bytes(native.tobytes())
    native_expected = []
    for row in expected:
        processed = FixedPitchShifter(row["ratio_q16"]).process(samples)
        packed = (processed.astype(np.int32) * 256) & 0xffffff
        result = np.repeat(packed.astype("<u4"), 2).tobytes()
        native_expected.append({"ratio_q16": row["ratio_q16"], "bytes": len(result),
                                "sha256": hashlib.sha256(result).hexdigest()})
    record["native_expected"] = native_expected
    record["native_input_sha256"] = hashlib.sha256(native.tobytes()).hexdigest()
    (output / "expected.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
