"""Integer PCM16 golden model for the fixed 1024-sample-window RTL."""

import math

import numpy as np


Q = 1 << 16
WINDOW = 1024
DEPTH = 2048
PHASE_MASK = WINDOW * Q - 1


def ratio_to_q16(ratio):
    if not math.isfinite(ratio) or not 0.5 <= ratio <= 2.0:
        raise ValueError("ratio must be finite and in [0.5, 2.0]")
    return int(round(ratio * Q))


class FixedPitchShifter:
    """Two taps, Q16 ratio/phase/weights, arithmetic floor at both mix stages.

    Zero-filled RAM on reset. One accepted input yields one output. TLAST is a
    transport marker and never resets this model. Ratio is fixed per instance.
    """

    def __init__(self, ratio_q16=Q):
        if not isinstance(ratio_q16, int) or not Q // 2 <= ratio_q16 <= 2 * Q:
            raise ValueError("ratio_q16 must be an integer in [32768, 131072]")
        self.ratio_q16 = ratio_q16
        self.reset()

    def reset(self):
        self.buffer = [0] * DEPTH
        self.write_index = 0
        self.phase = 0

    def _tap(self, phase):
        recent = (self.write_index - 2 - (phase >> 16)) & (DEPTH - 1)
        fraction = phase & (Q - 1)
        return ((self.buffer[recent] * (Q - fraction)
                 + self.buffer[(recent - 1) & (DEPTH - 1)] * fraction) >> 16)

    def process(self, samples):
        samples = np.asarray(samples)
        if (samples.ndim != 1 or not np.issubdtype(samples.dtype, np.integer)
                or np.any(samples < -32768) or np.any(samples > 32767)):
            raise ValueError("samples must be a mono integer PCM16 array")
        output = np.empty(len(samples), dtype=np.int16)
        for i, sample in enumerate(samples):
            sample = int(sample)
            self.buffer[self.write_index] = sample
            if self.ratio_q16 == Q:
                output[i] = sample
            else:
                weight = (self.phase >> 9) if self.phase < WINDOW * Q // 2 else (
                    2 * Q - (self.phase >> 9))
                other = self.phase ^ (WINDOW * Q // 2)
                output[i] = (self._tap(self.phase) * weight
                             + self._tap(other) * (Q - weight)) >> 16
                self.phase = (self.phase + Q - self.ratio_q16) & PHASE_MASK
            self.write_index = (self.write_index + 1) & (DEPTH - 1)
        return output
