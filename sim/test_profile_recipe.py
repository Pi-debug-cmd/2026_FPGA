"""Profile provenance and rejected mappings must not corrupt saved settings."""
import json
from pathlib import Path
import tempfile
import unittest

from src.ps.profile_recipe import build_recipe, load_recipe, mapping


def profile(f0):
    return {'version': 1, 'kind': 'f0_calibration_only', 'sample_rate': 16000,
            'f0_median_hz': f0, 'voiced_frame_coverage_s': 4, 'clip_fraction': 0}


class ProfileRecipeTests(unittest.TestCase):
    def test_mapping_and_hardware_boundaries(self):
        for source, target, q16 in [(160, 240, 98304), (200, 100, 32768),
                                    (100, 200, 131072), (200, 200, 65536)]:
            self.assertEqual(mapping(profile(source), profile(target))[1], q16)
        with self.assertRaises(ValueError):
            mapping(profile(100), profile(300))

    def test_bad_profiles_rejected(self):
        for field, value in [('f0_median_hz', float('nan')), ('f0_median_hz', True),
                             ('voiced_frame_coverage_s', 2.99), ('clip_fraction', 0.011),
                             ('kind', 'speaker_identity_model')]:
            bad = profile(160)
            bad[field] = value
            with self.assertRaises(ValueError):
                mapping(bad, profile(200))

    def test_roundtrip_preservation_and_tampered_ratio(self):
        root = Path(__file__).resolve().parents[1] / 'tmp'
        root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            base = Path(directory)
            source, target, output = [base / name for name in ['source.json', 'target.json', 'recipe.json']]
            source.write_text(json.dumps(profile(160)))
            target.write_text(json.dumps(profile(240)))
            build_recipe(source, target, output)
            recipe = load_recipe(output)
            self.assertEqual(recipe['ratio_q16'], 98304)
            original = output.read_bytes()
            target.write_text(json.dumps(profile(400)))
            with self.assertRaises(ValueError):
                build_recipe(source, target, output)
            self.assertEqual(output.read_bytes(), original)
            with self.assertRaises(ValueError):
                build_recipe(source, target, source)
            recipe['ratio_q16'] = 65536
            output.write_text(json.dumps(recipe))
            with self.assertRaises(ValueError):
                load_recipe(output)
