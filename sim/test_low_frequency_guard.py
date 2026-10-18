import unittest
import numpy as np
from src.reference.low_frequency_guard import suppress_low_events


class LowFrequencyGuardTests(unittest.TestCase):
    def test_voiced_signal_preserved_even_with_low_frequency_contamination(self):
        t = np.arange(32000) / 16000
        signal = .1 * np.sin(2 * np.pi * 120 * t) + .3 * np.sin(2 * np.pi * 35 * t)
        result, report = suppress_low_events(signal, np.full(201, 120.))
        np.testing.assert_allclose(result, signal, atol=1e-14)
        self.assertEqual(report['attenuated_frames'], 0)

    def test_low_frequency_event_reduced_but_not_deleted(self):
        t = np.arange(32000) / 16000
        signal = .15 * np.sin(2 * np.pi * 35 * t)
        result, report = suppress_low_events(signal, np.zeros(201))
        ratio = np.sqrt(np.mean(result[8000:24000] ** 2) / np.mean(signal[8000:24000] ** 2))
        self.assertGreater(ratio, .49)
        self.assertLess(ratio, .6)
        self.assertEqual(report['voiced_frames_attenuated'], 0)
        self.assertEqual(report['maximum_gain_difference_above_100hz'], 0)

    def test_unvoiced_high_frequency_noise_preserved(self):
        signal = np.random.default_rng(77).normal(0, .05, 32000)
        result, report = suppress_low_events(signal, np.zeros(201))
        np.testing.assert_allclose(result, signal, atol=1e-14)
        self.assertEqual(report['attenuated_frames'], 0)

    def test_silence_and_invalid_alignment(self):
        result, _ = suppress_low_events(np.zeros(32000), np.zeros(201))
        self.assertTrue(np.all(result == 0))
        with self.assertRaises(ValueError):
            suppress_low_events(np.zeros(32000), np.zeros(200))


if __name__ == '__main__':
    unittest.main()
