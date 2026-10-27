// Reuse Ooura plans within their owning thread; signal arithmetic is unchanged.
#include "world/fft.h"
#include <cstdio>
#include <cstdlib>
#include <pthread.h>

extern "C" {
fft_plan __real_fft_plan_dft_1d(int, fft_complex*, fft_complex*, int, unsigned);
fft_plan __real_fft_plan_dft_r2c_1d(int, double*, fft_complex*, unsigned);
fft_plan __real_fft_plan_dft_c2r_1d(int, fft_complex*, double*, unsigned);
void __real_fft_destroy_plan(fft_plan);
}

namespace {
struct Entry { fft_plan plan = {}; int type = 0; bool busy = false; };
struct Cache {
  Entry entries[32];
  int count = 0;
  unsigned long hits = 0, misses = 0;
  size_t bytes = 0;
  ~Cache() {
    for (int i = 0; i < count; ++i) __real_fft_destroy_plan(entries[i].plan);
    std::fprintf(stderr, "{\"kind\":\"world_fft_cache\",\"hits\":%lu,\"misses\":%lu,\"entries\":%d,\"bytes\":%zu}\n",
                 hits, misses, count, bytes);
  }
};
pthread_key_t cache_key;
pthread_once_t cache_once = PTHREAD_ONCE_INIT;
void DeleteCache(void* p) { delete static_cast<Cache*>(p); }
void DeleteMainCache() {
  void* p = pthread_getspecific(cache_key);
  pthread_setspecific(cache_key, NULL);
  DeleteCache(p);
}
void CreateKey() {
  if (pthread_key_create(&cache_key, DeleteCache)) std::abort();
  std::atexit(DeleteMainCache);
}
Cache& GetCache() {
  pthread_once(&cache_once, CreateKey);
  Cache* p = static_cast<Cache*>(pthread_getspecific(cache_key));
  if (!p) {
    p = new Cache;
    if (pthread_setspecific(cache_key, p)) std::abort();
  }
  return *p;
}
bool Enabled() {
  static const bool enabled = [] { const char* v = std::getenv("WORLD_FFT_CACHE"); return !v || v[0] != '0'; }();
  return enabled;
}
fft_plan Acquire(int n, int type, double* in, fft_complex* cin,
                 double* out, fft_complex* cout, int sign, unsigned flags) {
  Cache& cache = GetCache();
  if (Enabled()) {
    for (int i = 0; i < cache.count; ++i) {
      Entry& e = cache.entries[i];
      if (!e.busy && e.plan.n == n && e.type == type) {
        e.busy = true;
        ++cache.hits;
        fft_plan p = e.plan;
        p.in = in; p.c_in = cin; p.out = out; p.c_out = cout;
        p.sign = sign; p.flags = flags;
        return p;
      }
    }
  }
  fft_plan p = type == 0 ? __real_fft_plan_dft_r2c_1d(n, in, cout, flags) :
               type == 1 ? __real_fft_plan_dft_c2r_1d(n, cin, out, flags) :
                           __real_fft_plan_dft_1d(n, cin, cout, sign, flags);
  if (Enabled()) {
    ++cache.misses;
    const size_t bytes = sizeof(double) * n * (type == 2 ? 2 : 1) +
                         sizeof(int) * n + sizeof(double) * (n * 5 / 4);
    if (cache.count < 32 && cache.bytes + bytes <= 4 * 1024 * 1024) {
      Entry& e = cache.entries[cache.count++];
      e.plan = p; e.type = type; e.busy = true; cache.bytes += bytes;
    }
  }
  return p;
}
}

extern "C" {
fft_plan __wrap_fft_plan_dft_1d(int n, fft_complex* in, fft_complex* out, int sign, unsigned flags) {
  return Acquire(n, 2, NULL, in, NULL, out, sign, flags);
}
fft_plan __wrap_fft_plan_dft_r2c_1d(int n, double* in, fft_complex* out, unsigned flags) {
  return Acquire(n, 0, in, NULL, NULL, out, FFT_FORWARD, flags);
}
fft_plan __wrap_fft_plan_dft_c2r_1d(int n, fft_complex* in, double* out, unsigned flags) {
  return Acquire(n, 1, NULL, in, out, NULL, FFT_BACKWARD, flags);
}
void __wrap_fft_destroy_plan(fft_plan p) {
  Cache& cache = GetCache();
  for (int i = 0; i < cache.count; ++i) {
    Entry& e = cache.entries[i];
    if (e.plan.input == p.input) { e.busy = false; return; }
  }
  __real_fft_destroy_plan(p);
}
}
