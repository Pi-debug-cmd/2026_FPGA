# WORLD minimum-phase fusion Round16 RTL cosim

Task `PL-20261027-01`, Hardware-A / Codex, 2026-10-29. This resumes the short-path project paused on 2026-10-27; it does not touch the board or audio service.

## Result

Vitis HLS 2026.1 generated Verilog for `xc7z020clg400-2` and XSIM completed all 24 WORLD golden cases. C post-check returned maximum relative L2 `8.53141669198e-7` and `passed=true`. The generated cosim report records `Pass`, latency `32231..32232` cycles, interval `32245..32246` cycles, and `773889` total cycles for 24 transactions.

The HLS estimate remains 100 MHz target, 7.300 ns estimated clock, 10007 LUT, 7732 FF, 8 BRAM18K and 38 DSP. These are synthesis estimates, not routed whole-system results.

## Reproduction

```powershell
$env:WORLD_HLS_PROJECT='D:/wpl_20261027_r16/m'
& 'D:/USER_Software/vivado/2026.1/Vitis/bin/vitis-run.bat' --mode hls --tcl --input_file 'build/generated/run_minphase_cosim_round15.tcl'
```

The ignored wrapper sets the WORLD 0.3.5 source argument to `C:/Users/World/Desktop/2026_FPGA/build/generated/world_source_v035/pyworld-0.3.5/lib/World` and sources `build/cosim_world_minphase_hls.tcl`. Required source hashes and generated-report hashes are in the adjacent JSON.

## Remaining risk

XSIM's dependence monitor emitted 6720 warnings for addresses that overlap after the explicit `DEPENDENCE inter false` directives. The 24-case numerical result passed, so this is not a demonstrated data error, but it remains a signoff risk and must be preserved in the report. The next gate is OOC implementation and routed timing/resource inspection; board loading remains premature.

No recording, playback, listening, bitstream load, boot change, or board-side test was performed.
