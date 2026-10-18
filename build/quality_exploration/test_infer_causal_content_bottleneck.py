import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).with_name("infer_causal_content_bottleneck.py")
SPEC = importlib.util.spec_from_file_location("causal_bottleneck_infer", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CausalBottleneckInferenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        checkpoint = MODULE.DEFAULT_CHECKPOINT
        cls.model, cls.metadata, _, _, cls.validation, _ = MODULE.load_verified_checkpoint(checkpoint)
        cls.source = MODULE.read_features(cls.validation[0].source)

    def test_checkpoint_and_split_are_verified(self):
        expected = self.metadata["split"]
        self.assertTrue(set(expected["train_speakers"]).isdisjoint(expected["validation_speakers"]))
        self.assertEqual(len(self.validation), expected["validation_pairs"])

    def test_full_utterance_output_is_finite_and_same_length(self):
        converted = MODULE.infer_features(self.model, self.source)
        self.assertEqual(converted.shape, self.source.shape)
        self.assertEqual(converted.dtype, np.float32)
        self.assertTrue(np.isfinite(converted).all())

    def test_stateful_chunks_match_full_utterance(self):
        full = MODULE.infer_features(self.model, self.source)
        chunked = MODULE.infer_features(self.model, self.source, chunk_frames=37)
        self.assertLessEqual(float(np.max(np.abs(full - chunked))), 5e-6)


if __name__ == "__main__":
    unittest.main()
