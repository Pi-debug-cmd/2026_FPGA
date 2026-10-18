"""Native slot decoding must ignore pad bytes, preserve sign and select left."""
import io
import struct
import unittest
import wave

from board.pack_registration_audio import pack_native


class RegistrationCaptureTests(unittest.TestCase):
    def test_native_boundary_conversion(self):
        values = [-8388608, -257, -256, -1, 0, 255, 256, 8388607]
        raw = b''.join(struct.pack('<II', (value & 0xffffff) | 0xab000000, 123456)
                       for value in values)
        wav, clip = pack_native(raw)
        with wave.open(io.BytesIO(wav), 'rb') as reader:
            self.assertEqual((reader.getframerate(), reader.getnchannels(), reader.getsampwidth()),
                             (32000, 1, 2))
            actual = [x[0] for x in struct.iter_unpack('<h', reader.readframes(len(values)))]
        self.assertEqual(actual, [value // 256 for value in values])
        self.assertEqual(clip, 2 / len(values))

    def test_empty_or_partial_frame_rejected(self):
        for raw in [b'', b'\0' * 7, b'\0' * 9]:
            with self.assertRaises(ValueError):
                pack_native(raw)
