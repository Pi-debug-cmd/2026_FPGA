from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'native_llvc_small128_vmath.cpp').read_text()
old='''            for(int j=0;j<2*T;j++){
                float f=scores[j]/sum;
                for(int c=0;c<D/8;c++)result[t*D+head*(D/8)+c]+=f*v[j*D+head*(D/8)+c];
            }'''
new='''            float invsum=1.f/sum;
            for(int j=0;j<2*T;j++){
                float f=scores[j]*invsum;int c=0;
#ifdef __ARM_NEON
                for(;c+4<=D/8;c+=4){
                    float *dst=result.data()+t*D+head*(D/8)+c;
                    vst1q_f32(dst,vmlaq_n_f32(vld1q_f32(dst),vld1q_f32(v.data()+j*D+head*(D/8)+c),f));
                }
#endif
                for(;c<D/8;c++)result[t*D+head*(D/8)+c]+=f*v[j*D+head*(D/8)+c];
            }'''
assert old in source
source=source.replace(old,new).replace('native_fp32_vector_math_candidate','native_fp32_vector_attention_candidate')
(root/'native_llvc_small128_vattn.cpp').write_text(source)
