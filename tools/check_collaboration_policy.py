#!/usr/bin/env python3
"""Enforce one traceable scheme/test round per pull-request commit."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

TASK_SUBJECT = re.compile(
    r"^(?:PS|LOCAL-PS|PL|BASE|DOCS|BUILD|TEST)-\d{8}(?:-\d+)?: .+"
)
EVIDENCE_PREFIXES = ("board/", "build/", "report/", "sim/", "src/")
EXEMPT_REPORTS = {"report/ai_worklog.md"}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], check=True, text=True, capture_output=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    commits = git("rev-list", "--reverse", "--no-merges",
                  "%s..%s" % (args.base, args.head)).splitlines()
    failures = []
    for commit in commits:
        subject = git("show", "-s", "--format=%s", commit)
        files = set(git("diff-tree", "--no-commit-id", "--name-only", "-r",
                        commit).splitlines())
        if not TASK_SUBJECT.fullmatch(subject):
            failures.append(
                "%s subject must start with a task id: %r" % (commit[:12], subject)
            )
        evidence_changed = any(
            path.startswith(EVIDENCE_PREFIXES) and path not in EXEMPT_REPORTS
            for path in files
        )
        if evidence_changed and "coummucation.md" not in files:
            failures.append(
                "%s changes scheme/test evidence without coummucation.md" %
                commit[:12]
            )

    if failures:
        print("Collaboration policy failed:", file=sys.stderr)
        for failure in failures:
            print("- " + failure, file=sys.stderr)
        return 1
    print("Collaboration policy passed for %d commit(s)." % len(commits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
