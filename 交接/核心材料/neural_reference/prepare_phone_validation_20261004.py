"""Fixed synthetic minimal-pair controls; labels remain provisional until heard.

No target voice conversion/training or speech uploaded. TTS controls are not
claimed to be human-labelled phonetic gold data or an ASR->TTS project route.
"""
from pathlib import Path
import json,sys,types,tarfile,hashlib
from importlib.metadata import distribution
from run_rvc_pilot import settings
settings()
import numpy as np,torch,soundfile as sf,jieba
from scipy.signal import resample_poly
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/独立中文发音检查验证_2026-10-04')
SOURCE=BASE/'Allosaurus'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def main():
 OUT.mkdir(exist_ok=True);folder=OUT/'controls';folder.mkdir(exist_ok=True)
 archive=SOURCE/'uni2005.tar.gz';models=SOURCE/'allosaurus/pretrained';models.mkdir(exist_ok=True)
 if not (models/'uni2005/model.pt').exists():
  with tarfile.open(archive) as tar:
   root=models.resolve()
   for m in tar.getmembers():
    target=(root/m.name).resolve()
    if not target.is_relative_to(root):raise ValueError('Tar path outside model directory')
   tar.extractall(root,filter='data')
 save(OUT/'allosaurus_assets.json',dict(repository='https://github.com/xinjli/allosaurus',
  code_revision='d9f1adaf47d3b3765b41f4177da62a051516d636',model='uni2005',
  model_url='https://github.com/xinjli/allosaurus/releases/download/v1.0/uni2005.tar.gz',
  archive_path=str(archive),archive_sha256=sha(archive),
  assets=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in (models/'uni2005').glob('*') if p.is_file()],
  target_training=False,source_enrollment=False))
 jieba.dt.tmp_dir=str(BASE/'cache');jieba.dt.cache_file=str(BASE/'cache/jieba_phone_validation.cache')
 torch.set_num_threads(4)
 repo=json.loads((BASE/'kokoro_source/model_manifest.json').read_text(encoding='utf-8'))[0]
 local=Path(repo['local'])
 for r in repo['files']:assert sha(r['path'])==r['sha256']
 package=types.ModuleType('kokoro');package.__path__=[str(distribution('kokoro').locate_file('kokoro'))]
 sys.modules['kokoro']=package
 from kokoro.model import KModel
 from misaki.zh import ZHG2P
 model=KModel(repo_id=repo['repository'],config=str(local/'config.json'),model=str(local/'kokoro-v1_1-zh.pth')).to('cuda').eval()
 states=torch.load(local/'kokoro-v1_1-zh.pth',map_location='cpu',weights_only=True)
 fixes=[]
 for component,state in states.items():
  supplied={k.removeprefix('module.'):v for k,v in state.items()};network=getattr(model,component)
  for name,module in list(network.named_modules()):
   if isinstance(module,torch.nn.InstanceNorm1d) and module.affine and name+'.weight' not in supplied:
    assert torch.equal(module.weight,torch.ones_like(module.weight)) and torch.equal(module.bias,torch.zeros_like(module.bias))
    parent_name,_,child=name.rpartition('.')
    parent=network.get_submodule(parent_name) if parent_name else network
    setattr(parent,child,torch.nn.InstanceNorm1d(module.num_features,eps=module.eps,momentum=module.momentum,
     affine=False,track_running_stats=module.track_running_stats).to('cuda'));fixes.append(component+'.'+name)
  network.load_state_dict(supplied,strict=True)
 g2p=ZHG2P(version='1.1')
 syllables=[('shi4','是'),('xi4','戏'),('zhe4','这'),('jie4','借'),
            ('bie2','别'),('die2','蝶'),('bi2','鼻'),('bai2','白')]
 records=[]
 for voice in ['zm_010','zf_001']:
  pack=torch.load(local/'voices'/(voice+'.pt'),map_location='cpu',weights_only=True)
  for speed in [.85,1.15]:
   for label,character in syllables:
    text=character+'。';phones,_=g2p(text)
    assert len(phones)<510 and all(ch in model.vocab for ch in phones)
    torch.manual_seed(20261004)
    with torch.inference_mode():y=model(phones,pack[len(phones)-1],speed=speed).numpy()
    assert np.isfinite(y).all() and len(y)>2400
    y=resample_poly(y,2,3).astype('float32')
    y*=min(.04/max(float(np.sqrt(np.mean(y*y))),1e-8),.9/max(float(np.max(np.abs(y))),1e-8))
    dest=folder/f'{voice}_{speed}_{label}.wav';sf.write(dest,y,16000,subtype='PCM_16')
    records.append(dict(id=dest.stem,path=str(dest),sha256=sha(dest),text=text,expected_pinyin=label,
     voice=voice,speed=speed,seconds=len(y)/16000,tts_input_phone_symbols=phones,
     label_status='Synthetic intended pronunciation, NOT independently human-confirmed audio label',
     split='development' if voice=='zm_010' else 'heldout_voice',
     not_source_person_enrollment=True))
    print('CONTROL '+dest.stem+' '+repr(phones),flush=True)
 save(OUT/'synthetic_controls.json',dict(status='complete',files=records,tts_model=repo,
  normalization_compatibility_fixes=fixes,count=len(records),seed=20261004,
  no_tts_control_used_to_train_recognizer=True,provisional_synthetic_labels=True,
  scope='Screen discrimination of fixed same-tone syllable contrasts; not validated human real-speech gold.'))
 print('PREPARATION COMPLETE',flush=True)

if __name__=='__main__':main()
