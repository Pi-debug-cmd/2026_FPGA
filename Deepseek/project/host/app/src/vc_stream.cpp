// vc_stream.cpp -- board-side voice conversion (WORLD analysis -> v5 envelope
// residual MLP -> STFT envelope transplant), entirely offline/batch capable and
// speaking the predecessor v23 command line.
//
//   vc_stream <seconds> pcm16|native_s24 <prefill_ms> [out_gain_q16 [in_gain_q16]]
//             < in.raw > out.raw
//
// stdin/stdout are raw PCM, stderr carries a single JSON telemetry object, which
// is the contract of /opt/world_voice/world_budget_v23 (see
// board_20261025.md).  Audio is S24_LE / 32000 Hz / 2 ch on this board; the
// 24 valid bits sit left-justified in a 32-bit little-endian container
// (verified on the board by bringup_tool's wav24 mode).
//
// Algorithm (must match scripts/ ref_port.py line for line):
//   1. S24_LE 32 k stereo -> left channel -> float in [-1,1)
//   2. 32 k -> 16 k, 127-tap Hamming-windowed sinc
//   3. SoundTouch pitch 1.40 (WSOLA, sequence/seek/overlap = 30/10/10 ms)
//   4. WORLD: DIO + StoneMask + CheapTrick(fft=1024) + D4C  on the ORIGINAL
//      signal  -> log power spectrum (401 frames / 4 s, 513 bins), f0, ap
//   5. 68-dim frame features (32 cepstra + 4 + 32 deltas), 9-frame context,
//      utterance statistics (32 cepstra + median log-F0 + voiced fraction)
//      -> 646-dim input, per-dimension normalisation stored in the blob
//   6. 4x512 GELU MLP -> out_dim residual cepstra -> +source out_dim-cep ->
//      513-bin log envelope (the "predicted envelope"); out_dim comes from the
//      blob header (48 = student_v5/T4, 64 = O64)
//   7. gain = exp(0.5 * (pred - src_env)) with +-20 dB clamp per bin and
//      gain = 1 on silent frames, applied to the STFT of the PITCH-SHIFTED
//      signal, source phase untouched
//   8. ISTFT -> 16 k -> 32 k -> S24_LE stereo out
//
// Debug flags (after the positional arguments, they do not disturb the contract):
//   --nopitch            skip step 3 (the Python "A" control path)
//   --in-f32-16k         stdin is raw float32 mono 16 kHz; skips steps 1-2
//   --out-f32-16k        stdout is raw float32 mono 16 kHz; skips step 8
//   --dump DIR           write every intermediate stage as .f32 into DIR
//   --quiet              no telemetry JSON
//
// Build: see Makefile / build_arm.ps1.

#include <algorithm>
#include <cerrno>
#include <cmath>
#include <complex>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include <time.h>

#ifdef _WIN32
// desk-side numeric harness only (the shipped artefact is the ARM build)
#include <direct.h>
#include <fcntl.h>
#include <io.h>
#include <windows.h>
#else
#include <sys/stat.h>
#include <sys/types.h>
#endif

#include "world/cheaptrick.h"
#include "world/d4c.h"
#include "world/dio.h"
#include "world/stonemask.h"

#include "SoundTouch.h"

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#include <pthread.h>

#if defined(__ARM_NEON)
#include <arm_neon.h>
#endif

// ----------------------------------------------------------------------------
// constants -- every one of these mirrors a constant in the Python reference
// ----------------------------------------------------------------------------
static const int kSrIn = 32000;   // board capture/playback rate
static const int kSr = 16000;     // internal rate used by the model
static const int kNfft = 1024;
static const int kWin = 1024;     // librosa win_length = n_fft
static const int kHop = 160;      // 10 ms, same grid as WORLD frame_period=10
static const int kNbins = kNfft / 2 + 1;
static const double kSilenceDb = -45.0;
static const double kGainLimitDb = 20.0;
static const double kGainExponent = 0.5;
static const int kTaps = 127;     // Hamming-sinc resampler
// 7.5 kHz cutoff: with 127 Hamming taps at 32 kHz the transition band is about
// +-0.4 kHz, so everything above 8 kHz (which would fold back) is >=50 dB down
// while the whole 0-7.5 kHz model band is preserved.  8 kHz would alias.
static const double kCutoffHz = 7500.0;
static const int kChannels = 2;
static const double kDefaultPitch = 1.4;
// SoundTouch settings: WSOLA 30/10/10 ms (T4 desktop chain)
static const int kSeqMs = 30;
static const int kSeekMs = 10;
static const int kOverlapMs = 10;

// ----------------------------------------------------------------------------
// small helpers
// ----------------------------------------------------------------------------
static double now_ms() {
#ifdef _WIN32
  static LARGE_INTEGER freq = [] {
    LARGE_INTEGER f;
    QueryPerformanceFrequency(&f);
    return f;
  }();
  LARGE_INTEGER c;
  QueryPerformanceCounter(&c);
  return 1000.0 * (double)c.QuadPart / (double)freq.QuadPart;
#else
  struct timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6;
#endif
}

static void die(const char *fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  fputs("vc_stream: ", stderr);
  vfprintf(stderr, fmt, ap);
  va_end(ap);
  fputc('\n', stderr);
  exit(2);
}

static double median_of(std::vector<double> v) {
  if (v.empty()) return 0.0;
  size_t m = v.size() / 2;
  std::nth_element(v.begin(), v.begin() + m, v.end());
  double hi = v[m];
  if (v.size() & 1) return hi;
  std::nth_element(v.begin(), v.begin() + m - 1, v.end());
  return 0.5 * (v[m - 1] + hi);
}

// numpy's default (linear) percentile
static double percentile_of(std::vector<double> v, double q) {
  if (v.empty()) return 0.0;
  std::sort(v.begin(), v.end());
  double pos = q / 100.0 * (double)(v.size() - 1);
  size_t lo = (size_t)std::floor(pos);
  size_t hi = lo + 1 < v.size() ? lo + 1 : lo;
  double frac = pos - (double)lo;
  return v[lo] * (1.0 - frac) + v[hi] * frac;
}

// ----------------------------------------------------------------------------
// blob -----------------------------------------------------------------------
// ----------------------------------------------------------------------------
struct Model {
  int in_dim = 0, hidden = 0, layers = 0, out_dim = 0, context = 0;
  int nceps_in = 0, nceps_out = 0, n_bins = 0, fft_size = 0;
  int frame_period_x10 = 0, fs = 0;
  float pitch_ratio = 1.0f;
  const float *mu = nullptr, *sd = nullptr;
  const float *dct_in = nullptr, *dct_out = nullptr, *synth = nullptr;
  std::vector<const float *> W, B;
  const float *Wout = nullptr, *Bout = nullptr;

  // int8 copy of the same weights (per-output-channel scale).  Built once at load;
  // the fp32 arrays above stay authoritative so the two paths can be compared.
  struct QLayer {
    std::vector<int8_t> w;      // [hidden][in], row j = output neuron j
    std::vector<float> scale;   // per output neuron: max|W[j,:]| / 127
  };
  std::vector<QLayer> qW;
  QLayer qWout;                 // output layer: [out_dim][hidden]
  bool quantized = false;

  // synth transposed to [bin][cepstrum]: the inverse-DCT loop then reads out_dim
  // contiguous floats per bin instead of striding 2 KB through the rows.  Same
  // arithmetic in the same order, only a friendlier layout (measured: the
  // envelope stage drops from ~1.26 s to a few hundred ms on the board).
  std::vector<float> synth_T;   // [n_bins][out_dim]
  mutable std::vector<float> qa_scale;
};

static void build_synth_T(Model &m) {
  m.synth_T.assign((size_t)m.n_bins * m.out_dim, 0.0f);
  for (int b = 0; b < m.n_bins; b++)
    for (int k = 0; k < m.out_dim; k++)
      m.synth_T[(size_t)b * m.out_dim + k] = m.synth[(size_t)k * m.n_bins + b];
}

static void build_int8(Model &m) {
  auto quantize = [](const float *w, int rows, int cols, Model::QLayer &q) {
    q.w.assign((size_t)rows * cols, 0);
    q.scale.assign(rows, 0.0f);
    for (int j = 0; j < rows; j++) {
      const float *row = w + (size_t)j * cols;
      float mx = 0.0f;
      for (int i = 0; i < cols; i++) mx = std::max(mx, std::fabs(row[i]));
      const float s = (mx > 0.0f) ? mx / 127.0f : 1.0f;
      q.scale[j] = s;
      int8_t *dst = &q.w[(size_t)j * cols];
      for (int i = 0; i < cols; i++) {
        long v = lroundf(row[i] / s);
        dst[i] = (int8_t)std::min(127L, std::max(-127L, v));
      }
    }
  };
  m.qW.assign(m.layers, Model::QLayer());
  for (int l = 0; l < m.layers; l++) {
    const int in = (l == 0) ? m.in_dim : m.hidden;
    quantize(m.W[l], m.hidden, in, m.qW[l]);
  }
  quantize(m.Wout, m.out_dim, m.hidden, m.qWout);
  m.quantized = true;
}

static std::vector<uint8_t> read_file(const char *path) {
  FILE *f = fopen(path, "rb");
  if (!f) die("cannot open %s: %s", path, strerror(errno));
  if (fseek(f, 0, SEEK_END) != 0) die("seek failed on %s", path);
  long n = ftell(f);
  if (n <= 0) die("empty file %s", path);
  rewind(f);
  std::vector<uint8_t> buf((size_t)n);
  if (fread(buf.data(), 1, buf.size(), f) != buf.size()) die("short read on %s", path);
  fclose(f);
  return buf;
}

// The Model only holds pointers into the blob, so the blob must outlive it.
// (Getting this wrong is a silent heap-use-after-free: the first stages still
// read plausible values until something reuses the freed block.)
static std::vector<uint8_t> g_blob;

