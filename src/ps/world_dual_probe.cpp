// Paced file simulation only: no ALSA, DMA, PL or playback access.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <cerrno>
#include <pthread.h>
#include <time.h>
#ifdef __linux__
#include <sched.h>
#endif
#include "audioio.h"
#include "world/synthesisrealtime.h"
#include "world_sliding_analysis.h"

static double Now() {
  timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec + t.tv_nsec * 1e-9;
}
static void WaitUntil(double deadline) {
  for (;;) {
    const double left = deadline - Now();
    if (left <= 0) return;
    timespec t = {static_cast<time_t>(left),
      static_cast<long>((left - std::floor(left)) * 1e9)};
    while (nanosleep(&t, &t) && errno == EINTR) {}
  }
}
static int Pin(int cpu) {
#ifdef __linux__
  cpu_set_t set; CPU_ZERO(&set); CPU_SET(cpu, &set);
  return pthread_setaffinity_np(pthread_self(), sizeof(set), &set);
#else
  (void)cpu; return -1;  // Host timing is never ARM performance evidence.
#endif
}

struct Block {
  std::shared_ptr<Parameters> parameters;
  int first;
};
struct Pipeline {
  pthread_mutex_t mutex;
  pthread_cond_t available, space;
  std::deque<Block> queue;
  bool done = false;
  int error = 0, capacity, max_queue = 0, producer_waits = 0;
  int submitted = 0, consumed = 0, max_live_parameters = 0;
  int analysis_affinity = -1, synthesis_affinity = -1, pause_ms;
  size_t written = 0, late_chunks = 0, checked_chunks = 0;
  double started = 0, delay_s, analysis_s = 0, synthesis_s = 0;
  double queue_wait_s = 0, max_lateness_ms = 0, min_slack_ms = 1e9;
  std::vector<double> analysis_ms, analysis_lag_ms, synthesis_ms, output;
  Pipeline(int length, int slots, int delay, int pause): capacity(slots),
      pause_ms(pause), delay_s(delay / 1000.), output(length + 80) {
    pthread_mutex_init(&mutex, NULL);
    pthread_cond_init(&available, NULL); pthread_cond_init(&space, NULL);
  }
  ~Pipeline() {
    pthread_cond_destroy(&available); pthread_cond_destroy(&space);
    pthread_mutex_destroy(&mutex);
  }
  bool Push(const Block &block) {
    pthread_mutex_lock(&mutex);
    const double begin = Now();
    if (queue.size() == static_cast<size_t>(capacity)) ++producer_waits;
    while (queue.size() == static_cast<size_t>(capacity) && !error)
      pthread_cond_wait(&space, &mutex);
    queue_wait_s += Now() - begin;
    if (!error) {
      queue.push_back(block); ++submitted;
      max_queue = std::max(max_queue, static_cast<int>(queue.size()));
      pthread_cond_signal(&available);
    }
    const bool success = !error;
    pthread_mutex_unlock(&mutex); return success;
  }
};

