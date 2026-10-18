"""Apply a validated F0 recipe to a finite live PL run; no target timbre model."""
import argparse
from pathlib import Path
import subprocess
import time

from profile_recipe import load_recipe

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('recipe', type=Path)
parser.add_argument('--seconds', type=int, default=20)
parser.add_argument('--check-only', action='store_true')
parser.add_argument('--meter', action='store_true')
args = parser.parse_args()
try:
    if not 1 <= args.seconds <= 600:
        raise ValueError('Duration must be 1..600 seconds')
    recipe = load_recipe(args.recipe)
except (ValueError, KeyError) as exc:
    parser.exit(2, f'Recipe rejected: {exc}\n')
print(f"RECIPE_VALIDATED ratio_q16={recipe['ratio_q16']} kind={recipe['kind']}", flush=True)
if not args.check_only:
    script = '/tmp/codex_pl_control_20261011/live_pitch_control_trial_v2.sh'
    if args.meter:
        script = '/tmp/codex_pl_control_20261011/live_pitch_control_trial_meter.sh'
    tag = f'registered_{time.monotonic_ns()}'
    raise SystemExit(subprocess.run(['sh', script, str(recipe['ratio_q16']),
                                    str(args.seconds), tag]).returncode)
