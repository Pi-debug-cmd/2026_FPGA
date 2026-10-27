# Alignment and clipping diagnosis

Frozen Round88 checkpoint, same8 public validation sentences, production20ms-resampled target anchor bounds. No training, synthesis or candidate selection.

All8 source/teacher energy-envelope correlation maxima occur at zero lag in the predeclared±200ms range. Zero-lag correlations range0.9103–0.9723. Together with the historical Round35 prediction-lag audit, this provides no evidence for fixing the pipeline with a global time shift. Energy-envelope correlation does not establish local phoneme alignment.

| Group | Prediction dynamic ratio | After gain1.6 | After gain+clip | Gain values outside anchor range |
|---|---:|---:|---:|---:|
| spectrum | 0.7512 | 1.2019 | 1.1507 | 2.40% |
| log_f0 | 1.1244 | 1.1244 | 1.1244 | 0.00% |
| energy | 0.9091 | 1.4546 | 1.3718 | 27.97% |
| ap | 0.7711 | 1.2337 | 0.8835 | 51.14% |

Uniform gain is no longer a neutral correction of uniform under-variance. Spectrum starts at0.7512 and ends1.1507; energy starts0.9091 and ends1.3718. AP starts0.7711, is amplified to1.2337, but51.14% of values violate anchor bounds; clipping leaves dynamic ratio0.8835. Energy range violations reach27.97%. In contrast, teacher energy has0% violations and teacher AP averages0.923%. This supports a specific inference-pipeline hypothesis: gain and clipping interact differently across parameter groups.

It does not prove that removing AP/energy gain improves CER. RMS captures magnitude rather than accurate trajectories. These20ms statistics are not the exact final5ms clipping fractions. The next controlled diagnostic should freeze weights, spectrum gain1.6, bounds, synthesis and evaluator, then separately remove energy gain or AP gain. This tests a mechanism; do not tune another common gain or train another network before that result.

The adjacent JSON retains all lag correlations, group errors, out-of-range fractions, runtime hash and reproduction command. Process returned1 after writing a complete finite8-row report, which was independently inspected. No recording4/5, Track9, playback, recording, board, PS, PL or realtime evidence was produced.
