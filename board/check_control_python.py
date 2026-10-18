"""Read-only module and script-syntax preflight on the minimal factory Python."""
from pathlib import Path
import sys

failed = []
for name in ['array', 'fcntl', 'signal', 'subprocess', 'errno', 'struct', 'pathlib', 'json', 'hashlib', 'time']:
    try:
        __import__(name)
        print('MODULE_OK', name)
    except ImportError as exc:
        failed.append(name)
        print('MODULE_MISSING', name, str(exc))
for name in ['load_pitch_candidate.py', 'verify_dma_control_v2.py']:
    path = Path(sys.argv[1]) / name
    compile(path.read_text(), str(path), 'exec')
    print('SYNTAX_OK', name)
raise SystemExit(bool(failed))