static Model load_model(const char *path) {
  g_blob = read_file(path);
  std::vector<uint8_t> &buf = g_blob;
  if (buf.size() < 64 || memcmp(buf.data(), "VCB1", 4) != 0)
    die("%s: bad magic (expected VCB1)", path);
  const int32_t *h = (const int32_t *)(buf.data() + 4);
  if (h[0] != 1) die("%s: unsupported blob version %d", path, (int)h[0]);
  Model m;
  m.in_dim = h[1]; m.hidden = h[2]; m.layers = h[3]; m.out_dim = h[4];
  m.context = h[5]; m.nceps_in = h[6]; m.nceps_out = h[7];
  m.n_bins = h[8]; m.fft_size = h[9]; m.frame_period_x10 = h[10]; m.fs = h[11];

  if (m.n_bins != kNbins || m.fft_size != kNfft) die("blob fft/bins mismatch (%d/%d)", m.fft_size, m.n_bins);
  if (m.fs != kSr) die("blob fs %d != %d", m.fs, kSr);
  // 68 features * (2*context+1) + 34 utterance statistics
  const int expect_in = 68 * (2 * m.context + 1) + m.nceps_in + 2;
  if (m.in_dim != expect_in) die("blob in_dim %d != %d", m.in_dim, expect_in);

  const uint8_t *p = buf.data() + 4 + 12 * 4;
  m.pitch_ratio = *(const float *)p; p += 4;
  // The float payload is 4-byte aligned but not necessarily 8-byte aligned; the
  // arrays below are only ever read through float*, so 4-byte alignment is enough.
  const float *fp = (const float *)p;
  size_t off = 0;
  m.mu = fp + off;      off += m.in_dim;
  m.sd = fp + off;      off += m.in_dim;
  m.dct_in = fp + off;  off += (size_t)m.nceps_in * m.n_bins;
  m.dct_out = fp + off; off += (size_t)m.out_dim * m.n_bins;
  m.synth = fp + off;   off += (size_t)m.out_dim * m.n_bins;
  off += 1;  // duplicated pitch ratio
  for (int l = 0; l < m.layers; l++) {
    int in = (l == 0) ? m.in_dim : m.hidden;
    m.W.push_back(fp + off); off += (size_t)m.hidden * in;
    m.B.push_back(fp + off); off += (size_t)m.hidden;
  }
  m.Wout = fp + off; off += (size_t)m.out_dim * m.hidden;
  m.Bout = fp + off; off += m.out_dim;

  size_t need = (4 + 12 * 4 + 4) + off * 4;
  if (buf.size() < need) die("%s: truncated (have %zu need %zu)", path, buf.size(), need);
  return m;
}

// ----------------------------------------------------------------------------
// FFT (radix-2, single precision) ---------------------------------------------
//
// The STFT/ISTFT does 802 transforms of 1024 points per 4 s of audio, which was
// 518 ms on the board -- the third largest cost.  It was double precision, and the
// A9's VFP retires half as many doubles as floats per cycle with no double-precision
// NEON at all, so moving the transform to float is a straight ~2x.  The spectra are
// converted back to double where they enter the (double precision) gain and
// overlap-add, so only the transform itself loses precision (~1e-7 relative, i.e.
// far inside the 121 dB agreement with the reference).
struct Fft {
  int n = 0, logn = 0;
  std::vector<std::complex<float>> tw;
  std::vector<int> rev;

  void init(int n_) {
    n = n_;
    logn = 0;
    while ((1 << logn) < n) logn++;
    rev.resize(n);
    for (int i = 0; i < n; i++) {
      int r = 0;
      for (int b = 0; b < logn; b++) if (i & (1 << b)) r |= 1 << (logn - 1 - b);
      rev[i] = r;
    }
    tw.resize(n / 2);
    for (int i = 0; i < n / 2; i++) {
      double a = -2.0 * M_PI * (double)i / (double)n;
      tw[i] = std::complex<float>((float)cos(a), (float)sin(a));
    }
  }

  // in-place forward (e^{-i..})
  void forward(std::complex<float> *a) const {
    for (int i = 0; i < n; i++) if (i < rev[i]) std::swap(a[i], a[rev[i]]);
    for (int len = 2; len <= n; len <<= 1) {
      int half = len >> 1, step = n / len;
      for (int i = 0; i < n; i += len) {
        for (int j = 0; j < half; j++) {
          std::complex<float> u = a[i + j];
          std::complex<float> v = a[i + j + half] * tw[j * step];
          a[i + j] = u + v;
          a[i + j + half] = u - v;
        }
      }
    }
  }

  // in-place inverse including the 1/n of numpy.fft.irfft
  void inverse(std::complex<float> *a) const {
    for (int i = 0; i < n; i++) a[i] = std::conj(a[i]);
    forward(a);
    float s = 1.0f / (float)n;
    for (int i = 0; i < n; i++) a[i] = std::conj(a[i]) * s;
  }
};

// ----------------------------------------------------------------------------
// resampler: 127-tap Hamming-windowed sinc, rational L/M ---------------------
// ----------------------------------------------------------------------------
// v[i] = sum_k h[k] * xu[i-k] with xu the zero-stuffed input; y[m] = L*v[m*M+off].
// off is picked so that the group delay is a whole number of output samples at
// the rate we care about (31 samples for 32k->16k).
static void resample_fir(const std::vector<double> &x, int in_rate, int out_rate,
                         std::vector<double> &y) {
  int n_in = (int)x.size();
  int g = 1;
  for (int i = 1; i <= in_rate && i <= out_rate; i++)
    if (in_rate % i == 0 && out_rate % i == 0) g = i;
  const int L = out_rate / g, M = in_rate / g;
  const int fs_high = in_rate * L;
  const double fc = std::min(kCutoffHz, 0.499 * (double)(in_rate < out_rate ? in_rate : out_rate));
  const double fc_n = fc / (double)fs_high;          // cycles/sample at fs_high
  const int c = (kTaps - 1) / 2;

  std::vector<double> h(kTaps);
  double sum = 0.0;
  for (int k = 0; k < kTaps; k++) {
    int i = k - c;
    double s = (i == 0) ? 1.0 : sin(2.0 * M_PI * fc_n * (double)i) / (2.0 * M_PI * fc_n * (double)i);
    double w = 0.54 - 0.46 * cos(2.0 * M_PI * (double)k / (double)(kTaps - 1));  // Hamming
    h[k] = 2.0 * fc_n * s * w;
    sum += h[k];
  }
  for (int k = 0; k < kTaps; k++) h[k] /= sum;       // unity DC gain

  const int n_xu = n_in * L;
  // xu holds the zero-stuffed input with a (kTaps-1)-sample zero prefix so that
  // the convolution never reads before the buffer.
  const int pad = kTaps - 1;
  std::vector<double> xu((size_t)n_xu + pad + kTaps + 1, 0.0);
  for (int j = 0; j < n_xu; j++) if (j % L == 0) xu[(size_t)j + pad] = x[j / L];

  const int n_out = (int)((long long)n_in * out_rate / in_rate);
  const int off = (L > 1) ? 0 : 1;      // keeps the group delay a whole sample
  y.assign(n_out, 0.0);
  // h is symmetric (windowed sinc, odd length), so fold the taps pairwise: this
  // halves the multiplies.  Only the summation order changes, which is a 1e-16
  // effect in double.
  const int mid = kTaps / 2;
  for (int m = 0; m < n_out; m++) {
    const int base = m * M + off + pad;
    const double *xp = &xu[base];       // xu[base-k], k = 0 .. kTaps-1
    double acc = h[mid] * xp[-mid];
    for (int k = 0; k < mid; k++)
      acc += h[k] * (xp[-k] + xp[-(kTaps - 1 - k)]);
    y[m] = (double)L * acc;
  }
}

// ----------------------------------------------------------------------------
// WORLD analysis -------------------------------------------------------------
// ----------------------------------------------------------------------------
// accumulated WORLD sub-stage times (ms), filled by world_analyse()
static double g_t_dio = 0.0, g_t_sm = 0.0, g_t_ct = 0.0, g_t_d4c = 0.0;
static double g_t_feat = 0.0, g_t_mlp = 0.0;

struct WorldAna {
  int n_frames = 0;
  std::vector<double> t;        // temporal positions (seconds)
  std::vector<double> f0;       // stone-masked f0
  std::vector<double> logsp;    // n_frames * 513, ln(power)
  std::vector<double> ap;       // n_frames * 513 (only when D4C ran on every frame)
  std::vector<double> apmean;   // n_frames, mean aperiodicity (the only ap feature)
};

// D4C is the single most expensive WORLD stage (1.47 s / 4 s audio on the board)
// and the model consumes exactly one scalar from it: the per-frame mean of the
// aperiodicity over 513 bins.  Aperiodicity is smooth in time, so running D4C on
// every `ap_stride`-th frame and interpolating that scalar is enough.  Note that
// D4C takes the frame grid as an argument, so this is real work skipped rather
// than a re-weighting: the cost scales with the number of frames passed.
//
// The same argument applies to StoneMask (a per-frame refinement of f0) and to
// CheapTrick (a per-frame spectral envelope): both are functions of a single
// frame taken from the frame grid passed in, so a stride skips real work and the
// gap is filled by linear interpolation in log(f0) / log(power).  DIO cannot be
// strided: its cost is in the global contour tracking, not per frame.
//
// The model sees exactly the same quantities as before (513-bin log envelope,
// f0, aperiodicity mean); a stride only makes them slightly smoother in time.
// The gates used to accept a stride are waveform correlation >= 0.995 against the
// stride-1 version and UTMOS drop <= 0.03 -- see board_c_20261025_squeeze.md.

// linear interpolation of a per-frame scalar sequence from a stride-N grid
static void interp_series(const std::vector<double> &sub, int t_len, int stride,
                          int T, std::vector<double> &dst) {
  dst.assign(T, 0.0);
  if (stride == 1) {
    for (int i = 0; i < T; i++) dst[i] = sub[std::min(i, t_len - 1)];
    return;
  }
  for (int i = 0; i < T; i++) {
    const double pos = (double)i / (double)stride;
    const int lo = (int)std::floor(pos);
    if (lo >= t_len - 1) {
      dst[i] = sub[t_len - 1];
    } else {
      const double w = pos - (double)lo;
      dst[i] = sub[lo] * (1.0 - w) + sub[lo + 1] * w;
    }
  }
}

