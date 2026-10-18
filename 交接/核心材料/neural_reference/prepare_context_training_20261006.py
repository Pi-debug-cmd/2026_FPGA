from pathlib import Path
base=Path(__file__).resolve().parent
source=(base/'train_fargan_dynamics_20261006.py').read_text(encoding='utf-8')
source=source.replace('from fargan_mapper_v8_20261006 import MapperV8,pitch_aware_features','from fargan_mapper_context_20261006 import MapperContext,context_features')
source=source.replace("out=budget/'fargan_v8_dynamics'","out=budget/'fargan_context_v9'")
source=source.replace("parent=budget/'fargan_mapper_expanded_v8/checkpoint_step5000.pt'","parent=budget/'fargan_v8_dynamics/checkpoint_step4000.pt'")
source=source.replace("model=MapperV8(cp['mean'],cp['std']);model.load_state_dict(cp['model']);model=model.cuda()",'model=None')
source=source.replace('pitch_aware_features(', 'context_features(')
needle='length=400;warm=16;steps=4000;history=[];start=time.monotonic()'
assert source.count(needle)==1
source=source.replace(needle,'''all_x=torch.cat([pair[0] for pair in data+anchors]).cpu().numpy()
mean=all_x.mean(0);std=np.maximum(all_x.std(0),.1)
mean[:21]=np.asarray(cp['mean']);std[:21]=np.asarray(cp['std'])
model=MapperContext(mean,std)
state=model.state_dict()
for key,value in cp['model'].items():
    if key in ('mean','std'):continue
    if key=='pre.weight':
        state[key][:,:21]=value;state[key][:,21:]=0
    else:state[key]=value
model.load_state_dict(state);model=model.cuda()
length=400;warm=16;steps=10000;history=[];start=time.monotonic()''')
source=source.replace("out/'checkpoint_step4000.pt'","out/'checkpoint_step10000.pt'")
source=source.replace("mean=cp['mean'],std=cp['std']","mean=mean.tolist(),std=std.tolist()")
source=source.replace("out/'fargan_v8_dynamics.f32'","out/'fargan_context_v9.f32'")
source=source.replace("DYNAMICS_READY","CONTEXT_READY").replace("DYNAMICS_DONE","CONTEXT_DONE").replace("'DYNAMICS'","'CONTEXT'")
source=source.replace('Fixed4000-step V8 fine-tune','Fixed10000-step context-input fine-tune').replace('Same FMAP008 architecture and native runtime budget.','FMAP009: extra18 automatic causal context features, same128x2 GRU. Native budget must be measured.')
(base/'train_fargan_context_20261006.py').write_text(source,encoding='utf-8')
print('CONTEXT_TRAINER_PREPARED')
