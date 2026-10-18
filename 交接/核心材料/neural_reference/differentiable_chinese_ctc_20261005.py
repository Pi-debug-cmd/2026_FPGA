"""Frozen exact ONNX-operator replay for offline Chinese CTC guidance.
After use as training loss, this recognizer is NOT an independent approval judge.
No recognizer or frontend is deployed to7020. No expected text during eval.
"""
from pathlib import Path
import sys,json,hashlib
BASE=Path(__file__).resolve().parent;sys.path.insert(0,str(BASE/'onnx_gradient_lib'))
import onnx,numpy as np,torch
import torch.nn as nn
import torch.nn.functional as F
MODEL=BASE/'sensevoice_pinyin_assets/robinsonphan__sensevoice-small-zh-pinyin-dual-ctc/sensevoice_dual/outputs/sensevoice_dual.onnx'
class FrozenChineseCTC(nn.Module):
 def __init__(self):
  super().__init__();graph=onnx.load(str(MODEL)).graph;self.names={};self.constants={};self.nodes=[]
  for i,v in enumerate(graph.initializer):
   name='weight_'+str(i);self.register_buffer(name,torch.from_numpy(onnx.numpy_helper.to_array(v).copy()));self.names[v.name]=name
  for n in graph.node:
   attrs={a.name:onnx.helper.get_attribute_value(a) for a in n.attribute}
   if n.op_type=='Constant':self.constants[n.output[0]]=torch.from_numpy(onnx.numpy_helper.to_array(attrs['value']).copy())
   else:
    if n.op_type=='ConstantOfShape':attrs['value']=torch.from_numpy(onnx.numpy_helper.to_array(attrs['value']).copy())
    self.nodes.append((n.op_type,list(n.input),list(n.output),attrs))
  self.outputs=[v.name for v in graph.output];self.refs={}
  for _,ins,_,_ in self.nodes:
   for k in ins:
    if k:self.refs[k]=self.refs.get(k,0)+1
  self.model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest()
 def forward(self,features,lengths):
  values={k:getattr(self,v) for k,v in self.names.items()};values.update(self.constants);values.update(feats=features,feats_lens=lengths)
  refs=self.refs.copy()
  def ints(x):return [int(z) for z in x.reshape(-1).tolist()]
  def together(xs):
   device=next((x.device for x in xs if x.is_cuda),xs[0].device)
   return [x.to(device) if x.device!=device else x for x in xs]
  dtype={1:torch.float32,6:torch.int32,7:torch.int64,9:torch.bool,10:torch.float16,11:torch.float64}
  for op,ins,outs,a in self.nodes:
   xs=[values[k] for k in ins if k]
   try:
    if op=='Shape':y=torch.tensor(xs[0].shape,dtype=torch.int64)[a.get('start',0):a.get('end',xs[0].ndim)]
    elif op=='Gather':
     axis=a.get('axis',0);axis%=xs[0].ndim;idx=xs[1].long().to(xs[0].device);idx=torch.where(idx<0,idx+xs[0].shape[axis],idx)
     y=torch.index_select(xs[0],axis,idx.reshape(-1)).reshape(tuple(xs[0].shape[:axis])+tuple(idx.shape)+tuple(xs[0].shape[axis+1:]))
    elif op=='Cast':y=xs[0].to(dtype[a['to']])
    elif op=='Range':y=torch.arange(xs[0].item(),xs[1].item(),xs[2].item(),dtype=xs[0].dtype,device=xs[0].device)
    elif op=='Unsqueeze':
     y=xs[0];axes=a.get('axes',ints(xs[1]) if len(xs)>1 else [])
     final_dim=y.ndim+len(axes)
     for axis in sorted(z%final_dim for z in axes):y=y.unsqueeze(axis)
    elif op=='Squeeze':
     y=xs[0];axes=a.get('axes',ints(xs[1]) if len(xs)>1 else None)
     if axes is None:y=y.squeeze()
     else:
      for axis in sorted((z%y.ndim for z in axes),reverse=True):y=y.squeeze(axis)
    elif op in ['Add','Sub','Mul','Div','Pow','Less','Equal']:
     aa,bb=together(xs);y={'Add':torch.add,'Sub':torch.sub,'Mul':torch.mul,'Div':torch.div,'Pow':torch.pow,'Less':torch.lt,'Equal':torch.eq}[op](aa,bb)
    elif op in ['Neg','Exp','Sin','Cos','Sqrt','Relu']:
     y={'Neg':torch.neg,'Exp':torch.exp,'Sin':torch.sin,'Cos':torch.cos,'Sqrt':torch.sqrt,'Relu':F.relu}[op](xs[0])
    elif op=='Concat':y=torch.cat(together(xs),dim=a['axis'])
    elif op=='Reshape':
     shape=ints(xs[1]);shape=[xs[0].shape[i] if z==0 and not a.get('allowzero',0) else z for i,z in enumerate(shape)];y=xs[0].reshape(shape)
    elif op in ['ReduceMean','ReduceSum']:
     axes=a.get('axes',ints(xs[1]) if len(xs)>1 else list(range(xs[0].ndim)))
     y=(xs[0].mean if op=='ReduceMean' else xs[0].sum)(dim=tuple(axes),keepdim=bool(a.get('keepdims',1)))
    elif op=='MatMul':aa,bb=together(xs);y=aa@bb
    elif op=='Split':
     sizes=ints(xs[1]) if len(xs)>1 else a.get('split');axis=a.get('axis',0)
     y=list(torch.split(xs[0],sizes,dim=axis)) if sizes is not None else list(torch.chunk(xs[0],len(outs),dim=axis))
    elif op=='Transpose':y=xs[0].permute(*a.get('perm',list(range(xs[0].ndim))[::-1]))
    elif op=='ConstantOfShape':
     v=a['value'];y=torch.full(ints(xs[0]),v.item(),dtype=v.dtype,device=features.device)
    elif op=='Slice':
     starts,ends=ints(xs[1]),ints(xs[2]);axes=ints(xs[3]) if len(xs)>3 else list(range(len(starts)));steps=ints(xs[4]) if len(xs)>4 else [1]*len(starts)
     y=xs[0]
     for start,end,axis,step in zip(starts,ends,axes,steps):
      first,last,stride=slice(start,end,step).indices(y.shape[axis]);indices=torch.arange(first,last,stride,dtype=torch.long,device=y.device);y=torch.index_select(y,axis,indices)
    elif op=='Pad':
     pads=ints(xs[1]);rank=len(pads)//2;pad=[v for i in range(rank-1,-1,-1) for v in [pads[i],pads[i+rank]]];mode=a.get('mode',b'constant').decode();assert mode=='constant';y=F.pad(xs[0],pad,value=float(xs[2].item()) if len(xs)>2 else 0)
    elif op=='Conv':
     assert xs[0].ndim==3;pad=a.get('pads',[0,0]);assert pad[0]==pad[1];xx,ww=together(xs[:2]);bias=xs[2].to(xx.device) if len(xs)>2 else None
     y=F.conv1d(xx,ww,bias,stride=a.get('strides',[1])[0],padding=pad[0],dilation=a.get('dilations',[1])[0],groups=a.get('group',1))
    elif op=='Where':xx,aa,bb=together(xs);y=torch.where(xx,aa,bb)
    elif op=='Softmax':y=F.softmax(xs[0],dim=a.get('axis',-1))
    elif op=='LogSoftmax':y=F.log_softmax(xs[0],dim=a.get('axis',-1))
    else:raise NotImplementedError(op)
   except Exception as e:raise RuntimeError(f'{op} {outs} shapes={[tuple(x.shape) for x in xs]} attrs={a}: {e}') from e
   if len(outs)==1:values[outs[0]]=y
   else:
    assert len(y)==len(outs)
    for k,v in zip(outs,y):values[k]=v
   for k in ins:
    if not k:continue
    refs[k]-=1
    if refs[k]==0 and k not in self.outputs:values.pop(k,None)
  return tuple(values[k] for k in self.outputs)