static void world_analyse(const std::vector<double> &x, bool want_ap, int ap_stride,
                          int ct_stride, int sm_stride, WorldAna &out) {
  const int n = (int)x.size();
  if (n <= 0) die("empty signal for WORLD");

  DioOption dopt;
  InitializeDioOption(&dopt);
  dopt.f0_floor = 75.0;
  dopt.f0_ceil = 400.0;
  dopt.frame_period = 10.0;
  dopt.speed = 4;
  dopt.allowed_range = 0.1;

  const int f0_length = GetSamplesForDIO(kSr, n, dopt.frame_period);
  out.n_frames = f0_length;
  out.t.assign(f0_length, 0.0);
  std::vector<double> f0_raw(f0_length, 0.0);
  const double t0 = now_ms();
  Dio(x.data(), n, kSr, &dopt, out.t.data(), f0_raw.data());
  g_t_dio += now_ms() - t0;

  // ---- StoneMask, optionally strided (f0 is smooth, so interpolation is safe;
  // voicing is only kept when both bracketing analysed frames are voiced)
  out.f0.assign(f0_length, 0.0);
  const double t1 = now_ms();
  const int ss = std::max(1, sm_stride);
  if (ss == 1) {
    StoneMask(x.data(), n, kSr, out.t.data(), f0_raw.data(), f0_length, out.f0.data());
  } else {
    const int ts = (f0_length + ss - 1) / ss;
    std::vector<double> t_sub(ts), f0_sub(ts), f0_ref(ts);
    for (int i = 0; i < ts; i++) {
      const int src = std::min(i * ss, f0_length - 1);
      t_sub[i] = out.t[src];
      f0_sub[i] = f0_raw[src];
    }
    StoneMask(x.data(), n, kSr, t_sub.data(), f0_sub.data(), ts, f0_ref.data());
    for (int i = 0; i < f0_length; i++) {
      const double pos = (double)i / (double)ss;
      const int lo = (int)std::floor(pos);
      if (lo >= ts - 1) {
        out.f0[i] = f0_ref[ts - 1];
      } else {
        const double w = pos - (double)lo;
        const double a = f0_ref[lo], b = f0_ref[lo + 1];
        if (a > 0.0 && b > 0.0) out.f0[i] = a * (1.0 - w) + b * w;   // voiced both
        else out.f0[i] = (w < 0.5) ? a : b;                          // keep V/UV edges
      }
    }
  }
  g_t_sm += now_ms() - t1;

  // ---- CheapTrick, optionally strided
  CheapTrickOption copt;
  InitializeCheapTrickOption(kSr, &copt);
  copt.fft_size = kNfft;                  // pyworld: fft_size=1024 wins over f0_floor
  const int cs = std::max(1, ct_stride);
  const int tcs = (f0_length + cs - 1) / cs;
  std::vector<double> sp((size_t)tcs * kNbins, 0.0);
  std::vector<double *> sp_rows(tcs);
  std::vector<double> ct_t(tcs), ct_f0(tcs);
  for (int i = 0; i < tcs; i++) {
    const int src = std::min(i * cs, f0_length - 1);
    ct_t[i] = out.t[src];
    ct_f0[i] = out.f0[src];
    sp_rows[i] = &sp[(size_t)i * kNbins];
  }
  const double t2 = now_ms();
  CheapTrick(x.data(), n, kSr, ct_t.data(), ct_f0.data(), tcs, &copt, sp_rows.data());
  g_t_ct += now_ms() - t2;

  out.logsp.assign((size_t)f0_length * kNbins, 0.0);
  std::vector<double> ls((size_t)tcs * kNbins);
  for (size_t i = 0; i < ls.size(); i++) ls[i] = log(std::max(sp[i], 1e-16));
  if (cs == 1) {
    out.logsp = ls;
  } else {
    // Catmull-Rom (cubic) along time rather than linear: the log envelope of a
    // 20 ms gap is smooth with curvature, and cubic roughly halves the
    // interpolation error for the same stride (measured: waveform corr vs the
    // stride-1 version 0.9966 -> 0.9982, identity 0.611 -> 0.627).
    for (int t = 0; t < f0_length; t++) {
      const double pos = (double)t / (double)cs;
      const int lo = (int)std::floor(pos);
      const double w = pos - (double)lo;
      double *d = &out.logsp[(size_t)t * kNbins];
      if (lo >= tcs - 1) {
        memcpy(d, &ls[(size_t)(tcs - 1) * kNbins], kNbins * sizeof(double));
        continue;
      }
      const int i0 = std::max(lo - 1, 0), i1 = lo, i2 = lo + 1;
      const int i3 = std::min(lo + 2, tcs - 1);
      const double *p0 = &ls[(size_t)i0 * kNbins];
      const double *p1 = &ls[(size_t)i1 * kNbins];
      const double *p2 = &ls[(size_t)i2 * kNbins];
      const double *p3 = &ls[(size_t)i3 * kNbins];
      const double w2 = w * w, w3 = w2 * w;
      const double c0 = -0.5 * w3 + w2 - 0.5 * w;
      const double c1 = 1.5 * w3 - 2.5 * w2 + 1.0;
      const double c2 = -1.5 * w3 + 2.0 * w2 + 0.5 * w;
      const double c3 = 0.5 * w3 - 0.5 * w2;
      for (int k = 0; k < kNbins; k++)
        d[k] = c0 * p0[k] + c1 * p1[k] + c2 * p2[k] + c3 * p3[k];
    }
  }

  if (!want_ap) {
    out.ap.clear();
    out.apmean.assign(f0_length, 0.0);
    return;
  }

  D4COption aopt;
  InitializeD4COption(&aopt);
  aopt.threshold = 0.85;
  const int stride = std::max(1, ap_stride);
  const int t_len = (f0_length + stride - 1) / stride;
  std::vector<double> ap_sub((size_t)t_len * kNbins, 0.0);
  std::vector<double> t_sub(t_len), f0_sub(t_len);
  std::vector<double *> ap_rows(t_len);
  for (int i = 0; i < t_len; i++) {
    const int src = std::min(i * stride, f0_length - 1);
    t_sub[i] = out.t[src];
    f0_sub[i] = out.f0[src];
    ap_rows[i] = &ap_sub[(size_t)i * kNbins];
  }
  const double t3 = now_ms();
  D4C(x.data(), n, kSr, t_sub.data(), f0_sub.data(), t_len, kNfft, &aopt, ap_rows.data());
  g_t_d4c += now_ms() - t3;

  out.apmean.assign(f0_length, 0.0);
  std::vector<double> apm_sub(t_len, 0.0);
  for (int i = 0; i < t_len; i++) {
    double s = 0.0;
    for (int b = 0; b < kNbins; b++) s += ap_sub[(size_t)i * kNbins + b];
    apm_sub[i] = s / (double)kNbins;
  }
  if (stride == 1) {
    for (int i = 0; i < f0_length; i++) out.apmean[i] = apm_sub[i];
    out.ap = ap_sub;                                   // full grid: keep it for dumps
  } else {
    // linear interpolation between the analysed frames (edge-clamped)
    for (int i = 0; i < f0_length; i++) {
      double pos = (double)i / (double)stride;
      int lo = (int)std::floor(pos);
      if (lo >= t_len - 1) {
        out.apmean[i] = apm_sub[t_len - 1];
      } else {
        double w = pos - (double)lo;
        out.apmean[i] = apm_sub[lo] * (1.0 - w) + apm_sub[lo + 1] * w;
      }
    }
    out.ap.clear();
  }
}

// Cheap spectral envelope of the pitch-shifted signal, decimated in time.
//
// The exact way to get this is a full second WORLD pass (DIO + StoneMask +
// CheapTrick) on xB.  Two facts make that unnecessary:
//   * the pitch stage multiplies f0 by the same ratio that shifts the spectrum,
//     so f0_shifted = ratio * f0_source -- no second DIO/StoneMask is needed,
//     and the inherited contour is smoother than a re-estimate;
//   * a spectral envelope is smooth across 10 ms frames, so CheapTrick on every
//     `stride`-th frame plus linear interpolation between them is enough.
// CheapTrick takes the frame grid as an argument, so this skips real work.
static void analyse_shifted_env(const std::vector<double> &xB,
                                const std::vector<double> &f0_src, double ratio,
                                int stride, WorldAna &out) {
  const int n = (int)xB.size();
  const int T = GetSamplesForDIO(kSr, n, 10.0);
  out.n_frames = T;
  out.f0.assign(T, 0.0);
  out.ap.clear();
  out.apmean.assign(T, 0.0);

  const int st = std::max(1, stride);
  const int ts = (T + st - 1) / st;
  std::vector<double> t_sub(ts), f0_sub(ts);
  for (int i = 0; i < ts; i++) {
    const int src = std::min(i * st, T - 1);
    t_sub[i] = (double)src * 0.01;
    const double f = (src < (int)f0_src.size()) ? f0_src[src] : 0.0;
    f0_sub[i] = (f > 0.0) ? f * ratio : 0.0;
    out.f0[src] = f0_sub[i];
  }

  CheapTrickOption copt;
  InitializeCheapTrickOption(kSr, &copt);
  copt.fft_size = kNfft;
  std::vector<double> sp((size_t)ts * kNbins, 0.0);
  std::vector<double *> rows(ts);
  for (int i = 0; i < ts; i++) rows[i] = &sp[(size_t)i * kNbins];
  const double t0 = now_ms();
  CheapTrick(xB.data(), n, kSr, t_sub.data(), f0_sub.data(), ts, &copt, rows.data());
  g_t_ct += now_ms() - t0;

  out.logsp.assign((size_t)T * kNbins, 0.0);
  std::vector<double> ls((size_t)ts * kNbins);
  for (size_t i = 0; i < ls.size(); i++) ls[i] = log(std::max(sp[i], 1e-16));
  if (st == 1) {
    out.logsp = ls;
    return;
  }
  for (int t = 0; t < T; t++) {
    double pos = (double)t / (double)st;
    int lo = (int)std::floor(pos);
    double w = pos - (double)lo;
    if (lo >= ts - 1) {
      memcpy(&out.logsp[(size_t)t * kNbins], &ls[(size_t)(ts - 1) * kNbins],
             kNbins * sizeof(double));
    } else {
      const double *a = &ls[(size_t)lo * kNbins];
      const double *b = &ls[(size_t)(lo + 1) * kNbins];
      double *d = &out.logsp[(size_t)t * kNbins];
      for (int k = 0; k < kNbins; k++) d[k] = a[k] * (1.0 - w) + b[k] * w;
    }
  }
}

// CheapTrick once: the envelope of the pitch-shifted signal, derived from the
// source envelope by stretching the frequency axis instead of re-analysing.
//
// SoundTouch shifts pitch by resampling (f -> ratio*f, so the whole spectral
// envelope including the formants moves by `ratio`) followed by a WSOLA time
// stretch that is spectrally transparent.  Hence
//     logsp_shifted[t][b] ~= logsp_source[t][b / ratio]
// with linear interpolation between bins.  `ratio` is measured, not assumed: see
// measure_pitch_axis.py (desktop measurement gives 1.39x on this material).
static void derive_shifted_logsp(const std::vector<double> &logsp_src, int n_frames,
                                 double ratio, std::vector<double> &out) {
  out.assign((size_t)n_frames * kNbins, 0.0);
  for (int t = 0; t < n_frames; t++) {
    const double *src = &logsp_src[(size_t)t * kNbins];
    double *dst = &out[(size_t)t * kNbins];
    for (int b = 0; b < kNbins; b++) {
      double pos = (double)b / ratio;
      if (pos >= (double)(kNbins - 1)) {
        dst[b] = src[kNbins - 1];
      } else {
        int lo = (int)pos;
        double w = pos - (double)lo;
        dst[b] = src[lo] * (1.0 - w) + src[lo + 1] * w;
      }
    }
  }
}