static void *Render(void *opaque) {
  Pipeline &p = *static_cast<Pipeline *>(opaque);
  p.synthesis_affinity = Pin(1);
  WorldSynthesizer synth = {};
  InitializeSynthesizer(16000, 10, 1024, 128, 16, &synth);
  std::shared_ptr<Parameters> owners[16];
  int retired = 0, id = 0, expected_frame = 0, failure = 0;
  for (;;) {
    pthread_mutex_lock(&p.mutex);
    while (p.queue.empty() && !p.done) pthread_cond_wait(&p.available, &p.mutex);
    if (p.queue.empty()) { pthread_mutex_unlock(&p.mutex); break; }
    Block block = p.queue.front(); p.queue.pop_front();
    pthread_cond_signal(&p.space); pthread_mutex_unlock(&p.mutex);
    if (p.pause_ms && id % 20 == 0) WaitUntil(Now() + p.pause_ms / 1000.);
    const double begin = Now();
    const int count = static_cast<int>(block.parameters->f0.size());
    if (block.first != expected_frame || id - synth.current_pointer2 >= 16) {
      failure = 3; break;
    }
    expected_frame += count;
    // Only this thread owns WORLD; published arrays are never resized or edited.
    owners[id % 16] = block.parameters;
    if (!AddParameters(block.parameters->f0.data(), count,
        block.parameters->sp_rows.data(), block.parameters->ap_rows.data(), &synth)) {
      failure = 3; break;
    }
    ++id; ++p.consumed;
    p.max_live_parameters = std::max(p.max_live_parameters, id - retired);
    while (p.written < p.output.size() && Synthesis2(&synth)) {
      const size_t take = std::min(static_cast<size_t>(128), p.output.size() - p.written);
      std::copy(synth.buffer, synth.buffer + take, p.output.begin() + p.written);
      p.written += take;
      // Deadline is when a simulated sink would need the START of this chunk.
      // The extra 80 samples drain EOF; do not count them as playback deadlines.
      if (p.written - take < p.output.size() - 80) {
        const double slack = (p.started + p.delay_s + (p.written - take) / 16000. - Now()) * 1000;
        ++p.checked_chunks; p.min_slack_ms = std::min(p.min_slack_ms, slack);
        if (slack < 0) { ++p.late_chunks; p.max_lateness_ms = std::max(p.max_lateness_ms, -slack); }
      }
      // WORLD has advanced past these parameter pointers; release only now.
      while (retired < synth.current_pointer2) owners[(retired++) % 16].reset();
    }
    p.synthesis_ms.push_back((Now() - begin) * 1000);
    p.synthesis_s += Now() - begin;
  }
  DestroySynthesizer(&synth);  // Remaining owners outlive WORLD teardown.
  pthread_mutex_lock(&p.mutex);
  p.error = failure; pthread_cond_broadcast(&p.space);
  pthread_mutex_unlock(&p.mutex);
  return NULL;
}

static double Percentile(std::vector<double> values, double fraction) {
  if (values.empty()) return 0;
  std::sort(values.begin(), values.end());
  return values[static_cast<size_t>(fraction * (values.size() - 1))];
}
static int Number(const char *value, int low, int high) {
  char *end; const long n = strtol(value, &end, 10);
  return *value && !*end && n >= low && n <= high ? static_cast<int>(n) : -1;
}

