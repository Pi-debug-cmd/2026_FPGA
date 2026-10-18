"""Independent free pinyin CTC decoding, screened before any approval use."""
from pathlib import Path
from typing import Tuple
import ast,json,importlib.util,hashlib,time,re
from math import gcd
from run_rvc_pilot import settings
settings()
import numpy as np,torch,soundfile as sf,onnxruntime as ort,yaml
import torch.nn as nn
import torchaudio.compliance.kaldi as kaldi
from torch.nn.utils.rnn import pad_sequence
from scipy.signal import resample_poly
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/独立中文发音检查验证_2026-10-04')
ASSETS=BASE/'sensevoice_pinyin_assets'
MODEL=ASSETS/'robinsonphan__sensevoice-small-zh-pinyin-dual-ctc/sensevoice_dual'
FRONT=ASSETS/'FunAudioLLM__SenseVoiceSmall'
REFERENCE=BASE/'FunASR_reference/funasr/frontends/wav_frontend.py'
torch.set_num_threads(4)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_frontend():
 # Execute reviewed, unmodified frontend functions/class from pinned official code,
 # removing registration decorators and avoiding unrelated FunASR AutoModel loader.
 tree=ast.parse(REFERENCE.read_text(encoding='utf-8'))
 keep=[]
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in ['load_cmvn','apply_cmvn','apply_lfr','WavFrontend']:
   node.decorator_list=[];keep.append(node)
 namespace=dict(np=np,torch=torch,nn=nn,kaldi=kaldi,pad_sequence=pad_sequence,Tuple=Tuple)
 exec(compile(ast.Module(body=keep,type_ignores=[]),str(REFERENCE),'exec'),namespace)
 config=yaml.safe_load((FRONT/'config.yaml').read_text(encoding='utf-8'))['frontend_conf']
 config['cmvn_file']=str(FRONT/'am.mvn')
 frontend=namespace['WavFrontend'](**config).eval()
 assert frontend.cmvn.shape==(2,560)
 save(OUT/'sensevoice_frontend_manifest.json',dict(reference_repository='https://github.com/modelscope/FunASR',
  reference_revision='66d7a4c264a5993a2a63ed00c1f402c296ee521a',reference_path=str(REFERENCE),reference_sha256=sha(REFERENCE),
  extracted_definitions=['load_cmvn','apply_cmvn','apply_lfr','WavFrontend'],
  implementation_changes='Only registration decorators removed; Kaldi backend is installed torchaudio as official wrapper selects.',
  config=config,dither=frontend.dither,seed=20261004,cmvn_sha256=sha(FRONT/'am.mvn'),
  audio_normalization='mono/resample16k, peak normalized as author test_onnx.py; frontend rescales32768',
  no_base_neural_model_needed_for_frontend=True))
 return frontend

