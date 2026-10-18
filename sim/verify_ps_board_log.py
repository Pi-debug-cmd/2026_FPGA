"""Check board output lengths, return codes and SHA against frozen PCM vectors."""

import hashlib
import json
import re
from pathlib import Path


def main():
    expected = json.loads(Path("build/generated/ps_reference/expected.json").read_text())
    log = Path("report/board_ps_pitch_test.log").read_text(encoding="utf-8-sig")
    results = []
    for kind, rows, prefix in (("PCM", expected["expected"], "codex_pitch_out"),
                                ("NATIVE", expected["native_expected"], "codex_pitch_native_out")):
        for row in rows:
            path = f"/tmp/{prefix}_{row['ratio_q16']}.raw"
            pattern = (rf"{kind} RATIO={row['ratio_q16']} RC=0\s+"
                       rf"{row['bytes']} {re.escape(path)}\s+"
                       rf"{row['sha256']}  {re.escape(path)}")
            passed = re.search(pattern, log) is not None
            results.append({"format": kind, "ratio_q16": row["ratio_q16"], "passed": passed})
    invalid_passed = "INVALID_RATIO_RC=2" in log
    binary_sha = hashlib.sha256(Path("build/generated/ps_reference/pitch_fixed").read_bytes()).hexdigest()
    binary_matched = f"{binary_sha}  /tmp/codex_pitch_fixed" in log
    result = {"port": "COM14", "scope": "PS-only arithmetic and sample-format tests, no audio listening or PL run",
              "program_sha256": binary_sha, "binary_matched": binary_matched,
              "invalid_ratio_rejected": invalid_passed, "cases": results}
    Path("report/board_ps_pitch_check.json").write_text(json.dumps(result, indent=2) + "\n")
    if not binary_matched or not invalid_passed or not all(x["passed"] for x in results):
        raise SystemExit("Board reference verification FAILED")
    print(f"PASS: {len(results)} PCM16/native format cases and invalid-ratio rejection on COM14")


if __name__ == "__main__":
    main()
