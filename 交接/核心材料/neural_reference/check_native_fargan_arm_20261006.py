from pathlib import Path
import tarfile,json,subprocess,numpy as np,hashlib
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';budget=base.parent/'board_budget_20261005';out=budget/'fargan_native_stream_verification'
archive=native/'native_fargan_mapper_results.tar.gz'
with tarfile.open(archive) as t:
    for name in ['native_fargan_mapper_B.pcm','native_fargan_mapper_timing.json']:
        member=t.getmember(name);assert member.isfile();(out/name).write_bytes(t.extractfile(member).read())
with (budget/'fargan_probe/fixed_B.input.pcm').open('rb') as f,(out/'fixed_B.host.pcm').open('wb') as o:
    subprocess.run([str(native/'native_fargan_mapper_host.exe'),str(budget/'fargan_mapper_v1/fargan_mapper_v1.f32'),str(out/'fixed_B.host.json')],stdin=f,stdout=o,check=True)
host=np.fromfile(out/'fixed_B.host.pcm',dtype='<i2').astype('float64')/32768;arm=np.fromfile(out/'native_fargan_mapper_B.pcm',dtype='<i2').astype('float64')/32768
assert len(arm)==len(host)==69120 and np.isfinite(arm).all()
def envelope(x):
    frames=np.lib.stride_tricks.sliding_window_view(x,512)[::160]*np.hanning(512)
    return np.mean(np.abs(np.fft.rfft(frames))**2,axis=0)
a=envelope(arm);b=envelope(host);floor=max(float(np.max(b))*1e-6,1e-12)
report=dict(complete=True,board_timing=json.loads((out/'native_fargan_mapper_timing.json').read_text()),samples=len(arm),arm_rms=float(np.sqrt(np.mean(arm**2))),host_rms=float(np.sqrt(np.mean(host**2))),arm_peak=float(np.max(np.abs(arm))),arm_clip_count=int(np.count_nonzero(np.abs(arm)>=32767/32768)),waveform_nrmse=float(np.linalg.norm(arm-host)/np.linalg.norm(host)),mean_log_envelope_abs_difference=float(np.mean(np.abs(np.log(a+floor)-np.log(b+floor)))),output_bit_exact_claim=False,quality_accepted=False,board_live_deployed=False,archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
(out/'arm_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
