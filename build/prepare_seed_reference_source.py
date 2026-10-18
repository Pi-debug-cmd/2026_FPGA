"""Fetch/inspect pinned reference source only; never execute its setup scripts."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
original = json.loads((ROOT / '交接/核心材料/neural_reference/seed_source_manifest.json').read_text(encoding='utf-8'))
base = ROOT / 'build/generated/seed_reference_20261015'
base.mkdir(exist_ok=True)
archive = base / 'source.zip'
expected = original['source']['sha256']
if not archive.exists():
    temporary = archive.with_suffix('.part')
    with urllib.request.urlopen(original['source']['url'], timeout=45) as response, temporary.open('wb') as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
        raise ValueError('Pinned source SHA mismatch')
    temporary.replace(archive)
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise ValueError('Cached source SHA mismatch')
destination = base / 'source'
destination.mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as package:
    for member in package.infolist():
        target = (destination / member.filename).resolve()
        if not target.is_relative_to(destination.resolve()) or (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError('Unsafe archive member')
    package.extractall(destination)
record = {'repository': original['repository'], 'revision': original['revision'],
          'source_sha256': expected, 'source_bytes': archive.stat().st_size,
          'output': str(destination), 'upstream_scripts_executed': False,
          'weights_downloaded': False, 'board_accessed': False}
(ROOT / 'report/seed_reference_source_20261015.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record, indent=2))
