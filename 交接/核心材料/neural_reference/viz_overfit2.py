import numpy as np, librosa, matplotlib, json
matplotlib.use("Agg")
import matplotlib.pyplot as plt
CORP = r"D:\Tools_FPGA\workspace\voice_conversion_zynq7020\board_budget_20261005\full_train_corpus_16k"
m = json.load(open(CORP + r"\manifest.json"))
e = m["train"][0]
N = 32000
c = e["n"] // 2
tch = np.fromfile(e["tch"], dtype="<f4")[c:c+N]
out, _ = librosa.load(r"D:\总进度\overfit_test_20261007.wav", sr=16000)
fig, axes = plt.subplots(2, 1, figsize=(12, 5))
for ax, (name, y) in zip(axes, [("teacher (middle 2s)", tch), ("overfit output", out)]):
    S = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=1024, hop_length=160)), ref=np.max)
    librosa.display.specshow(S, sr=16000, hop_length=160, x_axis="time", y_axis="hz", ax=ax, cmap="magma")
    ax.set_title(name); ax.set_ylim(0, 6000)
plt.tight_layout()
plt.savefig(r"D:\总进度\overfit_spec_20261007.png", dpi=110)
print("saved")
