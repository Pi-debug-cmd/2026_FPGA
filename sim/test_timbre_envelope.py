"""Envelope transfer must preserve level and leave unvoiced speech intact."""
import unittest
import numpy as np
from src.reference.timbre_envelope import apply_envelope, normalized_log_shape, register_envelope


class TimbreEnvelopeTests(unittest.TestCase):
    def test_loudness_does_not_change_profile_shape(self):
        spectrum = np.exp(np.linspace(-2, 2, 513))[None, :]
        a = normalized_log_shape(spectrum, [True])
        b = normalized_log_shape(spectrum * 100, [True])
        np.testing.assert_allclose(a, b, atol=1e-12)
        profile = register_envelope(a, b, 16000)
        self.assertAlmostEqual(profile['formant_warp'], 1)
        self.assertLess(np.max(np.abs(profile['log_power_delta'])), 1e-10)

    def test_mapping_preserves_energy_and_unvoiced_frames(self):
        spectrum = np.random.default_rng(17).uniform(.1, 1, (3, 513))
        profile = {'formant_warp': 1.2, 'log_power_delta': np.linspace(-.5, .5, 513).tolist()}
        result = apply_envelope(spectrum, [True, False, True], profile)
        np.testing.assert_array_equal(result[1], spectrum[1])
        np.testing.assert_allclose(result.sum(axis=1), spectrum.sum(axis=1), rtol=1e-12)
        self.assertTrue(np.all(result > 0))
        np.testing.assert_allclose(apply_envelope(spectrum, [True] * 3, profile, 0), spectrum)

    def test_invalid_spectra_rejected(self):
        for spectrum in [np.zeros((1, 513)), np.full((1, 513), np.nan)]:
            with self.assertRaises(ValueError):
                normalized_log_shape(spectrum, [True])