// ----------------------------------------------------------------------------
// per-utterance prediction (features + MLP) ----------------------------------
// ----------------------------------------------------------------------------
struct Pred {
  int n_frames = 0;
  std::vector<float> feats;     // n_frames * 68
  std::vector<float> stats;     // 34
  std::vector<float> Xn;        // n_frames * in_dim (normalised)
  std::vector<float> res;       // n_frames * out_dim
  std::vector<double> logsp_pred;  // n_frames * 513
  int voiced = 0;
  double median_f0 = 0.0;
  bool threaded = false;
};

static float gelu_exact(float x) {
  // nn.GELU() default is the exact erf form, NOT the tanh approximation
  return 0.5f * x * (1.0f + erff(x * 0.70710678118654752440f));
}

// Batched inference, tiled over (frames x output neurons).
//
// The model is 4.6 MB of fp32 weights and the A9 has 32 KB L1 / 512 KB L2, so the
// naive per-frame loop streams the whole blob from DDR for every frame: measured
// on the board at 24 ms/frame (RTF 2.4), purely memory bound.  Blocking 8 frames
// x 8 neurons fixes the bandwidth but needs 64 live accumulators, which spills to
// the stack and puts a load+store on every MAC (9.5 ms/frame measured).
//
// The kernel blocks 8 frames x 4 neurons: two NEON vectors per neuron, so each
// weight load feeds 8 MACs instead of 4, which halves the weight traffic the
// bandwidth-bound loop was paying for (measured: 4->8 frames took the board MLP
// from 2097 ms to ~1200 ms).  Eight accumulators + two activation vectors fit the
// 16 NEON quad registers.  The portable fallback has the same loop shape so the
// desk-side build stays representative.
//
// Numerics: the NEON path uses fused multiply-add (single rounding) whereas the
// portable path rounds twice, so the two differ at the 1e-7 level.  Both are
// within the 121 dB agreement already established with the Python reference.
static const int kMlpNB = 8;   // frames per block = two NEON vectors
static const int kMlpJB = 4;   // neurons per block

#include "mlp_int8.inc"

__attribute__((noinline, optimize("O3")))
static void mlp_forward_batch(const Model &m, const float *X, int n_frames, float *Y) {
  if (g_mlp_int8) { mlp_forward_batch_int8(m, X, n_frames, Y); return; }
  // dbg 6: return immediately (measures predict() minus the MLP entirely)
  if (g_mlp_dbg == 6) { memset(Y, 0, sizeof(float) * (size_t)n_frames * m.out_dim); return; }
  const int NB = kMlpNB, JB = kMlpJB;
  const int kdbg = g_mlp_dbg;
  std::vector<float> in0((size_t)m.in_dim * NB);
  std::vector<float> cur((size_t)m.hidden * NB), nxt((size_t)m.hidden * NB);
  float acc[JB][NB];
  float tmp[NB];

  for (int f0 = 0; f0 < n_frames; f0 += NB) {
    // clamp instead of shrink: keeps every inner loop at a fixed trip count
    int idx[NB];
    for (int t = 0; t < NB; t++) idx[t] = std::min(f0 + t, n_frames - 1);
    for (int t = 0; t < NB; t++) {
      const float *src = X + (size_t)idx[t] * m.in_dim;
      for (int i = 0; i < m.in_dim; i++) in0[(size_t)i * NB + t] = src[i];
    }
    const float *inp = in0.data();
    float *a = cur.data(), *b = nxt.data();
    int in_dim = m.in_dim;
    for (int l = 0; l < m.layers; l++) {
      const int in = in_dim;
      const float *W = m.W[l], *Bb = m.B[l];
      for (int jb = 0; jb < m.hidden; jb += JB) {
        const float *w0 = W + (size_t)(jb + 0) * in;
        const float *w1 = W + (size_t)(jb + 1) * in;
        const float *w2 = W + (size_t)(jb + 2) * in;
        const float *w3 = W + (size_t)(jb + 3) * in;
#if defined(__ARM_NEON)
        float32x4_t c0a = vdupq_n_f32(Bb[jb + 0]), c0b = vdupq_n_f32(Bb[jb + 0]);
        float32x4_t c1a = vdupq_n_f32(Bb[jb + 1]), c1b = vdupq_n_f32(Bb[jb + 1]);
        float32x4_t c2a = vdupq_n_f32(Bb[jb + 2]), c2b = vdupq_n_f32(Bb[jb + 2]);
        float32x4_t c3a = vdupq_n_f32(Bb[jb + 3]), c3b = vdupq_n_f32(Bb[jb + 3]);
        const int kmax = (kdbg == 3) ? (in / 2) : ((kdbg == 2) ? 0 : in);
        for (int i = 0; i < kmax; i++) {
          const float32x4_t a0 = vld1q_f32(inp + (size_t)i * NB);
          const float32x4_t a1 = vld1q_f32(inp + (size_t)i * NB + 4);
          const float32_t q0 = w0[i], q1 = w1[i], q2 = w2[i], q3 = w3[i];
          c0a = vmlaq_n_f32(c0a, a0, q0); c0b = vmlaq_n_f32(c0b, a1, q0);
          c1a = vmlaq_n_f32(c1a, a0, q1); c1b = vmlaq_n_f32(c1b, a1, q1);
          c2a = vmlaq_n_f32(c2a, a0, q2); c2b = vmlaq_n_f32(c2b, a1, q2);
          c3a = vmlaq_n_f32(c3a, a0, q3); c3b = vmlaq_n_f32(c3b, a1, q3);
        }
        vst1q_f32(tmp, c0a); for (int t = 0; t < 4; t++) a[(size_t)(jb + 0) * NB + t] = (kdbg == 1) ? tmp[t] : gelu_exact(tmp[t]);
        vst1q_f32(tmp, c0b); for (int t = 0; t < 4; t++) a[(size_t)(jb + 0) * NB + 4 + t] = gelu_exact(tmp[t]);
        vst1q_f32(tmp, c1a); for (int t = 0; t < 4; t++) a[(size_t)(jb + 1) * NB + t] = gelu_exact(tmp[t]);
        vst1q_f32(tmp, c1b); for (int t = 0; t < 4; t++) a[(size_t)(jb + 1) * NB + 4 + t] = gelu_exact(tmp[t]);
        vst1q_f32(tmp, c2a); for (int t = 0; t < 4; t++) a[(size_t)(jb + 2) * NB + t] = gelu_exact(tmp[t]);
        vst1q_f32(tmp, c2b); for (int t = 0; t < 4; t++) a[(size_t)(jb + 2) * NB + 4 + t] = gelu_exact(tmp[t]);
        vst1q_f32(tmp, c3a); for (int t = 0; t < 4; t++) a[(size_t)(jb + 3) * NB + t] = gelu_exact(tmp[t]);
        vst1q_f32(tmp, c3b); for (int t = 0; t < 4; t++) a[(size_t)(jb + 3) * NB + 4 + t] = gelu_exact(tmp[t]);
#else
        for (int t = 0; t < NB; t++) {
          acc[0][t] = Bb[jb + 0]; acc[1][t] = Bb[jb + 1];
          acc[2][t] = Bb[jb + 2]; acc[3][t] = Bb[jb + 3];
        }
        for (int i = 0; i < in; i++) {
          const float *ip = inp + (size_t)i * NB;
          const float q0 = w0[i], q1 = w1[i], q2 = w2[i], q3 = w3[i];
          for (int t = 0; t < NB; t++) {
            const float av = ip[t];
            acc[0][t] += q0 * av; acc[1][t] += q1 * av;
            acc[2][t] += q2 * av; acc[3][t] += q3 * av;
          }
        }
        for (int j = 0; j < JB; j++)
          for (int t = 0; t < NB; t++) a[(size_t)(jb + j) * NB + t] = gelu_exact(acc[j][t]);
#endif
      }
      inp = a;
      std::swap(a, b);
      in_dim = m.hidden;
    }
    // output layer: keeps every value, no GELU.  out_dim is a multiple of JB.
    for (int jb = 0; jb < m.out_dim; jb += JB) {
      const float *w0 = m.Wout + (size_t)(jb + 0) * m.hidden;
      const float *w1 = m.Wout + (size_t)(jb + 1) * m.hidden;
      const float *w2 = m.Wout + (size_t)(jb + 2) * m.hidden;
      const float *w3 = m.Wout + (size_t)(jb + 3) * m.hidden;
#if defined(__ARM_NEON)
      float32x4_t c0a = vdupq_n_f32(m.Bout[jb + 0]), c0b = vdupq_n_f32(m.Bout[jb + 0]);
      float32x4_t c1a = vdupq_n_f32(m.Bout[jb + 1]), c1b = vdupq_n_f32(m.Bout[jb + 1]);
      float32x4_t c2a = vdupq_n_f32(m.Bout[jb + 2]), c2b = vdupq_n_f32(m.Bout[jb + 2]);
      float32x4_t c3a = vdupq_n_f32(m.Bout[jb + 3]), c3b = vdupq_n_f32(m.Bout[jb + 3]);
      for (int i = 0; i < m.hidden; i++) {
        const float32x4_t a0 = vld1q_f32(inp + (size_t)i * NB);
        const float32x4_t a1 = vld1q_f32(inp + (size_t)i * NB + 4);
        const float32_t q0 = w0[i], q1 = w1[i], q2 = w2[i], q3 = w3[i];
        c0a = vmlaq_n_f32(c0a, a0, q0); c0b = vmlaq_n_f32(c0b, a1, q0);
        c1a = vmlaq_n_f32(c1a, a0, q1); c1b = vmlaq_n_f32(c1b, a1, q1);
        c2a = vmlaq_n_f32(c2a, a0, q2); c2b = vmlaq_n_f32(c2b, a1, q2);
        c3a = vmlaq_n_f32(c3a, a0, q3); c3b = vmlaq_n_f32(c3b, a1, q3);
      }
      vst1q_f32(tmp, c0a); for (int t = 0; t < 4; t++) if (f0+t < n_frames) Y[(size_t)(f0+t)*m.out_dim + jb + 0] = tmp[t];
      vst1q_f32(tmp, c0b); for (int t = 0; t < 4; t++) if (f0+4+t < n_frames) Y[(size_t)(f0+4+t)*m.out_dim + jb + 0] = tmp[t];
      vst1q_f32(tmp, c1a); for (int t = 0; t < 4; t++) if (f0+t < n_frames) Y[(size_t)(f0+t)*m.out_dim + jb + 1] = tmp[t];
      vst1q_f32(tmp, c1b); for (int t = 0; t < 4; t++) if (f0+4+t < n_frames) Y[(size_t)(f0+4+t)*m.out_dim + jb + 1] = tmp[t];
      vst1q_f32(tmp, c2a); for (int t = 0; t < 4; t++) if (f0+t < n_frames) Y[(size_t)(f0+t)*m.out_dim + jb + 2] = tmp[t];
      vst1q_f32(tmp, c2b); for (int t = 0; t < 4; t++) if (f0+4+t < n_frames) Y[(size_t)(f0+4+t)*m.out_dim + jb + 2] = tmp[t];
      vst1q_f32(tmp, c3a); for (int t = 0; t < 4; t++) if (f0+t < n_frames) Y[(size_t)(f0+t)*m.out_dim + jb + 3] = tmp[t];
      vst1q_f32(tmp, c3b); for (int t = 0; t < 4; t++) if (f0+4+t < n_frames) Y[(size_t)(f0+4+t)*m.out_dim + jb + 3] = tmp[t];
#else
      for (int t = 0; t < NB; t++) {
        acc[0][t] = m.Bout[jb + 0]; acc[1][t] = m.Bout[jb + 1];
        acc[2][t] = m.Bout[jb + 2]; acc[3][t] = m.Bout[jb + 3];
      }
      for (int i = 0; i < m.hidden; i++) {
        const float *ip = inp + (size_t)i * NB;
        const float q0 = w0[i], q1 = w1[i], q2 = w2[i], q3 = w3[i];
        for (int t = 0; t < NB; t++) {
          const float av = ip[t];
          acc[0][t] += q0 * av; acc[1][t] += q1 * av;
          acc[2][t] += q2 * av; acc[3][t] += q3 * av;
        }
      }
      for (int j = 0; j < JB; j++)
        for (int t = 0; t < NB; t++)
          if (f0 + t < n_frames) Y[(size_t)(f0 + t) * m.out_dim + jb + j] = acc[j][t];
#endif
    }
  }
}

