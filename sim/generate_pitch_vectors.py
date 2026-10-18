"""Generate deterministic integer vectors into a specified simulation directory."""

import argparse
import json
from pathlib import Path

import numpy as np

from src.reference.pitch_shift_fixed import FixedPitchShifter, ratio_to_q16


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    ratios = [0.5, 0.8, 1.0, 1.25, 1.5, 2.0]
    generator = np.random.default_rng(20261009)
    cases = []
    for index, ratio in enumerate(ratios):
        samples = generator.integers(-32768, 32768, 4096, dtype=np.int32)
        samples[:16] = np.resize([-32768, -1, 0, 1, 32767, 0], 16)
        q16 = ratio_to_q16(ratio)
        output = FixedPitchShifter(q16).process(samples)
        for suffix, array in (("input", samples), ("expected", output)):
            (args.output / f"case{index}_{suffix}.hex").write_text(
                "".join(f"{int(x) & 0xffffffff:08x}\n" for x in array), encoding="ascii")
        cases.append({"index": index, "ratio": ratio, "ratio_q16": q16, "samples": len(samples)})
    (args.output / "ratios.hex").write_text(
        "".join(f"{x['ratio_q16']:05x}\n" for x in cases), encoding="ascii")
    (args.output / "vectors.json").write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(cases)} cases, {sum(x['samples'] for x in cases)} samples")


if __name__ == "__main__":
    main()
