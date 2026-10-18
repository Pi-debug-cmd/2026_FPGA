"""Fixed ordinary source -> native CV3 conversion, no waveform timing warp.

Track9 is diagnostic original/text only, never the conversion input or prompt.
Offline teacher test, not causal microphone/7020 acceptance.
"""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys,os,json,time
BASE=Path(__file__).resolve().parent;ROOT=BASE/'CosyVoice_reference'
sys.path[:0]=[str(ROOT),str(ROOT/'third_party/Matcha-TTS')]
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker
from prepare_aligned_teacher_pilot_20261004 import read_audio,sha
import torch,numpy as np,soundfile as sf
from transformers import Qwen2ForCausalLM,AutoConfig
from run_cosyvoice3_controls_20261004 import MODEL,ASSETS
OUT=Path('D:/总进度/目标人物分析/原台词_模型直接转换检查_2026-10-04');OUT.mkdir(exist_ok=True)
SOURCE=Path('D:/总进度/目标人物分析/音色与自然度复查/普通神经合成声_zm_010_同文本.wav')
TARGET=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')

def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')

def main():
    torch.set_num_threads(4);checker=PinyinChecker();decoded=checker.predict(SOURCE)
    assert sha(SOURCE)=='0e398b2ea6f8ca5b16feeebfa089477b4d5d5627cdb146a903eee1de66e23658'
    expected=['wo3','de5','xiao4','yuan2','hen3','mei3','zou3','jin4','da4','men2','jiu4','neng2','kan4','jian4','kuan1','kuo4','de5','cao1','chang3']
    save(OUT/'source_pinyin_probe.json',decoded)
    print('SOURCE_PINYIN_FIRST19',decoded['decoded'][:19],flush=True)
    bodies=lambda seq:[t.rstrip('12345') for t in seq]
    assert bodies(decoded['decoded'][:19])==bodies(expected)
    emissions=decoded['emissions'];start=max(0,emissions[0]['approximate_peak_seconds']-.3)
    end=(emissions[18]['approximate_peak_seconds']+emissions[19]['approximate_peak_seconds'])/2
    wave=read_audio(SOURCE)[int(start*16000):int(end*16000)]
    source=OUT/'普通男声输入_原台词.wav';sf.write(source,wave,16000,subtype='FLOAT')
    clipped=checker.predict(source);assert bodies(clipped['decoded'])==bodies(expected)
    save(OUT/'before_inference.json',dict(original_source=str(SOURCE),original_source_sha256=sha(SOURCE),cropped_source=str(source),
        cropped_source_sha256=sha(source),crop_start_seconds=start,crop_end_seconds=end,source_pinyin=clipped,
        source_is_generic_tts=True,source_kind='Frozen Kokoro preset zm_010 ordinary male, same unchanged text',source_is_target_person=False,target_reference=str(TARGET),target_reference_sha256=sha(TARGET),
        text='我的校园很美，走近大门就能看见宽阔的操场。',speed=1.,source_enrollment=False,target_track9_conditioning=False,
        no_teacher_audio_warp=True,board_deployed=False))
    del checker
    for r in json.loads((ASSETS/'manifest.json').read_text(encoding='utf8'))['files']:assert sha(r['path'])==r['sha256']
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
    torch.manual_seed(20261004);np.random.seed(20261004);torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats()
    begin=time.perf_counter();chunks=[]
    for result in model.inference_vc(str(source),str(TARGET),stream=False,speed=1.):chunks.append(result['tts_speech'].detach().cpu().float().numpy().reshape(-1))
    torch.cuda.synchronize();elapsed=time.perf_counter()-begin
    y=np.concatenate(chunks);assert np.isfinite(y).all()
    gain=min(.04/max(float(np.sqrt(np.mean(y*y))),1e-8),.95/max(float(np.max(np.abs(y))),1e-8));y*=gain
    path=OUT/'普通男声_模型直接转换目标声.wav';sf.write(path,y,model.sample_rate,subtype='PCM_24')
    save(OUT/'decision.json',dict(status='native_sametext_output_ready_for_machine_screening',path=str(path),sha256=sha(path),
        seconds=len(y)/model.sample_rate,source_seconds=len(wave)/16000,inference_seconds=elapsed,gain_only=gain,
        no_waveform_or_mel_timing_resampling=True,offline_noncausal_teacher=True,not_student_output=True,
        pretrained_model_target_reference_fixed=True,model_revision='29e01c4e8d000f4bcd70751be16fa94bf3d85a18',
        input_target_person_audio=False,input_generic_male_tts=True,source_enrollment=False,target_track9_not_conditioning=True,
        naturalness_accepted=False,pronunciation_accepted=False,board_deployed=False))
    print('NATIVE SAME-TEXT TEACHER COMPLETE',len(y)/model.sample_rate,len(wave)/16000,elapsed,flush=True)

if __name__=='__main__':main()
