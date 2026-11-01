// pl_stft.h - minimal user-space AXI DMA client for the PL STFT/gain/ISTFT core.
#pragma once
#include <cstdint>

// Returns 1 when /dev/mem, the AXI DMA and the PL core all answered.
int pl_stft_init();

// frames: number of 1024-sample frames.
//   x : frames*1024 int16 windowed time samples
//   g : frames*513  int32 gains, Q4.19
//   z : frames*1024 int32 out, value = z_sample * 256 (z_sample in int16 units)
// Returns 0 on success.
int pl_stft_run(const int16_t *x, const int32_t *g, int frames, int32_t *z);

// DMA wall time of the last run, seconds (for reporting).
double pl_stft_last_seconds();
