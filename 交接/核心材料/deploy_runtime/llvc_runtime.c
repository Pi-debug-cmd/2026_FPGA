// llvc_runtime.c - streaming LLVC inference, faithful to the PyTorch model
// (reduced: enc384/6 blocks, dec192/6 heads). Scalar correctness reference.
#include "llvc_runtime.h"
#include "gemm_backend.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

const float *fa(const llvc_t *m, uint32_t idx) {
    return m->floats + (m->hdr->float_arr_off[idx] / 4);
}
const uint8_t *mw(const llvc_t *m, uint32_t mi) {
    return m->packed + m->hdr->mat_packed_off[mi];
}
const float *ms(const llvc_t *m, uint32_t mi) {
    return m->scales + (m->hdr->mat_scale_off[mi] / 4);
}

// ---------- small ops ----------
static void layernorm(float *x, const float *g, const float *b,
                      unsigned frames, unsigned c) {
    for (unsigned t = 0; t < frames; ++t) {
        float *row = x + (size_t)t * c;
        float mu = 0;
        for (unsigned i = 0; i < c; ++i) mu += row[i];
        mu /= c;
        float var = 0;
        for (unsigned i = 0; i < c; ++i) { float d = row[i]-mu; var += d*d; }
        var /= c;
        float s = 1.0f / sqrtf(var + 1e-5f);
        for (unsigned i = 0; i < c; ++i) row[i] = g[i]*(row[i]-mu)*s + b[i];
    }
}
static void relu(float *x, unsigned frames, unsigned c) {
    for (unsigned t = 0; t < frames; ++t) {
        float *row = x + (size_t)t * c;
        for (unsigned i = 0; i < c; ++i) if (row[i] < 0) row[i] = 0;
    }
}

// depthwise conv: groups=c, k=3, dilation d, no padding. in: (2d+frames) x c
static void depthwise(const float *in, float *out, const float *w, const float *bias,
                      unsigned frames, unsigned c, unsigned d) {
    for (unsigned t = 0; t < frames; ++t) {
        const float *r0 = in + (size_t)t*c;
        const float *r1 = in + (size_t)(t+d)*c;
        const float *r2 = in + (size_t)(t+2*d)*c;
        float *o = out + (size_t)t*c;
        for (unsigned ch = 0; ch < c; ++ch)
            o[ch] = w[ch*3+0]*r0[ch] + w[ch*3+1]*r1[ch] + w[ch*3+2]*r2[ch] + bias[ch];
    }
}

// packed dense: float in (frames x in_c) -> float out (frames x out_c)
static int USE_FLOAT=0;
static void dense(llvc_t *m, unsigned mi, const float *in, float *out,
                  unsigned frames, unsigned in_c, unsigned out_c,
                  unsigned in_stride, unsigned out_stride,
                  const float *sw, const float *bias) {
    if (USE_FLOAT) {
        const uint8_t *pw = mw(m,mi);
        for (unsigned t=0;t<frames;++t){
            const float *r=in+(size_t)t*in_stride;
            float *o=out+(size_t)t*out_stride;
            for (unsigned j=0;j<out_c;++j){
                float acc=bias[j];
                for (unsigned k=0;k<in_c;++k)
                    acc+=(float)(int8_t)pw[(size_t)k*512+j]*sw[j]*r[k];
                o[j]=acc;
            }
        }
        return;
    }
    // per-activation scale from in rows
    float amax = 1e-8f;
    for (unsigned t = 0; t < frames; ++t) {
        const float *r = in + (size_t)t*in_stride;
        for (unsigned c = 0; c < in_c; ++c) { float a=fabsf(r[c]); if(a>amax)amax=a; }
    }
    float sx = amax/127.0f;
    uint8_t *xin = (uint8_t*)calloc((size_t)frames*512,1);
    int32_t *yout = (int32_t*)calloc((size_t)frames*512,sizeof(int32_t));
    for (unsigned t = 0; t < frames; ++t) {
        const float *r = in + (size_t)t*in_stride;
        uint8_t *o = xin + (size_t)t*512;
        for (unsigned c = 0; c < in_c; ++c) {
            float q = roundf(r[c]/sx);
            if(q>127)q=127; if(q<-128)q=-128;
            o[c]=(uint8_t)(int8_t)q;
        }
    }
    gemm_run_mi(mi, mw(m,mi), xin, yout, frames, in_c, out_c);
    for (unsigned t = 0; t < frames; ++t) {
        const int32_t *yr = yout + (size_t)t*512;
        float *o = out + (size_t)t*out_stride;
        for (unsigned j = 0; j < out_c; ++j)
            o[j] = (float)yr[j] * sx * sw[j] + bias[j];
    }
    free(xin); free(yout);
}
static void add_posenc(float *x, const float *table, unsigned frames, unsigned c) {
    for (unsigned i = 0; i < frames*c; ++i) x[i] += table[i];
}

