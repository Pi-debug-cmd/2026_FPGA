import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

from src.reference.world_registration import fit_configuration, save_configuration, load_enrollment
from src.reference.audio_io import write_pcm16
from src.reference.source_target_mapping import map_pitch
from src.reference.timbre_envelope import apply_envelope


class WorldRegistrationTests(unittest.TestCase):
    def test_configuration_roundtrip_preserves_pitch_and_spectral_mapping(self):
        pitch = 110 * np.exp(np.linspace(-.1, .1, 400))
        spectrum = np.tile(np.exp(np.linspace(2, -2, 513)), (400, 1))
        target_shape = np.linspace(1, -1, 513)
        config = fit_configuration(pitch, spectrum, pitch * 1.7, target_shape)
        with tempfile.TemporaryDirectory(dir='build/generated') as directory:
            path = Path(directory) / 'config.json'
            save_configuration(path, config)
            loaded = json.loads(path.read_text(encoding='utf-8'))
        np.testing.assert_allclose(map_pitch(pitch, loaded['pitch']), pitch * 1.7)
        mapped = apply_envelope(spectrum, np.ones(400, bool), loaded['envelope'], loaded['envelope_strength'])
        self.assertTrue(np.all(np.isfinite(mapped)))
        np.testing.assert_allclose(mapped.sum(axis=1), spectrum.sum(axis=1))
        self.assertFalse(loaded['speaker_identity_accepted'])
        self.assertFalse(loaded['realtime_accepted'])

    def test_nonfinite_configuration_does_not_replace_previous_file(self):
        with tempfile.TemporaryDirectory(dir='build/generated') as directory:
            path = Path(directory) / 'config.json'
            path.write_text('previous', encoding='utf-8')
            with self.assertRaises(ValueError):
                save_configuration(path, {'bad': float('nan')})
            self.assertEqual(path.read_text(encoding='utf-8'), 'previous')

    def test_short_or_clipped_enrollment_rejected(self):
        with tempfile.TemporaryDirectory(dir='build/generated') as directory:
            path = Path(directory) / 'capture.wav'
            for signal in [np.zeros(16000), np.ones(80000)]:
                write_pcm16(path, signal)
                with self.assertRaises(ValueError):
                    load_enrollment(path)

    def test_insufficient_voiced_input_rejected(self):
        with self.assertRaises(ValueError):
            fit_configuration(np.zeros(400), np.ones((400, 513)),
                              np.ones(400) * 200, np.zeros(513))


if __name__ == '__main__':
    unittest.main()
