// Finite raw-pipe runtime. ALSA lives in the supervised trial script.
#include <array>
#include <atomic>
#include <cerrno>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <pthread.h>
#include <stdint.h>
#include <time.h>
#ifdef __linux__
#include <fcntl.h>
#include <poll.h>
#include <sched.h>
#include <unistd.h>
#else
#include <io.h>
#include <fcntl.h>
#endif
#include "world/synthesisrealtime.h"
#include "world_sliding_analysis.h"

static volatile sig_atomic_t interrupted = 0;
static std::atomic<int> failure(0);
static void Signal(int) { interrupted = 1; }
static bool Stopped() { return interrupted || failure.load(); }
static void Fail(int code) { int zero = 0; failure.compare_exchange_strong(zero, code); }
static double Now() {
  timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec + t.tv_nsec * 1e-9;
}
static int Pin(int cpu) {
#ifdef __linux__
  cpu_set_t set; CPU_ZERO(&set); CPU_SET(cpu, &set);
  return pthread_setaffinity_np(pthread_self(), sizeof(set), &set);
#else
  (void)cpu; return -1;
#endif
}

static int Schedule(bool fifo, int priority) {
#ifdef __linux__
  const int requested = fifo ? SCHED_FIFO : SCHED_OTHER;
  sched_param settings = {}; settings.sched_priority = fifo ? priority : 0;
  int error = pthread_setschedparam(pthread_self(), requested, &settings);
  if (!error) {
    int policy;
    error = pthread_getschedparam(pthread_self(), &policy, &settings);
    if (!error && (policy != requested || settings.sched_priority != (fifo ? priority : 0))) error = EINVAL;
  }
#else
  (void)priority; const int error = fifo ? ENOSYS : 0;
#endif
  if (error) Fail(8);  // Requested scheduling must actually be installed.
  return error;
}

template<typename T> class Queue {
  pthread_mutex_t mutex;
  pthread_cond_t changed;
  std::deque<T> blocks;
  const size_t capacity;
  bool closed = false;
  void Wait() {
    timespec t; clock_gettime(CLOCK_REALTIME, &t);
    t.tv_nsec += 100000000;
    if (t.tv_nsec >= 1000000000) { ++t.tv_sec; t.tv_nsec -= 1000000000; }
    pthread_cond_timedwait(&changed, &mutex, &t);
  }
 public:
  size_t peak = 0, waits = 0;
  explicit Queue(size_t count): capacity(count) {
    pthread_mutex_init(&mutex, NULL); pthread_cond_init(&changed, NULL);
  }
  ~Queue() { pthread_cond_destroy(&changed); pthread_mutex_destroy(&mutex); }
  bool Push(const T &value) {
    pthread_mutex_lock(&mutex);
    if (blocks.size() == capacity) ++waits;
    while (blocks.size() == capacity && !closed && !Stopped()) Wait();
    const bool okay = !closed && !Stopped();
    if (okay) {
      blocks.push_back(value); peak = std::max(peak, blocks.size());
      pthread_cond_broadcast(&changed);
    }
    pthread_mutex_unlock(&mutex); return okay;
  }
  bool Pop(T &value) {
    pthread_mutex_lock(&mutex);
    while (blocks.empty() && !closed && !Stopped()) Wait();
    const bool okay = !blocks.empty() && !Stopped();
    if (okay) { value = blocks.front(); blocks.pop_front(); pthread_cond_broadcast(&changed); }
    pthread_mutex_unlock(&mutex); return okay;
  }
  void Close() {
    pthread_mutex_lock(&mutex); closed = true; pthread_cond_broadcast(&changed);
    pthread_mutex_unlock(&mutex);
  }
};

