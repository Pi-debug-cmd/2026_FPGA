import numpy as np, librosa, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axes = plt.subplots(2, 1, figsize=(12, 5))
files = [
 ("teacher (target)", r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\full_train_corpus_16k\src\..\tch\train1.wav"),
 ("overfit output", r"D:\总进度\overfit_test_20261007.wav"),
]
# find actual teacher file
import glob
tch = sorted(glob.glob(r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\full_train_corpus_16k\tch\*.wav"))[0]
files[0] = ("teacher", tch)
for ax, (name, p) in zip(axes, files):
    y, sr = librosa.load(p, sr=16000)
    S = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=1024, hop_length=160)), ref=np.max)
    librosa.display.specshow(S, sr=sr, hop_length=160, x_axis="time", y_axis="hz", ax=ax, cmap="magma")
    ax.set_title(name); ax.set_ylim(0, 6000)
plt.tight_layout()
out = r"D:\总进度\overfit_spec_20261007.png"
plt.savefig(out, dpi=110)
print("saved", out)
