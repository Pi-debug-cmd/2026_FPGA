"""Temporary WORLD PL swap with a verified factory recovery and binding journal.

--prepare is silent and never changes FPGA/driver/audio state.
--load/--restore require per-round operator readiness before invoking this script.
No boot partition or persistent startup configuration is modified.
"""
import argparse
import array
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

FACTORY_SHA = '16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61'
FACTORY_SERVICE = os.environ.get('WORLD_FACTORY_SERVICE', '/etc/init.d/world-voice')
AUDIO = [('platform', 'xlnx_snd_card', 'xlnx_snd_card.0.auto'),
         ('platform', 'xlnx_formatter_pcm', '43c40000.audio_formatter'),
         ('platform', 'xlnx_i2s', '43c60000.i2s_transmitter'),
         ('platform', 'xlnx_i2s', '43c50000.i2s_receiver'),
         ('platform', 'dglnt-dynclk', '43c20000.axi_dynclk'),
         ('i2c', 'wm8960', '0-001a')]


def run(*cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=45)
    if r.returncode:
        raise RuntimeError('%r: %s' % (cmd, r.stdout))
    return r.stdout


def binding(bus, driver, device, action):
    root = Path('/sys/bus') / bus / 'drivers' / driver
    target = root / device
    if target.exists() == (action == 'bind'):
        return
    try:
        (root / action).write_text(device)
    except OSError:
        if target.exists() != (action == 'bind'):
            raise
    if target.exists() != (action == 'bind'):
        raise RuntimeError('%s %s did not reach state' % (device, action))


def prepare(base):
    raw = Path('/boot/bit/zynq7020.bit').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FACTORY_SHA
    offset = 2 + int.from_bytes(raw[:2], 'big')
    assert raw[offset:offset+2] == b'\x00\x01'
    offset += 2
    while True:
        tag = raw[offset:offset+1]
        assert tag in (b'a', b'b', b'c', b'd', b'e')
        width = 4 if tag == b'e' else 2
        size = int.from_bytes(raw[offset+1:offset+1+width], 'big')
        offset += 1 + width
        payload = raw[offset:offset+size]
        offset += size
        assert len(payload) == size
        if tag == b'e':
            break
    assert offset == len(raw) and len(payload) % 4 == 0
    words = array.array('I', payload)
    assert words.itemsize == 4
    words.byteswap()
    swapped = words.tobytes()
    assert bytes.fromhex('665599aa') in swapped[:256]
    base.mkdir(parents=True, exist_ok=True)
    target = base / 'factory_restore.bin'
    target.write_bytes(swapped)
    record = {'factory_bit_sha256': FACTORY_SHA,
              'restore_sha256': hashlib.sha256(swapped).hexdigest(),
              'restore_bytes': len(swapped)}
    (base / 'recovery.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=Path, required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--load', type=Path)
    mode.add_argument('--restore', action='store_true')
    p.add_argument('--sha256')
    p.add_argument('--keep-stopped', action='store_true',
                   help='Restore FPGA/drivers without the audible v23 startup cue')
    args = p.parse_args()
    base = args.base
    if args.prepare:
        prepare(base)
        return
    recovery = json.loads((base/'recovery.json').read_text())
    restore = base/'factory_restore.bin'
    assert hashlib.sha256(restore.read_bytes()).hexdigest() == recovery['restore_sha256']
    if args.restore:
        image, expected = restore, recovery['restore_sha256']
    else:
        image, expected = args.load, args.sha256
    assert expected and hashlib.sha256(image.read_bytes()).hexdigest() == expected
    journal_path = base/'binding_journal.json'
    if args.restore:
        saved = json.loads(journal_path.read_text())
    else:
        assert not journal_path.exists(), 'Existing trial: restore before starting another'
        saved = {'original': [], 'stages': [], 'image_sha256': expected}
        for bus, driver, device in AUDIO:
            if (Path('/sys/bus')/bus/'drivers'/driver/device).exists():
                saved['original'].append([bus, driver, device])
        # Quiesce consumers of peripherals removed by the audio-only candidate.
        extra = []
        for node in Path('/sys/bus/platform/devices').iterdir():
            driver = node/'driver'
            if not driver.exists() or any(node.name == row[2] for row in AUDIO):
                continue
            if node.name.startswith(('43c', '4121', '4160', '42c', 'amba_pl:')) or node.name=='xlnx-drm.0':
                extra.append(['platform', driver.resolve().name, node.name])
        priority = {'xlnx-pl-disp': 0, 'xlnx-drm': 0, 'xilinx-video': 0, 'gpio-xilinx': 9}
        saved['original'] += sorted(extra, key=lambda row: priority.get(row[1], 5))
        run('alsactl', '-f', str(base/'mixer_before.state'), 'store', '0')
        journal_path.write_text(json.dumps(saved, indent=2)+'\n')

    def stage(name):
        saved['stages'].append(name)
        journal_path.write_text(json.dumps(saved, indent=2)+'\n')
        print(name, flush=True)

    run(FACTORY_SERVICE, 'stop')
    for node in ('pcm0p', 'pcm1c'):
        status = Path('/proc/asound/card0/'+node+'/sub0/status')
        assert (args.restore and not status.exists()) or status.read_text().strip() == 'closed'
    for module in ('world_fft_dma', 'world_exp_dma'):
        if Path('/sys/module', module).exists():
            run('rmmod', module)
    stage('audio_stopped')
    for row in saved['original']:
        binding(*row, 'unbind')
    stage('drivers_unbound')
    try:
        run('fpgautil', '-b', str(image), '-f', 'Full')
        assert Path('/sys/class/fpga_manager/fpga0/state').read_text().strip() == 'operating'
        stage('fpga_loaded')
        # Display/camera rebind stalled Linux during the first recovery trial.
        # Restore the audio path here; a normal boot restores other peripherals.
        selected = [row for row in saved['original']
                    if row in [list(x) for x in AUDIO] or row[1]=='xiic-i2c']
        if args.restore:
            saved['peripheral_rebind_deferred_until_boot'] = [
                row for row in saved['original'] if row not in selected]
        pending = list(reversed(selected))
        for attempt in range(3):
            remaining = []
            for row in pending:
                try:
                    stage('binding_'+row[2])
                    binding(*row, 'bind')
                except OSError:
                    remaining.append(row)
            pending = remaining
            if not pending:
                break
        if pending:
            raise RuntimeError('Driver restore pending: %r' % pending)
        deadline = time.monotonic() + 15
        while not Path('/dev/snd/controlC0').exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        assert Path('/dev/snd/controlC0').exists()
        run('alsactl', '-f', str(base/'mixer_before.state'), 'restore', '0')
        stage('drivers_bound')
    except Exception:
        stage('FAILED_run_restore_immediately')
        raise
    if args.restore:
        if args.keep_stopped:
            stage('factory_restored_audio_service_stopped')
        else:
            run(FACTORY_SERVICE, 'start')
            stage('factory_and_v23_restored')
    else:
        stage('candidate_ready_audio_service_stopped')


if __name__ == '__main__':
    main()
