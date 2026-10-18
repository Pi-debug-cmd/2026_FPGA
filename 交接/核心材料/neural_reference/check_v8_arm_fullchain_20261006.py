from pathlib import Path
import json,tarfile,numpy as np,soundfile as sf,hashlib
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';out=base.parent/'board_budget_20261005/fargan_v8_fullchain_verification';archive=native/'fargan_v8_file_results.tar.gz'
with tarfile.open(archive) as t:
    for name in ['fargan_v8_B.arm.pcm','fargan_v8_file_stats.json']:
        member=t.getmember(name);assert member.isfile();(out/name).write_bytes(t.extractfile(member).read())
actual=np.fromfile(out/'fargan_v8_B.arm.pcm',dtype='<i2').astype('float64')/32768;gold=np.fromfile(out/'pipeline.pcm',dtype='<i2').astype('float64')/32768
assert len(actual)==len(gold)==69120 and np.isfinite(actual).all()
stats=json.loads((out/'fargan_v8_file_stats.json').read_text());assert stats['frames']==432 and stats['wall_elapsed_ms']<4320 and stats['mean_compute_ms']<10
sf.write(out/'E_板端计算_同一句中文.wav',actual,16000,subtype='FLOAT')
report=dict(complete=True,board_throughput_verified_short_file=True,arm_stats=stats,arm_rms=float(np.sqrt(np.mean(actual**2))),host_rms=float(np.sqrt(np.mean(gold**2))),arm_peak=float(np.max(np.abs(actual))),arm_clip_count=int(np.count_nonzero(np.abs(actual)>=32767/32768)),waveform_nrmse=float(np.linalg.norm(actual-gold)/np.linalg.norm(gold)),bit_exact_claim=False,quality_accepted=False,board_live_verified=False,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
assert report['arm_clip_count']==0
(out/'arm_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
