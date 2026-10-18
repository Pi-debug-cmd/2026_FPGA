"""Existing public validation inputs only; diagnose level sensitivity, not quality approval."""
from pathlib import Path
import json,subprocess,hashlib,time,argparse
import numpy as np
import soundfile as sf
import torch,sentencepiece as spm
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,FRONT
from prepare_aligned_teacher_pilot_20261004 import read_audio,hanzi
from check_phasefree_student_20261004 import distance
BASE=Path(__file__).resolve().parent
NATIVE=BASE.parent/'board_support/native_llvc_20261005'
parser=argparse.ArgumentParser();parser.add_argument('--model',required=True);parser.add_argument('--outname',required=True);args=parser.parse_args();assert args.outname.replace('_','').isalnum()
OUT=BASE.parent/'board_budget_20261005'/args.outname;OUT.mkdir(exist_ok=True)
MODEL=Path(args.model)
assert MODEL.is_file()
rows=json.loads((BASE.parent/'board_budget_20261005/student_corpus/paired_manifest.json').read_text(encoding='utf-8'))['files']
chosen=[next(r for r in rows if r['split']=='validation' and r['gender']==g) for g in ['male','female']]
checker=PinyinChecker();sp=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
def decode(x):
 x=x.astype('float32');x=x/max(float(np.max(np.abs(x))),1e-8)
 with torch.inference_mode():f,l=checker.frontend(torch.from_numpy(x)[None],torch.tensor([len(x)]))
 h,p,n=checker.session.run(['hanzi_log_probs','pinyin_log_probs','encoder_lens'],dict(feats=f.numpy().astype('float32'),feats_lens=l.numpy().astype('int32')))
 ids=[];old=0
 for frame in h[:int(n[0]),0]:
  token=int(frame.argmax())
  if token and token!=old:ids.append(token)
  old=token
 return sp.decode(ids)
rng=np.random.default_rng(20261005+8);cases=[];begin=time.monotonic()
for row in chosen:
 original=read_audio(row['path']);speech=original*(.004/max(float(np.sqrt(np.mean(original**2))),1e-9));n=len(speech)+32000;t=np.arange(n)/16000
 white=rng.normal(size=n);colored=np.convolve(white,np.ones(16)/16,mode='same');colored=colored/max(float(np.sqrt(np.mean(colored*colored))),1e-9)
 noise=(.55*colored+.3*np.sin(2*np.pi*50*t)+.15*np.sin(2*np.pi*150*t));noise=noise*.0015/max(float(np.sqrt(np.mean(noise*noise))),1e-9)
 for condition in ['weak_clean','weak_synthetic_colored_noise']:
  signal=np.pad(speech,(0,32000))+(noise if condition.endswith('noise') else 0)
  source_text=decode(signal[:len(speech)])
  for gain in [1,4,8]:
   key=Path(row['filename']).stem+'_'+condition+'_gain'+str(gain);inp=OUT/(key+'.input.f32');yp=OUT/(key+'.output.f32');x=(signal*gain).astype('<f4');assert np.max(np.abs(x))<1;x.tofile(inp)
   subprocess.run([str(NATIVE/'native_llvc_small96_meter_host.exe'),str(MODEL),str(inp),str(yp)],capture_output=True,check=True)
   y=np.fromfile(yp,dtype='<f4');assert len(y)==len(x) and np.isfinite(y).all();text=decode(y[:len(speech)]);sf.write(OUT/(key+'.wav'),y[:len(speech)],16000,subtype='PCM_16')
   spoken=y[:len(speech)];quiet=y[-16000:]
   cases.append(dict(filename=row['filename'],gender=row['gender'],split='validation',condition=condition,gain=gain,publisher_text=row['text'],source_asr=source_text,source_edits=distance(hanzi(source_text),hanzi(row['text'])),converted_asr=text,converted_edits=distance(hanzi(text),hanzi(row['text'])),characters=len(hanzi(row['text'])),speech_output_rms=float(np.sqrt(np.mean(spoken*spoken))),last_1s_quiet_output_rms=float(np.sqrt(np.mean(quiet*quiet))),input_rms=float(np.sqrt(np.mean(x[:len(speech)]**2))),output_peak=float(np.max(np.abs(y))),wav=str(OUT/(key+'.wav'))))
   report=dict(cases=cases,complete=False,model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),synthetic_noise_not_measured_board_noise=True,user_audio_recorded=False,asr_not_human_quality_approval=True,heldout_test_not_used=True)
   (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('CASE',json.dumps(cases[-1],ensure_ascii=False),flush=True)
summary=[]
for condition in ['weak_clean','weak_synthetic_colored_noise']:
 for gain in [1,4,8]:
  cs=[c for c in cases if c['condition']==condition and c['gain']==gain];summary.append(dict(condition=condition,gain=gain,edits=sum(c['converted_edits'] for c in cs),characters=sum(c['characters'] for c in cs),mean_quiet_rms=float(np.mean([c['last_1s_quiet_output_rms'] for c in cs]))))
report.update(complete=True,summary=summary,seconds=time.monotonic()-begin);(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('DONE',json.dumps(summary),flush=True)
