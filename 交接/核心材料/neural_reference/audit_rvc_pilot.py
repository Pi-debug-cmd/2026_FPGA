from pathlib import Path
import hashlib,json,re
import torch

base=Path(__file__).resolve().parent
root=base/'RVC'
exp=root/'logs'/'target_person_pilot'
model=root/'assets'/'weights'/'target_person_pilot.pth'
ckpt=torch.load(model,map_location='cpu',weights_only=True)
finite=all(bool(torch.isfinite(t).all()) for t in ckpt['weight'].values())
if not finite: raise RuntimeError('Nonfinite exported model weights')
text=(exp/'filelist.txt').read_text(encoding='utf-8')
if 'heldout' in text or 'Track 9' in text: raise RuntimeError('Heldout leakage')
log=(exp/'train_20.console.log').read_text(encoding='utf-8')
if '正在保存最终检查点：成功' not in log: raise RuntimeError('No successful final export')
losses=[float(x) for x in re.findall(r'loss_(?:disc|gen|fm|mel|kl)=([0-9.eE+-]+)',log)]
if not losses or not all(x==x and abs(x)<1e20 for x in losses): raise RuntimeError('Invalid logged loss')
split=json.loads((base/'target_pilot_data'/'split_manifest.json').read_text(encoding='utf-8'))
out=Path('D:/总进度/目标人物分析/音色模型首次试训')
data=dict(model=str(model),sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
          bytes=model.stat().st_size,info=ckpt.get('info'),version=ckpt.get('version'),
          f0=ckpt.get('f0'),sample_rate=ckpt['config'][-1],
          finite_exported_weights=finite,training_speaker_id=0,
          training_files=len(text.strip().splitlines()),
          training_original_seconds=sum(f['seconds'] for f in split['files'] if f['split']=='train'),
          heldout_seconds=sum(f['seconds'] for f in split['files'] if f['split']=='heldout'),
          subjective_acceptance='pending',board_deployment=False,
          exported_model_is_teacher_pilot=True)
(out/'模型验证记录.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(data,ensure_ascii=False))