// ---------- multi-head attention ----------
static void attention(llvc_t *m, unsigned qmi, unsigned kvmi, unsigned omi,
                      const float *qin, const float *kvin,
                      unsigned qf, unsigned kf,
                      const float *qbias, const float *kbias,
                      const float *vbias, const float *obias,
                      float *out,
                      float *q, float *k, float *v, float *attn) {
    const unsigned C=DEC_DIM, HD=NHEAD, D=HEAD_DIM;
    dense(m, qmi, qin, q, qf, C, C, C, C, ms(m, qmi), qbias);
    dense(m, kvmi, kvin, k, kf, C, C, C, C, ms(m, kvmi), kbias);
    dense(m, kvmi+1, kvin, v, kf, C, C, C, C, ms(m, kvmi+1), vbias);
    for (unsigned h = 0; h < HD; ++h) {
        float scores[26];
        for (unsigned i = 0; i < qf; ++i) {
            const float *qr = q + (size_t)i*C + h*D;
            for (unsigned j = 0; j < kf; ++j) {
                const float *kr = k + (size_t)j*C + h*D;
                float s = 0;
                for (unsigned d = 0; d < D; ++d) s += qr[d]*kr[d];
                scores[j] = s / sqrtf((float)D);
            }
            float mx = scores[0];
            for (unsigned j = 1; j < kf; ++j) if (scores[j] > mx) mx = scores[j];
            float sum = 0;
            for (unsigned j = 0; j < kf; ++j) { scores[j] = expf(scores[j]-mx); sum += scores[j]; }
            float *ar = attn + (size_t)i*C + h*D;
            for (unsigned d = 0; d < D; ++d) {
                float val = 0;
                for (unsigned j = 0; j < kf; ++j)
                    val += (scores[j]/sum) * v[(size_t)j*C + h*D + d];
                ar[d] = val;
            }
        }
    }
    dense(m, omi, attn, out, qf, C, C, C, C, ms(m, omi), obias);
}

