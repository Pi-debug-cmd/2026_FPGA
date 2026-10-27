// ----------------------------------------------------------------------------
// streaming mode -------------------------------------------------------------
// ----------------------------------------------------------------------------
// The batch path needs the whole utterance because WORLD is non-causal and the
// model's conditioning statistics are utterance-level.  For the live demo
// (arecord | vc_stream | aplay) the tool has to emit audio while it reads, so
// this mode slices the input into blocks of `block_ms`, runs the whole chain on
// each block, and crossfades `fade_ms` across the seams.
//
// Consequences, all measurable (see board_c_20261025.md):
//   * latency is block_ms + processing time (~2x block_ms at RTF 1.0);
//   * the utterance statistics are estimated per block, so the timbre adaptation
//     granularity is coarser than the whole-utterance reference;
//   * SoundTouch is flushed per block, so WSOLA restarts every block; the fade
//     covers the seam.
// The resamplers carry their filter history across blocks so the 32k/16k
// conversions stay continuous.
struct StreamState {
  std::vector<double> hist32;    // tail of the 32 kHz input for the decimator
  std::vector<double> prev16;    // unused
  std::vector<double> pending;   // held-back tail of the previous block (32 kHz samples)
  std::vector<float> stats_ema;  // running utterance statistics (see predict)
  long long blocks = 0;
  double proc_ms = 0.0;
};

// decode one block of S24_LE stereo (4-byte container, 24 bits right justified)
static void decode_block(const std::vector<uint8_t> &raw, int n_frames, bool native_s24,
                         double in_gain, std::vector<double> &x32) {
  x32.assign((size_t)n_frames, 0.0);
  for (int i = 0; i < n_frames; i++) {
    double v;
    if (native_s24) {
      const uint8_t *b = &raw[(size_t)i * kChannels * 4];
      int32_t s = (int32_t)((uint32_t)b[0] | ((uint32_t)b[1] << 8) |
                           ((uint32_t)b[2] << 16) | ((uint32_t)b[3] << 24));
      v = (double)(static_cast<int32_t>((static_cast<uint32_t>(s) & 0xffffffu) ^ 0x800000u) - 0x800000) / 8388608.0;
    } else {
      const uint8_t *b = &raw[(size_t)i * kChannels * 2];
      int16_t s = (int16_t)((uint16_t)b[0] | ((uint16_t)b[1] << 8));
      v = (double)s / 32768.0;
    }
    x32[i] = v * in_gain;
  }
}

static void encode_block(const std::vector<double> &y32, double out_gain, bool native_s24,
                         std::vector<uint8_t> &out, long *clipped) {
  const size_t ns = y32.size();
  out.resize(ns * kChannels * (native_s24 ? 4 : 2));
  for (size_t i = 0; i < ns; i++) {
    double v = y32[i] * out_gain;
    if (v > 1.0 || v < -1.0) (*clipped)++;
    v = std::min(1.0, std::max(-1.0, v));
    if (native_s24) {
      int32_t q = (int32_t)llround(v * 8388608.0);
      q = std::min(8388607, std::max(-8388608, q));
      uint32_t u = (uint32_t)q;
      uint8_t *b = &out[i * kChannels * 4];
      for (int c = 0; c < kChannels; c++) {
        b[c * 4 + 0] = (uint8_t)(u & 0xFF);
        b[c * 4 + 1] = (uint8_t)((u >> 8) & 0xFF);
        b[c * 4 + 2] = (uint8_t)((u >> 16) & 0xFF);
        b[c * 4 + 3] = (uint8_t)((u >> 24) & 0xFF);
      }
    } else {
      int16_t q = (int16_t)llround(v * 32768.0);
      q = (int16_t)std::min(32767, std::max(-32768, (int)q));
      uint16_t u = (uint16_t)q;
      uint8_t *b = &out[i * kChannels * 2];
      for (int c = 0; c < kChannels; c++) {
        b[c * 2 + 0] = (uint8_t)(u & 0xFF);
        b[c * 2 + 1] = (uint8_t)((u >> 8) & 0xFF);
      }
    }
  }
}

