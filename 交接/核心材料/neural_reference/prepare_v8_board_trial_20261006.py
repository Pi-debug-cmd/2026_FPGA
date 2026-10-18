from pathlib import Path
import tarfile,json,hashlib
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';budget=base.parent/'board_budget_20261005'
helper=(native/'board_neural_fargan.sh').read_text(encoding='utf-8').replace('native_fargan_mapper_arm','native_fargan_v8_arm').replace('fargan_mapper_selected.f32','fargan_mapper_v8_selected.f32')
(native/'board_neural_fargan.sh').write_text(helper,encoding='utf-8',newline='\n')
bundle=native/'fargan_v8_trial_bundle_20261006.tar.gz';weight=budget/'fargan_mapper_expanded_v8/fargan_mapper_expanded_v8.f32'
with tarfile.open(bundle,'w:gz',compresslevel=9) as t:
    for p,name in [(native/'native_fargan_v8_arm','native_fargan_v8_arm'),(weight,'fargan_mapper_v8_selected.f32'),(native/'board_neural_fargan.sh','board_neural_fargan.sh'),(native/'fargan_live_watchdog.py','fargan_live_watchdog.py')]:t.add(p,arcname=name)
report=dict(bundle_bytes=bundle.stat().st_size,bundle_sha256=hashlib.sha256(bundle.read_bytes()).hexdigest(),weight_sha256=hashlib.sha256(weight.read_bytes()).hexdigest(),live_deployed=False,quality_accepted=False)
(native/'v8_trial_prepared.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
