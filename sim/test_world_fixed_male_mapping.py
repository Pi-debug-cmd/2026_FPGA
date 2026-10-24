import unittest

import numpy as np

from src.reference.world_fixed_male_mapping import (
    blend_aperiodicity,
    map_log_f0,
    normalized_log_shape,
    targetize_spectra,
    warp_bins,
)


class WorldFixedMaleMappingTest(unittest.TestCase):
    def test_warp_identity_and_validation(self):
        values = np.array([0.0, 1.0, 4.0, 9.0])
        np.testing.assert_allclose(warp_bins(values, 1.0), values)
        with self.assertRaises(ValueError):
            warp_bins(values, 0.0)

    def test_normalized_shape_ignores_frame_gain(self):
        spectra = np.array([[1.0, 2.0, 4.0], [3.0, 6.0, 12.0], [2.0, 1.0, 1.0]])
        shape = normalized_log_shape(spectra, np.array([True, True, False]))
        expected = np.log(np.array([1.0, 2.0, 4.0]))
        expected -= expected.mean()
        np.testing.assert_allclose(shape, expected, atol=1e-12)

    def test_zero_strength_preserves_spectrum_power(self):
        spectra = np.array([[1.0, 2.0, 3.0], [2.0, 3.0, 5.0]])
        voiced = np.array([True, False])
        shape = normalized_log_shape(spectra, np.array([True, True]))
        mapped = targetize_spectra(spectra, voiced, shape, shape, 1.0, 0.0, 1.0, 3.0)
        np.testing.assert_allclose(mapped, spectra)
        np.testing.assert_allclose(mapped.sum(axis=1), spectra.sum(axis=1))

    def test_pitch_mapping_preserves_unvoiced_and_hits_target_median(self):
        f0 = np.array([0.0, 90.0, 100.0, 110.0])
        mapped = map_log_f0(f0, (90.0, 100.0, 110.0), (180.0, 200.0, 220.0))
        self.assertEqual(mapped[0], 0.0)
        self.assertAlmostEqual(mapped[2], 200.0)

    def test_aperiodicity_endpoints(self):
        source = np.array([[0.1, 0.2], [0.3, 0.4]])
        target = np.array([0.7, 0.8])
        voiced = np.array([True, False])
        np.testing.assert_allclose(blend_aperiodicity(source, target, voiced, 0.0), source)
        mixed = blend_aperiodicity(source, target, voiced, 1.0)
        np.testing.assert_allclose(mixed[0], target)
        np.testing.assert_allclose(mixed[1], source[1])


if __name__ == '__main__':
    unittest.main()