// Linux raw pipe I/O is interruptible and has a progress timeout. No abandoned
// worker can leave the supervisor waiting forever on a blocked FIFO operation.
static bool Transfer(int fd, void *data, size_t bytes, bool writing) {
  unsigned char *p = static_cast<unsigned char *>(data);
  double progress = Now();
  while (bytes && !Stopped()) {
#ifdef __linux__
    pollfd item = {fd, static_cast<short>(writing ? POLLOUT : POLLIN), 0};
    const int ready = poll(&item, 1, 100);
    if (ready < 0 && errno == EINTR) continue;
    if (ready < 0) { Fail(4); return false; }
    if (!ready) {
      if (Now() - progress > 5) { Fail(7); return false; }
      continue;
    }
    const ssize_t n = writing ? write(fd, p, bytes) : read(fd, p, bytes);
#else
    const int n = writing ? _write(fd, p, static_cast<unsigned>(bytes)) :
      _read(fd, p, static_cast<unsigned>(bytes));
#endif
    if (n < 0 && (errno == EINTR || errno == EAGAIN)) {
      if (Now() - progress > 5) { Fail(7); return false; }
      continue;
    }
    if (n <= 0) { Fail(writing ? 4 : 3); return false; }
    p += n; bytes -= n; progress = Now();
  }
  return !bytes;
}

#include "world_stream_fir.h"

struct ParametersBlock { std::shared_ptr<Parameters> values; int first; };
struct Runtime {
  Queue<std::vector<double> > input{64}, output{32};
  Queue<ParametersBlock> parameters{8};
  int length, prefill_ms; bool native;
  bool fifo, fifo_io;
  size_t captured = 0, rendered = 0, played = 0, submitted = 0, consumed = 0;
  int reader_pin = -1, analysis_pin = -1, render_pin = -1, writer_pin = -1;
  int reader_sched = 0, analysis_sched = 0, render_sched = 0, writer_sched = 0;
  int max_live = 0, clipped = 0, voiced_frames = 0; size_t max_window = 0;
  double capture_peak = 0, capture_energy = 0, raw_capture_peak = 0;
  size_t raw_capture_clipped = 0;
  int raw_capture_first_clipped32k = -1, raw_capture_last_clipped32k = -1;
  double output_gain, input_gain;
  double analysis_s = 0, render_s = 0, analysis_max_ms = 0, output_peak = 0;
  AnalysisTiming analysis_timing;
  explicit Runtime(int seconds, int prefill, bool hardware, int gain, int input, bool scheduling, bool io_scheduling): length(seconds * 16000),
    prefill_ms(prefill), native(hardware), fifo(scheduling), fifo_io(io_scheduling),
    output_gain(gain / 65536.), input_gain(input / 65536.) {}
};

static void *Capture(void *opaque) {
  Runtime &p = *static_cast<Runtime *>(opaque); p.reader_pin = Pin(1);
  p.reader_sched = Schedule(p.fifo || p.fifo_io, 20);
  Fir filter;
  while (p.captured < static_cast<size_t>(p.length) && !Stopped()) {
    const size_t count = std::min(static_cast<size_t>(128), p.length - p.captured);
    std::vector<double> block(count);
    if (p.native) {
      uint32_t words[512];
      if (!Transfer(0, words, count * 16, false)) break;
      for (size_t i = 0; i < count * 2; ++i) {
        const int32_t value = static_cast<int32_t>((words[2 * i] & 0xffffffu) ^ 0x800000u) - 0x800000;
        p.raw_capture_peak = std::max(p.raw_capture_peak, std::abs(value / 8388608.));
        if (std::abs(value) >= 32760 * 256) {
          ++p.raw_capture_clipped;
          const int position = static_cast<int>(p.captured * 2 + i);
          if (p.raw_capture_first_clipped32k < 0) p.raw_capture_first_clipped32k = position;
          p.raw_capture_last_clipped32k = position;
        }
        const double sample = filter.Step(value / 8388608., !(i % 2));
        if (!(i % 2)) block[i / 2] = sample;
      }
    } else {
      int16_t samples[128];
      if (!Transfer(0, samples, count * 2, false)) break;
      for (size_t i = 0; i < count; ++i) block[i] = samples[i] / 32768.;
    }
    for (double &sample : block) {
      sample *= p.input_gain;
      p.capture_peak = std::max(p.capture_peak, std::abs(sample));
      p.capture_energy += sample * sample;
    }
    p.captured += count;
    if (!p.input.Push(block)) break;
  }
  p.input.Close(); return NULL;
}

