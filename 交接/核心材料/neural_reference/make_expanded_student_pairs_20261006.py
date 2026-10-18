"""Source-timed native VC teacher pairs. No ASR-to-TTS or waveform time warp."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys,os,json,time,hashlib
BASE=Path(__file__).resolve().parent;SRC=BASE/'CosyVoice_reference'
sys.path[:0]=[str(SRC),str(SRC/'third_party/Matcha-TTS')]
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
import torch,numpy as np,soundfile as sf
from scipy.signal import resample_poly
from math import gcd
from transformers import Qwen2ForCausalLM,AutoConfig
from run_cosyvoice3_controls_20261004 import MODEL,ASSETS,sha
OUT=BASE.parent/'board_budget_20261005/student_corpus_expanded'
TARGET=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')

def main():
    doc=json.loads((OUT/'source_manifest.json').read_text(encoding='utf-8'))
    torch.set_num_threads(4);torch.cuda.init()
    for r in json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))['files']:assert sha(r['path'])==r['sha256']
    assert sha(TARGET)=='4651ab56a9b285c0d645bd6f0b94f7987e6ed8bd5171e54c37048b436e177c8f'
    original=Qwen2ForCausalLM.from_pretrained
    def config_only(path,*a,**k):
        config=AutoConfig.from_pretrained(path,local_files_only=True);old=torch.get_default_dtype()
        try:torch.set_default_dtype(torch.float16);return Qwen2ForCausalLM(config)
        finally:torch.set_default_dtype(old)
    Qwen2ForCausalLM.from_pretrained=staticmethod(config_only)
    from cosyvoice.cli.model import CosyVoice3Model
    upstream=CosyVoice3Model.__init__
    def small(self,llm,flow,hift,*a,**k):llm.half();flow.half();upstream(self,llm,flow,hift,*a,**k)
    CosyVoice3Model.__init__=small
    from cosyvoice.cli.cosyvoice import CosyVoice3
    model=CosyVoice3(str(MODEL),fp16=True);Qwen2ForCausalLM.from_pretrained=original
    print('TEACHER_LOADED',flush=True)
    teacher=OUT/'teacher';teacher.mkdir(exist_ok=True)
    # Fixed identity frontend is computed once; every source token is extracted
    # from that actual source WAV. No source-person reference is conditioned.
    front=model.frontend.frontend_vc(doc['files'][0]['path'],str(TARGET),model.sample_rate)
    cache={k:v for k,v in front.items() if not k.startswith('source_')}
    previous={}
    manifest=OUT/'paired_manifest.json'
    if manifest.exists():previous={r['filename']:r for r in json.loads(manifest.read_text(encoding='utf-8'))['files']}
    rows=[]
    for row in doc['files']:
        assert sha(row['path'])==row['sha256']
        output=teacher/row['filename']
        old=previous.get(row['filename'])
        if old and output.exists() and sha(output)==old['teacher_sha256']:
            rows.append(old);continue
        torch.manual_seed(20261005);torch.cuda.empty_cache();start=time.perf_counter()
        token=model.frontend._extract_speech_token(row['path'])
        inputs={**cache,'source_speech_token':token[0],'source_speech_token_len':token[1]}
        parts=[]
        for item in model.model.tts(**inputs,stream=False,speed=1.):parts.append(item['tts_speech'].detach().cpu().float().numpy().reshape(-1))
        wave=np.concatenate(parts);wave=resample_poly(wave,16000//gcd(16000,model.sample_rate),model.sample_rate//gcd(16000,model.sample_rate)).astype('float32')
        source,sr=sf.read(row['path'],dtype='float32');source=source.mean(axis=1) if source.ndim==2 else source
        if sr!=16000:source=resample_poly(source,16000//gcd(sr,16000),sr//gcd(sr,16000)).astype('float32')
        assert np.isfinite(wave).all()
        rms=float(np.sqrt(np.mean(wave*wave)));gain=min(.08/max(rms,1e-8),.90/max(float(np.max(np.abs(wave))),1e-8))
        wave*=gain;sf.write(output,wave,16000,subtype='FLOAT')
        result=dict(row,teacher_path=str(output),teacher_sha256=sha(output),teacher_samples=len(wave),source_samples=len(source),
                    duration_difference_samples=len(wave)-len(source),inference_seconds=time.perf_counter()-start,gain_only=gain,
                    source_timed_native_vc=True,teacher_waveform_time_warp=False,teacher_human_quality_accepted=False)
        rows.append(result)
        save=dict(doc,files=rows,target_reference=str(TARGET),target_reference_sha256=sha(TARGET),teacher_model_revision='29e01c4e8d000f4bcd70751be16fa94bf3d85a18',
                  source_timed_conversion=True,asr_to_tts_used=False,source_enrollment=False,all_teacher_outputs_human_accepted=False,
                  board_teacher_deployment=False,complete=len(rows)==len(doc['files']))
        manifest.write_text(json.dumps(save,ensure_ascii=False,indent=2),encoding='utf-8')
        print('PAIRED',len(rows),len(doc['files']),row['split'],round(result['inference_seconds'],2),flush=True)
    print('TEACHER_PAIRS_READY',len(rows),flush=True)
if __name__=='__main__':main()
