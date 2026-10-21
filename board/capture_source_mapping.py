"""Finite source enrollment/holdout capture; --check never opens audio."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import signal
import subprocess
import struct
import time
import wave
from pack_registration_audio import pack_native


def write_cue(path):
    rate = 44100
    # Let the playback path open before two audible 600 ms pulses; 10 ms fades.
    count = int(3.5 * rate)
    samples = [0] * count
    for start in [int(rate), int(2.2 * rate)]:
        length = int(.6 * rate)
        for i in range(length):
            samples[start + i] = int(6553 * min(1., i / 441., (length - 1 - i) / 441.) *
                                     math.sin(2 * math.pi * 880 * i / rate))
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        stream.writeframes(struct.pack('<%dh' % count, *samples))


def idle():
    states = {name: Path('/proc/asound/card0', name, 'sub0/status').read_text().strip()
              for name in ['pcm1c', 'pcm0p']}
    if any(value != 'closed' for value in states.values()):
        raise RuntimeError('AUDIO_BUSY: ' + json.dumps(states))
    return states


def capture(speaker, role, seconds, cue_only=False):
    idle()
    run = Path('/tmp/codex_source_mapping_20261015') / (speaker + '_' + role + '_' + str(time.monotonic_ns()))
    run.mkdir(parents=True)
    state = run / 'mixer_before.state'
    saved, child = False, None
    record = {'speaker': speaker, 'role': role, 'seconds': seconds, 'directory': str(run),
              'cue_only': cue_only, 'cue_audibility_confirmed': False}
    try:
        subprocess.run(['alsactl', '-f', str(state), 'store', '0'], check=True, timeout=10)
        saved = True
        controls = [('Left Input Mixer Boost', 'on'), ('Right Boost Mixer RINPUT1', 'on'),
                    ('Right Input Mixer Boost', 'on'), ('Left Boost Mixer LINPUT1', 'on'),
                    ('Left Input Boost Mixer LINPUT1', '0'), ('Capture', '31,31', 'cap')]
        with (run / 'mixer_setup.log').open('wb') as log:
            for control in controls:
                subprocess.run(['amixer', 'sset', *control], stdout=log, stderr=log, check=True, timeout=10)
            subprocess.run(['amixer', 'cset', 'name=ADC Data Output Select', '1'],
                           stdout=log, stderr=log, check=True, timeout=10)
            for control in [('Left Output Mixer PCM', 'on'), ('Right Output Mixer PCM', 'on'),
                            ('Headphone Playback ZC', 'on'), ('Headphone', '105,105'), ('Playback', '230,230')]:
                subprocess.run(['amixer', 'sset', *control], stdout=log, stderr=log, check=True, timeout=10)
        cue = run / 'start_cue.wav'
        write_cue(cue)
        print('CUE_START: two tones, ' + ('no recording' if cue_only else 'speak after playback ends'), flush=True)
        with (run / 'cue_playback.log').open('wb') as log:
            child = subprocess.Popen(['aplay', '-v', '-D', 'default', str(cue)], stdout=log, stderr=log)
            time.sleep(.5)
            snapshot = {}
            for path in ['/proc/asound/card0/pcm0p/sub0/hw_params',
                         '/sys/kernel/debug/regmap/0-001a/registers',
                         '/sys/kernel/debug/clk/clk_summary']:
                try:
                    snapshot[path] = Path(path).read_text()
                except OSError as exc:
                    snapshot[path] = str(exc)
            (run / 'cue_active.json').write_text(json.dumps(snapshot, indent=2))
            if child.wait(timeout=10):
                raise RuntimeError('Cue player failed; capture not started')
        if 'underrun' in (run / 'cue_playback.log').read_text().lower():
            raise RuntimeError('Cue playback underrun; capture not started')
        # Playback has closed before capture opens; keep the tone out of enrollment.
        time.sleep(.15)
        record['start_cue'] = {'file_duration_s': 3.5, 'tone_count': 2, 'tone_duration_s': .6,
                               'frequency_hz': 880,
                               'playback_completed_before_capture': True}
        if cue_only:
            return
        print('CAPTURE_START speaker=%s role=%s seconds=%d' % (speaker, role, seconds), flush=True)
        with (run / 'capture.log').open('wb') as log:
            child = subprocess.Popen(['arecord', '-q', '-D', 'hw:0,1', '-t', 'raw', '-f', 'S24_LE',
                                      '-r', '32000', '-c', '2', '--period-size=512', '--buffer-size=4096',
                                      '-d', str(seconds), str(run / 'capture.raw')], stdout=log, stderr=log)
            code = child.wait(timeout=seconds + 10)
        record['capture_exit'] = code
        if code or 'overrun' in (run / 'capture.log').read_text().lower():
            raise RuntimeError('Capture failed or overran')
        if (run / 'capture.raw').stat().st_size != seconds * 32000 * 8:
            raise RuntimeError('Incomplete native capture')
        raw = (run / 'capture.raw').read_bytes()
        wav, clipped = pack_native(raw)
        packed = gzip.compress(wav, compresslevel=9, mtime=0)
        (run / 'capture.wav.gz').write_bytes(packed)
        record.update({'native_clip_fraction': clipped, 'raw_sha256': hashlib.sha256(raw).hexdigest(),
                       'wav_sha256': hashlib.sha256(wav).hexdigest(),
                       'gzip_sha256': hashlib.sha256(packed).hexdigest()})
        if clipped:
            raise RuntimeError('Native capture has near-full-scale samples; do not register')
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=3)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=3)
        if saved:
            with (run / 'mixer_restore.log').open('wb') as log:
                record['restore_exit'] = subprocess.run(['alsactl', '-f', str(state), 'restore', '0'],
                                                        stdout=log, stderr=log, timeout=10).returncode
        record['pcm_after'] = idle()
        (run / 'capture_manifest.json').write_text(json.dumps(record, indent=2))
        print(json.dumps(record), flush=True)
        if saved and record['restore_exit']:
            raise RuntimeError('Mixer restore failed')


def interrupted(signum, frame):
    raise SystemExit(128 + signum)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--run', action='store_true')
    action.add_argument('--cue-only', action='store_true')
    parser.add_argument('--speaker', default='speaker01')
    parser.add_argument('--role', choices=['calibration', 'train1', 'train2', 'train3',
                                           'validation', 'holdout'], default='calibration')
    parser.add_argument('--seconds', type=int, default=20, choices=range(10, 31))
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_]{1,32}', args.speaker):
        parser.error('Invalid speaker ID')
    if args.check:
        print(json.dumps({'pcm': idle(), 'cpu_online': Path('/sys/devices/system/cpu/online').read_text().strip()}))
    else:
        for number in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP]:
            signal.signal(number, interrupted)
        capture(args.speaker, args.role, args.seconds, args.cue_only)


if __name__ == '__main__':
    main()
