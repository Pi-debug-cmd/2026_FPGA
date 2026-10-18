"""Separate C-port errors from the effect of its exported int8 weights."""
from run_rvc_pilot import settings
settings()
from pathlib import Path
import sys, json, numpy as np, torch
BASE=Path(r'D:\Tools_FPGA\workspace\voice_conversion_zynq7020')
NR=BASE/'neural_reference'; BUD=BASE/'board_budget_20261005'; DEP=BASE/'deploy_runtime'
sys.path.insert(0,str(NR/'LLVC'))
from train_reduced_20261007 import build_net
from llvc_online_stream import LLVCAudioStream

net=build_net(NR/'LLVC/experiments/llvc/config_reduced.json')
ck=torch.load(BUD/'reduced_student_v2/final.pt',map_location='cpu',weights_only=True)
net.load_state_dict(ck['model'],strict=True);net.eval()
x=np.fromfile(DEP/'test/input.bin',dtype='<f4')
def synth():
    stream=LLVCAudioStream(net)
    with torch.inference_mode(): chunks=stream.feed(x);chunks+=stream.finish()
    return np.concatenate(chunks).astype('<f4')
original=synth()

raw=(BUD/'llvc_deploy_model_reduced.bin').read_bytes()
hdr=np.frombuffer(raw,dtype='<u4',count=1024)
packed_off=int(hdr[10]);scale_off=int(hdr[9]);mpo=hdr[139:155];mso=hdr[155:171]
sd=net.state_dict();tl='mask_gen.decoder.tf_dec_layers.0'
weight_targets=[]
for i in range(6):weight_targets.append(sd[f'mask_gen.encoder.dcc_layers.dcc_{i}.layers.3.weight'])
for att in ('self_attn','multihead_attn'):
    ip=sd[f'{tl}.{att}.in_proj_weight']
    for q in range(3):weight_targets.append(ip[q*192:(q+1)*192])
    weight_targets.append(sd[f'{tl}.{att}.out_proj.weight'])
weight_targets += [sd[f'{tl}.linear1.weight'],sd[f'{tl}.linear2.weight']]
assert len(weight_targets)==16
weight_errors=[]
with torch.no_grad():
    for i,w in enumerate(weight_targets):
        oc,ic=w.shape[:2]
        packed=np.frombuffer(raw,dtype=np.uint8,count=ic*512,offset=packed_off+int(mpo[i])).reshape(ic,512)
        sw=np.frombuffer(raw,dtype='<f4',count=oc,offset=scale_off+int(mso[i]))
        deq=(packed[:,:oc].astype(np.int8).T*sw[:,None]).astype(np.float32).reshape(w.shape)
        weight_errors.append(float(np.max(np.abs(w.numpy()-deq))))
        w.copy_(torch.from_numpy(deq))
stage={}
block_index=[-1]
orig_forward=net.forward
def numbered_forward(*args,**kwargs):
    block_index[0]+=1
    return orig_forward(*args,**kwargs)
net.forward=numbered_forward
hooks=[]
def capture(name):
    def hook(_module,_inputs,output):
        if block_index[0]==22:
            tensor=output[0] if isinstance(output,tuple) else output
            stage[name]=tensor.detach().cpu().numpy().copy()
            if name.startswith('dcc_'):
                stage[name+'_input']=_inputs[0].detach().cpu().numpy().copy()
    return hook
for name,mod in [('base',net.in_conv),('encoder',net.mask_gen.encoder),('proj_e',net.mask_gen.proj_e2d_e),('proj_l',net.mask_gen.proj_e2d_l),('decoder',net.mask_gen.decoder),('d2e',net.mask_gen.proj_d2e)]:
    hooks.append(mod.register_forward_hook(capture(name)))
for i in range(6):
    hooks.append(net.mask_gen.encoder.dcc_layers[i].register_forward_hook(capture(f'dcc_{i}')))
for layer,name in [(0,'enc0_dw'),(2,'enc0_densein'),(3,'enc0_pw')]:
    hooks.append(net.mask_gen.encoder.dcc_layers[0].layers[layer].register_forward_hook(capture(name)))
def before_decoder_layer(_module,inputs):
    if block_index[0]==22:
        stage['tgt26']=inputs[0].detach().cpu().numpy().copy()
        stage['mem26']=inputs[1].detach().cpu().numpy().copy()
