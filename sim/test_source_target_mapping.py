import unittest
import numpy as np
from src.reference.source_target_mapping import fit_pitch_mapping, map_pitch


class SourceTargetMappingTests(unittest.TestCase):
    def test_different_sources_reach_same_target_without_flattening(self):
        contour = np.linspace(-.12, .12, 501)
        target = 195 * np.exp(contour)
        for center in [90, 140, 260]:
            source = center * np.exp(contour)
            profile = fit_pitch_mapping(source, target)
            mapped = map_pitch(np.r_[0, source, 0], profile)
            self.assertEqual(mapped[0], 0)
            self.assertEqual(mapped[-1], 0)
            np.testing.assert_allclose(mapped[1:-1], target, rtol=1e-12)
            self.assertGreater(np.ptp(mapped), 30)

    def test_apply_uses_calibration_not_test_distribution(self):
        source = np.linspace(100, 130, 400)
        profile = fit_pitch_mapping(source, source * 1.5)
        np.testing.assert_allclose(map_pitch([110, 140], profile), [165, 210])

    def test_constant_enrollment_fallback_and_output_limits(self):
        profile = fit_pitch_mapping(np.full(400, 100.), np.full(400, 200.))
        self.assertTrue(profile['low_source_spread_fallback'])
        np.testing.assert_allclose(map_pitch([0, 1, 100, 1000], profile), [0, 75, 200, 400])

    def test_insufficient_or_invalid_calibration_rejected(self):
        good = np.full(400, 150.)
        for bad in [np.zeros(400), np.full(299, 100.), np.r_[good, np.nan], -good]:
            with self.assertRaises(ValueError):
                fit_pitch_mapping(bad, good)

    def test_spread_scale_bounded(self):
        source = np.exp(np.linspace(4.7, 4.8, 400))
        target = np.exp(np.linspace(4.4, 5.8, 400))
        self.assertEqual(fit_pitch_mapping(source, target)['scale'], 2.)


if __name__ == '__main__':
    unittest.main()
