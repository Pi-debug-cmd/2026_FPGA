import unittest
import numpy as np
from src.reference.spectral_balance import fit_balance, apply_balance, fit_low_shelf


class SpectralBalanceTests(unittest.TestCase):
    def test_low_shelf_requires_all_target_recordings_to_agree(self):
        frequency = np.linspace(0, 8000, 513)
        source = np.where(frequency < 400, 2., 0.)
        agreed = fit_low_shelf(source, [np.zeros(513), np.zeros(513)])
        self.assertTrue(agreed['all_target_recordings_support_reduction'])
        self.assertGreater(agreed['low_shelf_attenuation_db'], 0)
        conflict = fit_low_shelf(source, [np.zeros(513), source * 2])
        self.assertFalse(conflict['all_target_recordings_support_reduction'])
        self.assertEqual(conflict['low_shelf_attenuation_db'], 0)

    def test_known_tilt_fit_and_clipping(self):
        frequency = np.linspace(0, 8000, 513)
        target = 8 * np.log2(np.maximum(frequency, 80) / 1000) * np.log(10) / 10
        profile = fit_balance(np.zeros(513), target)
        self.assertAlmostEqual(profile['fitted_slope_db_per_octave'], 8)
        self.assertEqual(profile['slope_db_per_octave'], 4)

    def test_final_gains_bounded_with_frame_power_and_unvoiced_preserved(self):
        spectrum = np.exp(np.random.default_rng(8).normal(0, 2, (8, 513)))
        profile = fit_balance(np.zeros(513), np.linspace(-2, 2, 513))
        voiced = np.array([True] * 6 + [False] * 2)
        result = apply_balance(spectrum, voiced, profile)
        np.testing.assert_allclose(result.sum(axis=1), spectrum.sum(axis=1), rtol=1e-10)
        gain_db = 10 * np.log10(result / spectrum)
        self.assertLessEqual(np.max(abs(gain_db)), 4.00000001)
        np.testing.assert_array_equal(result[~voiced], spectrum[~voiced])

    def test_flat_mapping_preserved(self):
        spectrum = np.ones((3, 513))
        profile = fit_balance(np.zeros(513), np.zeros(513))
        np.testing.assert_allclose(apply_balance(spectrum, np.ones(3, bool), profile), spectrum, atol=1e-10)


if __name__ == '__main__':
    unittest.main()