// The spectral envelope of the pitch-shifted signal (second WORLD pass) does not
// depend on the MLP, so with two cores it is run on the worker thread *before*
// that thread takes its share of the MLP frames.  The frame split is biased
// (3/4 on the main thread) because the worker also carries the side job.
struct SideJob {
  const std::vector<double> *xB;
  const std::vector<double> *f0_src;
  double ratio;
  int den_stride;
  WorldAna *out;
};

struct MlpHalfJob {
  const Model *m;
  const float *X;
  int n;
  float *Y;
  SideJob *side;      // optional, executed before the MLP share
};

static void *mlp_half_thread(void *p) {
  MlpHalfJob *j = (MlpHalfJob *)p;
  if (j->side) {
    if (j->side->den_stride > 0)
      analyse_shifted_env(*j->side->xB, *j->side->f0_src, j->side->ratio,
                          j->side->den_stride, *j->side->out);
    else
      world_analyse(*j->side->xB, false, 1, 1, 1, *j->side->out);
  }
  mlp_forward_batch(*j->m, j->X, j->n, j->Y);
  return nullptr;
}

// frame_features() + utterance_stats() + stack_context(), transcribed from
// scripts/train_student.py and scripts/train_v5.py.
static void predict(const Model &m, const WorldAna &a, Pred &p, int n_threads,
                    SideJob *side, std::vector<float> *stats_ema = nullptr) {
  const int T = a.n_frames;
  const double t_feat0 = now_ms();
  p.n_frames = T;
  p.feats.assign((size_t)T * 68, 0.0f);
  p.stats.assign(m.nceps_in + 2, 0.0f);

  // --- cepstra, utterance mean, gain, voiced stats
  std::vector<double> ceps((size_t)T * m.nceps_in, 0.0);
  for (int t = 0; t < T; t++) {
    const double *ls = &a.logsp[(size_t)t * kNbins];
    for (int k = 0; k < m.nceps_in; k++) {
      const float *d = m.dct_in + (size_t)k * kNbins;
      double s = 0.0;
      for (int b = 0; b < kNbins; b++) s += ls[b] * (double)d[b];
      ceps[(size_t)t * m.nceps_in + k] = s;
    }
  }
  std::vector<double> cmu(m.nceps_in, 0.0);
  for (int t = 0; t < T; t++)
    for (int k = 0; k < m.nceps_in; k++) cmu[k] += ceps[(size_t)t * m.nceps_in + k];
  for (int k = 0; k < m.nceps_in; k++) cmu[k] /= (double)T;

  std::vector<double> gain(T, 0.0), logf0(T, 0.0), apmean(T, 0.0);
  std::vector<double> ceps_c((size_t)T * m.nceps_in, 0.0);
  std::vector<double> voiced_logf0;
  int nvoiced = 0;
  for (int t = 0; t < T; t++) {
    double g = 0.0;
    const double *ls = &a.logsp[(size_t)t * kNbins];
    for (int b = 0; b < kNbins; b++) g += ls[b];
    gain[t] = g / (double)kNbins;
    for (int k = 0; k < m.nceps_in; k++)
      ceps_c[(size_t)t * m.nceps_in + k] = ceps[(size_t)t * m.nceps_in + k] - cmu[k];
    if (a.f0[t] > 0.0) {
      logf0[t] = log(std::max(a.f0[t], 1e-3));
      voiced_logf0.push_back(logf0[t]);
      nvoiced++;
    } else {
      logf0[t] = 0.0;
    }
    if (!a.apmean.empty()) apmean[t] = a.apmean[t];
  }
  p.voiced = nvoiced;
  const int voiced_flag_scale = T;  // (f0 > 0) as float
  double logf0_mean = 0.0;
  if (!voiced_logf0.empty()) {
    for (double v : voiced_logf0) logf0_mean += v;
    logf0_mean /= (double)voiced_logf0.size();
  }
  double gain_mean = 0.0;
  for (int t = 0; t < T; t++) gain_mean += gain[t];
  gain_mean /= (double)T;

  // --- 68-dim frame features
  for (int t = 0; t < T; t++) {
    float *f = &p.feats[(size_t)t * 68];
    for (int k = 0; k < m.nceps_in; k++) f[k] = (float)ceps_c[(size_t)t * m.nceps_in + k];
    f[32] = (float)(logf0[t] - logf0_mean);
    f[33] = (a.f0[t] > 0.0) ? 1.0f : 0.0f;
    f[34] = (float)(gain[t] - gain_mean);
    f[35] = (float)apmean[t];
    for (int k = 0; k < m.nceps_in; k++) {
      double prev = (t == 0) ? ceps_c[k] : ceps_c[(size_t)(t - 1) * m.nceps_in + k];
      f[36 + k] = (float)(ceps_c[(size_t)t * m.nceps_in + k] - prev);  // np.diff prepend
    }
  }

  // --- utterance statistics: mean cepstrum, median log-F0, voiced fraction
  for (int k = 0; k < m.nceps_in; k++) p.stats[k] = (float)cmu[k];
  p.stats[m.nceps_in] = (float)(voiced_logf0.empty() ? 0.0 : median_of(voiced_logf0));
  p.stats[m.nceps_in + 1] = (float)((double)nvoiced / (double)T);
  // Streaming only: per-block statistics make the predicted timbre jump from block
  // to block.  A first-order smoother (new = 0.5 old + 0.5 fresh) keeps them close
  // to the utterance-level estimate that the batch path uses.
  if (stats_ema) {
    if (stats_ema->empty()) *stats_ema = p.stats;
    else {
      for (size_t k = 0; k < p.stats.size(); k++)
        (*stats_ema)[k] = 0.5f * (*stats_ema)[k] + 0.5f * p.stats[k];
      p.stats = *stats_ema;
    }
  }
  p.median_f0 = voiced_logf0.empty() ? 0.0 : exp(median_of(voiced_logf0));

  // --- context stack + normalisation + MLP
  const int ctx = m.context, span = 2 * ctx + 1;
  const int body = 68 * span;
  std::vector<float> xn((size_t)m.in_dim, 0.0f);
  p.Xn.assign((size_t)T * m.in_dim, 0.0f);
  p.res.assign((size_t)T * m.out_dim, 0.0f);
  for (int t = 0; t < T; t++) {
    int col = 0;
    for (int c = 0; c < span; c++) {
      int src = t + c - ctx;
      if (src < 0) src = 0;                 // np.pad(mode="edge")
      if (src > T - 1) src = T - 1;
      memcpy(&xn[col], &p.feats[(size_t)src * 68], 68 * sizeof(float));
      col += 68;
    }
    for (int k = 0; k < m.nceps_in + 2; k++) xn[body + k] = p.stats[k];
    if (col != body) die("internal: context layout");

    float *dst = &p.Xn[(size_t)t * m.in_dim];
    for (int i = 0; i < m.in_dim; i++) dst[i] = (xn[i] - m.mu[i]) / m.sd[i];
  }
  g_t_feat += now_ms() - t_feat0;
  // MLP over all frames; with 2 threads the frame range is split in half.  The two
  // halves touch disjoint output rows and mlp_forward_batch keeps no state, so this
  // is exact (identical results to the serial run, just on two cores).
  // A static glibc can fail to start a thread (the pthread stubs in libc.a return
  // ENOSYS unless libpthread.a is linked whole); in that case fall back to the
  // serial path instead of dying, and report which path actually ran.
  const double t_mlp0 = now_ms();
  bool threaded = false;
  if (n_threads >= 2 && T >= 2 * kMlpNB) {
    int split = (int)((3.0 * (double)T / 4.0) / kMlpNB) * kMlpNB;
    split = std::max(kMlpNB, std::min(split, T - kMlpNB));
    MlpHalfJob job{&m, p.Xn.data() + (size_t)split * m.in_dim, T - split,
                   p.res.data() + (size_t)split * m.out_dim, side};
    pthread_t th;
    // raw pthread API on purpose: std::thread terminates the process in a fully
    // static binary when the libpthread stubs are used instead of the real ones
    if (pthread_create(&th, nullptr, &mlp_half_thread, &job) == 0) {
      mlp_forward_batch(m, p.Xn.data(), split, p.res.data());
      pthread_join(th, nullptr);
      threaded = true;
    } else {
      fprintf(stderr, "vc_stream: pthread_create failed; running serial\n");
    }
  }
  if (!threaded) {
    if (side) {
      if (side->den_stride > 0)
        analyse_shifted_env(*side->xB, *side->f0_src, side->ratio, side->den_stride, *side->out);
      else
        world_analyse(*side->xB, false, 1, 1, 1, *side->out);
    }
    mlp_forward_batch(m, p.Xn.data(), T, p.res.data());
  }
  p.threaded = threaded;

  // --- envelope: 48 source cepstra + residual, then inverse DCT
  p.logsp_pred.assign((size_t)T * kNbins, 0.0);
  std::vector<double> c48(m.nceps_out);   // out_dim source cepstra (48 or 64)
  for (int t = 0; t < T; t++) {
    const double *ls = &a.logsp[(size_t)t * kNbins];
    for (int k = 0; k < m.nceps_out; k++) {
      const float *d = m.dct_out + (size_t)k * kNbins;
      double s = 0.0;
      for (int b = 0; b < kNbins; b++) s += ls[b] * (double)d[b];
      c48[k] = s + (double)p.res[(size_t)t * m.out_dim + k];
    }
    double *lp = &p.logsp_pred[(size_t)t * kNbins];
    for (int b = 0; b < kNbins; b++) {
      const float *sr = &m.synth_T[(size_t)b * m.nceps_out];
      double s = 0.0;
      for (int k = 0; k < m.nceps_out; k++) s += c48[k] * (double)sr[k];
      lp[b] = s;
    }
  }
  (void)voiced_flag_scale;
}

