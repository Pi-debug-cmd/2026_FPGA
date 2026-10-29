# Frozen group-gain ablation

Status: no material content breakthrough. Round88 weights, spectrum gain1.6, production20ms target-anchor bounds, VUV/F0 and synthesis are frozen. Eight public validation sentences; no training or parameter grid.

| Variant | Edits/152 | CER | Mean UTMOS |
|---|---:|---:|---:|
| student_gain1_6 | 44/152 | 0.289474 | 2.457535 |
| no_energy_gain | 40/152 | 0.263158 | 2.448939 |
| no_ap_gain | 44/152 | 0.289474 | 2.474633 |

| Speaker | Variant | CER | UTMOS |
|---|---|---:|---:|
| SSB0080 | student_gain1_6 | 0.186667 | 2.613651 |
| SSB0080 | no_energy_gain | 0.146667 | 2.561476 |
| SSB0080 | no_ap_gain | 0.186667 | 2.628351 |
| SSB0434 | student_gain1_6 | 0.389610 | 2.301418 |
| SSB0434 | no_energy_gain | 0.376623 | 2.336402 |
| SSB0434 | no_ap_gain | 0.389610 | 2.320915 |

Removing energy gain improves total CER by4 edits, but SSB0080 UTMOS drops2.61365→2.56148. It fails the predeclared cross-speaker nonregression requirement and is not selected. Removing AP gain improves UTMOS slightly in both speakers (+0.01470 and+0.01950) while every sentence retains the same CER; overall improvement+0.01710 is small. All AP-ablation WAV hashes differ from baseline, confirming a real signal change despite identical CER. This is not a fix for the major content loss and does not justify another local parameter scan.

The previous parameter audit identified a real gain/clipping interaction, but that alone did not establish perceptual harm or causality for CER. This controlled result limits that hypothesis: simple removal of either group gain does not recover teacher-level content. Prioritize supervised content information and source-specific coverage next, rather than combine small postfilter changes and claim a breakthrough.

Reference remains corpus declared text, not independently verified ground truth. Same Whisper-small/OpenCC0.1.7 CER is used. UTMOS uses existing6s nonoverlap/tail>=1.5s/RMS0.04 rules within each utterance, then reports an unweighted mean over8 utterances. No listening or significance claim is made.

Generation returned1 after emitting all24 valid WAV and8-row manifest; evaluation returned0. Hashes were checked before scoring and again before reporting. JSON preserves per-sentence scores/transcripts/hashes, model/corpus/cache hashes, exact commands and script SHA. Generated audio remains ignored. No recording4/5 orTrack9, new training, playback, board, PS, PL or realtime test was performed. No production candidate is selected.
