"""Bounded-input adapter for the unchanged LLVC chunk inference contract.

Uses one chunk plus L samples of lookahead; does not require the future file.
Target identity depends on trained weights; this adapter provides no identity.
"""
import numpy as np
import torch


class LLVCAudioStream:
    def __init__(self, model, device=None):
        if not model.lookahead:
            raise ValueError('This adapter explicitly implements the lookahead=True reference contract')
        self.model = model
        self.device = device if device is not None else next(model.parameters()).device
        self.L = model.L
        self.chunk_samples = model.dec_chunk_size * self.L
        self.pending = np.empty(0, dtype=np.float32)
        self.front = torch.zeros(2 * self.L, device=self.device)
        self.enc, self.dec, self.out = model.init_buffers(1, self.device)
        self.pre = model.convnet_pre.init_ctx_buf(1, self.device) if hasattr(model, 'convnet_pre') else None
        self.received = self.produced = 0
        self.closed = False

    def _consume(self):
        results = []
        while len(self.pending) >= self.chunk_samples + self.L:
            shifted = torch.from_numpy(self.pending[self.L:self.L + self.chunk_samples].copy()).to(self.device)
            block = torch.cat((self.front, shifted)).reshape(1, 1, -1)
            with torch.inference_mode():
                speech, self.enc, self.dec, self.out, self.pre = self.model(
                    block, self.enc, self.dec, self.out, self.pre, pad=False)
            self.front = shifted[-2 * self.L:].clone()
            self.pending = self.pending[self.chunk_samples:].copy()
            y = speech.detach().cpu().numpy().reshape(-1).copy()
            assert len(y) == self.chunk_samples and np.isfinite(y).all()
            results.append(y)
            self.produced += len(y)
        return results

    def feed(self, samples):
        if self.closed:
            raise RuntimeError('Stream already finalized')
        x = np.asarray(samples, dtype=np.float32)
        if x.ndim != 1 or not np.isfinite(x).all():
            raise ValueError('Expected finite mono PCM')
        self.received += len(x)
        self.pending = np.concatenate((self.pending, x))
        return self._consume()

    def finish(self):
        if self.closed:
            raise RuntimeError('Stream already finalized')
        self.closed = True
        if self.received == 0:
            return []
        missing = self.received - self.produced
        padding = (-self.received) % self.chunk_samples
        self.pending = np.concatenate((self.pending, np.zeros(padding + self.L, dtype=np.float32)))
        results = self._consume()
        result = np.concatenate(results)[:missing] if results else np.empty(0, dtype=np.float32)
        self.produced = self.received
        assert len(result) == missing
        return [result] if len(result) else []
