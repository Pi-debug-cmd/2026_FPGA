"""Exact operator replay of fixed WeSpeaker ONNX for auxiliary training loss.

No weights are changed. Once used as a loss, this evaluator is NOT an
independent identity judge and cannot grant acceptance. Human hearing remains
required. Numeric and gradient checks precede use.
"""
from pathlib import Path
import sys,json,hashlib
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'onnx_gradient_lib'))
import onnx,numpy as np,torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio.compliance.kaldi as kaldi
MODEL=BASE/'cross_evaluators/cnceleb_resnet34_LM.onnx'

class FrozenSpeaker(nn.Module):
    def __init__(self):
        super().__init__()
        assert hashlib.sha256(MODEL.read_bytes()).hexdigest()=='e7584940aeac8d5512d875e58ce6c09ba4ddad65d8128e1dac0d93aadd087ebb'
        graph=onnx.load(MODEL).graph;self.nodes=[];self.names={}
        for i,value in enumerate(graph.initializer):
            name='weight_'+str(i);self.register_buffer(name,torch.from_numpy(onnx.numpy_helper.to_array(value).copy()));self.names[value.name]=name
        for i,node in enumerate(graph.node):
            attrs={a.name:onnx.helper.get_attribute_value(a) for a in node.attribute}
            if node.op_type=='Constant':
                name='constant_'+str(i);self.register_buffer(name,torch.from_numpy(onnx.numpy_helper.to_array(attrs['value']).copy()));self.names[node.output[0]]=name
            else:self.nodes.append((node.op_type,list(node.input),node.output[0],attrs))
        self.output=graph.output[0].name
    def forward(self,features):
        values={k:getattr(self,v) for k,v in self.names.items()};values['feats']=features
        for op,inputs,output,a in self.nodes:
            xs=[values[k] for k in inputs if k]
            if op=='Conv':
                pads=a.get('pads',[0,0,0,0]);assert pads[:2]==pads[2:],pads
                y=F.conv2d(xs[0],xs[1],xs[2] if len(xs)>2 else None,stride=tuple(a.get('strides',[1,1])),padding=tuple(pads[:2]),dilation=tuple(a.get('dilations',[1,1])),groups=a.get('group',1))
            elif op=='Relu':y=F.relu(xs[0])
            elif op=='Add':y=xs[0]+xs[1]
            elif op=='Sub':y=xs[0]-xs[1]
            elif op=='Mul':y=xs[0]*xs[1]
            elif op=='Div':y=xs[0]/xs[1]
            elif op=='Sqrt':y=xs[0].sqrt()
            elif op=='Transpose':y=xs[0].permute(*a['perm'])
            elif op=='Unsqueeze':
                y=xs[0]
                for axis in sorted(a.get('axes',xs[1].tolist() if len(xs)>1 else [])):y=y.unsqueeze(axis)
            elif op=='ReduceMean':y=xs[0].mean(dim=tuple(a.get('axes',range(xs[0].ndim))),keepdim=bool(a.get('keepdims',1)))
            elif op=='Shape':y=torch.tensor(xs[0].shape,dtype=torch.int64,device=xs[0].device)
            elif op=='Gather':
                axis=a.get('axis',0);assert axis==0 and xs[0].ndim==1
                indices=xs[1];y=xs[0][indices]
            elif op=='ReduceProd':
                assert 'axes' not in a;y=xs[0].prod()
                if a.get('keepdims',1):y=y.reshape([1]*xs[0].ndim)
            elif op=='Cast':
                assert a['to']==1;y=xs[0].float()
            elif op=='Flatten':y=xs[0].flatten(start_dim=a.get('axis',1))
            elif op=='Concat':y=torch.cat(xs,dim=a['axis'])
            elif op=='Gemm':
                left=xs[0].T if a.get('transA',0) else xs[0];right=xs[1].T if a.get('transB',0) else xs[1]
                y=a.get('alpha',1)*(left@right)+a.get('beta',1)*xs[2]
            else:raise NotImplementedError(op)
            values[output]=y
        return values[self.output]
    def embedding(self,wave):
        if wave.ndim==1:wave=wave[None]
        features=[]
        for x in wave:
            x=x*.04/x.square().mean().sqrt().clamp_min(1e-8)
            f=kaldi.fbank((x*32768)[None],num_mel_bins=80,frame_length=25,frame_shift=10,sample_frequency=16000,window_type='hamming',dither=0.)
            features.append(f-f.mean(dim=0))
        return F.normalize(self(torch.stack(features)),dim=-1)

def main():
    from run_rvc_pilot import settings
    settings()
    import soundfile as sf,onnxruntime as ort
    from scipy.signal import resample_poly
    path=Path('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav')
    from math import gcd
    x,sr=sf.read(path,dtype='float32')
    if x.ndim==2:x=x.mean(axis=1)
    if sr!=16000:x=resample_poly(x,16000//gcd(sr,16000),sr//gcd(sr,16000)).astype('float32')
    torch.set_num_threads(4);model=FrozenSpeaker().eval();wave=torch.tensor(x)
    normalized=wave*.04/wave.square().mean().sqrt()
    f=kaldi.fbank((normalized*32768)[None],num_mel_bins=80,frame_length=25,frame_shift=10,sample_frequency=16000,window_type='hamming',dither=0.)
    f=(f-f.mean(dim=0))[None]
    session=ort.InferenceSession(str(MODEL),providers=['CPUExecutionProvider'])
    gold=session.run(None,{'feats':f.numpy()})[0]
    with torch.no_grad():actual=model(f).numpy()
    nrmse=float(np.linalg.norm(actual-gold)/np.linalg.norm(gold));assert nrmse<1e-4,nrmse
    live=torch.tensor(x[:24000],device='cuda',requires_grad=True);model=model.to('cuda')
    loss=(model.embedding(live)-torch.tensor(gold,device='cuda')).square().mean();loss.backward()
    assert torch.isfinite(live.grad).all() and live.grad.abs().max()>0
    report=dict(onnx_torch_nrmse=nrmse,waveform_gradient_finite=True,model_weights_unchanged=True,
                training_use_retires_independent_identity_evaluator=True,speech_quality_accepted=False)
    out=BASE.parent/'board_budget_20261005/differentiable_speaker_verification.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))
if __name__=='__main__':main()