class PinyinChecker:
 def __init__(self):
  for repo in read(ASSETS/'manifest.json'):
   for f in repo['files']: assert sha(f['path'])==f['sha256']
  self.frontend=load_frontend()
  vocabulary=read(MODEL/'data/vocab_pinyin.json');self.vocabulary=vocabulary
  self.id2token={v:k for k,v in vocabulary.items()}
  assert vocabulary['<blank>']==0
  opts=ort.SessionOptions();opts.intra_op_num_threads=4;opts.inter_op_num_threads=1
  self.session=ort.InferenceSession(str(MODEL/'outputs/sensevoice_dual.onnx'),sess_options=opts,providers=['CPUExecutionProvider'])
  save(OUT/'sensevoice_session.json',dict(inputs=[dict(name=i.name,shape=i.shape,type=i.type) for i in self.session.get_inputs()],
   outputs=[dict(name=i.name,shape=i.shape,type=i.type) for i in self.session.get_outputs()],
   vocabulary_size=len(vocabulary),no_expected_text_supplied_to_recognizer=True,
   no_hanzi_to_pinyin_conversion_in_inference=True,no_language_model_or_beam_search=True))

 def predict(self,path,diagnostic_name=None):
  x,sr=sf.read(path,dtype='float32');x=x.mean(axis=1) if x.ndim==2 else x
  if sr!=16000:x=resample_poly(x,16000//gcd(sr,16000),sr//gcd(sr,16000)).astype('float32')
  x=x/(float(np.max(np.abs(x)))+1e-8)
  wave=torch.from_numpy(x).unsqueeze(0);torch.manual_seed(20261004)
  with torch.inference_mode():feats,lens=self.frontend(wave,torch.tensor([len(x)]))
  assert feats.ndim==3 and feats.shape[-1]==560 and torch.isfinite(feats).all()
  begun=time.perf_counter()
  probs,lengths=self.session.run(['pinyin_log_probs','encoder_lens'],{'feats':feats.numpy().astype('float32'),'feats_lens':lens.numpy().astype('int32')})
  assert probs.ndim==3 and probs.shape[1]==1 and probs.shape[2]==len(self.vocabulary) and np.isfinite(probs).all()
  probs=probs[:,0];assert np.max(np.abs(np.exp(probs).sum(axis=-1)-1))<1e-3
  result=[];previous=0
  for frame,row in enumerate(probs):
   token=int(np.argmax(row))
   if token and token!=previous:
    result.append(dict(pinyin=self.id2token[token],frame=frame,
     approximate_peak_seconds=frame*.06,acoustic_posterior=float(np.exp(row[token]))))
   previous=token
  if diagnostic_name:np.savez_compressed(OUT/(diagnostic_name+'_pinyin_posteriors.npz'),log_probs=probs)
  return dict(decoded=[r['pinyin'] for r in result],emissions=result,
   frame_period_seconds=.06,frame_times_are_ctc_peaks_not_syllable_boundaries=True,
   seconds=len(x)/16000,onnx_seconds=time.perf_counter()-begun,
   posterior_is_not_calibrated_pronunciation_correctness=True)

def main():
 checker=PinyinChecker();results=[]
 for r in read(OUT/'synthetic_controls.json')['files']:
  assert sha(r['path'])==r['sha256'];result=checker.predict(r['path'])
  result=dict(r,**result)
  result['intended_syllable_body_matched']=[re.sub(r'\d','',x) for x in result['decoded']]==[re.sub(r'\d','',r['expected_pinyin'])]
  results.append(result);print(r['id']+' => '+' '.join(result['decoded']),flush=True)
  save(OUT/'sensevoice_synthetic_results.json',dict(status='running',files=results))
 summaries=[]
 for split in ['development','heldout_voice']:
  for syllable in ['shi4','xi4','zhe4','jie4','bie2','die2','bi2','bai2']:
   rows=[r for r in results if r['split']==split and r['expected_pinyin']==syllable]
   summaries.append(dict(split=split,syllable=syllable,correct_bodies=sum(r['intended_syllable_body_matched'] for r in rows),n=len(rows)))
 save(OUT/'sensevoice_synthetic_results.json',dict(status='complete',files=results,summary=summaries,
  correct_intended_bodies=sum(r['intended_syllable_body_matched'] for r in results),count=len(results),
  provisional_synthetic_labels=True,not_human_gold_or_final_validator=True))
 originals=read(Path('D:/总进度/目标人物分析/真实声母错误定位_2026-10-04/diagnostic_items.json'))
 ablation=read(Path('D:/总进度/目标人物分析/别字后处理拆分对照_2026-10-04/evaluation_items.json'))
 rows=originals+[r for r in ablation if r['label'] in ['raw_vc_only_clarity2dB','raw_vc_env_on_eq_off']]
 diagnostic=[]
 for r in rows:
  assert sha(r['path'])==r['sha256']
  result=checker.predict(r['path'],r['label'])
  record=dict(label=r['label'],path=r['path'],sha256=r['sha256'],**result,
   human_pronunciation_acceptance=False,expected_text=r['expected_text'],
   not_used_to_train_or_tune_checker=True)
  diagnostic.append(record)
  print('REAL '+r['label']+' => '+' '.join(record['decoded']),flush=True)
 save(OUT/'sensevoice_real_exploratory.json',dict(files=diagnostic,scope='Exploratory independent pinyin decoding; not automatic approval.'))
 print('SENSEVOICE VALIDATION COMPLETE',flush=True)

if __name__=='__main__':main()
