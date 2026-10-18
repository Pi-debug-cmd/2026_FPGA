"""Visualize spectrograms: target A, teacher C, student D, raw G5000."""
import numpy as np, librosa, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
files = [
 ("A target", r"D:\总进度\全尺寸学生试听_2026-10-06\1_目标人物原声.wav"),
 ("C teacher CV3", r"D:\总进度\全尺寸学生试听_2026-10-06\3_教师CV3转换.wav"),
 ("D student", r"D:\总进度\全尺寸学生试听_2026-10-06\4_全尺寸学生转换.wav"),
 ("raw G5000", r"D:\总进度\raw_G5000_test_20261007\raw_G5000_output.wav"),
]
fig, axes = plt.subplots(4, 1, figsize=(12, 10))
for ax, (name, p) in zip(axes, files):
    y, sr = librosa.load(p, sr=16000)
    S = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=1024, hop_length=160)), ref=np.max)
    img = librosa.display.specshow(S, sr=sr, hop_length=160, x_axis="time", y_axis="hz", ax=ax, cmap="magma")
    ax.set_title(name); ax.set_ylim(0, 6000)
plt.tight_layout()
out = r"D:\总进度\spectrogram_compare_20261007.png"
plt.savefig(out, dpi=110)
print("saved", out)
