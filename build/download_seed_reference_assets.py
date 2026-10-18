"""Download pinned public reference weights with range/size/SHA checks."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
base = ROOT / 'build/generated/seed_reference_20261015/assets'
base.mkdir(exist_ok=True)
plan = json.loads((ROOT / 'report/seed_reference_asset_plan_20261015.json').read_text(encoding='utf-8'))


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while data := stream.read(1024 * 1024):
            digest.update(data)
    return digest.hexdigest()


def fetch(job):
    repository, item = job
    directory = base / repository['repository'].replace('/', '__')
    directory.mkdir(exist_ok=True)
    path = directory / item['name']
    expected = item['sha256']
    if path.exists():
        actual = sha(path)
        if path.stat().st_size != item['size'] or (expected and actual != expected):
            raise ValueError('Cached asset mismatch: ' + str(path))
        return dict(item, path=str(path), actual_sha256=actual, repository=repository['repository'])
    temporary = path.with_suffix(path.suffix + '.part')
    size, step = item['size'], 32 * 1024 * 1024
    if size > 100 * 1024 * 1024:
        pieces = directory / (item['name'] + '.ranges')
        pieces.mkdir(exist_ok=True)
        def segment(index):
            first, last = index * step, min(size - 1, (index + 1) * step - 1)
            piece = pieces / ('%04d.bin' % index)
            if piece.exists() and piece.stat().st_size == last - first + 1:
                return piece
            for attempt in range(3):
                try:
                    url = item['url'] + '?download=true&segment=' + str(index)
                    request = urllib.request.Request(url, headers={'Range': 'bytes=%d-%d' % (first, last)})
                    with urllib.request.urlopen(request, timeout=45) as response:
                        if response.status != 206 or response.headers.get('Content-Range') != 'bytes %d-%d/%d' % (first, last, size):
                            raise ValueError('Unexpected range response')
                        pending = piece.with_suffix('.part')
                        with pending.open('wb') as output:
                            while data := response.read(1024 * 1024):
                                output.write(data)
                    if pending.stat().st_size != last - first + 1:
                        raise ValueError('Short segment')
                    pending.replace(piece)
                    print('RANGE_OK', item['name'], index + 1, '/', (size + step - 1) // step, flush=True)
                    return piece
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            ready = list(pool.map(segment, range((size + step - 1) // step)))
        with temporary.open('wb') as output:
            for piece in ready:
                with piece.open('rb') as source:
                    while data := source.read(1024 * 1024):
                        output.write(data)
    else:
        with urllib.request.urlopen(item['url'], timeout=45) as response, temporary.open('wb') as output:
            while data := response.read(1024 * 1024):
                output.write(data)
    actual = sha(temporary)
    if temporary.stat().st_size != size or (expected and actual != expected):
        raise ValueError('Final asset size/SHA mismatch: ' + item['name'])
    temporary.replace(path)
    print('ASSET_VERIFIED', repository['repository'], item['name'], flush=True)
    return dict(item, path=str(path), actual_sha256=actual, repository=repository['repository'])


jobs = [(repository, item) for repository in plan['repositories'] for item in repository['files']]
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures = [pool.submit(fetch, job) for job in jobs]
    for future in concurrent.futures.as_completed(futures):
        results.append(future.result())
        (ROOT / 'report/seed_reference_assets_20261015.json').write_text(json.dumps({'complete': len(results) == len(jobs), 'files': results}, indent=2), encoding='utf-8')
print('ALL_ASSETS_VERIFIED', len(results), flush=True)
