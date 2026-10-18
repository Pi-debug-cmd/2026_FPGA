from pathlib import Path
import json,tarfile,numpy as np
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';out=base.parent/'board_budget_20261005/fargan_probe'
with tarfile.open(native/'fargan_B.results.tar.gz','r:gz') as t:
 for name in ['fargan_B.arm_features.f32','fargan_B.arm.pcm','fargan_B.features.json','fargan_B.synthesis.json']:(out/name).write_bytes(t.extractfile(name).read())
a=np.fromfile(out/'fixed_B.features.f32',dtype=np.float32).reshape(-1,20);b=np.fromfile(out/'fargan_B.arm_features.f32',dtype=np.float32).reshape(-1,20)
assert a.shape==b.shape and np.isfinite(b).all()
r=dict(feature_normalized_rmse=float(np.sqrt(np.sum((a-b).astype('float64')**2)/np.sum(a.astype('float64')**2))),max_feature_abs=float(np.max(np.abs(a-b))),feature_per_dimension_max=np.max(np.abs(a-b),axis=0).tolist(),frames=len(a),analysis=json.loads((out/'fargan_B.features.json').read_text()),synthesis=json.loads((out/'fargan_B.synthesis.json').read_text()),actual_arm_execution=True,baseline_restored_after_file_benchmark=True,live_conversion_not_started=True,quality_accepted=False)
r['total_mean_frame_ms']=r['analysis']['mean_frame_ms']+r['synthesis']['mean_frame_ms']
(out/'arm_evidence.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r),flush=True)
