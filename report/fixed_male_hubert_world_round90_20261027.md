# Fixed-Male HuBERT/WORLD Round 90

Status: REJECTED. Relative to Round88, HuBERT PCA dimensions increase from96 to192, growing the input linear layer from99 to195 features. GRU hidden192/two layers, crop128, batch8, dynamic loss1.20, VUV BCE0.35, variance matching, source prosody, anchor0.25, seed, early stopping and gain1.6 are unchanged.

| Metric | Result | Gate | Pass |
|---|---:|---:|---|
| identity | 0.643984 | >=0.45 | True |
| identity_p10 | 0.615765 | >=0.35 | True |
| leakage | 0.126283 | <=0.10 | False |
| utmos | 2.185500 | >=2.30 | False |
| cer | 0.455882 | <=0.15 | False |

Completed step1400; best step600, validation loss 0.8022358119. Parameters: 496779. Checkpoint SHA-256: `2a29d614f6995fd0a4d3d4d349d2860fbe07a2017d988bfc6b853d82e43eab95`. WAV SHA-256: `fb8bc99c9a5319c58c96f6c0e2684fe69c36863918efc3119f899a5ef50c6c52`.

Evaluation now uses actual OpenCC0.1.7 t2s normalization; historical default remains identity mode for reproducing Rounds88/89. Rescoring their saved ASR transcripts with real OpenCC leaves both CER values unchanged (18/68 and25/68). This correction does not explain away their content failures. Raw CER for this candidate is 0.4558823529; normalized CER is 0.4558823529. Whisper source text is still not manually verified ground truth.

PCA and normalizers fit only192 public paired training rows;184 are long enough for crop128. Eight public validation rows select checkpoints. Target Tracks5-8 are self-reconstruction anchors; male recordings1-3 define only the evaluation source centroid. Only recording4 was evaluated; recording5 and Track9 remained locked. No playback or board/PS/PL/realtime evidence is claimed.

Training and candidate launchers returned1 after emitting completion artifacts. Checkpoint finite weights, history, dimensions, cache SHA and WAV SHA were independently verified; evaluation returned0. The adjacent JSON retains full history, per-window metrics, transcripts, normalization audit and reproduction commands. Generated weights and audio remain ignored.
