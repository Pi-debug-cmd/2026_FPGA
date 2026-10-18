"""Native stream must match exact extract -> map -> synth file chain."""
from pathlib import Path
import numpy as np,json,subprocess,hashlib,argparse
parser=argparse.ArgumentParser();parser.add_argument('--candidate',choices=['v1','pitchaware','perceptual','truncated'],default='v1');args=parser.parse_args()
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';budget=base.parent/'board_budget_20261005';out=budget/('fargan_native_stream_verification' if args.candidate=='v1' else 'fargan_native_stream_'+args.candidate);out.mkdir(exist_ok=True)
manifest=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'));row=next(r for r in manifest['files'] if r['split']=='validation')
raw=Path(row['source_features']).with_name(Path(row['source_features']).name.replace('.features.f32','.pcm'))
weight=budget/('fargan_mapper_'+args.candidate)/('fargan_mapper_'+args.candidate+'.f32')
subprocess.run([str(native/'fargan_mapper_probe_host.exe'),str(weight),row['source_features'],str(out/'features.f32'),str(out/'mapper.json')],check=True)
subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(out/'features.f32'),str(out/'file.pcm'),str(out/'file.json')],check=True)
with raw.open('rb') as f,(out/'stream.pcm').open('wb') as o:
    subprocess.run([str(native/'native_fargan_mapper_host.exe'),str(weight),str(out/'stream.json')],stdin=f,stdout=o,check=True)
actual=np.fromfile(out/'stream.pcm',dtype='<i2');gold=np.fromfile(out/'file.pcm',dtype='<i2')
assert actual.shape==gold.shape and np.array_equal(actual,gold)
report=dict(complete=True,stream_file_chain_bit_exact=True,samples=len(actual),sha256=hashlib.sha256((out/'stream.pcm').read_bytes()).hexdigest(),stats=json.loads((out/'stream.json').read_text()),quality_accepted=False,board_live_deployed=False)
(out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
