"""Offline teacher-only conditioning trial; defaults and board remain untouched.
Any input voice is estimated automatically. Reference stats use Track5-8 only.
Full-utterance statistics are NOT a causal streaming implementation.
"""
import types
import numpy as np

def map_pitch(raw,target_center,target_width,preserve_uv=False):
    raw=np.asarray(raw,dtype=np.float64)
    uv=raw<=0
    positives=raw[~uv]
    if len(positives)<8:
        return raw.copy(),dict(adapted=False,reason='Too few positive F0 frames')
    log=np.log(positives)
    center=float(np.median(log))
    p10,p90=np.percentile(log,[10,90])
    width=float(p90-p10)
    scale=float(np.clip(target_width/max(width,.05),.45,1.6))
    strength=.75
    mapped_log=(1-strength)*log+strength*(target_center+(log-center)*scale)
    f0=raw.copy()
    f0[~uv]=np.clip(np.exp(mapped_log),50,1100)
    if not preserve_uv:
        f0[uv]=np.interp(np.where(uv)[0],np.where(~uv)[0],f0[~uv])
    return f0,dict(adapted=True,input_median_hz=float(np.exp(center)),
                  input_log_p10_p90_width=width,target_median_hz=float(np.exp(target_center)),
                  target_log_p10_p90_width=target_width,range_scale=scale,strength=strength,
                  preserve_uv=preserve_uv)

def install(vc,policy,target_center,target_width):
    if policy=='original': return
    original=vc.pipeline.get_f0
    def get_f0(self,x,p_len,f0_up_key,f0_method):
        # Initializes the author's RMVPE; recompute its raw UV mask because the
        # default method has interpolated zeros before returning pitchf.
        original(x,p_len,f0_up_key,f0_method)
        raw=self.model_rmvpe.infer_from_audio(x,thred=.03)
        f0,metadata=map_pitch(raw,target_center,target_width,policy=='target_range_uv')
        vc.pitch_experiment_metadata=metadata
        f0*=2**(f0_up_key/12)
        mel=1127*np.log(1+f0/700)
        minimum=1127*np.log(1+50/700)
        maximum=1127*np.log(1+1100/700)
        active=mel>0
        mel[active]=(mel[active]-minimum)*254/(maximum-minimum)+1
        coarse=np.rint(np.clip(mel,1,255)).astype(np.int32)
        return coarse,f0.astype(np.float32)
    vc.pipeline.get_f0=types.MethodType(get_f0,vc.pipeline)

def verify_mapping():
    mixed=np.array([0,110,120,140,170,210,240,260,280,300,0,0],dtype=float)
    result,metadata=map_pitch(mixed,np.log(193),.3,True)
    assert np.array_equal(result[mixed==0],np.zeros(3))
    assert np.isfinite(result).all() and len(result)==len(mixed)
    assert np.all((result[mixed>0]>=50)&(result[mixed>0]<=1100))
    silent,_=map_pitch(np.zeros(100),np.log(193),.3,True)
    assert np.array_equal(silent,np.zeros(100))
    assert metadata['range_scale']<1

if __name__=='__main__':
    verify_mapping()
    print('Pitch mapping silence/UV/finite/frame-count checks passed')
