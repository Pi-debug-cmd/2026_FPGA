"""Streaming floating-point pitch baseline; no target timbre conversion yet."""

import argparse
import math
import wave
from pathlib import Path

import numpy as np


class PitchShifter:
    """Two variable delay taps with linear interpolation and triangle fades.

    State persists across process() calls. Configure a fixed ratio per run;
    live parameter switching and fixed-point equivalence are not implemented.
    Input/output are mono PCM amplitudes represented as float64.
    """

    def __init__(self, ratio=1.0, window=1024):
        if not math.isfinite(ratio) or not 0.5 <= ratio <= 2.0:
            raise ValueError("ratio must be finite and in [0.5, 2.0]")
        if not isinstance(window, int) or window < 16:
            raise ValueError("window must be an integer >= 16")
        self.ratio = ratio
        self.window = window
        self.reset()

    def reset(self):
        self.buffer = np.zeros(self.window + 4, dtype=np.float64)
        self.write_index = 0
        self.phase = 0.0

    def _tap(self, phase):
        # At least two samples behind the current write avoids reading future data.
        position = (self.write_index - (2.0 + phase * self.window)) % len(self.buffer)
        index = int(position)
        fraction = position - index
        return (self.buffer[index] * (1.0 - fraction)
                + self.buffer[(index + 1) % len(self.buffer)] * fraction)

    def process(self, samples):
        samples = np.asarray(samples, dtype=np.float64)
        if samples.ndim != 1 or not np.all(np.isfinite(samples)):
            raise ValueError("samples must be a finite mono array")
        output = np.empty(len(samples), dtype=np.float64)
        for i, sample in enumerate(samples):
            self.buffer[self.write_index] = sample
            if self.ratio == 1.0:
                output[i] = sample  # Exact bypass; delay differs from shifted mode.
            else:
                weight = 1.0 - abs(2.0 * self.phase - 1.0)
                other_phase = (self.phase + 0.5) % 1.0
                output[i] = (weight * self._tap(self.phase)
                             + (1.0 - weight) * self._tap(other_phase))
                self.phase = (self.phase + (1.0 - self.ratio) / self.window) % 1.0
            self.write_index = (self.write_index + 1) % len(self.buffer)
        return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ratio", type=float, default=1.0)
    parser.add_argument("--window", type=int, default=1024)
    parser.add_argument("--block", type=int, default=256)
    args = parser.parse_args()
    if args.block <= 0:
        parser.error("--block must be positive")
    if args.input.resolve() == args.output.resolve():
        parser.error("input and output must be different files")
    shifter = PitchShifter(args.ratio, args.window)
    with wave.open(str(args.input), "rb") as source:
        if (source.getnchannels(), source.getsampwidth(), source.getcomptype()) != (1, 2, "NONE"):
            parser.error("input must be uncompressed mono PCM16 WAV")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(args.output), "wb") as destination:
            destination.setparams(source.getparams())
            while raw := source.readframes(args.block):
                samples = np.frombuffer(raw, dtype="<i2").astype(np.float64)
                processed = shifter.process(samples)
                pcm = np.clip(np.rint(processed), -32768, 32767).astype("<i2")
                destination.writeframes(pcm.tobytes())


if __name__ == "__main__":
    main()
