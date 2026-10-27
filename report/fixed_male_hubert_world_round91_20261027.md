# Fixed-Male HuBERT/WORLD Round 91

Status: REJECTED. Target self-reconstruction anchor probability increases from0.25 to0.50 relative to Round88. PCA96/input99, GRU hidden192/two layers, crop128, batch8, dynamic loss1.20, VUV BCE0.35, variance matching, source prosody, seed, early stopping and inference gain1.6 are unchanged. Longer crops and increased PCA dimensions from Rounds89/90 are not used.

| Metric | Result | Gate | Pass |
|---|---:|---:|---|
| identity | 0.693630 | >=0.45 | True |
| identity_p10 | 0.672396 | >=0.35 | True |
| leakage | 0.113065 | <=0.10 | False |
| utmos | 2.201187 | >=2.30 | False |
| cer | 0.308824 | <=0.15 | False |

Completed step1800; best step1000, validation loss 0.8054647967. Parameters: 478347. Checkpoint SHA-256: `fbc00a21c1360c3b57d900a521d8303d29b8fa0595caeac49ebf7f6335ecee2f`. WAV SHA-256: `a7f803ac6791dd4f30e9e801737486cee37321505c68c5c3f0f281965703199f`.

More target-anchor samples imply fewer public paired samples under the same step/batch budget. PCA and normalizers still fit only192 public paired training rows;184 are long enough for crop128. Eight public validation rows select checkpoints. Target Tracks5-8 are self-reconstruction anchors and do not select checkpoints. Male recordings1-3 define only the evaluation source centroid. Only recording4 was evaluated; recording5 and Track9 remained locked.

The evaluator uses actual OpenCC0.1.7 t2s normalization. Raw CER is 0.3088235294; normalized CER is 0.3088235294. Source Whisper text is not manually verified ground truth. Training and candidate launchers returned1 after emitting completion artifacts; finite weights, history, dimensions, cache SHA and WAV SHA were independently verified. Evaluation returned0. No playback or board/PS/PL/realtime result is claimed.

The adjacent JSON contains full training history, per-window metrics, ASR text, runtime source hashes and four-stage reproduction commands. Weights and generated audio remain ignored.

A supplementary prosody audit reads only male recordings1-3. Their log-F0/VUV/log-energy mean shifts relative to public training are all below one training standard deviation; this does not demonstrate a severe mean-distribution mismatch. No calibration or candidate change was made. The adjacent JSON retains per-recording SHA/statistics and the portable audit command; its launcher returned1 after writing a valid finite JSON. This audit does not establish phonetic coverage or human intelligibility.
