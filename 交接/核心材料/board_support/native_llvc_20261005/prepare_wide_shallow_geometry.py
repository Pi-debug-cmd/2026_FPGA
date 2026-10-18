"""Wider waveform basis, fewer encoder stages; measured board experiment only."""
from prepare_small_geometry import build_small,export,stream,ROOT
from pathlib import Path
import json,torch,numpy as np,copy,hashlib

def build_wide_shallow():
 parent,cfg,selection=build_small(192)
 cfg=copy.deepcopy(cfg);cfg['num_enc_layers']=2
 model=type(parent)(**cfg).eval()
 state=parent.state_dict();model.load_state_dict({name:state[name] for name in model.state_dict()},strict=True)
 selection=dict(selection,encoder_stages_retained=[0,1],encoder_history_samples=6*16,output_basis_channels=192,decoder_channels=96,initialization_does_not_preserve_voice_quality=True)
 return model,cfg,selection

def main():
 model,cfg,selection=build_wide_shallow();export(model,ROOT/'wide192_shallow2_initial.f32')
 torch.save(dict(model=model.state_dict(),config=cfg,selection=selection,trained=False),ROOT/'wide192_shallow2_initial.pt')
 for case in ['real_16000','tone_1000','fleurs_full']:
  x=np.fromfile(ROOT/(case+'.input.f32'),dtype='<f4');y=stream(model,x);assert len(x)==len(y) and np.isfinite(y).all();y.tofile(ROOT/(case+'.wide192_shallow2_initial.torch.f32'))
 source=(ROOT/'native_llvc_small128_vattn.cpp').read_text()
 source=source.replace('E=128, D=64','E=192, D=96')
 source=source.replace('if(n!=148)','if(n!=100)')
 source=source.replace('enc_pos[8]','enc_pos[2]').replace('V enc[8]','V enc[2]')
 source=source.replace('for(int i=0;i<8;i++)','for(int i=0;i<2;i++)').replace('for(int layer=0;layer<8;layer++)','for(int layer=0;layer<2;layer++)')
 source=source.replace('native_fp32_vector_attention_candidate','native_fp32_wide_shallow_candidate')
 (ROOT/'native_llvc_wide192_shallow2.cpp').write_text(source)
 report=dict(config=cfg,selection=selection,parameters=sum(p.numel() for p in model.parameters()),weights_bytes=(ROOT/'wide192_shallow2_initial.f32').stat().st_size,weights_sha256=hashlib.sha256((ROOT/'wide192_shallow2_initial.f32').read_bytes()).hexdigest(),trained=False,quality_accepted=False,board_realtime_verified=False,source_enrollment=False)
 (ROOT/'wide192_shallow2_manifest.json').write_text(json.dumps(report,indent=2));print('WIDE_SHALLOW_PREPARED',report['parameters'],flush=True)
if __name__=='__main__':main()
