"""Export exact existing checkpoint for independent ARM native inference.
No training, no source enrollment, no teacher substitution. Quality unapproved.
"""
from pathlib import Path
import sys,struct,json,hashlib
import numpy as np,torch,soundfile as sf
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
BASE=ROOT/'neural_reference'
sys.path.insert(0,str(BASE))
from load_llvc_audit_model import load_model,digest
from llvc_online_stream import LLVCAudioStream
torch.set_num_threads(4)
model,config=load_model(True)
checkpoint=ROOT/'board_budget_20261004/phasefree_student_pilot/checkpoint_step20.pt'
assert digest(checkpoint)=='8e59d86f3eaed1221e24568bc5eedff0335f88936a62a8f2c7298bd73a34cb35'
state=torch.load(checkpoint,map_location='cpu',weights_only=True)
assert state['steps']==20 and not state['production_approved']
model.load_state_dict(state['model'],strict=True)
model.eval()
with torch.inference_mode():
    label=model.label_embedding(torch.zeros(1,1))[0].numpy()
tensors={k:v.detach().cpu().float().contiguous().numpy() for k,v in model.state_dict().items()}
tensors['derived.label']=label
target=OUT/'llvc_step20.f32'
with target.open('wb') as f:
    f.write(b'LLVCF001')
    f.write(struct.pack('<I',len(tensors)))
    for name,a in tensors.items():
        assert np.isfinite(a).all()
        b=name.encode('utf8')
        f.write(struct.pack('<II',len(b),a.ndim));f.write(b)
        f.write(struct.pack('<'+'I'*a.ndim,*a.shape))
        f.write(a.astype('<f4',copy=False).tobytes())
manifest=dict(purpose='Exact portable target-step20 inference trial, quality NOT approved',checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),
    full_state_dict_strict=True,weights_path=str(target),weights_sha256=digest(target),weights_bytes=target.stat().st_size,
    tensor_count=len(tensors),parameter_count=sum(v.numel() for v in model.parameters()),model_config=config['model_params'],
    fixed_label_precomputed=True,source_enrollment=False,teacher_substituted=False,production_approved=False,board_deployed=False)
(OUT/'model_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
source=BASE/'public_chinese_validation/fleurs_test_row0_id1906.wav'
wave,sr=sf.read(source,dtype='float32');assert sr==16000 and wave.ndim==1
# Short contract tests include startup and many chunk boundaries. Full unseen
# Chinese input is reserved for optional board timing once connected.
tests={'silence_416':np.zeros(416,np.float32),
       'tone_1000':(.1*np.sin(2*np.pi*220*np.arange(1000)/16000)).astype(np.float32),
       'real_16000':wave[:16000],
       'edge_209':wave[:209]}
rows=[]
for name,x in tests.items():
    stream=LLVCAudioStream(model);ys=[]
    for start in range(0,len(x),256):ys.extend(stream.feed(x[start:start+256]))
    ys.extend(stream.finish())
    y=np.concatenate(ys) if ys else np.empty(0,np.float32)
    assert len(y)==len(x) and np.isfinite(y).all()
    x.tofile(OUT/(name+'.input.f32'));y.tofile(OUT/(name+'.torch.f32'))
    rows.append(dict(name=name,samples=len(x),source_kind='frozen real FLEURS' if name.startswith(('real','edge')) else 'numerical contract control',
                     input_sha256=digest(OUT/(name+'.input.f32')),reference_sha256=digest(OUT/(name+'.torch.f32'))))
wave.tofile(OUT/'fleurs_full.input.f32')
(OUT/'numerical_tests.json').write_text(json.dumps(dict(tests=rows,reference='Unmodified PyTorch exact checkpoint LLVCAudioStream'),indent=2),encoding='utf8')
print(json.dumps(dict(weights_bytes=manifest['weights_bytes'],tensors=len(tensors),tests=rows),indent=2),flush=True)