static void *Render(void *opaque) {
  Runtime &p = *static_cast<Runtime *>(opaque); p.render_pin = Pin(1);
  p.render_sched = Schedule(p.fifo, 10);
  WorldSynthesizer synth = {};
  InitializeSynthesizer(16000, 10, 1024, 128, 16, &synth);
  std::shared_ptr<Parameters> owners[16]; int id = 0, retired = 0, expected = 0;
  ParametersBlock block;
  while (p.parameters.Pop(block)) {
    const double begin = Now(); const int count = static_cast<int>(block.values->f0.size());
    if (block.first != expected || id - synth.current_pointer2 >= 16) { Fail(5); break; }
    expected += count; owners[id % 16] = block.values;
    if (!AddParameters(block.values->f0.data(), count, block.values->sp_rows.data(),
        block.values->ap_rows.data(), &synth)) { Fail(5); break; }
    ++id; ++p.consumed; p.max_live = std::max(p.max_live, id - retired);
    while (!Stopped() && p.rendered < static_cast<size_t>(p.length + 80) && Synthesis2(&synth)) {
      const size_t take = std::min(static_cast<size_t>(128), p.length + 80 - p.rendered);
      const size_t emit = p.rendered < static_cast<size_t>(p.length) ?
        std::min(take, p.length - p.rendered) : 0;
      std::vector<double> audio(synth.buffer, synth.buffer + emit);
      p.rendered += take;
      if (emit && !p.output.Push(audio)) break;
      while (retired < synth.current_pointer2) owners[(retired++) % 16].reset();
    }
    p.render_s += Now() - begin;
  }
  DestroySynthesizer(&synth); p.output.Close(); return NULL;
}

static bool WriteAudio(Runtime &p, InterpolateFir &filter, const std::vector<double> &audio) {
  uint32_t native[512]; int16_t pcm[128];
  for (size_t i = 0; i < audio.size(); ++i) {
    if (!std::isfinite(audio[i])) { Fail(5); return false; }
    if (p.native) {
      double converted[2]; filter.Step(audio[i] * p.output_gain, converted);
      for (int phase = 0; phase < 2; ++phase) {
        const double sample = converted[phase];
        p.output_peak = std::max(p.output_peak, std::abs(sample));
        if (std::abs(sample) >= 1) ++p.clipped;
        const double bounded = std::max(-1., std::min(1., sample));
        const int32_t value = static_cast<int32_t>(bounded * 8388607);
        const uint32_t word = static_cast<uint32_t>(value) & 0xffffffu;
        native[4 * i + 2 * phase] = native[4 * i + 2 * phase + 1] = word;
      }
    } else {
      const double sample = audio[i] * p.output_gain;
      p.output_peak = std::max(p.output_peak, std::abs(sample));
      if (std::abs(sample) >= 1) ++p.clipped;
      pcm[i] = static_cast<int16_t>(std::max(-32768, std::min(32767, static_cast<int>(sample * 32767))));
    }
  }
  return p.native ? Transfer(1, native, audio.size() * 16, true) :
    Transfer(1, pcm, audio.size() * 2, true);
}
static void *Playback(void *opaque) {
  Runtime &p = *static_cast<Runtime *>(opaque); p.writer_pin = Pin(1); InterpolateFir filter;
  p.writer_sched = Schedule(p.fifo || p.fifo_io, 20);
  // Prefill is emitted separately; it never advances WORLD or source numbering.
  int remaining = p.prefill_ms * 16;
  while (remaining > 0 && !Stopped()) {
    const int take = std::min(128, remaining);
    if (!WriteAudio(p, filter, std::vector<double>(take, 0))) break;
    remaining -= take;
  }
  std::vector<double> audio;
  while (!Stopped() && p.output.Pop(audio)) {
    if (!WriteAudio(p, filter, audio)) break;
    p.played += audio.size();
  }
  return NULL;
}

