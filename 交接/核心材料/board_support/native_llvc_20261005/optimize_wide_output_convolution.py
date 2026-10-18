from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'native_llvc_wide192_shallow2.cpp').read_text()
source=source.replace('front;float pre[12][2];V label,pos;', 'front;float pre[12][2];V label,pos,outpacked;')
needle='''        label=w.get("derived.label",E);pos=w.get("mask_gen.decoder.pos_enc.pe",200*D);'''
source=source.replace(needle,needle+'''
        const V &ow=w.get("out_conv.0.weight",E*80);outpacked.resize(E*80);
        for(int j=0;j<80;j+=4)for(int c=0;c<E;c++)for(int k=0;k<4;k++)outpacked[j*E+c*4+k]=ow[c*80+j+k];''')
start=source.index('        for(int t=0;t<17;t++)for(int c=0;c<E;c++){')
end=source.index('        for(int i=0;i<CHUNK;i++)output[i]=tanh_approx',start)
source=source[:start]+'''        for(int t=0;t<17;t++){
            int begin=std::max(0,64-t*16),end=std::min(80,CHUNK+64-t*16);
            int j=begin;
#ifdef __ARM_NEON
            for(;j+4<=end;j+=4){
                float *dst=output.data()+t*16+j-64;
                float32x4_t acc=vld1q_f32(dst);
                for(int c=0;c<E;c++)acc=vmlaq_n_f32(acc,vld1q_f32(outpacked.data()+j*E+c*4),total[t*E+c]);
                vst1q_f32(dst,acc);
            }
#endif
            for(;j<end;j++)for(int c=0;c<E;c++)output[t*16+j-64]+=total[t*E+c]*ow[c*80+j];
        }
'''+source[end:]
source=source.replace('native_fp32_wide_shallow_candidate','native_fp32_wide_packed_output_candidate')
(root/'native_llvc_wide192_shallow2_outpack.cpp').write_text(source)