dl=net.mask_gen.decoder.tf_dec_layers[0]
hooks.append(dl.register_forward_pre_hook(before_decoder_layer))
for name,mod in [('q_after_self',dl.norm1),('kv_after_cross',dl.norm2),('attn_after_ffn',dl.norm3)]:
    hooks.append(mod.register_forward_hook(capture(name)))
w8=synth()
for hook in hooks:hook.remove()
net.forward=orig_forward
cfloat=np.fromfile(DEP/'review_float_20261008.bin',dtype='<f4')
cint8=np.fromfile(DEP/'review_int8_20261008.bin',dtype='<f4')
assert len(original)==len(w8)==len(cfloat)==len(cint8)
def score(a,b):return dict(correlation=float(np.corrcoef(a,b)[0,1]),rmse=float(np.sqrt(np.mean((a-b)**2))),rms_a=float(np.sqrt(np.mean(a*a))))
report=dict(samples=len(x),weight_max_abs_error=max(weight_errors),
    original_vs_w8=score(original,w8),c_float_vs_w8=score(cfloat,w8),
    c_float_vs_original=score(cfloat,original),c_int8_vs_w8=score(cint8,w8),
    same_4p32s_fixed_input=True,board_unchanged=True)
def stage_score(c,ref):
    c=c.reshape(-1);ref=ref.reshape(-1)
    return {'correlation':float(np.corrcoef(c,ref)[0,1]),'rmse':float(np.sqrt(np.mean((c-ref)**2))),'max_abs_error':float(np.max(np.abs(c-ref)))}
stage_report={}
for name,cfile,refname in [('base','dmp_base.bin','base'),('encoder','dmp_e_after_enc.bin','encoder'),('decoder','dmp_attn_after_ffn.bin','decoder'),('d2e','dmp_mout.bin','d2e')]:
    c=np.fromfile(DEP/cfile,dtype='<f4')
    ref=stage[refname]
    if ref.ndim==3:ref=ref[0].T
    if c.size==ref.size:stage_report[name]=stage_score(c,ref)
for i in range(6):
    name=f'dcc_{i}'
    residual=stage[name+'_input'][...,-13:]+stage[name]
    c=np.fromfile(DEP/f'dmp_enc_{i}.bin',dtype='<f4')
    stage_report[name]=stage_score(c,residual[0].T)
for name in ('enc0_din','enc0_dw','enc0_densein','enc0_pw'):
    ref=stage['dcc_0_input'] if name=='enc0_din' else stage[name]
    c=np.fromfile(DEP/f'dmp_{name}.bin',dtype='<f4')
    stage_report[name]=stage_score(c,ref[0].T)
for name in ('tgt26','mem26','q_after_self','kv_after_cross','attn_after_ffn'):
    c=np.fromfile(DEP/f'dmp_{name}.bin',dtype='<f4')
    ref=stage[name]
    stage_report[name]=stage_score(c,ref[0])
    if name in ('tgt26','mem26'):
        stage_report[name]['first_13']=stage_score(c.reshape(26,192)[:13],ref[0,:13])
        stage_report[name]['last_13']=stage_score(c.reshape(26,192)[13:],ref[0,13:])
        stage_report[name]['first_8_c']=c[:8].tolist()
        stage_report[name]['first_8_ref']=ref.reshape(-1)[:8].tolist()
        stage_report[name]['row13_8_c']=c.reshape(26,192)[13,:8].tolist()
        stage_report[name]['row13_8_ref']=ref[0,13,:8].tolist()
pe=net.mask_gen.decoder.pos_enc(torch.zeros(1,26,192)).numpy()[0]
for c_name,ref_name in [('mem26','proj_e'),('tgt26','proj_l')]:
    c=np.fromfile(DEP/f'dmp_{c_name}.bin',dtype='<f4').reshape(26,192)
    stage_report[ref_name+'_vs_c_raw']=stage_score(c[13:]-pe[13:],stage[ref_name][0].T)
report['stages_block22']=stage_report
p=BUD/'reduced_student_v2/review_w8_parity_20261008.json';p.write_text(json.dumps(report,indent=2))
print(json.dumps(report))
