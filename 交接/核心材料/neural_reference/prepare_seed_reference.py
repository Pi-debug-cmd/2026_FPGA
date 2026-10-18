"""Download pinned source and prepare a PC-only quality reference."""
from pathlib import Path
import hashlib,json,zipfile
from download_cross_evaluators import download
BASE=Path(__file__).resolve().parent
REF='51383efd921027683c89e5348211d93ff12ac2a8'
ROOT=BASE/'Seed-VC'
data=download('https://codeload.github.com/Plachtaa/seed-vc/zip/'+REF,BASE/'seed_vc_source.zip')
if not ROOT.exists():
    with zipfile.ZipFile(data['path']) as archive:
        for member in archive.infolist():
            target=(BASE/member.filename).resolve()
            if not target.is_relative_to(BASE): raise RuntimeError('Unsafe archive path')
        archive.extractall(BASE)
    (BASE/('seed-vc-'+REF)).rename(ROOT)
(BASE/'seed_source_manifest.json').write_text(json.dumps(dict(repository='Plachtaa/seed-vc',revision=REF,source=data,root=str(ROOT)),indent=2),encoding='utf-8')
print('Source ready: '+str(ROOT))
