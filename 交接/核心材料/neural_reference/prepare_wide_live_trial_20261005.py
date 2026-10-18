from train_board_student_20261005 import BASE,read,stream
from prepare_wide_shallow_geometry import build_wide_shallow
from pathlib import Path
import torch,numpy as np,json,hashlib,tarfile,shutil
torch.set_num_threads(4)
out=BASE.parent/'board_budget_20261005/wide192_shallow2_target_anchor';native=BASE.parent/'board_support/native_llvc_20261005'
decision=json.loads((out/'decision.json').read_text(encoding='utf-8'));assert decision['complete'] and decision['steps']==800
weight=out/'wide192_shallow2_target_anchor.f32';assert hashlib.sha256(weight.read_bytes()).hexdigest()==decision['weights_sha256']
selected=native/'wide192_shallow2_target_anchor_selected.f32';shutil.copyfile(weight,selected)
model,cfg,_=build_wide_shallow();model.load_state_dict(torch.load(out/'checkpoint_step800.pt',map_location='cpu',weights_only=True)['model'],strict=True);model.eval()
source=Path('D:/总进度/目标人物分析/原台词_模型直接转换检查_2026-10-04/B_普通男声输入.wav')
x=read(source);assert len(x)==69120;x.tofile(native/'fixed_text_B_wide.input.f32');y=stream(model,x);y.tofile(native/'fixed_text_B_wide.torch.f32')
assert len(y)==len(x) and np.isfinite(y).all() and np.max(np.abs(y))<.9
helper=native/'board_neural_wide192.sh';text=helper.read_text()
text=text.replace('export ALSA_CONFIG_PATH="$DIR/asound_neural.conf"','export ALSA_CONFIG_PATH="$DIR/asound_neural.conf"\nexport LLVC_INPUT_GAIN=1\nexport LLVC_OUTPUT_GAIN=1')
helper.write_text(text,newline='\n')
bundle=native/'wide192_live_trial.tar.gz'
files=['native_llvc_wide192_shallow2_meter_arm','wide192_shallow2_target_anchor_selected.f32','board_neural_wide192.sh','fixed_text_B_wide.input.f32']
with tarfile.open(bundle,'w:gz') as tar:
 for name in files:tar.add(native/name,arcname=name)
report=dict(model_sha256=decision['weights_sha256'],bundle_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),bundle_bytes=bundle.stat().st_size,source_path=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_is_synthetic_male=True,source_text='我的校园很美，走近大门就能看见宽阔的操场。',samples=len(x),model_output_rms=float(np.sqrt(np.mean(y*y))),model_output_peak=float(np.max(np.abs(y))),original_signal_mixed_into_output=False,source_enrollment=False,model_quality_accepted=False,live_board_started=False)
(native/'wide192_live_preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('WIDE_LIVE_TRIAL_PREPARED',report['bundle_bytes'],report['bundle_sha256'],flush=True)
