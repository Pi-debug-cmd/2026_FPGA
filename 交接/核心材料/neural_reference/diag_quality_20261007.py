import numpy as np, librosa, sys, json
D = r'D:\总进度\全尺寸学生试听_2026-10-06'
files = {
 'A_target': D+r'\1_目标人物原声.wav',
 'B_input':  D+r'\2_普通男声输入.wav',
 'C_teacher':D+r'\3_教师CV3转换.wav',
 'D_student':D+r'\4_全尺寸学生转换.wav',
}
def analyze(p):
    y, sr = librosa.load(p, sr=16000)
    r = {}
    r['dur'] = len(y)/sr
    r['rms'] = float(np.sqrt((y**2).mean()))
    r['peak'] = float(np.abs(y).max())
    r['clip_frac'] = float((np.abs(y)>0.98).mean())
    # zero crossing rate (noise/roughness)
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=512, hop_length=160)[0]
    r['zcr_med'] = float(np.median(zcr)); r['zcr_p90']=float(np.percentile(zcr,90))
    # frame energy hop (208-sample frames = model chunk) -> discontinuity
    n = len(y)//208
    fr = np.array([np.sqrt((y[i*208:(i+1)*208]**2).mean()+1e-10) for i in range(n)])
    d = np.abs(np.diff(fr))/(fr[:-1]+1e-6)
    r['frame_jump_med']=float(np.median(d)); r['frame_jump_p90']=float(np.percentile(d,90))
    # spectral flatness / noise floor in speech-band vs high band
    S = np.abs(librosa.stft(y, n_fft=1024, hop_length=160))**2
    freqs = librosa.fft_frequencies(sr=16000, n_fft=1024)
    speech = S[(freqs>=300)&(freqs<3400)].mean()
    high = S[(freqs>=6000)].mean()
    r['noise_high_ratio']=float(high/(speech+1e-12))
    # spectral rolloff/roughness
    flat = librosa.feature.spectral_flatness(y=y, n_fft=1024, hop_length=160)[0]
    r['flatness_med']=float(np.median(flat))
    return r
out={}
for k,p in files.items():
    out[k]=analyze(p)
for k,v in out.items():
    print(k, json.dumps(v, ensure_ascii=False))
