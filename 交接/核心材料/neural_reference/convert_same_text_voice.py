"""Generic local TTS of target transcript -> fixed target RVC model.
The target recording is a reference only, never the conversion input here.
"""
from pathlib import Path
import hashlib
import json
import os
import random
import sys
import numpy as np
import soundfile as sf
import torch
import run_rvc_pilot as pilot

BASE = Path(__file__).resolve().parent
ROOT = BASE/'RVC'
OUT = Path('D:/总进度/目标人物分析/素材同文本普通声转换对比')

def save_aligned(x, sr, name):
    x = np.asarray(x,dtype=np.float64)
    if x.ndim == 2: x=x.mean(axis=1)
    rms=float(np.sqrt(np.mean(x*x)))
    peak=float(np.max(np.abs(x)))
    if not np.isfinite(x).all() or rms<=0: raise RuntimeError('Invalid audio')
    path=OUT/name
    sf.write(path,x*min(.04/rms,.95/peak),sr,subtype='PCM_16')
    saved,_=sf.read(path)
    if np.max(np.abs(saved))>=1 or not np.isfinite(saved).all(): raise RuntimeError('Invalid saved audio')
    return dict(path=str(path),sr=sr,seconds=len(saved)/sr,
                rms=float(np.sqrt(np.mean(saved*saved))),peak=float(np.max(np.abs(saved))),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    pilot.settings()
    sys.path.insert(0,str(ROOT))
    os.chdir(ROOT)
    from infer.cli import create_config
    from infer.vc.modules import VC
    model=ROOT/'assets/weights/target_person_corrected.pth'
    index=next((ROOT/'logs/target_person_corrected').glob('added_IVF*_Flat_nprobe_1_*.index'))
    source=OUT/'普通合成声_原始.wav'
    text=(OUT/'素材前15秒_识别文本.txt').read_text(encoding='utf-8').strip()
    audio,sr=sf.read(source)
    source_record=save_aligned(audio,sr,'普通声_转换前.wav')
    target,target_sr=sf.read(OUT/'目标人物原声_前15秒.wav')
    target_record=save_aligned(target,target_sr,'目标人物原声_试听.wav')
    vc=VC(create_config())
    vc.get_vc(model.name)
    random.seed(20261003)
    np.random.seed(20261003)
    torch.manual_seed(20261003)
    torch.cuda.manual_seed_all(20261003)
    status,result=vc.vc_single(0,str(source),0,'rmvpe',str(index),.75,0,1.,.33)
    if not result or result[0] is None or result[1] is None: raise RuntimeError(status)
    output_sr,converted=result
    if np.issubdtype(converted.dtype,np.integer):
        converted=converted.astype(np.float64)/(np.iinfo(converted.dtype).max+1)
    converted_record=save_aligned(converted,output_sr,'普通声_转换成目标人物.wav')
    if abs(converted_record['seconds']-source_record['seconds'])>.1: raise RuntimeError('Duration mismatch')
    report=dict(text=text,text_origin='Local ASR of Track9 first 15 seconds; not human verified',
                conversion_source=str(source),source_kind='Local Microsoft Kangkang ordinary synthetic voice',
                target_audio_is_conversion_input=False,target_audio_is_reference_only=True,
                tts_text_rewritten=False,tts_text_file=str(OUT/'素材前15秒_识别文本.txt'),
                model=str(model),model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
                pitch_semitones=0,index_rate=.75,protect=.33,
                board_deployed=False,subjective_acceptance='pending',
                comparison_scope='Same text, generic TTS to target; does not validate all live speakers',
                files=[target_record,source_record,converted_record])
    (OUT/'同文本转换记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__': main()
