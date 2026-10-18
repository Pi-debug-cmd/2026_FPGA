"""Three targeted controls: self-identity diagnostic and precision mismatch."""
from pathlib import Path
from types import SimpleNamespace
import time
import personalize_seed_teacher as personal
import torch,numpy as np,soundfile as sf
OUT=Path('D:/总进度/目标人物分析/内容保持模块隔离_2026-10-04')
read=personal.read;save=personal.save;sha=personal.sha
def main():
 src=read(OUT/'source_manifest.json')[0];original=read(OUT/'evaluation_items.json')
 baseline=next(r for r in original if r['label']=='personal_both_fleurs1906')
 experiment=read(OUT/'experiment_before_inference.json')
 target=Path(experiment['target_path']);ckpt=experiment['personal_checkpoint']['path']
 personal.pinned_loaders();import inference
 kwargs=dict(diffusion_steps=30,length_adjust=1.,inference_cfg_rate=.3,f0_condition=False,auto_f0_adjust=False,
  semi_tone_shift=0,checkpoint=ckpt,config=str(personal.OUT/'personal_strong_config.yml'),fp16=True)
 loaded=inference.load_models(SimpleNamespace(**kwargs));inference.load_models=lambda _:loaded
 encoders=[c.cell_contents for c in loaded[1].__closure__ if isinstance(c.cell_contents,torch.nn.Module)]
 assert len(encoders)==1;encoder=encoders[0];assert next(encoder.parameters()).dtype==torch.float16
 cases=[dict(label='self_identity_diagnostic_fp16',semantic_fp32=False,generator_fp32=False,target=src['prepared'],target_conversion=False),
  dict(label='target_voice_semantic_fp32',semantic_fp32=True,generator_fp32=False,target=str(target),target_conversion=True),
  dict(label='target_voice_all_fp32',semantic_fp32=True,generator_fp32=True,target=str(target),target_conversion=True)]
 save(OUT/'precision_experiment_before_inference.json',dict(cases=cases,source=src,checkpoint_sha256=sha(ckpt),
  rationale='Fine-tuning used FP32 frozen Whisper, original inference uses FP16. Self-reference tests source-to-source generator with no target voice transfer.',
  fixed_steps=30,fixed_cfg=.3,seed=20261003,no_source_registration_for_operational_system=True,
  self_identity_output_not_voice_conversion_evidence=True,no_training=True))
 records=[]
 for case in cases:
  encoder.float() if case['semantic_fp32'] else encoder.half()
  inference.fp16=not case['generator_fp32']
  folder=OUT/case['label'];folder.mkdir(exist_ok=True);torch.manual_seed(20261003);torch.cuda.synchronize();start=time.perf_counter()
  inference.main(SimpleNamespace(**kwargs,source=src['prepared'],target=case['target'],output=str(folder)))
  torch.cuda.synchronize();elapsed=time.perf_counter()-start
  p=folder/f'vc_{Path(src["prepared"]).stem}_{Path(case["target"]).stem}_1.0_30_0.3.wav'
  x,sr=sf.read(p,dtype='float32');assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6
  records.append(dict(label=case['label'],group=case['label'],path=str(p),sha256=sha(p),expected_text=src['text'],
   source_path=src['path'],source_sha256=src['sha256'],test_name='fleurs1906',
   semantic_fp32=case['semantic_fp32'],generator_fp32=case['generator_fp32'],
   target_conversion=case['target_conversion'],reference_path=case['target'],reference_sha256=sha(case['target']),
   seconds=len(x)/sr,inference_seconds=elapsed,peak=float(np.max(np.abs(x))),
   clipped_fraction=float(np.mean(np.abs(x)>=.999)),subjective_acceptance=False,board_deployed=False,causal_streaming=False))
  save(OUT/'precision_items.json',records);print(case['label'],elapsed,flush=True)
 print('STYLE PRECISION CONTROLS COMPLETE',flush=True)
if __name__=='__main__':main()
