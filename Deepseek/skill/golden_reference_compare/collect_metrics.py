#!/usr/bin/env python3
"""collect_metrics.py - pull the numbers out of Vivado reports and program telemetry
   and write them as one long-format CSV (+ an optional markdown table).

Why: a submission dies on "your resource / timing / RTF numbers are not traceable".
Every row produced here carries the file it came from, so each number can be
re-derived instead of copied from a screenshot.

Inputs it understands
---------------------
* Vivado `report_utilization` text  -> Slice LUTs, FF, BRAM, DSP, IOB, %
* Vivado `report_timing_summary`    -> WNS/TNS/WHS/THS/WPWS + failing endpoints
* `vc_stream` stderr JSON           -> rtf, total_ms, analysis_rtf, peak, clipped
* anything via --extra name=value   -> board id, clock, run count, notes

Usage
-----
  python3 collect_metrics.py --vivado-dir ../fpga/report \
      --telemetry telemetry/*.json --out metrics.csv --md metrics.md \
      --meta "board=xc7z020clg400-2" --meta "clock_mhz=100" --meta "runs=3"
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

UTIL_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|")
UTIL_WANT = ["Slice LUTs", "Slice Registers", "Block RAM Tile", "DSPs", "Bonded IOB"]


def parse_utilization(path: Path):
    rows, seen = [], set()
    text = path.read_text(errors="replace")
    for line in text.splitlines():
        m = UTIL_RE.match(line)
        if not m:
            continue
        name, used = m.group(1).strip().rstrip("*").strip(), int(m.group(2))
        if name in UTIL_WANT and name not in seen:
            seen.add(name)
            pct = ""
            tail = line.rsplit("|", 2)
            if len(tail) >= 2 and re.match(r"\s*[\d.]+\s*$", tail[1]):
                pct = tail[1].strip()
            rows.append(("utilization", name.replace(" ", "_").lower(), used,
                         "count", path.name, "%s%%" % pct if pct else ""))
    return rows


def parse_timing(path: Path):
    lines = path.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        if "WNS(ns)" not in line or "WHS(ns)" not in line:
            continue
        for j in range(i + 1, min(i + 4, len(lines))):
            toks = lines[j].split()
            if len(toks) >= 12 and re.match(r"^-?\d", toks[0]):
                names = ["WNS", "TNS", "TNS_fail_ep", "TNS_total_ep",
                         "WHS", "THS", "THS_fail_ep", "THS_total_ep",
                         "WPWS", "TPWS", "TPWS_fail_ep", "TPWS_total_ep"]
                return [("timing", n.lower(), float(v),
                         "count" if n.endswith("_ep") else "ns", path.name, "")
                        for n, v in zip(names, toks[:12])]
    return []


TELE_KEYS = [("rtf", "ratio"), ("total_ms", "ms"), ("analysis_rtf", "ratio"),
             ("render_rtf", "ratio"), ("peak_out", "fs"), ("rms_out", "fs"),
             ("clipped_samples", "count"), ("blocks", "count"),
             ("proc_ms", "ms"), ("wall_ms", "ms"), ("block_ms", "ms"),
             ("fade_ms", "ms"), ("frames_world", "count"), ("model_bytes", "bytes")]


def parse_telemetry(path: Path):
    rows = []
    try:
        obj = json.loads(path.read_text(errors="replace"))
    except json.JSONDecodeError:
        # vc_stream in stream mode prints one JSON object per block, plus a summary
        obj = None
        for line in reversed(path.read_text(errors="replace").splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    obj = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
    if not isinstance(obj, dict):
        print("WARN: %s is not JSON telemetry" % path, file=sys.stderr)
        return rows
    for key, unit in TELE_KEYS:
        if key in obj and isinstance(obj[key], (int, float)):
            rows.append(("telemetry", key, obj[key], unit, path.name,
                         "mode=%s" % obj.get("mode", "batch")))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vivado-dir", type=Path, default=None)
    ap.add_argument("--telemetry", nargs="*", type=Path, default=[])
    ap.add_argument("--extra", nargs="*", default=[],
                    help="free-form section.name=value rows")
    ap.add_argument("--meta", nargs="*", default=[],
                    help="run conditions, written as their own section")
    ap.add_argument("--out", type=Path, default=Path("metrics.csv"))
    ap.add_argument("--md", type=Path, default=None)
    args = ap.parse_args(argv)

    rows = []
    if args.vivado_dir:
        d = args.vivado_dir
        for p in sorted(d.glob("impl_utilization.txt")) + sorted(d.glob("synth_utilization.txt")):
            rows += [("utilization:" + ("impl" if p.name.startswith("impl") else "synth"),
                      r[1], r[2], r[3], p.name, r[5]) for r in parse_utilization(p)]
        for p in sorted(d.glob("impl_timing.txt")) + sorted(d.glob("synth_timing.txt")):
            stage = "impl" if p.name.startswith("impl") else "synth"
            rows += [("timing:" + stage, r[1], r[2], r[3], p.name, r[5])
                     for r in parse_timing(p)]
    for p in args.telemetry:
        rows += parse_telemetry(p)
    for spec in args.extra:
        k, _, v = spec.partition("=")
        sec, _, name = k.rpartition(".")
        rows.append((sec or "extra", name or k, v, "", "argument", ""))
    for spec in args.meta:
        k, _, v = spec.partition("=")
        rows.append(("conditions", k, v, "", "argument", ""))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["section", "metric", "value", "unit", "source", "note"])
        w.writerows(rows)
    print("wrote %s (%d rows)" % (args.out, len(rows)))

    if args.md:
        lines = ["| section | metric | value | unit | source |",
                 "|---|---|---|---|---|"]
        for sec, name, val, unit, src, _note in rows:
            lines.append("| %s | %s | %s | %s | %s |" % (sec, name, val, unit, src))
        args.md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("wrote %s" % args.md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
