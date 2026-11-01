#!/usr/bin/env python3
"""gen_demo.py - build four *known-bad* DUT files and check that golden_compare.py
   names the right failure class for each. Runs anywhere with numpy; no board needed.

    python3 gen_demo.py            # writes demo_*.raw / demo_*.f32 into ./demo/
    python3 gen_demo.py --keep     # keep the generated binaries

This is the regression test for the verdict heuristics: if a refactor of
golden_compare.py stops recognising the cache-line fingerprint, this fails.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "golden_compare.py"
OUT = HERE / "demo"


def chirp(n=32000, fs=16000.0):
    t = np.arange(n) / fs
    f0, f1 = 120.0, 3000.0
    k = (f1 - f0) / t[-1]
    return 0.5 * np.sin(2 * np.pi * (f0 * t + 0.5 * k * t * t))


def write_i16(path: Path, x: np.ndarray):
    np.clip(np.round(x * 32767.0), -32768, 32767).astype("<i2").tofile(path)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true")
    args = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)

    ref = np.round(chirp() * 32767.0)
    write_i16(OUT / "demo_ref.raw", ref / 32767.0)

    cases = {}

    # (a) cache-line fingerprint: two 8-sample all-zero runs on 32-byte boundaries
    bad = ref.copy()
    for start in (1024, 20000):
        bad[start:start + 8] = 0.0
    write_i16(OUT / "demo_zero_lines.raw", bad / 32767.0)
    cases["demo_zero_lines.raw"] = "cache-line"

    # (b) pure rounding difference, integer LSB scale
    bad = ref + np.where(np.arange(ref.size) % 3 == 0, 1.0, 0.0)
    write_i16(OUT / "demo_1lsb.raw", bad / 32767.0)
    cases["demo_1lsb.raw"] = "LSB"

    # (c) group delay of 3 samples
    bad = np.concatenate([np.zeros(3), ref[:-3]])
    write_i16(OUT / "demo_lag3.raw", bad / 32767.0)
    cases["demo_lag3.raw"] = "lag (must still PASS after alignment)"

    # (d) every bin of every frame wrong: 401x513 envelope, +1.5 everywhere
    rng = np.random.default_rng(0)
    ref2d = (rng.standard_normal((401, 513)) * 4.0).astype("<f4")
    bad2d = (ref2d + 1.5).astype("<f4")
    ref2d.tofile(OUT / "demo_2d_ref.f32")
    bad2d.tofile(OUT / "demo_2d_dut.f32")
    cases["demo_2d_dut.f32"] = "every bin of every frame"

    rows = []
    for name, expect in cases.items():
        if name.endswith(".f32"):
            cmd = [sys.executable, str(TOOL), str(OUT / "demo_2d_ref.f32"),
                   str(OUT / name), "--shape", "401x513", "--max-lag", "0"]
        else:
            cmd = [sys.executable, str(TOOL), str(OUT / "demo_ref.raw"), str(OUT / name)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        verdict = "?"
        for line in r.stdout.splitlines():
            if '"verdict"' in line:
                verdict = line.split(":", 1)[1].strip().strip('",')
        rows.append((name, expect, verdict, "OK" if expect.split()[0].lower() in verdict.lower()
                     or (expect.startswith("lag") and "PASS" in verdict) else "MISMATCH"))

    width = max(len(r[2]) for r in rows)
    print("\n%-22s %-30s %-*s %s" % ("case", "expected class", width, "verdict", "check"))
    ok = True
    for name, expect, verdict, check in rows:
        print("%-22s %-30s %-*s %s" % (name, expect, width, verdict, check))
        ok &= check == "OK"
    print("\nDEMO", "PASS" if ok else "FAIL")
    if not args.keep:
        for f in OUT.glob("demo_*.raw"):
            f.unlink()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
