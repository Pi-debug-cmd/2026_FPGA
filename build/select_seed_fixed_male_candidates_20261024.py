"""Apply the frozen five-gate rule to a fixed per-utterance candidate matrix."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


GATES = {"identity": 0.45, "identity_p10": 0.35, "leakage": 0.10, "utmos": 2.30, "cer": 0.15}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def passes(metrics: dict) -> dict:
    if set(metrics) != set(GATES) or not all(math.isfinite(float(value)) for value in metrics.values()):
        raise ValueError("Each candidate must have five finite metrics")
    return {
        "identity": metrics["identity"] >= GATES["identity"],
        "identity_p10": metrics["identity_p10"] >= GATES["identity_p10"],
        "leakage": metrics["leakage"] <= GATES["leakage"],
        "utmos": metrics["utmos"] >= GATES["utmos"],
        "cer": metrics["cer"] <= GATES["cer"],
    }


def main() -> None:
    args = parse_args()
    matrix = json.loads(args.matrix.read_text(encoding="utf-8"))
    datasets = []
    for item in matrix["datasets"]:
        if {candidate["candidate"] for candidate in item["candidates"]} != {"A", "B"}:
            raise ValueError(f"{item['dataset']} does not contain exactly candidates A and B")
        evaluated = []
        for candidate in item["candidates"]:
            passed = passes(candidate["metrics"])
            evaluated.append({**candidate, "passed": passed, "all_gates_pass": all(passed.values())})
        eligible = [candidate for candidate in evaluated if candidate["all_gates_pass"]]
        selected = max(eligible, key=lambda candidate: candidate["metrics"]["identity"])["candidate"] if eligible else None
        datasets.append({"dataset": item["dataset"], "candidates": evaluated, "selected": selected, "passed": selected is not None})

    result = {
        "kind": "strict_fixed_male_gated_candidate_selection",
        "task": matrix["task"],
        "date": matrix["date"],
        "gates": GATES,
        "selection_rule": "discard any candidate failing a gate, then select highest target identity",
        "candidate_definitions": matrix["candidate_definitions"],
        "datasets": datasets,
        "all_datasets_pass": all(item["passed"] for item in datasets),
        "played": False,
        "board_touched": False,
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in datasets:
        print(f"{item['dataset']} selected={item['selected']} pass={item['passed']}")
    print(f"ALL_DATASETS_PASS {result['all_datasets_pass']}")


if __name__ == "__main__":
    main()