int main(int argc, char **argv) {
  if (argc != 9) {
    fprintf(stderr, "usage: world_dual_probe input16k.wav output.wav hop_ms repeats paced|burst delay_ms queue_slots consumer_pause_ms\n");
    return 2;
  }
  const int hop_ms = Number(argv[3], 30, 40), repeats = Number(argv[4], 1, 120);
  const int delay = Number(argv[6], 1, 2000), slots = Number(argv[7], 1, 8);
  const int pause = Number(argv[8], 0, 1000);
  const bool paced = !strcmp(argv[5], "paced");
  if ((hop_ms != 30 && hop_ms != 40) || repeats < 0 || delay < 0 || slots < 0 || pause < 0 ||
      (!paced && strcmp(argv[5], "burst"))) return 2;
  const int source_length = GetAudioLength(argv[1]);
  if (source_length < 8000 || source_length > 80000) return 2;
  std::vector<double> source(source_length); int rate, bits;
  wavread(argv[1], &rate, &bits, source.data());
  if (rate != 16000 || bits != 16) return 2;
  const int length = source_length * repeats, frames_per_block = hop_ms / 10;
  std::vector<double> input(length);
  for (int i = 0; i < repeats; ++i) std::copy(source.begin(), source.end(), input.begin() + i * source_length);
  Pipeline p(length, slots, delay, pause);
  p.analysis_affinity = Pin(0);
  p.started = Now(); pthread_t consumer;
  const int create_error = pthread_create(&consumer, NULL, Render, &p);
  if (create_error) { fprintf(stderr, "PTHREAD_CREATE_FAILED:%d\n", create_error); return 3; }
  const int total_frames = length / 160 + 1;
  std::shared_ptr<Parameters> last;
  for (int first = 0; first < total_frames;) {
    const int count = std::min(frames_per_block, total_frames - first);
    const int end = std::min(length, (first + count - 1) * 160 + 640);
    const double release = p.started + end / 16000.;
    if (paced) WaitUntil(release);
    const double begin = Now();
    std::shared_ptr<Parameters> block = Analyze(input, first, count);
    const double completed = Now();
    p.analysis_s += completed - begin; p.analysis_ms.push_back((completed - begin) * 1000);
    p.analysis_lag_ms.push_back((completed - release) * 1000);
    last = block;
    if (!p.Push({block, first})) break;
    first += count;
  }
  // Match the serial probe's EOF policy exactly; padding is not live lookahead.
  if (last) {
    std::shared_ptr<Parameters> tail(new Parameters(12));
    for (int i = 0; i < 12; ++i) {
      tail->f0[i] = last->f0.back();
      std::copy(last->sp_rows.back(), last->sp_rows.back() + 513, tail->sp_rows[i]);
      std::copy(last->ap_rows.back(), last->ap_rows.back() + 513, tail->ap_rows[i]);
    }
    p.Push({tail, total_frames});
  }
  pthread_mutex_lock(&p.mutex); p.done = true;
  pthread_cond_broadcast(&p.available); pthread_mutex_unlock(&p.mutex);
  pthread_join(consumer, NULL);
  const double elapsed = Now() - p.started;
  if (p.error || p.written != p.output.size() || p.submitted != p.consumed) {
    fprintf(stderr, "PIPELINE_FAILED:%d written=%zu/%zu submitted=%d consumed=%d\n",
      p.error, p.written, p.output.size(), p.submitted, p.consumed); return 4;
  }
  double peak = 0;
  for (int i = 0; i < length; ++i) {
    if (!std::isfinite(p.output[i])) return 4;
    peak = std::max(peak, std::abs(p.output[i]));
  }
  if (peak >= 1) return 5;
  wavwrite(p.output.data(), length, rate, 16, argv[2]);
  printf("{\"kind\":\"dual_core_file_schedule_probe\",\"paced\":%s,\"hop_ms\":%d,\"repeats\":%d,"
    "\"audio_s\":%.6f,\"elapsed_s\":%.6f,\"analysis_rtf\":%.6f,\"synthesis_rtf\":%.6f,"
    "\"analysis_p95_ms\":%.6f,\"analysis_max_ms\":%.6f,\"analysis_completion_lag_max_ms\":%.6f,"
    "\"synthesis_p95_ms\":%.6f,\"max_queue\":%d,\"queue_capacity\":%d,\"producer_waits\":%d,\"queue_wait_ms\":%.6f,"
    "\"submitted\":%d,\"consumed\":%d,\"max_live_parameters\":%d,"
    "\"output_delay_ms\":%d,\"checked_chunks\":%zu,\"late_chunks\":%zu,\"min_slack_ms\":%.6f,\"max_lateness_ms\":%.6f,"
    "\"analysis_affinity_error\":%d,\"synthesis_affinity_error\":%d,\"consumer_pause_ms\":%d,\"peak\":%.9f}\n",
    paced ? "true" : "false", hop_ms, repeats, length / 16000., elapsed,
    p.analysis_s * 16000 / length, p.synthesis_s * 16000 / length,
    Percentile(p.analysis_ms, .95), Percentile(p.analysis_ms, 1), Percentile(p.analysis_lag_ms, 1),
    Percentile(p.synthesis_ms, .95), p.max_queue, slots, p.producer_waits, p.queue_wait_s * 1000,
    p.submitted, p.consumed, p.max_live_parameters, delay, p.checked_chunks, p.late_chunks,
    p.min_slack_ms, p.max_lateness_ms, p.analysis_affinity, p.synthesis_affinity, pause, peak);
  // A deliberately overloaded paced trial must fail its deadline gate.
  return paced && p.late_chunks ? 6 : 0;
}
