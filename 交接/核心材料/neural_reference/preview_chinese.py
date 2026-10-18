"""Chinese audition using the unchanged epoch-20 pilot and local Kangkang TTS.
Pitch shift and retrieval settings match the previous English pitch-0 audition.
This is an offline PC test, not a live microphone or Zynq model deployment.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import soundfile as sf
from run_rvc_pilot import settings,command,ROOT

OUT=Path('D:/总进度/目标人物分析/中文音色试听_第20轮')
TEXT='你好，这是中文人声转换测试。现在测试声音是否自然，吐字是否清楚。'
SOURCE=OUT/'中文合成男声_转换前_原始.wav'
MODEL=ROOT/'assets'/'weights'/'target_person_pilot.pth'
CONVERTED=OUT/'中文男声_人物模型转换后_原始.wav'

def main():
    settings()
    if not SOURCE.is_file(): raise FileNotFoundError(SOURCE)
    if not MODEL.is_file(): raise FileNotFoundError(MODEL)
    digest=hashlib.sha256(MODEL.read_bytes()).hexdigest()
    expected='4247a6478cb915efabe7e49f69143bb5d6edf7141e36e7124f99c767e8934f18'
    if digest!=expected: raise RuntimeError('Model changed; this comparison must use epoch-20 pilot')
    command('preview_chinese_pitch0','-m','infer.cli','--model',MODEL,
            '--input',SOURCE,'--output',CONVERTED,'--pitch',0,
            '--speaker-id',0,'--index-rate',0.75,'--overwrite')
    results=[]
    for source,label in [(SOURCE,'中文合成男声_转换前.wav'),
                         (CONVERTED,'中文男声_人物模型转换后.wav')]:
        x,sr=sf.read(source,dtype='float64')
        peak=float(np.max(np.abs(x)))
        rms=float(np.sqrt(np.mean(x*x)))
        if not np.isfinite(x).all() or peak==0 or rms==0:
            raise RuntimeError('Nonfinite or silent audio: '+str(source))
        gain=min(.04/rms,.95/peak)
        dest=OUT/label
        sf.write(dest,x*gain,sr,subtype='PCM_16')
        y,_=sf.read(dest)
        results.append(dict(raw=str(source),audition=str(dest),sr=sr,
                            seconds=len(x)/sr,raw_peak=peak,raw_rms=rms,
                            audition_peak=float(np.max(np.abs(y))),
                            audition_rms=float(np.sqrt(np.mean(y*y))),
                            sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
    if abs(results[0]['seconds']-results[1]['seconds'])>.1:
        raise RuntimeError('Duration mismatch')
    report=dict(text=TEXT,source_kind='Local Microsoft Kangkang Chinese synthetic male voice',
                source_is_user=False,offline_pc=True,board_deployed=False,
                model=str(MODEL),model_sha256=digest,epoch=20,pitch_semitones=0,
                speaker_id=0,index_rate=.75,subjective_acceptance='pending',files=results)
    (OUT/'试听记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'中文试听内容.txt').write_text(TEXT+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
