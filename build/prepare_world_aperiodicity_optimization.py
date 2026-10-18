"""Separate D4C math experiment; preserve the pinned upstream source."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root / 'build/generated/world_source_v035/pyworld-0.3.5/lib/World/src/d4c.cpp'
destination = root / 'build/generated/world_budget/optimized_aperiodicity'
original = source.read_text(encoding='utf-8')
before = 'aperiodicity[i] = pow(10.0, aperiodicity[i] / 20.0);'
after = 'aperiodicity[i] = exp((aperiodicity[i] / 20.0) * 2.302585092994045684);'
if original.count(before) != 1:
    raise RuntimeError('Pinned D4C conversion statement changed')
destination.mkdir(exist_ok=True)
output = destination / 'd4c.cpp'
output.write_text(original.replace(before, after), encoding='utf-8')
(destination / 'manifest.json').write_text(json.dumps({
    'original_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'modified_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
    'change': 'pow(10,x) to exp(x*ln(10)) in the aperiodicity conversion only',
    'limitation': 'Numerical experiment; floating-point equivalence and speed require verification.'
}, indent=2) + '\n')
print(output)
