// Non-x86 stubs for SoundTouch.
//
// FIRFilter::newInstance() and TDStretch::newInstance() call
// detectCPUextensions() unconditionally, but SoundTouch only ships an
// implementation for x86 (source/SoundTouch/cpu_detect_x86.cpp, which compiles
// to nothing on ARM).  Cortex-A9 has no MMX/SSE, so the correct stub is 0.
#include <cstdint>

typedef unsigned long uint;

// C++ linkage on purpose: cpu_detect.h declares these without extern "C".
uint detectCPUextensions(void) { return 0u; }
void disableExtensions(uint) {}
