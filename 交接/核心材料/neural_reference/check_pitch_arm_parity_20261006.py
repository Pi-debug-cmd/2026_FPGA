from pathlib import Path
import numpy as np,json,tarfile
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';out=base.parent/'board_budget_20261005/pitch_stream_contract'
with tarfile.open(native/'pitch_benchmark.results.tar.gz','r:gz') as t:
 for name in ['pitch_benchmark.output.f32','pitch_benchmark.status.json']:
  (out/name).write_bytes(t.extractfile(name).read())
host=np.fromfile(out/'fixed_B_normalized.f32',dtype=np.float32);arm=np.fromfile(out/'pitch_benchmark.output.f32',dtype=np.float32)
assert len(host)==len(arm) and np.isfinite(arm).all()
error=float(np.sqrt(np.sum((host-arm).astype('float64')**2)/np.sum(host.astype('float64')**2)))
report=dict(normalized_rmse=error,max_abs=float(np.max(np.abs(host-arm))),samples=len(host),actual_arm_execution=True,board_benchmark_under_existing_neural_live_load=True,board=json.loads((out/'pitch_benchmark.status.json').read_text()))
(out/'arm_parity.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report),flush=True)
