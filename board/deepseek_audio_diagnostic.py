"""One authorized Deepseek hardware-format diagnostic, with mixer restoration."""
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--capture', action='store_true')
    args = ap.parse_args()
    root = Path('/tmp/codex_deepseek_ds01')
    report = {'diagnostic_only': True, 'pl_enabled': False, 'capture': args.capture}
    state = root / 'mixer_before.state'
    def call(command, timeout=15):
        p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        report.setdefault('commands', []).append({'command': command, 'exit': p.returncode, 'output': p.stdout.decode(errors='replace')})
        p.check_returncode()
        return p
    def play(path):
        return call(['aplay', '-D', 'default', '-t', 'raw', '-f', 'S24_LE', '-r', '32000', '-c', '2', str(path)])
    saved = False
    try:
        call(['alsactl', '-f', str(state), 'store', '0']); saved = True
        call(['amixer', 'sget', 'Headphone'])
        call(['amixer', 'sget', 'Playback'])
        for name, seconds, frequency in [('tone', .7, 660), ('cue', .3, 880)]:
            count = round(32000 * seconds)
            data = bytearray()
            for i in range(count):
                fade = min(1, i / 320, (count - 1 - i) / 320)
                v = round(.025 * 8388607 * fade * math.sin(2 * math.pi * frequency * i / 32000))
                data.extend(struct.pack('<ii', v, v))
            (root / (name + '.raw')).write_bytes(data)
        play(root / 'tone.raw')
        # First use the approved validation recording, not newly captured speech.
        if (root / 'native_output.raw').exists():
            source = array.array('i'); source.frombytes((root / 'native_output.raw').read_bytes())
            quiet = array.array('i', (int(v * .3) for v in source))
            (root / 'playback_quiet.raw').write_bytes(quiet.tobytes())
            play(root / 'playback_quiet.raw')
        if args.capture:
            play(root / 'cue.raw'); time.sleep(.15)
            call(['arecord', '-D', 'hw:0,1', '-t', 'raw', '-f', 'S24_LE', '-r', '32000', '-c', '2', '-d', '8', str(root / 'mic.raw')], timeout=12)
            words = array.array('I'); words.frombytes((root / 'mic.raw').read_bytes())
            channels=[]
            for ch in (0, 1):
                values=[((v & 0xffffff) ^ 0x800000) - 0x800000 for v in words[ch::2]]
                channels.append({'peak': max(map(abs,values))/8388608, 'rms': math.sqrt(sum(v*v for v in values)/len(values))/8388608, 'clip_fraction': sum(abs(v)>=32760*256 for v in values)/len(values)})
            report['capture_channels']=channels
            report['capture_sha256']=hashlib.sha256((root / 'mic.raw').read_bytes()).hexdigest()
            cmd=[str(root / 'vc_s24fix_arm'), '8', 'native_s24', '200', '--model', str(root / 'model.blob'), '--preset', 'live', '--stream', '300']
            before=time.monotonic()
            with (root / 'mic.raw').open('rb') as inp, (root / 'mic_output.raw').open('wb') as out, (root / 'mic_conversion.log').open('wb') as log:
                p=subprocess.run(cmd, stdin=inp, stdout=out, stderr=log, timeout=40)
            report['conversion']={'command':cmd,'exit':p.returncode,'wall_s':time.monotonic()-before,'output_bytes':(root/'mic_output.raw').stat().st_size,'telemetry':(root/'mic_conversion.log').read_text()}
            p.check_returncode()
            # Store converted voice locally; quality gates have not been established.
    finally:
        if saved:
            try: call(['alsactl', '-f', str(state), 'restore', '0'])
            except Exception as exc: report['restore_error']=str(exc)
        (root / 'audio_report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
