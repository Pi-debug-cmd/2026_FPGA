from pathlib import Path
base=Path(__file__).resolve().parent
source=(base/'train_fargan_perceptual_20261006.py').read_text(encoding='utf-8')
source=source.replace('Fixed180-step','Fixed240-step').replace("OUT=budget/'fargan_mapper_perceptual'","OUT=budget/'fargan_mapper_truncated'")
source=source.replace('vocoder=FrozenFargan().cuda()','vocoder=FrozenFargan(truncate_frames=8).cuda()')
source=source.replace('steps=180','steps=240').replace('checkpoint_step180.pt','checkpoint_step240.pt').replace('fargan_mapper_perceptual.f32','fargan_mapper_truncated.f32')
source=source.replace('training_vocoder_surrogate_not_bit_exact=True','training_gradient_truncation_frames=8,training_vocoder_surrogate_not_bit_exact=True')
(base/'train_fargan_truncated_20261006.py').write_text(source,encoding='utf-8')
for name in ['evaluate_board_phonetic_naturalness_20261005.py','screen_board_phonetic_pilot_20261005.py']:
    p=base/name;s=p.read_text(encoding='utf-8')
    if "'fargan_mapper_perceptual'" not in s:s=s.replace("'fargan_cmn_direct']","'fargan_cmn_direct','fargan_mapper_perceptual','fargan_mapper_truncated']")
    p.write_text(s,encoding='utf-8')
print('TRUNCATED_TRAINING_PREPARED')
