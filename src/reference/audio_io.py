"""PCM WAV decoding and offline integer-ratio FIR downsampling to 16 kHz."""

import hashlib
import wave
from pathlib import Path

import numpy as np


def read_pcm_wav(path, channel=0):
    with wave.open(str(path), "rb") as stream:
        rate = stream.getframerate()
        channels = stream.getnchannels()
        width = stream.getsampwidth()
        if stream.getcomptype() != "NONE" or width not in (1, 2, 3, 4):
            raise ValueError("Expected uncompressed integer PCM WAV")
        if not 0 <= channel < channels:
            raise ValueError("Requested channel is absent")
        raw = stream.readframes(stream.getnframes())
    if width == 1:
        samples = (np.frombuffer(raw, np.uint8).astype(np.float64) - 128) / 128
    elif width == 3:
        packed = np.frombuffer(raw, np.uint8).reshape(-1, 3).astype(np.int32)
        signed = packed[:, 0] | (packed[:, 1] << 8) | (packed[:, 2] << 16)
        samples = ((signed ^ 0x800000) - 0x800000).astype(np.float64) / 8388608
    else:
        samples = np.frombuffer(raw, dtype=f"<i{width}").astype(np.float64) / (1 << (8 * width - 1))
    return rate, samples.reshape(-1, channels)[:, channel].copy()


def downsample_16k(rate, samples):
    samples = np.asarray(samples, dtype=np.float64)
    if samples.ndim != 1 or not np.all(np.isfinite(samples)):
        raise ValueError("Expected finite mono samples")
    if rate == 16000:
        return samples.copy()
    if rate not in (32000, 48000) or len(samples) < 127:
        raise ValueError("Offline resampling supports 16, 32 or 48 kHz; need >=127 samples")
    factor = rate // 16000
    offsets = np.arange(127, dtype=np.float64) - 63
    cutoff = 0.45 / factor
    kernel = 2 * cutoff * np.sinc(2 * cutoff * offsets) * np.hamming(127)
    kernel /= kernel.sum()
    # Centered offline filter; 63-sample future context, zero-padded boundaries.
    return np.convolve(samples, kernel, mode="same")[::factor]


def write_pcm16(path, samples, rate=16000):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(np.rint(np.asarray(samples) * 32768), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        stream.writeframes(pcm.tobytes())


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()
