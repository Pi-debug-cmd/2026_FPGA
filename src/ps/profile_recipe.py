"""Portable F0 profile-to-PL recipe; stdlib only, usable on the factory Linux."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def validate_profile(profile):
    if (profile.get('version') != 1 or profile.get('kind') != 'f0_calibration_only'
            or profile.get('sample_rate') != 16000):
        raise ValueError('Expected a version 1 F0 calibration profile')
    f0 = profile.get('f0_median_hz')
    coverage = profile.get('voiced_frame_coverage_s')
    clipping = profile.get('clip_fraction')
    for value in [f0, coverage, clipping]:
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('Profile statistics must be finite numbers')
    if not 75 <= f0 <= 400 or coverage < 3 or not 0 <= clipping <= 0.01:
        raise ValueError('Profile failed F0, voiced coverage or clipping checks')
    return float(f0)


def mapping(source, target):
    ratio = validate_profile(target) / validate_profile(source)
    if not 0.5 <= ratio <= 2.0:
        raise ValueError('Target/source F0 ratio exceeds PL range [0.5, 2.0]')
    return ratio, int(round(ratio * 65536))


def build_recipe(source_path, target_path, output_path):
    source_path, target_path, output_path = map(Path, [source_path, target_path, output_path])
    if output_path.resolve() in [source_path.resolve(), target_path.resolve()]:
        raise ValueError('Recipe output must differ from both profile inputs')
    source_raw, target_raw = source_path.read_bytes(), target_path.read_bytes()
    source, target = json.loads(source_raw), json.loads(target_raw)
    ratio, q16 = mapping(source, target)
    recipe = {'version': 1, 'kind': 'f0_pitch_mapping_only', 'hardware': 'pitch_control_v2',
              'source_profile': source, 'target_profile': target,
              'source_profile_sha256': hashlib.sha256(source_raw).hexdigest(),
              'target_profile_sha256': hashlib.sha256(target_raw).hexdigest(),
              'ratio': ratio, 'ratio_q16': q16}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + '.tmp')
    temporary.write_text(json.dumps(recipe, indent=2) + '\n', encoding='utf-8')
    temporary.replace(output_path)
    return recipe


def load_recipe(path):
    recipe = json.loads(Path(path).read_text())
    if (recipe.get('version') != 1 or recipe.get('kind') != 'f0_pitch_mapping_only'
            or recipe.get('hardware') != 'pitch_control_v2'):
        raise ValueError('Unsupported recipe or hardware version')
    ratio, q16 = mapping(recipe['source_profile'], recipe['target_profile'])
    if type(recipe.get('ratio_q16')) is not int or recipe['ratio_q16'] != q16:
        raise ValueError('Stored ratio does not match embedded profiles')
    if recipe.get('ratio') != ratio:
        raise ValueError('Stored floating ratio does not match embedded profiles')
    return recipe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('target', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        recipe = build_recipe(args.source, args.target, args.output)
    except (ValueError, KeyError) as exc:
        parser.exit(2, f'Calibration rejected: {exc}\n')
    print(f"ratio={recipe['ratio']:.6f} ratio_q16={recipe['ratio_q16']}")


if __name__ == '__main__':
    main()
