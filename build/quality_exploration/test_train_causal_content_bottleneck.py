import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import torch


MODULE_PATH = Path(__file__).with_name("train_causal_content_bottleneck.py")
SPEC = importlib.util.spec_from_file_location("causal_bottleneck", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CausalContentBottleneckTest(unittest.TestCase):
    def make_model(self):
        torch.manual_seed(7)
        return MODULE.CausalContentBottleneck(
            np.zeros(17, dtype=np.float32), np.ones(17, dtype=np.float32),
            np.zeros(40, dtype=np.float32), speakers=3, latent_dim=24)

    def test_future_changes_do_not_change_prefix(self):
        model = self.make_model().eval()
        source = torch.randn(2, 20, 20)
        prosody = torch.randn(2, 20, 4)
        self.assertEqual(MODULE.verify_causality(model, source, prosody, boundary=8), 0.0)

    def test_zero_weights_expose_no_source_residual_path(self):
        model = self.make_model().eval()
        for parameter in model.parameters():
            parameter.data.zero_()
        prosody = torch.zeros(1, 12, 4)
        first, _ = model(torch.zeros(1, 12, 17), prosody)
        second, _ = model(torch.full((1, 12, 17), 9.0), prosody)
        self.assertTrue(torch.equal(first, second))
        self.assertEqual(tuple(first.shape), (1, 12, 20))

    def test_relative_prosody_uses_no_future_frame(self):
        frames = np.zeros((12, 20), dtype=np.float32)
        frames[:, 0] = np.linspace(-5, -1, 12)
        frames[:, 18] = np.linspace(-0.3, 0.4, 12)
        frames[:, 19] = 0.3
        changed = frames.copy()
        changed[7:, 0] += 10
        changed[7:, 18] -= 1
        changed[7:, 19] = -20
        self.assertTrue(np.array_equal(
            MODULE.causal_prosody(frames)[:7], MODULE.causal_prosody(changed)[:7]))

    def test_gradient_reversal_changes_only_backward_sign(self):
        value = torch.tensor([1.0, -2.0], requires_grad=True)
        output = MODULE.GradientReverse.apply(value, 0.25)
        self.assertTrue(torch.equal(output, value))
        output.sum().backward()
        self.assertTrue(torch.equal(value.grad, torch.full_like(value, -0.25)))

    def test_manifest_split_has_no_speaker_leakage(self):
        document, _ = MODULE.load_manifest()
        train, validation = MODULE.split_pairs(document)
        self.assertTrue({row.speaker for row in train}.isdisjoint(
            {row.speaker for row in validation}))

    def test_random_crop_is_deterministic_for_same_seed(self):
        pair = MODULE.Pair("speaker", Path("source"), Path("teacher"))
        frames = np.arange(80 * 20, dtype=np.float32).reshape(80, 20)
        with mock.patch.object(MODULE, "read_features", return_value=frames):
            first = MODULE.crop_pair(pair, 32, np.random.default_rng(11))
            second = MODULE.crop_pair(pair, 32, np.random.default_rng(11))
        for left, right in zip(first, second):
            self.assertTrue(np.array_equal(left, right))

    def test_fixed_crop_rejects_short_pair(self):
        pair = MODULE.Pair("speaker", Path("source"), Path("teacher"))
        with mock.patch.object(MODULE, "read_features",
                               return_value=np.zeros((15, 20), dtype=np.float32)):
            with self.assertRaisesRegex(ValueError, "shorter than fixed crop"):
                MODULE.crop_pair(pair, 16, np.random.default_rng(1))

    def test_checkpoint_contains_reproducibility_metadata(self):
        document, manifest = MODULE.load_manifest()
        train, validation = MODULE.split_pairs(document)
        model = self.make_model()
        optimizer = torch.optim.AdamW(model.parameters())
        payload = MODULE.checkpoint_payload(
            model, optimizer, manifest, train, validation, {"seed": 7}, [], 1,
            {"estimated_from_train_speakers_only": True}, {"a": 0})
        self.assertEqual(payload["format"], "causal_content_bottleneck_v1")
        self.assertEqual(len(payload["manifest_sha256"]), 64)
        self.assertTrue(set(payload["split"]["train_speakers"]).isdisjoint(
            payload["split"]["validation_speakers"]))
        for key in ("config", "normalization", "history", "model", "optimizer"):
            self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()
