from pathlib import Path
import unittest

from src.reference.quality_identity.target_profile import build_profile, parse_world_profile, verify_profile


class TargetProfileV2Tests(unittest.TestCase):
    WORLD = Path('build/generated/world_register_20261016/target_t5_8_20s.profile.txt')

    def test_world_parse_and_integrity(self):
        self.assertEqual(len(parse_world_profile(self.WORLD)['spectrum_db']), 513)
        profile = build_profile(self.WORLD)
        self.assertTrue(profile['runtime_capabilities']['a1_world_ready'])
        self.assertFalse(profile['runtime_capabilities']['neural_target_condition_ready'])
        self.assertTrue(verify_profile(profile))
        profile['pitch_hz']['median'] = 191
        self.assertFalse(verify_profile(profile))

    def test_neural_gate_requires_all_evidence(self):
        profile = build_profile(self.WORLD, speaker_embedding=[0.1, 0.2],
                                embedding_model='test', snr_db=25, native_clip_samples=0)
        self.assertTrue(profile['runtime_capabilities']['neural_target_condition_ready'])
        self.assertTrue(verify_profile(profile))


if __name__ == '__main__':
    unittest.main()
