"""Separate candidates: zero-copy encoder history and vector output convolution."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
encoder=r'''
    V encoder(V x){
        for(int layer=0;layer<8;layer++){
            int dil=1<<layer,context=2*dil;
            std::string p="mask_gen.encoder.dcc_layers.dcc_"+std::to_string(layer)+".layers.";
            const V &dw=w.get(p+"0.weight",E*3),&db=w.get(p+"0.bias",E);
            V y(T*E);
            auto row=[&](int index)->const float*{
                if(index>=context)return x.data()+(index-context)*E;
                return enc[layer].data()+((enc_pos[layer]+index)%context)*E;
            };
            for(int t=0;t<T;t++){
                const float *a=row(t),*b=row(t+dil),*c=row(t+2*dil);
                int ch=0;
#ifdef __ARM_NEON
                for(;ch+4<=E;ch+=4){
                    float32x4x3_t weights=vld3q_f32(dw.data()+ch*3);
                    float32x4_t v=vmlaq_f32(vld1q_f32(db.data()+ch),vld1q_f32(a+ch),weights.val[0]);
                    v=vmlaq_f32(v,vld1q_f32(b+ch),weights.val[1]);
                    v=vmlaq_f32(v,vld1q_f32(c+ch),weights.val[2]);vst1q_f32(y.data()+t*E+ch,v);
                }
#endif
                for(;ch<E;ch++)y[t*E+ch]=db[ch]+a[ch]*dw[ch*3]+b[ch]*dw[ch*3+1]+c[ch]*dw[ch*3+2];
            }
            for(int t=0;t<T;t++)std::memcpy(enc[layer].data()+((enc_pos[layer]+t)%context)*E,x.data()+t*E,E*sizeof(float));
            enc_pos[layer]=(enc_pos[layer]+T)%context;
            norm(y,T,E,w.get(p+"1.weight",E),w.get(p+"1.bias",E));relu(y);
            y=linear(y,T,E,E,w.get(p+"3.weight",E*E),w.get(p+"3.bias",E));
            norm(y,T,E,w.get(p+"4.weight",E),w.get(p+"4.bias",E));relu(y);
            for(size_t j=0;j<x.size();j++)x[j]+=y[j];
        }
        return x;
    }
'''
oldout='''            for(int j=begin;j<end;j++)output[t*16+j-64]+=f*ow[c*80+j];'''
newout='''            int j=begin;
#ifdef __ARM_NEON
            for(;j+4<=end;j+=4){
                float *dst=output.data()+t*16+j-64;
                vst1q_f32(dst,vmlaq_n_f32(vld1q_f32(dst),vld1q_f32(ow.data()+c*80+j),f));
            }
#endif
            for(;j<end;j++)output[t*16+j-64]+=f*ow[c*80+j];'''
for name in ['small128','small96']:
    source=(ROOT/('native_llvc_'+name+'.cpp')).read_text(encoding='utf-8')
    source=source.replace('const Weights &w; V enc[8]', 'int enc_pos[8]; const Weights &w; V enc[8]')
    source=source.replace('std::memset(pre,0,sizeof(pre));','std::memset(pre,0,sizeof(pre));std::memset(enc_pos,0,sizeof(enc_pos));')
    start=source.index('    V encoder(');end=source.index('    V project_e2d(',start)
    source=source[:start]+encoder+source[end:]
    assert oldout in source
    source=source.replace(oldout,newout)
    source=source.replace('native_fp32_packed_candidate','native_fp32_ring_candidate')
    (ROOT/('native_llvc_'+name+'_ring.cpp')).write_text(source,encoding='utf-8')
print('Created two separate ring/SIMD candidates; baseline unchanged.')
