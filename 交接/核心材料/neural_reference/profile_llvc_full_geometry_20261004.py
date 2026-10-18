from pathlib import Path
import ast,sys,math,json,zipfile,hashlib,time
from run_rvc_pilot import settings
settings()
import torch,torch.nn as nn
BASE=Path(__file__).resolve().parent;SOURCE=BASE/'LLVC';OUT=Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/board_budget_20261004/full_llvc_geometry');OUT.mkdir(exist_ok=True)
wheel=BASE/'dependency_source_audit/speechbrain-0.5.16-py3-none-any.whl'
with zipfile.ZipFile(wheel) as z:pos_source=z.read('speechbrain/lobes/models/transformer/Transformer.py').decode()
pos_tree=ast.parse(pos_source);cls=next(n for n in pos_tree.body if isinstance(n,ast.ClassDef) and n.name=='PositionalEncoding')
ns=dict(torch=torch,nn=nn,math=math);exec(compile(ast.Module(body=[cls],type_ignores=[]),str(wheel)+'::PositionalEncoding','exec'),ns)
# Exact primary class from the pinned wheel; no substitute positional math.
model_source=(SOURCE/'model.py').read_text();tree=ast.parse(model_source)
tree.body=[n for n in tree.body if not(isinstance(n,ast.ImportFrom) and n.module=='speechbrain.lobes.models.transformer.Transformer')]
sys.path.insert(0,str(SOURCE));scope={'PositionalEncoding':ns['PositionalEncoding'],'__name__':'llvc_geometry_audit'}
exec(compile(tree,str(SOURCE/'model.py'),'exec'),scope)
config=json.loads((SOURCE/'experiments/llvc/config.json').read_text());torch.manual_seed(20261004);torch.set_num_threads(4)
net=scope['Net'](**config['model_params']).eval();rows=[];norms=[]
def hook(name):
 def count(m,args,result):
  x=args[0];out=result[0] if isinstance(result,tuple) else result;mac=0;kind=type(m).__name__;details={}
  if isinstance(m,nn.Conv1d):mac=out.numel()*(m.in_channels//m.groups)*m.kernel_size[0]
  elif isinstance(m,nn.ConvTranspose1d):mac=x.numel()*(m.out_channels//m.groups)*m.kernel_size[0];details['cropped_boundary_products_included_upper_bound']=True
  elif isinstance(m,nn.Linear):mac=out.numel()*m.in_features
  elif isinstance(m,nn.MultiheadAttention):
   q,k,v=args[:3];b,q_len,d=q.shape;k_len=k.shape[1]
   projections=q.numel()*d+k.numel()*d+v.numel()*d+q.numel()*d
   dot_products=2*b*q_len*k_len*d;mac=projections+dot_products
   details=dict(query_shape=list(q.shape),key_shape=list(k.shape),value_shape=list(v.shape),projection_macs=projections,attention_dot_macs=dot_products,softmax_elements=b*m.num_heads*q_len*k_len)
  elif isinstance(m,nn.LayerNorm):norms.append(dict(name=name,elements=x.numel(),normalized_shape=list(m.normalized_shape)));return
  if mac:rows.append(dict(name=name,kind=kind,macs=int(mac),input_shape=list(x.shape),output_shape=list(out.shape),details=details))
 return count
handles=[]
for name,m in net.named_modules():
 if isinstance(m,(nn.Conv1d,nn.ConvTranspose1d,nn.Linear,nn.MultiheadAttention,nn.LayerNorm)):handles.append(m.register_forward_hook(hook(name)))
x=torch.randn(1,1,208);start=time.perf_counter()
with torch.inference_mode():y=net(x)
assert tuple(y.shape)==tuple(x.shape) and torch.isfinite(y).all()
assert not any(r['name'].endswith('out_proj') for r in rows), 'Avoid counting MHA output projection twice'
for h in handles:h.remove()
buffers=net.init_buffers(1,'cpu');pre=net.convnet_pre.init_ctx_buf(1,'cpu')
def tensors(obj):
 if torch.is_tensor(obj):return [obj]
 if isinstance(obj,(tuple,list)):return sum((tensors(v) for v in obj),[])
 if isinstance(obj,dict):return sum((tensors(v) for v in obj.values()),[])
 return []
all_buffers=tensors(buffers)+tensors(pre)
static_label=sum(r['macs'] for r in rows if r['name'].startswith('label_embedding'))
pointwise=sum(r['macs'] for r in rows if r['name'].startswith('mask_gen.encoder') and r['kind']=='Conv1d' and r['input_shape'][1]==r['output_shape'][1] and r['macs']==13*512*512)
params=sum(p.numel() for p in net.parameters());total=sum(r['macs'] for r in rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
data=dict(status='untrained_original_geometry_profiled',primary_llvc_revision='1627c5d358cf9bb2b92b0ccc513d8b36807c923d',model_source_sha256=sha(SOURCE/'model.py'),config_source_sha256=sha(SOURCE/'experiments/llvc/config.json'),positional_class_source='Unmodified AST of PositionalEncoding from speechbrain0.5.16 wheel; full unrelated package not imported or installed.',dependency_wheel_sha256=sha(wheel),untrained_weights=True,target_voice_model=False,source_audio='Deterministic random208samples for geometry only',sample_rate=16000,chunk_audio_ms=13,parameter_count=params,fp32_parameter_bytes=params*4,ideal_int8_weight_bytes=params,int8_runtime_or_quality_validated=False,context_buffers_fp32_bytes=sum(t.numel()*t.element_size() for t in all_buffers),context_shapes=[list(t.shape) for t in all_buffers],tracked_macs_per_chunk_upper_bound=total,static_label_macs_per_call=static_label,static_label_can_cache_without_source_dependency=True,encoder_pointwise_macs=pointwise,remaining_tracked_macs=total-pointwise-static_label,tracked_gmac_per_second=(total-static_label)/.013/1e9,operations_not_in_mac_count=['LayerNorm mean/variance/reciprocal sqrt','softmax exponential/division','activation/tanh/sigmoid','elementwise products/residual additions','state moves','audio IO/resampling','DDR stalls'],layer_norms=norms,operators=rows,board_deployed=False,trained=False,measured_wall_time_not_board_performance=True)
(OUT/'geometry_profile.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:data[k] for k in ['parameter_count','fp32_parameter_bytes','context_buffers_fp32_bytes','tracked_macs_per_chunk_upper_bound','encoder_pointwise_macs','remaining_tracked_macs','tracked_gmac_per_second']},ensure_ascii=True))
