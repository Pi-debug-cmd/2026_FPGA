from pathlib import Path
import tarfile,hashlib,json
base=Path(__file__).resolve().parent;ref=base/'Opus_FARGAN_reference/opus-main'
expected='a5177ec6fb7d15058e99e57029746100121f68e4890b1467d4094aa336b6013e'
archive=base/('opus_data-'+expected+'.tar.gz');assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
records=[]
with tarfile.open(archive,'r:gz') as tar:
 for item in tar.getmembers():
  name=Path(item.name)
  if item.isfile() and ((name.suffix in ['.c','.h']) or 'fargan' in item.name):
   assert not name.is_absolute() and '..' not in name.parts
   p=ref/name;p.parent.mkdir(parents=True,exist_ok=True);data=tar.extractfile(item).read();p.write_bytes(data);records.append(dict(path=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
native=base.parent/'board_support/native_llvc_20261005'
(native/'fargan_assets.json').write_text(json.dumps(dict(archive_sha256=expected,repo_url='https://github.com/xiph/opus',source_zip_sha256=hashlib.sha256((base/'opus_fargan_main_20261006.zip').read_bytes()).hexdigest(),extracted=records),indent=2),encoding='utf-8')
print('FARGAN_ASSETS',[(Path(r['path']).name,r['bytes']) for r in records if 'fargan' in r['path']],flush=True)