// ---------- load ----------
static float *newf(size_t frames, unsigned c) {
    float *p = malloc(frames*c*sizeof(float));
    memset(p, 0, frames*c*sizeof(float));
    return p;
}
int llvc_load(llvc_t *m, const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror("open"); return 1; }
    fseek(f, 0, SEEK_END); long fsize = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *p = malloc(fsize);
    if (fread(p, 1, fsize, f) != (size_t)fsize) { perror("read"); return 1; }
    fclose(f);
    m->file = p;
    m->hdr = (model_header_t*)p;
    if (fsize < HDR_SIZE || m->hdr->magic != 0x4C4C5643 ||
        m->hdr->version != 2 || m->hdr->enc_dim != ENC_DIM ||
        m->hdr->dec_dim != DEC_DIM || m->hdr->float_off >= (uint32_t)fsize ||
        m->hdr->scale_off >= (uint32_t)fsize || m->hdr->packed_off >= (uint32_t)fsize) {
        fputs("unsupported or corrupt reduced LLVC model\n", stderr);
        free(p);
        return 1;
    }
    m->floats = (const float*)(m->file + m->hdr->float_off);
    m->scales = (const float*)(m->file + m->hdr->scale_off);
    m->packed = m->file + m->hdr->packed_off;

    m->xin = malloc(26*512);
    m->yout = malloc(26*512*sizeof(int32_t));
    m->e = newf(13,ENC_DIM); m->base = newf(13,ENC_DIM); m->dccw = newf(269,ENC_DIM);
    m->dccout = newf(13,ENC_DIM); m->pwout = newf(13,ENC_DIM); m->l = newf(13,ENC_DIM);
    m->mem = newf(26,DEC_DIM); m->tgt = newf(26,DEC_DIM);
    m->q = newf(26,DEC_DIM); m->cq = newf(26,DEC_DIM);
    m->kv = newf(26,DEC_DIM); m->vv = newf(26,ENC_DIM);
    m->attn = newf(13,DEC_DIM); m->decout = newf(13,DEC_DIM);
    m->mout = newf(13,ENC_DIM); m->outin = newf(17,ENC_DIM);
    m->cn_ctx = calloc(24, sizeof(float));
    m->enc_buf = calloc(204*ENC_DIM, sizeof(float));
    m->mem_ctx = calloc(13*DEC_DIM, sizeof(float));
    m->tgt_ctx = calloc(13*DEC_DIM, sizeof(float));
    m->out_buf = calloc(4*ENC_DIM, sizeof(float));
    if (gemm_setup(m)) { fputs("gemm_setup failed\n", stderr); return 1; }
    llvc_reset_state(m);
    return 0;
}

void llvc_reset_state(llvc_t *m) {
    memset(m->cn_ctx,0,24*sizeof(float));
    memset(m->enc_buf,0,204*ENC_DIM*sizeof(float));
    memset(m->mem_ctx,0,13*DEC_DIM*sizeof(float));
    memset(m->tgt_ctx,0,13*DEC_DIM*sizeof(float));
    memset(m->out_buf,0,4*ENC_DIM*sizeof(float));
}

// ---------- per-block (240 in = front32 + shifted208) ----------
static int DUMP=0, DUMP_BLOCK=-1, BLOCKNO=0;
static void dumpf(const char*name,const float*p,size_t n){
    if(!DUMP||BLOCKNO!=DUMP_BLOCK)return; char fn[128];
    snprintf(fn,sizeof(fn),"dmp_%s.bin",name);
    FILE*f=fopen(fn,"wb"); fwrite(p,sizeof(float),n,f); fclose(f); }
