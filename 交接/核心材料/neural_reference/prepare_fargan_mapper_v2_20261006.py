from pathlib import Path
import json,numpy as np
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';manifest=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'))
values=[]
for r in manifest['target_training']:
 x=np.fromfile(r['features'],dtype=np.float32).reshape(-1,20);values.append(x[x[:,0]>-7,1:18])
reference=np.concatenate(values).mean(axis=0)
(budget/'fargan_corpus/target_spectral_reference.json').write_text(json.dumps(dict(reference=reference.tolist(),target_tracks=[5,6,7,8],track9_used=False,active_energy_feature_threshold=-7,frames=sum(len(x) for x in values)),indent=2),encoding='utf-8')
source=(base/'train_fargan_mapper_20261006.py').read_text(encoding='utf-8')
source=source.replace('normalize_pitch,export_mapper','normalize_pitch,normalize_spectrum,export_mapper')
source=source.replace("out=budget/'fargan_mapper_v1'","out=budget/'fargan_mapper_v2'")
source=source.replace("torch.set_num_threads(4);torch.manual_seed(20261006)","reference=np.array(json.loads((budget/'fargan_corpus/target_spectral_reference.json').read_text())['reference'],dtype=np.float32)\ntorch.set_num_threads(4);torch.manual_seed(20261006+2)")
source=source.replace('x=normalize_pitch(raw)','x=normalize_spectrum(raw,reference)')
source=source.replace("anchors.append(torch.tensor(x,device=device));all_inputs.append(x)","y=raw.copy();y[:,18]=normalize_pitch(raw)[:,18];anchors.append((torch.tensor(x,device=device),torch.tensor(y,device=device)));all_inputs.append(x)")
source=source.replace("else:xx,_=crop(anchors[int(rng.integers(len(anchors)))]);yy=xx.clone()","else:\n            ax,ay=anchors[int(rng.integers(len(anchors)))];xx,at=crop(ax);yy=ay[at:at+length]")
source=source.replace('steps=1200','steps=2000').replace('checkpoint_step1200.pt','checkpoint_step2000.pt').replace('fargan_mapper_v1.f32','fargan_mapper_v2.f32')
source=source.replace('vocoder_finetuned=False,target_track9_used=False','vocoder_finetuned=False,causal_spectral_normalization=True,spectral_reference=reference.tolist(),target_track9_used=False')
(base/'train_fargan_mapper_v2_20261006.py').write_text(source,encoding='utf-8');print('FARGAN_MAPPER_V2_PREPARED',flush=True)