// Whole chain on one block of 16 kHz audio.  Mirrors the batch pipeline; kept
// separate so the batch path stays untouched and verified.
static void process_block(const Model &model, const std::vector<double> &x16,
                          const std::vector<double> &xB, int ap_stride,
                          const Fft &fft, std::vector<double> &y16,
                          std::vector<float> *stats_ema, int n_threads,
                          int ct_stride, int sm_stride) {
  WorldAna ana;
  world_analyse(x16, true, ap_stride, ct_stride, sm_stride, ana);
  Pred pred;
  // Same two-core arrangement as the batch path: the second WORLD pass runs on
  // the worker thread ahead of its share of the MLP frames.
  WorldAna ana_b;
  SideJob side{&xB, &ana.f0, model.pitch_ratio, 0, &ana_b};
  predict(model, ana, pred, n_threads, &side, stats_ema);
  TransStats tstats;
  transplant(model, xB, pred.logsp_pred, ana_b.logsp, fft, y16, nullptr, nullptr,
             &tstats, false);
}

static void pitch_block(const Model &model, const std::vector<double> &x16,
                        std::vector<double> &xB) {
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
  std::vector<float> out, tmp(4096);
  uint avail;
  while ((avail = st.numSamples()) > 0) {
    uint want = avail < (uint)tmp.size() ? avail : (uint)tmp.size();
    uint rec = st.receiveSamples(tmp.data(), want);
    if (rec == 0) break;
    out.insert(out.end(), tmp.begin(), tmp.begin() + rec);
  }
  xB.assign(out.begin(), out.end());
  const size_t n = x16.size();
  if (xB.size() < n) xB.resize(n, 0.0);
  else if (xB.size() > n) xB.resize(n);
}

