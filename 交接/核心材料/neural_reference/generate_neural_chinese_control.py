"""Local generic Mandarin TTS controls; target audio is never used as TTS input."""
from pathlib import Path
import hashlib,json,os,sys,types
from importlib.metadata import distribution
import run_rvc_pilot as pilot
pilot.settings()
import numpy as np
import torch
import soundfile as sf
import jieba
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/音色与自然度复查')
OUT.mkdir(parents=True,exist_ok=True)
jieba.dt.tmp_dir=str(BASE/'cache');jieba.dt.cache_file=str(BASE/'cache/jieba_neural_tts.cache')
os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
torch.set_num_threads(4)
manifest=json.loads((BASE/'kokoro_source/model_manifest.json').read_text(encoding='utf-8'))
repo=manifest[0];folder=Path(repo['local'])
for row in repo['files']:
    assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']
# KModel can be used directly. Avoid importing the unrelated English pipeline and its spaCy dependencies.
package=types.ModuleType('kokoro');package.__path__=[str(distribution('kokoro').locate_file('kokoro'))]
sys.modules['kokoro']=package
from kokoro.model import KModel
from misaki.zh import ZHG2P
text_path=Path('D:/总进度/目标人物分析/素材同文本普通声转换对比/素材前15秒_识别文本.txt')
text=text_path.read_text(encoding='utf-8').strip()
from opencc import OpenCC
# Simplified/traditional representation is normalized, spoken content is unchanged.
text=OpenCC('t2s').convert(text)
model=KModel(repo_id=repo['repository'],config=str(folder/'config.json'),model=str(folder/'kokoro-v1_1-zh.pth')).to('cuda').eval()
states=torch.load(folder/'kokoro-v1_1-zh.pth',map_location='cpu',weights_only=True)
normalization_fixes=[]
for component,state in states.items():
    source={k.removeprefix('module.'):v for k,v in state.items()}
    network=getattr(model,component)
    # PyPI code adds affine=True only for old ONNX export compatibility.
    # The pinned Chinese checkpoint has no such affine parameters; restore its affine=False normalization.
    for name,module in list(network.named_modules()):
        if isinstance(module,torch.nn.InstanceNorm1d) and module.affine and name+'.weight' not in source:
            assert torch.equal(module.weight,torch.ones_like(module.weight)) and torch.equal(module.bias,torch.zeros_like(module.bias))
            parent_name,_,child_name=name.rpartition('.')
            parent=network.get_submodule(parent_name) if parent_name else network
            setattr(parent,child_name,torch.nn.InstanceNorm1d(module.num_features,eps=module.eps,momentum=module.momentum,affine=False,track_running_stats=module.track_running_stats).to('cuda'))
            normalization_fixes.append(component+'.'+name)
    network.load_state_dict(source,strict=True)
    for key,p in getattr(model,component).named_parameters():
        assert key in source and source[key].shape==p.shape,(component,key)
g2p=ZHG2P(version='1.1');phonemes,_=g2p(text)
assert len(phonemes)<510 and '❓' not in phonemes
assert all(ch in model.vocab for ch in phonemes),sorted(set(phonemes)-set(model.vocab))
records=[]
for voice in ['zm_010','zf_001']:
    torch.manual_seed(20261003)
    pack=torch.load(folder/'voices'/(voice+'.pt'),map_location='cpu',weights_only=True)
    with torch.inference_mode():audio=model(phonemes,pack[len(phonemes)-1],speed=1).numpy()
    assert np.isfinite(audio).all() and np.sqrt(np.mean(audio*audio))>1e-6
    dest=OUT/f'普通神经合成声_{voice}_同文本.wav';sf.write(dest,audio,24000,subtype='PCM_24')
    records.append(dict(label='generic_neural_'+voice,path=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),
        expected_text=text,text_origin='same ASR-derived target text, simplified representation, no content edits',
        seconds=len(audio)/24000,voice=voice,role='ordinary input only; not target impersonation',
        dataset='generic Kokoro Mandarin TTS',repository=repo['repository'],revision=repo['revision'],
        source_speaker_enrollment=False,audio_uploaded=False))
(OUT/'neural_control_manifest.json').write_text(json.dumps(dict(status='complete',files=records,assets=manifest,
    phonemes=phonemes,text=text,text_source_sha256=hashlib.sha256(text_path.read_bytes()).hexdigest(),
    model_parameters=sum(p.numel() for p in model.parameters()),
    normalization_compatibility='Restored affine=False per checkpoint; removed only newly added identity1/0 affine terms for old ONNX export compatibility',
    normalization_fixes=normalization_fixes,
    purpose='Test source naturalness confound only; live project never requires source transcription/TTS.'),ensure_ascii=False,indent=2),encoding='utf-8')
print('Two generic same-text Mandarin controls generated locally.',flush=True)
