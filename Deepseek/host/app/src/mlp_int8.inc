// int8 inference for the v5 envelope MLP.
//
// Weights  : int8, per-output-neuron scale (max|row| / 127), quantised once at load.
// Activations: int16, per-tensor scale recomputed per layer per frame block.
// Accumulate : int32, via NEON vmlal.s16 (4 int16 MACs per instruction), so eight
//              frames cost 1 vdup + 2 vmlal per weight.
//
// Motivation on this hardware: the fp32 weights are 4.57 MB and a block of eight
// frames streams all of them, i.e. ~57 MB/s from DDR while the model runs.  int8
// makes that 14 MB/s.  The broadcast+widening MAC has roughly the same instruction
// count as the fp32 kernel, so whether this actually helps answers the question
// "is the MLP traffic-bound or issue-bound?" -- see the report.
//
// Included by vc_stream.cpp before mlp_forward_batch so the dispatcher can call it.
static bool g_mlp_int8 = false;
// diagnostics for the fp32 kernel: 0 normal, 1 no-GELU, 2 skip the K loop, 3 half K
static int g_mlp_dbg = 0;

static void mlp_forward_batch_int8(const Model &m, const float *X, int n_frames, float *Y) {
  const int NB = kMlpNB, JB = kMlpJB;
  std::vector<float> in0((size_t)m.in_dim * NB);
  std::vector<float> act((size_t)m.hidden * NB);      // float activations (transposed)
  std::vector<int16_t> qa((size_t)m.hidden * NB);     // quantised activations
  std::vector<int16_t> qin((size_t)m.in_dim * NB);
  int32_t acci[JB][NB];
  float sa = 1.0f;                                    // current activation scale

  for (int f0 = 0; f0 < n_frames; f0 += NB) {
    int idx[NB];
    for (int t = 0; t < NB; t++) idx[t] = std::min(f0 + t, n_frames - 1);
    float amax = 0.0f;
    for (int t = 0; t < NB; t++) {
      const float *src = X + (size_t)idx[t] * m.in_dim;
      for (int i = 0; i < m.in_dim; i++) {
        const float v = src[i];
        in0[(size_t)i * NB + t] = v;
        amax = std::max(amax, std::fabs(v));
      }
    }
    sa = (amax > 0.0f) ? amax / 32767.0f : 1.0f;
    for (size_t k = 0; k < in0.size(); k++) {
      float q = std::round(in0[k] / sa);
      q = std::min(32767.0f, std::max(-32767.0f, q));
      qin[k] = (int16_t)q;
    }

    const int16_t *aq = qin.data();
    int in_dim = m.in_dim;
    for (int l = 0; l < m.layers; l++) {
      const int in = in_dim;
      const Model::QLayer &Q = m.qW[l];
      const float *Bb = m.B[l];
      float lmax = 0.0f;
      for (int jb = 0; jb < m.hidden; jb += JB) {
        const int8_t *w0 = &Q.w[(size_t)(jb + 0) * in];
        const int8_t *w1 = &Q.w[(size_t)(jb + 1) * in];
        const int8_t *w2 = &Q.w[(size_t)(jb + 2) * in];
        const int8_t *w3 = &Q.w[(size_t)(jb + 3) * in];
#if defined(__ARM_NEON)
        int32x4_t c00 = vdupq_n_s32(0), c01 = vdupq_n_s32(0);
        int32x4_t c10 = vdupq_n_s32(0), c11 = vdupq_n_s32(0);
        int32x4_t c20 = vdupq_n_s32(0), c21 = vdupq_n_s32(0);
        int32x4_t c30 = vdupq_n_s32(0), c31 = vdupq_n_s32(0);
        for (int i = 0; i < in; i++) {
          const int16x8_t av = vld1q_s16(aq + (size_t)i * NB);
          const int16x4_t al = vget_low_s16(av), ah = vget_high_s16(av);
          const int16x8_t v0 = vdupq_n_s16((int16_t)w0[i]);
          const int16x8_t v1 = vdupq_n_s16((int16_t)w1[i]);
          const int16x8_t v2 = vdupq_n_s16((int16_t)w2[i]);
          const int16x8_t v3 = vdupq_n_s16((int16_t)w3[i]);
          c00 = vmlal_s16(c00, vget_low_s16(v0), al);
          c01 = vmlal_s16(c01, vget_high_s16(v0), ah);
          c10 = vmlal_s16(c10, vget_low_s16(v1), al);
          c11 = vmlal_s16(c11, vget_high_s16(v1), ah);
          c20 = vmlal_s16(c20, vget_low_s16(v2), al);
          c21 = vmlal_s16(c21, vget_high_s16(v2), ah);
          c30 = vmlal_s16(c30, vget_low_s16(v3), al);
          c31 = vmlal_s16(c31, vget_high_s16(v3), ah);
        }
        vst1q_s32(&acci[0][0], c00); vst1q_s32(&acci[0][4], c01);
        vst1q_s32(&acci[1][0], c10); vst1q_s32(&acci[1][4], c11);
        vst1q_s32(&acci[2][0], c20); vst1q_s32(&acci[2][4], c21);
        vst1q_s32(&acci[3][0], c30); vst1q_s32(&acci[3][4], c31);
#else
        for (int j = 0; j < JB; j++)
          for (int t = 0; t < NB; t++) acci[j][t] = 0;
        for (int i = 0; i < in; i++) {
          const int16_t *ap = aq + (size_t)i * NB;
          const int q0 = w0[i], q1 = w1[i], q2 = w2[i], q3 = w3[i];
          for (int t = 0; t < NB; t++) {
            const int av = ap[t];
            acci[0][t] += q0 * av; acci[1][t] += q1 * av;
            acci[2][t] += q2 * av; acci[3][t] += q3 * av;
          }
        }
#endif
        for (int j = 0; j < JB; j++)
          for (int t = 0; t < NB; t++) {
            const float v = (float)acci[j][t] * (Q.scale[jb + j] * sa) + Bb[jb + j];
            const float g = gelu_exact(v);
            act[(size_t)(jb + j) * NB + t] = g;
            lmax = std::max(lmax, std::fabs(g));
          }
      }
      // requantise this layer's output (per-tensor scale) for the next layer
      sa = (lmax > 0.0f) ? lmax / 32767.0f : 1.0f;
      for (int j = 0; j < m.hidden; j++)
        for (int t = 0; t < NB; t++) {
          float q = std::round(act[(size_t)j * NB + t] / sa);
          q = std::min(32767.0f, std::max(-32767.0f, q));
          qa[(size_t)j * NB + t] = (int16_t)q;
        }
      aq = qa.data();
      in_dim = m.hidden;
    }

    // output layer: same integer kernel, no GELU, no requantisation
    {
      const Model::QLayer &Q = m.qWout;
      for (int jb = 0; jb < m.out_dim; jb += JB) {
        const int8_t *w0 = &Q.w[(size_t)(jb + 0) * m.hidden];
        const int8_t *w1 = &Q.w[(size_t)(jb + 1) * m.hidden];
        const int8_t *w2 = &Q.w[(size_t)(jb + 2) * m.hidden];
        const int8_t *w3 = &Q.w[(size_t)(jb + 3) * m.hidden];
#if defined(__ARM_NEON)
        int32x4_t c00 = vdupq_n_s32(0), c01 = vdupq_n_s32(0);
        int32x4_t c10 = vdupq_n_s32(0), c11 = vdupq_n_s32(0);
        int32x4_t c20 = vdupq_n_s32(0), c21 = vdupq_n_s32(0);
        int32x4_t c30 = vdupq_n_s32(0), c31 = vdupq_n_s32(0);
        for (int i = 0; i < m.hidden; i++) {
          const int16x8_t av = vld1q_s16(aq + (size_t)i * NB);
          const int16x4_t al = vget_low_s16(av), ah = vget_high_s16(av);
          const int16x8_t v0 = vdupq_n_s16((int16_t)w0[i]);
          const int16x8_t v1 = vdupq_n_s16((int16_t)w1[i]);
          const int16x8_t v2 = vdupq_n_s16((int16_t)w2[i]);
          const int16x8_t v3 = vdupq_n_s16((int16_t)w3[i]);
          c00 = vmlal_s16(c00, vget_low_s16(v0), al);
          c01 = vmlal_s16(c01, vget_high_s16(v0), ah);
          c10 = vmlal_s16(c10, vget_low_s16(v1), al);
          c11 = vmlal_s16(c11, vget_high_s16(v1), ah);
          c20 = vmlal_s16(c20, vget_low_s16(v2), al);
          c21 = vmlal_s16(c21, vget_high_s16(v2), ah);
          c30 = vmlal_s16(c30, vget_low_s16(v3), al);
          c31 = vmlal_s16(c31, vget_high_s16(v3), ah);
        }
        vst1q_s32(&acci[0][0], c00); vst1q_s32(&acci[0][4], c01);
        vst1q_s32(&acci[1][0], c10); vst1q_s32(&acci[1][4], c11);
        vst1q_s32(&acci[2][0], c20); vst1q_s32(&acci[2][4], c21);
        vst1q_s32(&acci[3][0], c30); vst1q_s32(&acci[3][4], c31);
#else
        for (int j = 0; j < JB; j++)
          for (int t = 0; t < NB; t++) acci[j][t] = 0;
        for (int i = 0; i < m.hidden; i++) {
          const int16_t *ap = aq + (size_t)i * NB;
          const int q0 = w0[i], q1 = w1[i], q2 = w2[i], q3 = w3[i];
          for (int t = 0; t < NB; t++) {
            const int av = ap[t];
            acci[0][t] += q0 * av; acci[1][t] += q1 * av;
            acci[2][t] += q2 * av; acci[3][t] += q3 * av;
          }
        }
#endif
        for (int j = 0; j < JB; j++) {
          const int fj = jb + j;
          for (int t = 0; t < NB; t++) {
            const int f = f0 + t;
            if (f < n_frames)
              Y[(size_t)f * m.out_dim + fj] =
                  (float)acci[j][t] * (Q.scale[fj] * sa) + m.Bout[fj];
          }
        }
      }
    }
  }
}
