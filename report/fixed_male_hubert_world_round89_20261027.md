# Fixed-Male HuBERT/WORLD Round 89

Status: REJECTED. Crop length increased from 128 to 192 frames (2.56 to 3.84 seconds) relative to Round88. Dynamic loss 1.20, VUV BCE 0.35, variance matching, source prosody, anchor probability 0.25, seed, early stopping and inference gain 1.6 are unchanged.

| Metric | Result | Gate | Pass |
|---|---:|---:|---|
| identity | 0.677727 | >=0.45 | True |
| identity_p10 | 0.656802 | >=0.35 | True |
| leakage | 0.122857 | <=0.10 | False |
| utmos | 2.055849 | >=2.30 | False |
| cer | 0.367647 | <=0.15 | False |

Early stopping completed at step1300; best checkpoint step500, validation loss 0.8019716069. Checkpoint SHA-256: `5846de735d14ddeccb44257901abc551efdb994c136a8d3dfc7005d60ff4761a`. WAV SHA-256: `48095635b1a4e21fc5c23659ee0fafbc5c16c788dba23c1ae9f575c479329c6b`.

The longer crop excludes more short training rows: 140/192 eligible versus 184/192 in Round88. This confounds context length with training coverage. PCA and normalizers still fit all 192 public paired training rows; 8 public validation rows select checkpoints. Target Tracks5-8 are reconstruction anchors. Fixed male recordings1-3 define only the evaluator source centroid. Only recording4 was evaluated; recording5 and Track9 remained locked.

The evaluator uses an identity OpenCC shim and does not convert Chinese scripts, despite its raw protocol description. CER compares Whisper transcripts and has no manually verified reference. No full protocol acceptance is claimed. Training and candidate launchers returned1 after emitting completion artifacts; checkpoint finite weights/history/cache SHA and candidate SHA were independently verified. Evaluation returned0. No playback, board, PS, PL or realtime validation was performed.

Full training history, per-window metrics, ASR text and four-stage reproduction commands are in the adjacent JSON. `build/reproduce_hubert_world_round88_20261027.py --experiment-round 89` reproduces this configuration with external assets. Weights and generated audio remain ignored.
