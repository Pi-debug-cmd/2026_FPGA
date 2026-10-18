"""Synthetic correctness gates, not speech quality or board performance claims."""

import unittest
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

from src.reference.pitch_shift import PitchShifter


class PitchShiftTests(unittest.TestCase):
    def test_bypass_is_exact(self):
        samples = np.array([-32768, -1, 0, 1, 32767] * 1000)
        np.testing.assert_array_equal(PitchShifter().process(samples), samples)

    def test_chunk_boundaries_preserve_state(self):
        samples = np.random.default_rng(2026).integers(-32768, 32768, 8000)
        for ratio in (0.5, 0.8, 1.0, 1.25, 2.0):
            with self.subTest(ratio=ratio):
                expected = PitchShifter(ratio).process(samples)
                model = PitchShifter(ratio)
                parts = [model.process(part) for part in np.array_split(samples, 73)]
                np.testing.assert_array_equal(np.concatenate(parts), expected)

    def test_reset_reproduces_startup(self):
        model = PitchShifter(1.5)
        samples = np.arange(5000, dtype=np.float64)
        expected = model.process(samples)
        model.reset()
        np.testing.assert_array_equal(model.process(samples), expected)

    def test_silence_and_amplitude_bounds(self):
        for ratio in (0.5, 1.0, 2.0):
            model = PitchShifter(ratio)
            np.testing.assert_array_equal(model.process(np.zeros(2000)), 0)
            samples = np.random.default_rng(7).integers(-32768, 32768, 10000)
            output = model.process(samples)
            self.assertTrue(np.all(np.isfinite(output)))
            self.assertGreaterEqual(output.min(), -32768)
            self.assertLessEqual(output.max(), 32767)

    def test_sine_frequency_ratio(self):
        rate = 16000
        frequency = 400
        samples = 12000 * np.sin(2 * np.pi * frequency * np.arange(rate * 2) / rate)
        for ratio in (0.5, 0.8, 1.25, 1.5, 2.0):
            with self.subTest(ratio=ratio):
                output = PitchShifter(ratio).process(samples)[rate:]
                spectrum = abs(np.fft.rfft(output * np.hanning(len(output))))
                peak = np.fft.rfftfreq(len(output), 1 / rate)[np.argmax(spectrum)]
                self.assertLessEqual(abs(peak / (frequency * ratio) - 1), 0.02)

    def test_reject_invalid_input(self):
        for ratio in (float("nan"), float("inf"), 0.4, 2.1):
            with self.assertRaises(ValueError):
                PitchShifter(ratio)
        for samples in ([[1, 2]], [float("nan")], [float("inf")]):
            with self.assertRaises(ValueError):
                PitchShifter().process(samples)

    def test_wav_cli_preserves_pcm_and_format_in_bypass(self):
        samples = np.array([-32768, -1, 0, 1, 32767] * 101, dtype="<i2")
        root = Path(__file__).resolve().parents[1]
        temporary_root = root / "tmp"
        temporary_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
            source = Path(directory) / "input.wav"
            output = Path(directory) / "output.wav"
            with wave.open(str(source), "wb") as stream:
                stream.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                stream.writeframes(samples.tobytes())
            subprocess.run([sys.executable, str(root / "src/reference/pitch_shift.py"),
                            str(source), str(output), "--block", "73"], check=True)
            with wave.open(str(output), "rb") as stream:
                self.assertEqual((stream.getnchannels(), stream.getsampwidth(),
                                  stream.getframerate(), stream.getnframes()),
                                 (1, 2, 16000, len(samples)))
                self.assertEqual(stream.readframes(len(samples)), samples.tobytes())


if __name__ == "__main__":
    unittest.main()