// ----------------------------------------------------------------------------
// STFT / ISTFT (librosa semantics: periodic Hann, center=True, zero pad) -----
// ----------------------------------------------------------------------------
static std::vector<double> hann_periodic(int n) {
  std::vector<double> w(n);
  for (int i = 0; i < n; i++) w[i] = 0.5 - 0.5 * cos(2.0 * M_PI * (double)i / (double)n);
  return w;
}

struct Spec {
  int n_frames = 0;
  std::vector<std::complex<double>> X;   // [t * kNbins + k]
};

static void stft(const std::vector<double> &x, const std::vector<double> &win,
                 const Fft &fft, Spec &s) {
  const int n = (int)x.size();
  const int pad = kNfft / 2;
  s.n_frames = 1 + n / kHop;             // librosa: 1 + (n + 2*pad - n_fft)//hop
  s.X.assign((size_t)s.n_frames * kNbins, std::complex<double>(0.0, 0.0));
  std::vector<std::complex<float>> buf(kNfft);
  for (int t = 0; t < s.n_frames; t++) {
    const int start = t * kHop - pad;
    for (int i = 0; i < kNfft; i++) {
      int j = start + i;
      double v = (j >= 0 && j < n) ? x[j] : 0.0;
      buf[i] = std::complex<float>((float)(v * win[i]), 0.0f);
    }
    fft.forward(buf.data());
    for (int k = 0; k < kNbins; k++)
      s.X[(size_t)t * kNbins + k] = std::complex<double>(buf[k].real(), buf[k].imag());
  }
}

static void istft(const Spec &s, const std::vector<double> &win, const Fft &fft,
                  int out_len, std::vector<double> &y) {
  const int n_full = kNfft + kHop * (s.n_frames - 1);
  std::vector<double> acc((size_t)n_full, 0.0), wsum((size_t)n_full, 0.0);
  std::vector<std::complex<float>> buf(kNfft);
  for (int t = 0; t < s.n_frames; t++) {
    // Hermitian expansion then inverse FFT (numpy.fft.irfft(n=n_fft) semantics)
    for (int k = 0; k < kNbins; k++) {
      const std::complex<double> v = s.X[(size_t)t * kNbins + k];
      buf[k] = std::complex<float>((float)v.real(), (float)v.imag());
    }
    for (int k = kNbins; k < kNfft; k++) {
      const std::complex<double> v = s.X[(size_t)t * kNbins + (kNfft - k)];
      buf[k] = std::complex<float>((float)v.real(), (float)-v.imag());
    }
    fft.inverse(buf.data());
    const int start = t * kHop;
    for (int i = 0; i < kNfft; i++) {
      double w = win[i];
      acc[start + i] += w * buf[i].real();
      wsum[start + i] += w * w;
    }
  }
  const int pad = kNfft / 2;
  y.assign(out_len, 0.0);
  for (int i = 0; i < out_len; i++) {
    int j = i + pad;
    double d = (j < n_full) ? wsum[j] : 0.0;
    double v = (j < n_full) ? acc[j] : 0.0;
    y[i] = (d > 0.0) ? v / d : 0.0;
  }
}

// ----------------------------------------------------------------------------
// envelope transplant --------------------------------------------------------
// ----------------------------------------------------------------------------
struct TransStats {
  double clip_frac = 0.0;    // fraction of (frame,bin) gains outside +-20 dB
  double median_db = 0.0;    // median applied gain over non-silent frames
  int silent_frames = 0;
  int frames = 0;
};

static void transplant(const Model &m, const std::vector<double> &xB,
                       const std::vector<double> &logsp_pred,
                       const std::vector<double> &logsp_src, const Fft &fft,
                       std::vector<double> &y, std::vector<double> *dump_diff,
                       std::vector<float> *dump_mask, TransStats *st,
                       bool env_from_stft) {
  const std::vector<double> win = hann_periodic(kWin);
  Spec s;
  stft(xB, win, fft, s);
  const int T = s.n_frames;
  const int n = (int)xB.size();

  // grid alignment: WORLD and STFT frames are both 10 ms; identical here, the
  // interpolation branch only exists to mirror to_stft_grid().
  auto grid = [&](const std::vector<double> &A) {
    std::vector<double> out((size_t)T * kNbins);
    int na = (int)(A.size() / kNbins);
    if (na == T) {
      out = A;
    } else {
      for (int t = 0; t < T; t++) {
        double pos = (T == 1) ? 0.0 : (double)t * (double)(na - 1) / (double)(T - 1);
        int lo = (int)floor(pos);
        int hi = std::min(lo + 1, na - 1);
        double w = pos - (double)lo;
        for (int b = 0; b < kNbins; b++)
          out[(size_t)t * kNbins + b] =
              A[(size_t)lo * kNbins + b] * (1.0 - w) + A[(size_t)hi * kNbins + b] * w;
      }
    }
    return out;
  };
  // The denominator envelope.  Default is the exact WORLD/CheapTrick envelope of
  // the pitch-shifted signal (a second analysis pass).  With env_from_stft the
  // envelope is estimated from the STFT that this function already computes:
  // log|X|^2 pushed through the model's own out_dim-order cepstral pair (dct_out
  // then synth), which is a smooth spectral envelope and costs almost nothing.
  std::vector<double> src;
  if (env_from_stft) {
    src.assign((size_t)T * kNbins, 0.0);
    std::vector<double> c(m.out_dim), logp(kNbins);
    for (int t = 0; t < T; t++) {
      const std::complex<double> *X = &s.X[(size_t)t * kNbins];
      for (int b = 0; b < kNbins; b++) {
        double p = X[b].real() * X[b].real() + X[b].imag() * X[b].imag();
        logp[b] = log(std::max(p, 1e-16));
      }
      for (int k = 0; k < m.out_dim; k++) {
        const float *d = m.dct_out + (size_t)k * kNbins;
        double acc = 0.0;
        for (int b = 0; b < kNbins; b++) acc += logp[b] * (double)d[b];
        c[k] = acc;
      }
      double *dst = &src[(size_t)t * kNbins];
      for (int b = 0; b < kNbins; b++) {
        const float *sr = &m.synth_T[(size_t)b * m.out_dim];
        double acc = 0.0;
        for (int k = 0; k < m.out_dim; k++) acc += c[k] * (double)sr[k];
        dst[b] = acc;
      }
    }
  } else {
    src = grid(logsp_src);
  }
  const std::vector<double> prd = grid(logsp_pred);

  // frame RMS on the zero-padded signal, exactly like frame_rms()
  std::vector<double> rms(T, 0.0);
  {
    const int pad = kWin / 2;
    const int np = n + 2 * pad;
    std::vector<double> c((size_t)np + 1, 0.0);
    for (int i = 0; i < np; i++) {
      int j = i - pad;
      double v = (j >= 0 && j < n) ? xB[j] : 0.0;
      c[i + 1] = c[i] + v * v;
    }
    std::vector<double> lo(T), hi(T);
    for (int t = 0; t < T; t++) { lo[t] = (double)(t * kHop); hi[t] = lo[t] + kWin; }
    if (T > 0) hi[T - 1] = std::min(hi[T - 1], (double)np);
    for (int t = 0; t < T; t++) {
      double e = (c[(size_t)hi[t]] - c[(size_t)lo[t]]) / (double)kWin;
      rms[t] = sqrt(std::max(e, 0.0));
    }
  }
  const double ref = percentile_of(rms, 95.0);
  const double thr = std::max(1e-4, ref * pow(10.0, kSilenceDb / 20.0));
  std::vector<double> silent(T, 0.0), mask(T, 0.0);
  for (int t = 0; t < T; t++) silent[t] = (rms[t] < thr) ? 1.0 : 0.0;
  // np.convolve(m, [0.25,0.5,0.25], mode="same") -- zero padded outside
  for (int t = 0; t < T; t++) {
    double v = 0.0;
    if (t > 0) v += 0.25 * silent[t - 1];
    v += 0.5 * silent[t];
    if (t + 1 < T) v += 0.25 * silent[t + 1];
    mask[t] = std::min(1.0, std::max(0.0, v));
  }

  // gain in dB, clamped, then back to natural log and masked
  std::vector<double> diff((size_t)T * kNbins, 0.0);
  long clipped = 0;
  for (size_t i = 0; i < diff.size(); i++) {
    double db = kGainExponent * (prd[i] - src[i]) * (20.0 / log(10.0));
    if (fabs(db) > kGainLimitDb) clipped++;
    diff[i] = std::min(kGainLimitDb, std::max(-kGainLimitDb, db));
  }
  if (dump_diff) *dump_diff = diff;
  if (dump_mask) *dump_mask = std::vector<float>(mask.begin(), mask.end());

  if (st) {
    st->clip_frac = (double)clipped / (double)diff.size();
    st->frames = T;
    for (int t = 0; t < T; t++) if (silent[t] > 0.5) st->silent_frames++;
    // median gain over non-silent frames, on the same (pre-clamp) values the
    // Python stats report: np.median(diff_db[~silent]) over whole frames.
    std::vector<double> act;
    act.reserve(diff.size());
    for (int t = 0; t < T; t++) {
      if (silent[t] > 0.5) continue;
      const double *pr = &prd[(size_t)t * kNbins];
      const double *sr = &src[(size_t)t * kNbins];
      for (int b = 0; b < kNbins; b++)
        act.push_back(kGainExponent * (pr[b] - sr[b]) * (20.0 / log(10.0)));
    }
    st->median_db = act.empty() ? 0.0 : median_of(act);
  }

  const double ln10_20 = log(10.0) / 20.0;
  for (int t = 0; t < T; t++) {
    double w = 1.0 - mask[t];
    std::complex<double> *X = &s.X[(size_t)t * kNbins];
    const double *d = &diff[(size_t)t * kNbins];
    for (int k = 0; k < kNbins; k++) X[k] *= exp(d[k] * ln10_20 * w);
  }
  istft(s, win, fft, n, y);
  (void)clipped;
  (void)m;
}

