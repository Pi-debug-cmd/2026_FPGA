// GCC6 lacks newer intrinsic spelling; equivalent unaligned32bit load.
#include <immintrin.h>
#include <string.h>
static inline __m128i fargan_loadu_si32(const void *p){int x;memcpy(&x,p,4);return _mm_cvtsi32_si128(x);}
#define _mm_loadu_si32(p) fargan_loadu_si32(p)
