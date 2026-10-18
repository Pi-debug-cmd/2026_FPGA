"""Fixed-point gates against float reference, input boundaries and streaming."""

import unittest

import numpy as np

from src.reference.pitch_shift import PitchShifter
from src.reference.pitch_shift_fixed import FixedPitchShifter, ratio_to_q16


class FixedPitchTests(unittest.TestCase):
    def test_float_error_with_same_quantized_ratio(self):
        samples = np.random.default_rng(88).integers(-32768, 32768, 12000)
        for ratio in (0.5, 0.8, 1.0, 1.25, 1.5, 2.0):
            with self.subTest(ratio=ratio):
                quantized = ratio_to_q16(ratio)
                expected = PitchShifter(quantized / 65536).process(samples)
                actual = FixedPitchShifter(quantized).process(samples).astype(np.float64)
                # Interpolation floor <1 LSB, weight truncation <1 LSB, mix floor <1.
                self.assertLess(np.max(np.abs(expected - actual)), 3.0)

    def test_blocks_and_reset(self):
        samples = np.random.default_rng(9).integers(-32768, 32768, 7001)
        model = FixedPitchShifter(ratio_to_q16(1.25))
        expected = model.process(samples)
        model.reset()
        actual = np.concatenate([model.process(x) for x in np.array_split(samples, 61)])
        np.testing.assert_array_equal(actual, expected)

    def test_bypass_and_range(self):
        samples = np.array([-32768, -1, 0, 1, 32767] * 2000, dtype=np.int16)
        np.testing.assert_array_equal(FixedPitchShifter().process(samples), samples)
        for ratio in (0.5, 0.8, 1.25, 2.0):
            output = FixedPitchShifter(ratio_to_q16(ratio)).process(samples)
            self.assertGreaterEqual(int(output.min()), -32768)
            self.assertLessEqual(int(output.max()), 32767)

    def test_invalid_samples_and_ratio(self):
        for samples in ([1.5], [32768], [-32769], [[1, 2]]):
            with self.assertRaises(ValueError):
                FixedPitchShifter().process(samples)
        for ratio in (32767, 131073, 65536.5):
            with self.assertRaises(ValueError):
                FixedPitchShifter(ratio)


if __name__ == "__main__":
    unittest.main()
