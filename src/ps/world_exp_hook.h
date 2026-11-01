#ifndef WORLD_EXP_HOOK_H
#define WORLD_EXP_HOOK_H
// Returns false only for CPU mode or an unsupported numeric domain.
bool WorldExpOffload(double (*spectrum)[2], int fft_size);
#endif