// ----------------------------------------------------------------------------
// dumping helpers ------------------------------------------------------------
// ----------------------------------------------------------------------------
// create the dump directory when missing (fopen does not); harmless if it exists
static void ensure_dir(const std::string &dir) {
#if defined(_WIN32)
  _mkdir(dir.c_str());
#else
  mkdir(dir.c_str(), 0777);
#endif
}

static void dump_f32(const std::string &dir, const char *name, const float *data, size_t n) {
  if (dir.empty() || n == 0) return;
  ensure_dir(dir);
  std::string path = dir + "/" + name;
  FILE *f = fopen(path.c_str(), "wb");
  if (!f) die("cannot write %s", path.c_str());
  fwrite(data, sizeof(float), n, f);
  fclose(f);
}

// The pipeline runs in double, the Python oracle saves float32, so narrow on the
// way out.  (Writing a double array with sizeof(float) silently produces the
// first half of the bytes reinterpreted -- it looks like NaN snow.)
static void dump_f32(const std::string &dir, const char *name, const double *data, size_t n) {
  if (dir.empty() || n == 0) return;
  std::vector<float> tmp(data, data + n);
  dump_f32(dir, name, tmp.data(), tmp.size());
}

// ----------------------------------------------------------------------------
// main ----------------------------------------------------------------------
// ----------------------------------------------------------------------------
#include "stream_mode.inc"

