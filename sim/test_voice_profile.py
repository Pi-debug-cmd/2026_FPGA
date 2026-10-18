"""Registration rejection, known F0 and PCM24/channel/resampling tests."""

import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from src.reference.audio_io import downsample_16k, read_pcm_wav, write_pcm16
from src.reference.voice_profile import build_profile, calibration_ratio, estimate_f0, register_wav


class VoiceProfileTests(unittest.TestCase):
    def test_known_f0_and_ratio(self):
        time = np.arange(16000 * 4) / 16000
        source = build_profile(0.2 * np.sin(2 * np.pi * 160 * time))
        target = build_profile(0.2 * np.sin(2 * np.pi * 240 * time))
        self.assertLess(abs(source["f0_median_hz"] - 160), 0.5)
        ratio, quantized = calibration_ratio(source, target)
        self.assertLess(abs(ratio - 1.5), 0.01)
        self.assertLess(abs(quantized / 65536 - 1.5), 0.01)

    def test_silence_clipping_and_noise_rejected(self):
        for samples in (np.zeros(64000), np.ones(64000),
                        np.random.default_rng(7).normal(0, 0.1, 64000)):
            with self.assertRaises(ValueError):
                build_profile(samples)

    def test_pcm24_channel_decode(self):
        root = Path(__file__).resolve().parents[1] / "tmp"
        root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            path = Path(directory) / "pcm24.wav"
            values = np.array([[-8388608, 8388607], [-1, 1], [0, 0]], dtype=np.int32)
            flat = values.reshape(-1)
            packed = np.column_stack([flat & 255, (flat >> 8) & 255,
                                      (flat >> 16) & 255]).astype(np.uint8)
            with wave.open(str(path), "wb") as stream:
                stream.setparams((2, 3, 48000, 0, "NONE", "not compressed"))
                stream.writeframes(packed.tobytes())
            for channel in (0, 1):
                rate, samples = read_pcm_wav(path, channel)
                self.assertEqual(rate, 48000)
                np.testing.assert_array_equal(samples, values[:, channel] / 8388608)

    def test_fir_rejects_alias_and_retains_voice_frequency(self):
        time = np.arange(48000) / 48000
        low = downsample_16k(48000, np.sin(2 * np.pi * 400 * time))[100:-100]
        high = downsample_16k(48000, np.sin(2 * np.pi * 12000 * time))[100:-100]
        self.assertGreater(np.sqrt(np.mean(low * low)), 0.69)
        self.assertLess(np.sqrt(np.mean(high * high)), 0.001)
        self.assertEqual(len(downsample_16k(48000, np.ones(48000))), 16000)

    def test_invalid_registration_preserves_profile(self):
        root = Path(__file__).resolve().parents[1] / "tmp"
        root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            path, profile = Path(directory) / "silence.wav", Path(directory) / "target.json"
            write_pcm16(path, np.zeros(64000))
            profile.write_text("existing profile", encoding="utf-8")
            with self.assertRaises(ValueError):
                register_wav(path, profile)
            self.assertEqual(profile.read_text(encoding="utf-8"), "existing profile")

    def test_short_recording_and_out_of_range_mapping_rejected(self):
        f0, frames = estimate_f0(np.zeros(100))
        self.assertEqual((len(f0), frames), (0, 0))
        with self.assertRaises(ValueError):
            calibration_ratio({"f0_median_hz": 100}, {"f0_median_hz": 300})


if __name__ == "__main__":
    unittest.main()