static void AnalyzeStream(Runtime &p) {
  p.analysis_pin = Pin(0);
  p.analysis_sched = Schedule(p.fifo, 10);
  const int total_frames = p.length / 160 + 1;
  std::vector<double> window, incoming;
  std::shared_ptr<Parameters> last; int base = 0;
  for (int first = 0; first < total_frames && !Stopped();) {
    const int count = std::min(4, total_frames - first);
    const int end = std::min(p.length, (first + count - 1) * 160 + 640);
    while (base + static_cast<int>(window.size()) < end && !Stopped()) {
      if (!p.input.Pop(incoming)) { if (!Stopped()) Fail(3); return; }
      window.insert(window.end(), incoming.begin(), incoming.end());
    }
    if (Stopped()) break;
    p.max_window = std::max(p.max_window, window.size());
    std::vector<double> snapshot(window.begin(), window.begin() + end - base);
    const double begin = Now();
    last = Analyze(snapshot, first - base / 160, count, &p.analysis_timing);
    for (double f0 : last->f0) if (f0 > 0) ++p.voiced_frames;
    const double seconds = Now() - begin;
    p.analysis_s += seconds; p.analysis_max_ms = std::max(p.analysis_max_ms, seconds * 1000);
    if (!p.parameters.Push({last, first})) break;
    ++p.submitted; first += count;
    const int next_base = std::max(0, first * 160 - 2560);
    // During EOF drain next_base can exceed the last requested start; no further read.
    if (first < total_frames) {
      window.erase(window.begin(), window.begin() + next_base - base); base = next_base;
    }
  }
  if (last && !Stopped()) {
    std::shared_ptr<Parameters> tail(new Parameters(12));
    for (int i = 0; i < 12; ++i) {
      tail->f0[i] = last->f0.back();
      std::copy(last->sp_rows.back(), last->sp_rows.back() + 513, tail->sp_rows[i]);
      std::copy(last->ap_rows.back(), last->ap_rows.back() + 513, tail->ap_rows[i]);
    }
    if (p.parameters.Push({tail, total_frames})) ++p.submitted;
  }
}