// returns process exit code
static int run_stream(const Model &model, double seconds, bool native_s24, bool out_f32,
                      bool nopitch, int ap_stride, double out_gain, double in_gain,
                      int block_ms, int fade_ms, int n_threads, bool quiet,
                      int ct_stride, int sm_stride) {
  const int bytes_per_sample = native_s24 ? 4 : 2;
  const int block_in32 = std::max(1, block_ms * kSrIn / 1000);      // 32 kHz frames
  const int fade = std::max(0, fade_ms * kSr / 1000);               // 16 kHz samples
  const long long total_in = (long long)llround(seconds * kSrIn);   // 32 kHz frames
  Fft fft;
  fft.init(kNfft);
  StreamState st;
  st.hist32.assign(kTaps, 0.0);
  st.pending.clear();
  long long done = 0;
  long clipped_total = 0;
  const double t_all = now_ms();
  std::vector<uint8_t> raw, outbuf;
  std::vector<double> y32;

  while (done < total_in) {
    const int want = (int)std::min<long long>(block_in32, total_in - done);
    raw.resize((size_t)want * kChannels * bytes_per_sample);
    const size_t got = fread(raw.data(), 1, raw.size(), stdin);
    const int nf = (int)(got / (kChannels * bytes_per_sample));
    if (nf <= 0) break;
    const double tb = now_ms();

    std::vector<double> x32blk;
    decode_block(raw, nf, native_s24, in_gain, x32blk);

    // 32k -> 16k with the previous block's tail carried in front, then drop the
    // samples that belong to the carried part (group delay is 31 output samples)
    std::vector<double> ext(st.hist32);
    ext.insert(ext.end(), x32blk.begin(), x32blk.end());
    std::vector<double> x16ext;
    resample_fir(ext, kSrIn, kSr, x16ext);
    const int drop = (int)st.hist32.size() / 2;
    std::vector<double> x16(x16ext.begin() + std::min(drop, (int)x16ext.size()), x16ext.end());
    if ((int)x16.size() < kNfft) x16.resize(kNfft, 0.0);
    st.hist32.assign(x32blk.end() - std::min((size_t)kTaps, x32blk.size()), x32blk.end());

    std::vector<double> xB;
    if (nopitch) xB = x16;
    else pitch_block(model, x16, xB);

    std::vector<double> y16;
    process_block(model, x16, xB, ap_stride, fft, y16, &st.stats_ema, n_threads,
                  ct_stride, sm_stride);

    // 16k -> 32k
    std::vector<double> y32blk;
    resample_fir(y16, kSr, kSrIn, y32blk);

    // Proper seam handling: hold back the last `fade` samples of this block and
    // crossfade them with the head of the NEXT block.  The output therefore lags
    // the input by `fade_ms` (20 ms by default), and no audio is duplicated.
    std::vector<double> yq = st.pending;            // previous block's held tail
    yq.insert(yq.end(), y32blk.begin(), y32blk.end());
    const int f2 = (int)st.pending.size();          // held samples (16 kHz units)
    if (f2 > 0 && (int)y32blk.size() >= f2) {
      // yq[0..f2) is the held tail, yq[f2..) is this block; blend over 2*f2
      const int nf2 = 2 * f2;
      for (int i = 0; i < nf2; i++) {
        const double w = (double)i / (double)nf2;   // 0 -> previous, 1 -> current
        const double prev = st.pending[i / 2];
        yq[i] = prev * (1.0 - w) + yq[i] * w;
      }
    }
    // hold back the new tail
    std::vector<double> held;
    if (fade > 0 && (int)yq.size() > 2 * fade) {
      held.assign(yq.end() - 2 * fade, yq.end());
      yq.resize(yq.size() - 2 * fade);
    }
    st.pending = held;
    st.prev16.assign(1, 0.0);                       // unused, kept for state stability

    if (out_f32) {
      std::vector<float> yf(yq.begin(), yq.end());
      outbuf.resize(yf.size() * 4);
      memcpy(outbuf.data(), yf.data(), outbuf.size());
    } else {
      encode_block(yq, out_gain, native_s24, outbuf, &clipped_total);
    }
    if (fwrite(outbuf.data(), 1, outbuf.size(), stdout) != outbuf.size())
      die("short write on stdout");
    fflush(stdout);

    st.proc_ms += now_ms() - tb;
    st.blocks++;
    done += nf;
    // the held tail is flushed after the loop
    if (!quiet) {
      const double audio_ms = 1000.0 * (double)nf / kSrIn;
      fprintf(stderr,
              "{\"block\":%lld,\"frames_in\":%d,\"audio_ms\":%.1f,\"proc_ms\":%.1f,"
              "\"block_rtf\":%.3f,\"cum_rtf\":%.3f,\"done_s\":%.3f}\n",
              st.blocks, nf, audio_ms, st.proc_ms, st.proc_ms / audio_ms,
              st.proc_ms / (1000.0 * (double)done / kSrIn), (double)done / kSrIn);
    }
  }
  // flush the tail held back for crossfading
  if (!st.pending.empty()) {
    std::vector<uint8_t> tailbuf;
    if (out_f32) {
      std::vector<float> yf(st.pending.begin(), st.pending.end());
      tailbuf.resize(yf.size() * 4);
      memcpy(tailbuf.data(), yf.data(), tailbuf.size());
    } else {
      encode_block(st.pending, out_gain, native_s24, tailbuf, &clipped_total);
    }
    if (fwrite(tailbuf.data(), 1, tailbuf.size(), stdout) != tailbuf.size())
      die("short write on stdout (tail)");
    fflush(stdout);
    st.pending.clear();
  }
  const double wall = now_ms() - t_all;
  if (!quiet) {
    fprintf(stderr,
            "{\"ok\":true,\"mode\":\"stream\",\"blocks\":%lld,\"seconds\":%.4f,"
            "\"block_ms\":%d,\"fade_ms\":%d,\"threads\":%d,"
            "\"proc_ms\":%.2f,\"wall_ms\":%.2f,\"rtf\":%.4f,\"clipped_samples\":%ld}\n",
            st.blocks, (double)done / kSrIn, block_ms, fade_ms, n_threads,
            st.proc_ms, wall, st.proc_ms / (1000.0 * (double)done / kSrIn),
            clipped_total);
  }
  return 0;
}

