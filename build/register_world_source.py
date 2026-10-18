"""Generate a conversion configuration; optional file preview never plays audio."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'build/generated/world_deps'))
from src.reference.world_registration import register, convert_file
from src.reference.audio_io import write_pcm16, file_sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--target-manifest', type=Path, default=ROOT / 'data/profiles/target.json')
    parser.add_argument('--analysis-gain', type=float, default=1.)
    parser.add_argument('--test-input', type=Path)
    parser.add_argument('--preview', type=Path)
    args = parser.parse_args()
    if bool(args.test_input) != bool(args.preview):
        parser.error('--test-input and --preview must be supplied together')
    if args.test_input and (args.test_input.resolve() == args.source.resolve() or
                            args.output.resolve() == args.test_input.resolve()):
        parser.error('Enrollment, evaluation and configuration files must differ')
    if args.preview and args.preview.resolve() in [p.resolve() for p in
            [args.source, args.output, args.test_input, args.target_manifest]]:
        parser.error('Preview must not overwrite inputs or configuration')
    configuration = register(args.source, args.target_manifest, ROOT, args.output, args.analysis_gain)
    record = {'configuration': str(args.output), 'configuration_sha256': file_sha256(args.output),
              'speaker_identity_accepted': False, 'realtime_accepted': False}
    if args.test_input:
        result = convert_file(args.test_input, configuration)
        peak = float(np.max(np.abs(result)))
        gain = min(1., .9 / max(peak, 1e-12))
        write_pcm16(args.preview, result * gain)
        record.update({'evaluation_input_sha256': file_sha256(args.test_input),
                       'preview_sha256': file_sha256(args.preview), 'raw_peak': peak,
                       'raw_clip_samples': int(np.sum(np.abs(result) >= 1)), 'archive_gain': gain})
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
