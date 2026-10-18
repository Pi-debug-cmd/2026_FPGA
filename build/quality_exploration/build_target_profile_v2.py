"""Wrap a proven board WORLD registration profile in the frozen TargetProfile v2 contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.reference.quality_identity.target_profile import build_profile, verify_profile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('world_profile', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    profile = build_profile(args.world_profile)
    if not verify_profile(profile):
        raise RuntimeError('Generated profile failed integrity verification')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'output': str(args.output), 'integrity': profile['integrity'],
        'runtime_capabilities': profile['runtime_capabilities'],
        'acceptance': profile['acceptance'],
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
