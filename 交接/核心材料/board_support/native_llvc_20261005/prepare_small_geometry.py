"""Structured initialization and measured deployment geometry, not accepted VC.

Keep all 8 dilation stages and target label, choose paired encoder channels and
equal channel counts per attention head. Cropping is NOT quality preservation.
Never use held-out sources to update weights or choose a checkpoint.
"""
from pathlib import Path
import sys,json,struct,hashlib,copy
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'neural_reference'
sys.path.insert(0,str(BASE))
from load_llvc_audit_model import load_model,digest
from llvc_online_stream import LLVCAudioStream
import torch,numpy as np
torch.set_num_threads(4)

def build_small(enc_dim=128):
    parent,config=load_model(True)
    checkpoint=ROOT.parents[1]/'board_budget_20261004/phasefree_student_pilot/checkpoint_step20.pt'
    parent.load_state_dict(torch.load(checkpoint,map_location='cpu',weights_only=True)['model'],strict=True)
    cfg=copy.deepcopy(config['model_params']);cfg['enc_dim']=enc_dim;cfg['dec_dim']=enc_dim//2
    small=type(parent)(**cfg).eval()
    d=cfg['dec_dim'];per_head=d//8
    # Even coverage of original head coordinates, preserve grouped input pairs.
    di=torch.tensor([h*32+k*32//per_head for h in range(8) for k in range(per_head)])
    ei=torch.stack([2*di,2*di+1],dim=1).reshape(-1)
    original=parent.state_dict();s={};shapes={}
    for name,want in small.state_dict().items():
        v=original[name]
        if name.startswith('convnet_pre.') or name.startswith('label_embedding.0.') or name.startswith('label_embedding.1.'):
            got=v
        elif name.startswith(('in_conv.','out_conv.','label_embedding.3.','label_embedding.4.')):
            got=v[ei]
        elif name.startswith('mask_gen.encoder.'):
            got=v[ei]
            if '.layers.3.weight' in name:got=got[:,ei]
        elif name.startswith(('mask_gen.proj_e2d_e.','mask_gen.proj_e2d_l.')):got=v[di]
        elif name.startswith('mask_gen.proj_d2e.'):got=v[ei]
        elif name.endswith('pos_enc.pe'):got=v[...,di]
        elif '.in_proj_weight' in name:
            got=torch.cat([v[j*256:(j+1)*256][di][:,di] for j in range(3)],dim=0)
        elif '.in_proj_bias' in name:got=torch.cat([v[j*256:(j+1)*256][di] for j in range(3)],dim=0)
        elif '.out_proj.weight' in name:got=v[di][:,di]
        elif '.out_proj.bias' in name or '.norm' in name:got=v[di]
        elif '.linear1.weight' in name:got=v[ei][:,di]
        elif '.linear1.bias' in name:got=v[ei]
        elif '.linear2.weight' in name:got=v[di][:,ei]
        elif '.linear2.bias' in name:got=v[di]
        else:raise RuntimeError('unhandled '+name)
        assert got.shape==want.shape,(name,got.shape,want.shape)
        s[name]=got.contiguous().clone();shapes[name]=list(got.shape)
    small.load_state_dict(s,strict=True)
    return small,cfg,dict(encoder_indices=ei.tolist(),decoder_indices=di.tolist(),shapes=shapes,
                          original_checkpoint_sha256=digest(checkpoint))

def export(model,path):
    with torch.inference_mode():label=model.label_embedding(torch.zeros(1,1))[0].numpy()
    values={k:v.detach().cpu().float().contiguous().numpy() for k,v in model.state_dict().items()}
    values['derived.label']=label
    with path.open('wb') as f:
        f.write(b'LLVCF001');f.write(struct.pack('<I',len(values)))
        for name,a in values.items():
            b=name.encode();f.write(struct.pack('<II',len(b),a.ndim));f.write(b)
            f.write(struct.pack('<'+'I'*a.ndim,*a.shape));f.write(a.astype('<f4').tobytes())

def stream(model,x):
    adapter=LLVCAudioStream(model);parts=[]
    for start in range(0,len(x),256):parts.extend(adapter.feed(x[start:start+256]))
    parts.extend(adapter.finish());return np.concatenate(parts) if parts else np.empty(0,np.float32)

def main():
    for enc in [128,96]:
        model,cfg,selection=build_small(enc);name='small'+str(enc)
        export(model,ROOT/(name+'_initial.f32'))
        checkpoint=ROOT/(name+'_initial.pt')
        torch.save(dict(model=model.state_dict(),config=cfg,selection=selection,
                        initialized_only=True,trained=False,quality_accepted=False),checkpoint)
        for case in ['silence_416','tone_1000','edge_209','real_16000']:
            x=np.fromfile(ROOT/(case+'.input.f32'),dtype='<f4');y=stream(model,x)
            assert len(y)==len(x) and np.isfinite(y).all()
            y.tofile(ROOT/(case+'.'+name+'_initial.torch.f32'))
        cpp=(ROOT/'native_llvc_fast.cpp').read_text(encoding='utf-8')
        cpp=cpp.replace('E=512, D=256','E='+str(enc)+', D='+str(enc//2))
        start=cpp.index('    V mha(');end=cpp.index('    V decoder(',start)
        mha=cpp[start:end]
        mha=mha.replace('std::sqrt(32.f)','std::sqrt(float(D/8))').replace('head*32','head*(D/8)')
        mha=mha.replace('],32)*scale','],D/8)*scale').replace('c<32','c<D/8')
        cpp=cpp[:start]+mha+cpp[end:]
        (ROOT/('native_llvc_'+name+'.cpp')).write_text(cpp,encoding='utf-8')
        manifest=dict(config=cfg,selection=selection,parameters=sum(p.numel() for p in model.parameters()),
                      weights_bytes=(ROOT/(name+'_initial.f32')).stat().st_size,
                      weights_sha256=digest(ROOT/(name+'_initial.f32')),initialized_only=True,
                      target_quality_accepted=False,real_time_not_yet_measured=True,
                      source_speaker_enrollment=False,target_track9_used_for_training=False)
        (ROOT/(name+'_manifest.json')).write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print(name,manifest['parameters'],manifest['weights_bytes'],flush=True)
if __name__=='__main__':main()