int main(int argc, char **argv) {
#ifdef _WIN32
  // The desk-side build reads raw PCM from a Windows console stream: without
  // this, Ctrl-Z (0x1A) in the payload is taken as EOF and the input is cut short.
  _setmode(_fileno(stdin), _O_BINARY);
  _setmode(_fileno(stdout), _O_BINARY);
#endif
  if (argc < 4) {
    fprintf(stderr,
            "usage: %s seconds pcm16|native_s24 prefill_ms [out_gain_q16 [in_gain_q16]]\n"
            "          [--nopitch] [--in-f32-16k] [--out-f32-16k] [--dump DIR] [--quiet]\n"
            "       %s --model path/to/student_v5.blob <positional args...>\n",
            argv[0], argv[0]);
    return 1;
  }
  const double seconds = atof(argv[1]);
  const std::string fmt = argv[2];
  const int prefill_ms = atoi(argv[3]);
  // Defaults follow the v23 scheduler: 39322/65536 = 0.6 output gain (the model
  // lifts the envelope by ~3 dB on a 32 kHz-sourced input, so unity would clip),
  // and 1.0 input gain.  Pass 65536 65536 for unity on both.
  double out_gain = 39322.0 / 65536.0, in_gain = 1.0;
  std::string model_path, dump_dir, xb_path;
  bool nopitch = false, in_f32 = false, out_f32 = false, quiet = false;
  int ap_stride = 10;            // D4C every Nth frame (1 = exact reference, 10 = measured)
  int ct_stride = 1;             // CheapTrick every Nth frame + interpolation
  // StoneMask stride 2 is the default: measured as free (identity -0.0026, CER and
  // UTMOS unchanged, waveform corr ~1) and it saves 87 ms of the 4 s budget.
  int sm_stride = 2;             // StoneMask every Nth frame + interpolation
  std::string ct_mode = "off";    // off | stretch | stft : how to get the shifted envelope
  int n_threads = 2;             // 2 = use both A9 cores (MLP halves + overlapped 2nd pass)
  int den_stride = 0;            // 0 = full 2nd WORLD pass (hidden behind the MLP); N>=1 = inherit f0
  int stream_ms = 0;             // >0 = live streaming mode with this block size
  int fade_ms = 20;              // crossfade across stream block seams
  double pitch_axis_ratio = 1.4; // measured formant/envelope shift of the pitch stage
  bool mlp_int8 = false;   // int8 weights (see mlp_int8.inc)

  int pos = 0;
  for (int i = 4; i < argc; i++) {
    std::string a = argv[i];
    if (a == "--nopitch") { nopitch = true; continue; }
    if (a == "--in-f32-16k") { in_f32 = true; continue; }
    if (a == "--out-f32-16k") { out_f32 = true; continue; }
    if (a == "--xB-f32") { if (i + 1 >= argc) die("--xB-f32 needs a path"); xb_path = argv[++i]; continue; }
    if (a == "--ap-stride") { if (i + 1 >= argc) die("--ap-stride needs a number"); ap_stride = atoi(argv[++i]); continue; }
    if (a == "--ct-stride") { if (i + 1 >= argc) die("--ct-stride needs a number"); ct_stride = atoi(argv[++i]); continue; }
    if (a == "--sm-stride") { if (i + 1 >= argc) die("--sm-stride needs a number"); sm_stride = atoi(argv[++i]); continue; }
    if (a == "--ct-once") { ct_mode = "stretch"; continue; }
    if (a == "--ct-stft") { ct_mode = "stft"; continue; }
    if (a == "--threads") { if (i + 1 >= argc) die("--threads needs a number"); n_threads = atoi(argv[++i]); continue; }
    if (a == "--den-stride") { if (i + 1 >= argc) die("--den-stride needs a number"); den_stride = atoi(argv[++i]); continue; }
    if (a == "--stream") { if (i + 1 >= argc) die("--stream needs a block size in ms"); stream_ms = atoi(argv[++i]); continue; }
    if (a == "--fade-ms") { if (i + 1 >= argc) die("--fade-ms needs a number"); fade_ms = atoi(argv[++i]); continue; }
    if (a == "--mlp-int8") { mlp_int8 = true; continue; }
    if (a == "--pitch-axis-ratio") { if (i + 1 >= argc) die("--pitch-axis-ratio needs a number"); pitch_axis_ratio = atof(argv[++i]); continue; }
    // One flag for the measured demo configuration (see board_c_20261025_squeeze.md):
    // CheapTrick stride 2 + StoneMask stride 2 + int8 weights.  The model input is
    // unchanged (same 513-bin envelope / f0 / aperiodicity), only smoother in time.
    if (a == "--mlp-dbg") { if (i + 1 >= argc) die("--mlp-dbg needs N"); g_mlp_dbg = atoi(argv[++i]); continue; }
    if (a == "--preset") {
      if (i + 1 >= argc) die("--preset needs a name (live)");
      const std::string p = argv[++i];
      if (p == "live") { ct_stride = 2; sm_stride = 2; mlp_int8 = true; }
      else if (p == "safe") { sm_stride = 2; }
      else if (p == "off") { ct_stride = 1; sm_stride = 1; mlp_int8 = false; }
      else die("unknown preset %s (live|safe|off)", p.c_str());
      continue;
    }
    if (a == "--quiet") { quiet = true; continue; }
    if (a == "--model") { if (i + 1 >= argc) die("--model needs a path"); model_path = argv[++i]; continue; }
    if (a == "--dump") { if (i + 1 >= argc) die("--dump needs a dir"); dump_dir = argv[++i]; continue; }
    if (!a.empty() && a[0] == '-') die("unknown option %s", a.c_str());
    if (pos == 0) out_gain = atof(argv[i]) / 65536.0;
    else if (pos == 1) in_gain = atof(argv[i]) / 65536.0;
    else { /* v23 transport selector (normal|fifo|fifo_io): accepted, ignored */ }
    pos++;
  }
  if (model_path.empty()) {
    const char *env = getenv("VC_MODEL");
    model_path = env ? env : "student_v5.blob";
  }
  const bool native_s24 = (fmt == "native_s24");
  if (fmt != "native_s24" && fmt != "pcm16") die("format must be pcm16 or native_s24");

  const double t_start = now_ms();
  Model model = load_model(model_path.c_str());
  // Output-order contract.  48 = student_v5/T4 blob, 64 = O64 blob; both are
  // read from the header, so the only hard requirement is that the residual and
  // source cepstra have the same order and that the MLP kernel, which emits
  // kMlpJB (4) neurons per pass, can tile the output layer exactly.
  if (model.out_dim != model.nceps_out)
    die("blob out_dim %d != nceps_out %d", model.out_dim, model.nceps_out);
  if (model.out_dim % kMlpJB != 0)
    die("blob out_dim %d is not a multiple of kMlpJB=%d", model.out_dim, kMlpJB);
  build_synth_T(model);
  if (mlp_int8) { build_int8(model); g_mlp_int8 = true; }

  if (stream_ms > 0) {
    return run_stream(model, seconds, native_s24, out_f32, nopitch, ap_stride,
                      out_gain, in_gain, stream_ms, fade_ms, n_threads, quiet,
                      ct_stride, sm_stride);
  }

  // ---------------- input
  const int bytes_per_sample = in_f32 ? 4 : (native_s24 ? 4 : 2);
  int n_in;
  if (in_f32) n_in = (int)llround(seconds * kSr);
  else n_in = (int)(llround(seconds * kSrIn) * kChannels);
  std::vector<uint8_t> raw((size_t)n_in * bytes_per_sample);
  size_t got = fread(raw.data(), 1, raw.size(), stdin);
  if (got != raw.size())
    die("short input: wanted %zu bytes (%.3f s), got %zu", raw.size(), seconds, got);

  const double t_in = now_ms();

  // ---------------- 1/2: left channel -> 16 kHz mono double
  std::vector<double> x16;
  if (in_f32) {
    const float *p = (const float *)raw.data();
    x16.assign(p, p + n_in);
  } else {
    std::vector<double> x32((size_t)n_in / kChannels);
    for (int i = 0; i < n_in / kChannels; i++) {
      double v;
      if (native_s24) {
        const uint8_t *b = &raw[(size_t)i * kChannels * 4];
        int32_t s = (int32_t)((uint32_t)b[0] | ((uint32_t)b[1] << 8) |
                             ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24));
        // 24 valid bits, left justified in the 32-bit container
        v = (double)(s >> 8) / 8388608.0;
      } else {
        const uint8_t *b = &raw[(size_t)i * kChannels * 2];
        int16_t s = (int16_t)((uint16_t)b[0] | ((uint16_t)b[1] << 8));
        v = (double)s / 32768.0;
      }
      x32[i] = v * in_gain;
    }
    resample_fir(x32, kSrIn, kSr, x16);
  }
  const int n = (int)x16.size();
  if (n < kNfft) die("input too short (%d samples)", n);

  Fft fft;
  fft.init(kNfft);

  // ---------------- 3: SoundTouch pitch shift
  const double t_res = now_ms();
  std::vector<double> xB;
  if (!xb_path.empty()) {
    // Test hook, mirroring ref_port.py --xB-f32: take the pitch-shifted signal
    // from a file so the C build and the Python oracle can be fed byte-identical
    // inputs.  This is what makes the board comparison measure code differences
    // instead of float32 rounding of the dumped intermediate.
    std::vector<uint8_t> raw_xb = read_file(xb_path.c_str());
    const size_t cnt = raw_xb.size() / 4;
    const float *pf = (const float *)raw_xb.data();
    xB.assign(pf, pf + cnt);
    if ((int)xB.size() < n) xB.resize(n, 0.0);
    else if ((int)xB.size() > n) xB.resize(n);
  } else if (nopitch) {
    xB = x16;
  } else {
    soundtouch::SoundTouch st;
    st.setSampleRate(kSr);
    st.setChannels(1);
    st.setPitch((float)model.pitch_ratio);
    st.setSetting(SETTING_SEQUENCE_MS, kSeqMs);
    st.setSetting(SETTING_SEEKWINDOW_MS, kSeekMs);
    st.setSetting(SETTING_OVERLAP_MS, kOverlapMs);
    st.setSetting(SETTING_USE_AA_FILTER, 1);
    std::vector<float> buf(x16.begin(), x16.end());
    st.putSamples(buf.data(), (uint)buf.size());
    st.flush();
    std::vector<float> out;
    std::vector<float> tmp(4096);
    uint avail;
    while ((avail = st.numSamples()) > 0) {
      uint want = avail < (uint)tmp.size() ? avail : (uint)tmp.size();
      uint rec = st.receiveSamples(tmp.data(), want);
      if (rec == 0) break;
      out.insert(out.end(), tmp.begin(), tmp.begin() + rec);
    }
    xB.assign(out.begin(), out.end());
    // Python pads/truncates the shifted signal to the source length
    if ((int)xB.size() < n) xB.resize(n, 0.0);
    else if ((int)xB.size() > n) xB.resize(n);
  }
  const double t_pitch = now_ms();

  // ---------------- 4/5/6: WORLD analysis and envelope prediction
  WorldAna ana;
  world_analyse(x16, true, ap_stride, ct_stride, sm_stride, ana);
  const double t_world1 = now_ms();

  // The denominator envelope is needed only after the MLP, so hand it to the MLP
  // worker thread (see SideJob) instead of running it on the critical path.
  std::vector<double> logsp_derived;
  const std::vector<double> *logsp_den = &ana.logsp;
  WorldAna ana_b;
  SideJob side;
  SideJob *side_ptr = nullptr;
  if (!nopitch && ct_mode == "off") {
    side = SideJob{&xB, &ana.f0, pitch_axis_ratio, den_stride, &ana_b};
    side_ptr = &side;
  }

  Pred pred;
  predict(model, ana, pred, n_threads, side_ptr);
  const double t_pred = now_ms();

  // denominator envelope: either a second WORLD pass on the pitch-shifted signal
  // (exact) or the source envelope with its frequency axis stretched (cheap).
  // Run on the worker thread above when threading is available.
  if (!nopitch) {
    if (ct_mode == "stretch") {
      derive_shifted_logsp(ana.logsp, ana.n_frames, pitch_axis_ratio, logsp_derived);
      logsp_den = &logsp_derived;
    } else if (ct_mode != "stft") {
      if (!(side_ptr && pred.threaded)) {
        // serial fallback: the side job did not run yet
        if (den_stride > 0) {
          analyse_shifted_env(xB, ana.f0, pitch_axis_ratio, den_stride, ana_b);
        } else {
          world_analyse(xB, false, 1, 1, 1, ana_b);
        }
      }
      logsp_den = &ana_b.logsp;
    }
  }
  const double t_ana2 = now_ms();

  // ---------------- 7: envelope transplant, source phase kept
  std::vector<double> y16;
  std::vector<double> dump_diff;
  std::vector<float> dump_mask;
  TransStats tstats;
  transplant(model, xB, pred.logsp_pred, *logsp_den, fft, y16,
             dump_dir.empty() ? nullptr : &dump_diff,
             dump_dir.empty() ? nullptr : &dump_mask,
             &tstats, ct_mode == "stft");
  const double t_syn = now_ms();

  // ---------------- 8: back to 32 kHz and pack
  std::vector<uint8_t> outbuf;
  long out_clipped = 0;
  if (out_f32) {
    std::vector<float> yf(y16.begin(), y16.end());
    outbuf.resize(yf.size() * 4);
    memcpy(outbuf.data(), yf.data(), outbuf.size());
  } else {
    std::vector<double> y32;
    resample_fir(y16, kSr, kSrIn, y32);
    const size_t ns = y32.size();
    outbuf.resize(ns * kChannels * bytes_per_sample);
    long clipped = 0;
    for (size_t i = 0; i < ns; i++) {
      double v = y32[i] * out_gain;
      if (v > 1.0 || v < -1.0) clipped++;
      v = std::min(1.0, std::max(-1.0, v));
      if (native_s24) {
        int32_t q = (int32_t)llround(v * 8388608.0);
        q = std::min(8388607, std::max(-8388608, q));
        uint32_t u = (uint32_t)q << 8;              // 24 valid bits, left justified
        uint8_t *b = &outbuf[(size_t)i * kChannels * 4];
        for (int c = 0; c < kChannels; c++) {
          b[c * 4 + 0] = (uint8_t)(u & 0xFF);
          b[c * 4 + 1] = (uint8_t)((u >> 8) & 0xFF);
          b[c * 4 + 2] = (uint8_t)((u >> 16) & 0xFF);
          b[c * 4 + 3] = (uint8_t)((u >> 24) & 0xFF);
        }
      } else {
        int16_t q = (int16_t)llround(v * 32768.0);
        q = (int16_t)std::min(32767, std::max(-32768, (int)q));
        uint8_t *b = &outbuf[(size_t)i * kChannels * 2];
        for (int c = 0; c < kChannels; c++) {
          uint16_t u = (uint16_t)q;
          b[c * 2 + 0] = (uint8_t)(u & 0xFF);
          b[c * 2 + 1] = (uint8_t)((u >> 8) & 0xFF);
        }
      }
    }
    out_clipped = clipped;
  }
  const double t_out = now_ms();

  if (fwrite(outbuf.data(), 1, outbuf.size(), stdout) != outbuf.size())
    die("short write on stdout");
  fflush(stdout);

  // ---------------- dumps for the C/Python comparison
  if (!dump_dir.empty()) {
    dump_f32(dump_dir, "x16.f32", x16.data(), x16.size());
    dump_f32(dump_dir, "xb16.f32", xB.data(), xB.size());
    dump_f32(dump_dir, "f0.f32", ana.f0.data(), ana.f0.size());
    dump_f32(dump_dir, "logsp.f32", ana.logsp.data(), ana.logsp.size());
    dump_f32(dump_dir, "ap.f32", ana.ap.data(), ana.ap.size());
    dump_f32(dump_dir, "feats.f32", pred.feats.data(), pred.feats.size());
    dump_f32(dump_dir, "stats.f32", pred.stats.data(), pred.stats.size());
    dump_f32(dump_dir, "xn.f32", pred.Xn.data(), pred.Xn.size());
    dump_f32(dump_dir, "res.f32", pred.res.data(), pred.res.size());
    dump_f32(dump_dir, "logsp_pred.f32", pred.logsp_pred.data(), pred.logsp_pred.size());
    if (!logsp_den->empty())
      dump_f32(dump_dir, "logsp_den.f32", logsp_den->data(), logsp_den->size());
    if (!dump_diff.empty())
      dump_f32(dump_dir, "diff_db.f32", dump_diff.data(), dump_diff.size());
    if (!dump_mask.empty())
      dump_f32(dump_dir, "mask.f32", dump_mask.data(), dump_mask.size());
    dump_f32(dump_dir, "y16.f32", y16.data(), y16.size());
  }

  const double total_ms = now_ms() - t_start;
  const double audio_ms = 1000.0 * (double)n / (double)kSr;
  if (!quiet) {
    double peak = 0.0, rms = 0.0;
    for (double v : y16) { peak = std::max(peak, fabs(v)); rms += v * v; }
    rms = sqrt(rms / std::max<size_t>(1, y16.size()));
    fprintf(stderr,
            "{\"ok\":true,\"seconds\":%.4f,\"samples_in\":%d,\"samples_out\":%d,"
            "\"frames_world\":%d,\"frames_stft\":%d,\"voiced_frames\":%d,"
            "\"median_f0_hz\":%.3f,\"pitch_ratio\":%.4f,\"pitch_impl\":\"%s\","
            "\"prefill_ms\":%d,\"format\":\"%s\",\"model_bytes\":%zu,"
            "\"peak_out\":%.6f,\"rms_out\":%.6f,\"clipped_samples\":%ld,"
            "\"median_gain_db\":%.3f,\"gain_clipped_frac\":%.5f,"
            "\"silent_frames\":%d,"
            "\"world_ms\":%.2f,\"mlp_ms\":%.2f,\"feat_ms\":%.2f,\"mlp_only_ms\":%.2f,\"world_b_ms\":%.2f,"
            "\"dio_ms\":%.2f,\"stonemask_ms\":%.2f,\"cheaptrick_ms\":%.2f,\"d4c_ms\":%.2f,"
            "\"ap_stride\":%d,\"ct_stride\":%d,\"sm_stride\":%d,\"ct_mode\":\"%s\",\"pitch_axis_ratio\":%.4f,\"den_stride\":%d,"
            "\"threads\":%d,\"threaded\":%s,"
            "\"analysis_ms\":%.2f,\"pitch_ms\":%.2f,"
            "\"stft_env_ms\":%.2f,\"output_ms\":%.2f,\"total_ms\":%.2f,"
            "\"analysis_rtf\":%.4f,\"render_rtf_including_output_wait\":%.4f,"
            "\"rtf\":%.4f}\n",
            1000.0 * n / kSr / 1000.0, (int)x16.size(), (int)y16.size(),
            ana.n_frames, pred.n_frames, pred.voiced, pred.median_f0,
            nopitch ? 1.0 : (double)model.pitch_ratio, nopitch ? "none" : "soundtouch_wsola",
            prefill_ms, fmt.c_str(), g_blob.size(),
            peak, rms, out_clipped,
            tstats.median_db, tstats.clip_frac, tstats.silent_frames,
            t_world1 - t_pitch, t_pred - t_world1, g_t_feat, g_t_mlp, t_ana2 - t_pred,
            g_t_dio, g_t_sm, g_t_ct, g_t_d4c, ap_stride, ct_stride, sm_stride, ct_mode.c_str(), pitch_axis_ratio, den_stride, n_threads, pred.threaded ? "true" : "false",
            t_pred - t_res, t_pitch - t_res,
            t_syn - t_ana2, t_out - t_syn, total_ms,
            (t_pred - t_res) / audio_ms, (t_out - t_ana2) / audio_ms,
            total_ms / audio_ms);
  }
  return 0;
}
