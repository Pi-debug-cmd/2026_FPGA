from pathlib import Path
import json,tarfile,numpy as np,hashlib
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';out=base.parent/'board_budget_20261005/fargan_mapper_c_verification'
archive=native/'fargan_mapper_probe_results.tar.gz'
with tarfile.open(archive) as tar:
    for name in ['fargan_mapper_probe_output.f32','fargan_mapper_probe_stats.json']:
        member=tar.getmember(name);assert member.isfile();(out/name).write_bytes(tar.extractfile(member).read())
gold=np.fromfile(out/'reference.f32',dtype='float32');actual=np.fromfile(out/'fargan_mapper_probe_output.f32',dtype='float32')
report=dict(nrmse=float(np.linalg.norm(actual-gold)/np.linalg.norm(gold)),max_abs=float(np.max(np.abs(actual-gold))),board_timing=json.loads((out/'fargan_mapper_probe_stats.json').read_text()),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),arm_verified=False,quality_accepted=False,live_deployed=False)
assert report['nrmse']<1e-5 and report['max_abs']<1e-4,report
report['arm_verified']=True;(out/'arm_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