void llvc_process_block(llvc_t *m, const float *block240, float *out208) {
    DUMP=getenv("LLVC_DUMP")?1:0;
    USE_FLOAT=getenv("LLVC_FLOAT")?1:0;
    if(getenv("LLVC_DUMP_BLOCK"))DUMP_BLOCK=atoi(getenv("LLVC_DUMP_BLOCK"));
    BLOCKNO++;
    float cn[240];
    memcpy(cn, block240, sizeof(cn));
    dumpf("block_input",block240,240);
    for (unsigned i = 0; i < 12; ++i) {
        const float *fw = fa(m, 4*i), *fb = fa(m, 4*i+1);
        const float *gw = fa(m, 4*i+2), *gb = fa(m, 4*i+3);
        float *ctx = m->cn_ctx + 2*i;
        float cin[242];
        cin[0]=ctx[0]; cin[1]=ctx[1];
        memcpy(cin+2, cn, 240*sizeof(float));
        ctx[0]=cin[240]; ctx[1]=cin[241];
        for (unsigned t = 0; t < 240; ++t) {
            float f = fw[0]*cin[t]+fw[1]*cin[t+1]+fw[2]*cin[t+2]+fb[0];
            float g = gw[0]*cin[t]+gw[1]*cin[t+1]+gw[2]*cin[t+2]+gb[0];
            float r = tanhf(f) * (1.0f/(1.0f+expf(-g)));
            cn[t] = cin[t+2] + r;
        }
    }
    for (unsigned i = 0; i < 240; ++i) cn[i] = block240[i] + cn[i];
    dumpf("cn",cn,240);

    // in_conv 240 -> 13 x ENC_DIM
    const float *iw = fa(m, FA_IN_CONV_W);
    for (unsigned t = 0; t < 13; ++t) {
        float *o = m->e + (size_t)t*ENC_DIM;
        for (unsigned c = 0; c < ENC_DIM; ++c) {
            float s = 0;
            for (unsigned k = 0; k < 48; ++k) s += iw[c*48+k]*cn[t*16+k];
            o[c] = s > 0 ? s : 0;
        }
    }

    memcpy(m->base, m->e, 13*ENC_DIM*sizeof(float));
    dumpf("base",m->base,13*ENC_DIM);
    // DCC encoder (6 blocks)
    for (unsigned i = 0; i < N_ENC_LAYERS; ++i) {
        unsigned d = 1u<<i, bl = 2*d;
        unsigned base = FA_DCC_BASE + 7*i;
        const float *dw = fa(m,base), *db = fa(m,base+1);
        const float *ln1w = fa(m,base+2), *ln1b = fa(m,base+3);
        const float *pb = fa(m,base+4);
        const float *ln2w = fa(m,base+5), *ln2b = fa(m,base+6);
        float *din = m->dccw;
        float *cbuf = m->enc_buf + (size_t)dcc_buf_start(i)*ENC_DIM;
        memcpy(din, cbuf, bl*ENC_DIM*sizeof(float));
        memcpy(din + (size_t)bl*ENC_DIM, m->e, 13*ENC_DIM*sizeof(float));
        memcpy(cbuf, din + (size_t)13*ENC_DIM, bl*ENC_DIM*sizeof(float));
        if (i == 0) dumpf("enc0_din", din, (bl+13)*ENC_DIM);
        depthwise(din, m->dccout, dw, db, 13, ENC_DIM, d);
        if (i == 0) dumpf("enc0_dw", m->dccout, 13*ENC_DIM);
        layernorm(m->dccout, ln1w, ln1b, 13, ENC_DIM);
        relu(m->dccout, 13, ENC_DIM);
        if (i == 0) dumpf("enc0_densein", m->dccout, 13*ENC_DIM);
        dense(m, M_ENC0+i, m->dccout, m->pwout, 13, ENC_DIM, ENC_DIM,
              ENC_DIM, ENC_DIM, ms(m, M_ENC0+i), pb);
        if (i == 0) dumpf("enc0_pw", m->pwout, 13*ENC_DIM);
        layernorm(m->pwout, ln2w, ln2b, 13, ENC_DIM);
        relu(m->pwout, 13, ENC_DIM);
        for (unsigned t = 0; t < 13; ++t)
            for (unsigned c = 0; c < ENC_DIM; ++c)
                m->e[(size_t)t*ENC_DIM+c] += m->pwout[(size_t)t*ENC_DIM+c];
        if (DUMP && BLOCKNO == DUMP_BLOCK) {
            char name[24];
            snprintf(name, sizeof(name), "enc_%u", i);
            dumpf(name, m->e, 13*ENC_DIM);
        }
    }

    // label integration: l = lconst * e
    const float *lconst = fa(m, FA_LABEL);
    dumpf("e_after_enc",m->e,13*ENC_DIM);
    for (unsigned t = 0; t < 13; ++t)
        for (unsigned c = 0; c < ENC_DIM; ++c)
            m->l[(size_t)t*ENC_DIM+c] = lconst[c]*m->e[(size_t)t*ENC_DIM+c];
    dumpf("l",m->l,13*ENC_DIM);

    // proj e2d_e / e2d_l (grouped 2->1): 13 x ENC_DIM -> 13 x DEC_DIM
    const float *pew = fa(m, FA_PROJ_BASE), *peb = fa(m, FA_PROJ_BASE+1);
    const float *plw = fa(m, FA_PROJ_BASE+2), *plb = fa(m, FA_PROJ_BASE+3);
    for (unsigned t = 0; t < 13; ++t) {
        float *mr = m->mem + (size_t)t*DEC_DIM;
        float *tr = m->tgt + (size_t)t*DEC_DIM;
        const float *er = m->e + (size_t)t*ENC_DIM;
        const float *lr = m->l + (size_t)t*ENC_DIM;
        for (unsigned c = 0; c < DEC_DIM; ++c) {
            mr[c] = pew[c*2]*er[2*c]+pew[c*2+1]*er[2*c+1];
            tr[c] = plw[c*2]*lr[2*c]+plw[c*2+1]*lr[2*c+1];
        }
    }
    for (unsigned t = 0; t < 13; ++t) {
        float *mr = m->mem + (size_t)t*DEC_DIM;
        float *tr = m->tgt + (size_t)t*DEC_DIM;
        for (unsigned c = 0; c < DEC_DIM; ++c) {
            float v = mr[c]+peb[c]; mr[c] = v>0?v:0;
            v = tr[c]+plb[c]; tr[c] = v>0?v:0;
        }
    }

    // decoder: prepend contexts -> 26 frames.
    memmove(m->mem + 13*DEC_DIM, m->mem, 13*DEC_DIM*sizeof(float));
    for (unsigned t = 0; t < 13; ++t) {
        memcpy(m->mem + (size_t)t*DEC_DIM, m->mem_ctx + (size_t)t*DEC_DIM, DEC_DIM*sizeof(float));
        memcpy(m->mem_ctx + (size_t)t*DEC_DIM, m->mem + (size_t)(13+t)*DEC_DIM, DEC_DIM*sizeof(float));
    }
    memmove(m->tgt + 13*DEC_DIM, m->tgt, 13*DEC_DIM*sizeof(float));
    for (unsigned t = 0; t < 13; ++t) {
        memcpy(m->tgt + (size_t)t*DEC_DIM, m->tgt_ctx + (size_t)t*DEC_DIM, DEC_DIM*sizeof(float));
        memcpy(m->tgt_ctx + (size_t)t*DEC_DIM, m->tgt + (size_t)(13+t)*DEC_DIM, DEC_DIM*sizeof(float));
    }
    add_posenc(m->mem, fa(m, FA_POSENC_26), 26, DEC_DIM);
    add_posenc(m->tgt, fa(m, FA_POSENC_26), 26, DEC_DIM);
    dumpf("mem26",m->mem,26*DEC_DIM);
    dumpf("tgt26",m->tgt,26*DEC_DIM);

    // self attention: query = last 13 of tgt, key/value = tgt(26)
    const float *sipb = fa(m, FA_TF_BASE), *sob = fa(m, FA_TF_BASE+1);
    attention(m, M_SELF_Q, M_SELF_K, M_SELF_O,
              m->tgt+13*DEC_DIM, m->tgt, 13, 26,
              sipb, sipb+DEC_DIM, sipb+2*DEC_DIM, sob,
              m->decout, m->q, m->kv, m->vv, m->attn);
    for (unsigned t = 0; t < 13; ++t)
        for (unsigned c = 0; c < DEC_DIM; ++c)
            m->q[(size_t)t*DEC_DIM+c] = m->tgt[(size_t)(t+13)*DEC_DIM+c]+m->decout[(size_t)t*DEC_DIM+c];
    layernorm(m->q, fa(m,FA_TF_BASE+6), fa(m,FA_TF_BASE+7), 13, DEC_DIM);
    dumpf("q_after_self",m->q,13*DEC_DIM);
    // cross attention: query = q, key/value = mem
    const float *cipb = fa(m, FA_TF_BASE+2), *cob = fa(m, FA_TF_BASE+3);
    attention(m, M_CROSS_Q, M_CROSS_K, M_CROSS_O,
              m->q, m->mem, 13, 26,
              cipb, cipb+DEC_DIM, cipb+2*DEC_DIM, cob,
              m->decout, m->cq, m->kv, m->vv, m->attn);
    for (unsigned t = 0; t < 13; ++t)
        for (unsigned c = 0; c < DEC_DIM; ++c)
            m->kv[(size_t)t*DEC_DIM+c] = m->q[(size_t)t*DEC_DIM+c]+m->decout[(size_t)t*DEC_DIM+c];
    layernorm(m->kv, fa(m,FA_TF_BASE+8), fa(m,FA_TF_BASE+9), 13, DEC_DIM);
    dumpf("kv_after_cross",m->kv,13*DEC_DIM);
    // FFN
    dense(m, M_FFN1, m->kv, m->vv, 13, DEC_DIM, ENC_DIM,
          DEC_DIM, ENC_DIM, ms(m,M_FFN1), fa(m,FA_TF_BASE+4));
    relu(m->vv, 13, ENC_DIM);
    dense(m, M_FFN2, m->vv, m->decout, 13, ENC_DIM, DEC_DIM,
          ENC_DIM, DEC_DIM, ms(m,M_FFN2), fa(m,FA_TF_BASE+5));
    for (unsigned t = 0; t < 13; ++t)
        for (unsigned c = 0; c < DEC_DIM; ++c)
            m->attn[(size_t)t*DEC_DIM+c] = m->kv[(size_t)t*DEC_DIM+c]+m->decout[(size_t)t*DEC_DIM+c];
    layernorm(m->attn, fa(m,FA_TF_BASE+10), fa(m,FA_TF_BASE+11), 13, DEC_DIM);
    dumpf("attn_after_ffn",m->attn,13*DEC_DIM);

    // proj_d2e: 13 x DEC_DIM -> 13 x ENC_DIM
    const float *pdw = fa(m, FA_PROJ_BASE+4), *pdb = fa(m, FA_PROJ_BASE+5);
    for (unsigned t = 0; t < 13; ++t) {
        const float *ar = m->attn + (size_t)t*DEC_DIM;
        float *mr = m->mout + (size_t)t*ENC_DIM;
        for (unsigned c = 0; c < DEC_DIM; ++c) {
            mr[2*c]   = pdw[2*c]*ar[c];
            mr[2*c+1] = pdw[2*c+1]*ar[c];
        }
    }
    for (unsigned t = 0; t < 13; ++t) {
        float *mr = m->mout + (size_t)t*ENC_DIM;
        for (unsigned c = 0; c < ENC_DIM; ++c) {
            float v = mr[c]+pdb[c]; mr[c] = v>0?v:0;
        }
    }
    for (unsigned t = 0; t < 13; ++t)
        for (unsigned c = 0; c < ENC_DIM; ++c)
            m->mout[(size_t)t*ENC_DIM+c] += m->l[(size_t)t*ENC_DIM+c];
    dumpf("mout",m->mout,13*ENC_DIM);

    // x = base(in_conv) * m ; cat out_buf (4) + 13 = 17
    memcpy(m->outin, m->out_buf, 4*ENC_DIM*sizeof(float));
    for (unsigned t = 0; t < 13; ++t)
        for (unsigned c = 0; c < ENC_DIM; ++c)
            m->outin[(size_t)(t+4)*ENC_DIM+c] = m->base[(size_t)t*ENC_DIM+c]*m->mout[(size_t)t*ENC_DIM+c];
    memcpy(m->out_buf, m->outin + 13*ENC_DIM, 4*ENC_DIM*sizeof(float));
    dumpf("outin",m->outin,17*ENC_DIM);

    // out_conv: 17 frames -> 208 samples + tanh (scalar gather form)
    const float *ow = fa(m, FA_OUT_CONV_W);
    for (unsigned s = 0; s < 208; ++s) {
        float acc = 0;
        for (unsigned t = 0; t < 17; ++t) {
            int k = (int)s + 64 - 16*(int)t;
            if (k >= 0 && k < 80) {
                const float *r = m->outin + (size_t)t*ENC_DIM;
                for (unsigned c = 0; c < ENC_DIM; ++c)
                    acc += ow[(size_t)c*80+k]*r[c];
            }
        }
        out208[s] = tanhf(acc);
    }
}
