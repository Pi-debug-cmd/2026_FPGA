from pathlib import Path
base=Path(__file__).resolve().parent
source=(base/'train_fargan_mapper_20261006.py').read_text(encoding='utf-8')
source=source.replace('import FeatureMapper,normalize_pitch,export_mapper','import PitchAwareMapper as FeatureMapper,pitch_aware_features as normalize_pitch,export_mapper')
source=source.replace("out=budget/'fargan_mapper_v1'","out=budget/'fargan_mapper_pitchaware'").replace('steps=1200','steps=3000').replace('checkpoint_step1200.pt','checkpoint_step3000.pt').replace('fargan_mapper_v1.f32','fargan_mapper_pitchaware.f32')
source=source.replace('yy=xx.clone()','yy=xx[:,:20].clone()')
old="model=FeatureMapper(mean,std).to(device);optimizer="
new="""parent=torch.load(budget/'fargan_mapper_v1/checkpoint_step1200.pt',map_location='cpu',weights_only=False)
mean[:20]=np.asarray(parent['mean']);std[:20]=np.asarray(parent['std'])
model=FeatureMapper(mean,std).to(device)
with torch.no_grad():
    state=model.state_dict()
    for name,value in parent['model'].items():
        if name in ['mean','std']:continue
        if name=='pre.weight':state[name][:,:20].copy_(value);state[name][:,20].zero_()
        else:state[name].copy_(value)
optimizer="""
assert old in source;source=source.replace(old,new)
source=source.replace('raw_waveform_bypass=False','source_raw_pitch_retained_as_network_feature=True,raw_waveform_bypass=False')
(base/'train_fargan_pitchaware_20261006.py').write_text(source,encoding='utf-8')
for name in ['evaluate_board_phonetic_naturalness_20261005.py','screen_board_phonetic_pilot_20261005.py']:
    p=base/name;s=p.read_text(encoding='utf-8')
    if "'fargan_mapper_pitchaware'" not in s:s=s.replace("'fargan_mapper_truncated']","'fargan_mapper_truncated','fargan_mapper_pitchaware']")
    p.write_text(s,encoding='utf-8')
print('PITCH_AWARE_TRAINING_PREPARED')