int main(int argc, char **argv) {
  if ((argc < 4 || argc > 7) || (strcmp(argv[2], "pcm16") && strcmp(argv[2], "native_s24"))) {
    fprintf(stderr, "usage: world_live_stream seconds pcm16|native_s24 prefill_ms [output_gain_q16 [input_gain_q16 [normal|fifo|fifo_io]]] < input.raw > output.raw\n"); return 2;
  }
  char *end; const long seconds = strtol(argv[1], &end, 10);
  if (!*argv[1] || *end || seconds < 1 || seconds > 600) return 2;
  const long prefill = strtol(argv[3], &end, 10);
  if (!*argv[3] || *end || prefill < 0 || prefill > 500) return 2;
  const long gain = argc >= 5 ? strtol(argv[4], &end, 10) : 65536;
  if ((argc >= 5 && (!*argv[4] || *end)) || gain < 1 || gain > 65536) return 2;
  const long input_gain = argc >= 6 ? strtol(argv[5], &end, 10) : 65536;
  if ((argc >= 6 && (!*argv[5] || *end)) || input_gain < 1 || input_gain > 262144) return 2;
  if (argc == 7 && strcmp(argv[6], "fifo") && strcmp(argv[6], "normal") && strcmp(argv[6], "fifo_io")) return 2;
  const bool fifo = argc == 7 && !strcmp(argv[6], "fifo");
  const bool fifo_io = argc == 7 && !strcmp(argv[6], "fifo_io");
  signal(SIGINT, Signal); signal(SIGTERM, Signal);
#ifdef __linux__
  signal(SIGPIPE, SIG_IGN);
  if (fcntl(0, F_SETFL, fcntl(0, F_GETFL) | O_NONBLOCK) < 0 ||
      fcntl(1, F_SETFL, fcntl(1, F_GETFL) | O_NONBLOCK) < 0) return 4;
#else
  _setmode(0, _O_BINARY); _setmode(1, _O_BINARY);
#endif
  Runtime p(static_cast<int>(seconds), static_cast<int>(prefill), !strcmp(argv[2], "native_s24"),
    static_cast<int>(gain), static_cast<int>(input_gain), fifo, fifo_io);
  pthread_t threads[3]; const double started = Now();
  void *(*workers[3])(void *) = {Capture, Render, Playback};
  int created = 0;
  for (; created < 3; ++created) if (pthread_create(&threads[created], NULL, workers[created], &p)) { Fail(8); break; }
  if (!Stopped()) AnalyzeStream(p);
  p.parameters.Close();
  for (int i = 0; i < created; ++i) pthread_join(threads[i], NULL);
  if (interrupted) Fail(130);
  if (!failure.load() && (p.captured != static_cast<size_t>(p.length) || p.played != p.captured ||
      p.rendered != p.captured + 80 || p.submitted != p.consumed)) Fail(5);
  if (!failure.load() && p.clipped) Fail(6);
  fprintf(stderr, "{\"kind\":\"world_raw_stream_runtime\",\"exit_code\":%d,\"seconds\":%ld,\"native_s24\":%s,"
    "\"prefill_ms\":%ld,\"captured16k\":%zu,\"rendered16k_with_tail\":%zu,\"played16k\":%zu,"
    "\"submitted\":%zu,\"consumed\":%zu,\"input_queue_peak\":%zu,\"parameter_queue_peak\":%zu,\"output_queue_peak\":%zu,"
    "\"input_queue_waits\":%zu,\"output_queue_waits\":%zu,\"window_samples_max\":%zu,\"live_parameters_max\":%d,"
    "\"analysis_rtf\":%.6f,\"render_rtf_including_output_wait\":%.6f,\"analysis_max_ms\":%.6f,\"elapsed_s\":%.6f,"
    "\"analysis_stage_s\":{\"dio\":%.6f,\"refine\":%.6f,\"spectrum\":%.6f,\"aperiodic\":%.6f,\"warp\":%.6f},"
    "\"reader_cpu\":1,\"analysis_cpu\":0,\"render_cpu\":1,\"writer_cpu\":1,"
    "\"reader_pin_error\":%d,\"analysis_pin_error\":%d,\"render_pin_error\":%d,\"writer_pin_error\":%d,"
    "\"scheduling_fifo\":%s,\"scheduling_fifo_io\":%s,\"reader_sched_error\":%d,\"analysis_sched_error\":%d,\"render_sched_error\":%d,\"writer_sched_error\":%d,"
    "\"capture_peak\":%.9f,\"capture_rms\":%.9f,\"voiced_frames\":%d,\"raw_capture_peak\":%.9f,"
    "\"raw_capture_clipped_samples\":%zu,\"raw_capture_first_clipped32k\":%d,\"raw_capture_last_clipped32k\":%d,"
    "\"output_gain_q16\":%ld,\"input_gain_q16\":%ld,\"output_peak\":%.9f,\"clipped_samples\":%d}\n",
    failure.load(), seconds, p.native ? "true" : "false", prefill, p.captured, p.rendered, p.played,
    p.submitted, p.consumed, p.input.peak, p.parameters.peak, p.output.peak, p.input.waits, p.output.waits,
    p.max_window, p.max_live, p.analysis_s / seconds, p.render_s / seconds, p.analysis_max_ms, Now() - started,
    p.analysis_timing.dio_s, p.analysis_timing.refine_s, p.analysis_timing.spectrum_s,
    p.analysis_timing.aperiodic_s, p.analysis_timing.warp_s,
    p.reader_pin, p.analysis_pin, p.render_pin, p.writer_pin,
    fifo ? "true" : "false", fifo_io ? "true" : "false", p.reader_sched, p.analysis_sched, p.render_sched, p.writer_sched,
    p.capture_peak, p.captured ? std::sqrt(p.capture_energy / p.captured) : 0, p.voiced_frames,
    p.raw_capture_peak, p.raw_capture_clipped, p.raw_capture_first_clipped32k, p.raw_capture_last_clipped32k,
    gain, input_gain, p.output_peak, p.clipped);
  return failure.load();
}
