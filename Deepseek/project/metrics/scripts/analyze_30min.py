"""Analyse a stab30.sh run: per-block processing distribution, underruns, clipping,
memory trend and whether the block stream is continuous.

Usage: analyze_30min.py <dir-with-blocks.jsonl-aplay.log-mem.csv-env.txt> [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np


def pct(vals: list[float], q: float) -> float:
    if not vals:
        return float("nan")
    a = np.sort(np.asarray(vals, dtype=np.float64))
    k = int((len(a) - 1) * q) + 1
    k = min(max(k, 1), len(a))
    return float(a[k - 1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", type=Path)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--block-ms", type=int, default=300)
    args = ap.parse_args()
    d = args.dir

    blocks, cum, audio = [], [], []
    summary = {}
    for line in (d / "blocks.jsonl").read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "block" in o:
            blocks.append(int(o["block"]))
            cum.append(float(o["proc_ms"]))
            audio.append(float(o["audio_ms"]))
        elif o.get("ok") is True:
            summary = o

    proc = [cum[0]] + [cum[i] - cum[i - 1] for i in range(1, len(cum))] if cum else []
    vals = {
        "blocks": len(blocks),
        "expected_blocks": None,
        "audio_s": round(sum(audio) / 1000.0, 2) if audio else 0.0,
        "proc_min_ms": round(min(proc), 2) if proc else None,
        "proc_p50_ms": round(pct(proc, 0.50), 2) if proc else None,
        "proc_p95_ms": round(pct(proc, 0.95), 2) if proc else None,
        "proc_p99_ms": round(pct(proc, 0.99), 2) if proc else None,
        "proc_max_ms": round(max(proc), 2) if proc else None,
        "proc_mean_ms": round(float(np.mean(proc)), 2) if proc else None,
        "proc_sum_ms": round(sum(proc), 2) if proc else None,
        "summary_proc_ms": summary.get("proc_ms"),
        "summary_rtf": summary.get("rtf"),
        "clipped_samples": summary.get("clipped_samples"),
        "summary_blocks": summary.get("blocks"),
        "summary_seconds": summary.get("seconds"),
        "e2e_p50_ms": round(args.block_ms + pct(proc, 0.50), 2) if proc else None,
        "e2e_p95_ms": round(args.block_ms + pct(proc, 0.95), 2) if proc else None,
        "e2e_p99_ms": round(args.block_ms + pct(proc, 0.99), 2) if proc else None,
        "e2e_max_ms": round(args.block_ms + max(proc), 2) if proc else None,
    }
    if summary.get("seconds"):
        vals["expected_blocks"] = int(round(float(summary["seconds"]) * 1000 / args.block_ms))

    # block-number continuity: a gap means the block stream stalled
    gaps = []
    for a, b in zip(blocks, blocks[1:]):
        if b != a + 1:
            gaps.append([a, b])
    vals["block_index_gaps"] = gaps[:20]
    vals["block_index_gap_count"] = len(gaps)

    aplay = (d / "aplay.log").read_text(encoding="utf-8", errors="replace") if (d / "aplay.log").exists() else ""
    vals["aplay_underrun_lines"] = len(re.findall(r"(?i)underrun", aplay))
    vals["aplay_error_lines"] = [
        ln for ln in aplay.splitlines()
        if re.search(r"(?i)error|cannot|failed|broken|busy", ln)
    ][:10]

    mem = []
    mp = d / "mem.csv"
    if mp.exists():
        for line in mp.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
            p = line.split(",")
            if len(p) >= 5:
                try:
                    mem.append({"t": int(p[0]), "rss_kb": int(p[1]), "free_kb": int(p[2]),
                                "avail_kb": int(p[3]), "blocks": int(p[4])})
                except ValueError:
                    pass
    if mem:
        rss = [m["rss_kb"] for m in mem]
        vals["mem_samples"] = len(mem)
        vals["rss_first_kb"] = rss[0]
        vals["rss_last_kb"] = rss[-1]
        vals["rss_max_kb"] = max(rss)
        vals["rss_delta_kb"] = rss[-1] - rss[0]
        vals["rss_growth_pct"] = round(100.0 * (rss[-1] - rss[0]) / max(rss[0], 1), 2)
        vals["free_first_kb"] = mem[0]["free_kb"]
        vals["free_last_kb"] = mem[-1]["free_kb"]

    env = {}
    ep = d / "env.txt"
    if ep.exists():
        for line in ep.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    vals["env"] = env

    print(json.dumps(vals, ensure_ascii=False, indent=2))
    if args.json:
        args.json.write_text(json.dumps(vals, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
