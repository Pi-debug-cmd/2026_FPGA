| dut | shape | samples | max_abs_diff | snr_db | mismatches | verdict |
|---|---|---|---|---|---|---|
| arm_vs_x86_x16 | [64000] | 64000 | 0 | inf | 0 | PASS (bit-exact) |
| board_vs_oracle_y16_1ulp_in | [64000] | 64000 | 0.000431 | 74.86 | 56524 | FAIL - differs almost everywhere but only by <=1.9e-03 of signal RMS: numeric axis (1-ulp input amplification, rounding mode), not a structural bug |
| logsp_base_vs_all_401x513 | [401, 513] | 205713 | 0 | inf | 0 | PASS (bit-exact) |
| fp32_vs_int8 | [64000] | 64000 | 0.0144 | 41.67 | 57007 | FAIL |
