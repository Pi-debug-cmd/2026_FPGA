#!/usr/bin/env python3
"""Reload the 2026 PL image and run command-level ALSA checks.

This changes live FPGA and audio-driver state. Run only after the user confirms
that a board test may start. Python 3.8 compatible.
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

FW = Path(sys.argv[1] if len(sys.argv) > 1 else
          '/tmp/codex_pl2026_20261019/zynq_swap.bin')
JOURNAL = Path(sys.argv[2] if len(sys.argv) > 2 else
               '/tmp/codex_pl2026_20261019/reload_journal.json')
TONE = Path('/tmp/codex_pl2026_20261019/tone.wav')
CAPTURE = Path('/tmp/rec_check.wav')
RUN = JOURNAL.parent

# Unbind consumers before providers; bind providers before consumers.
UNBIND = [
    ('platform', 'xlnx_snd_card', 'xlnx_snd_card.0.auto'),
    ('platform', 'xlnx_formatter_pcm', '43c40000.audio_formatter'),
    ('platform', 'xlnx_i2s', '43c60000.i2s_transmitter'),
    ('platform', 'xlnx_i2s', '43c50000.i2s_receiver'),
    ('platform', 'dglnt-dynclk', '43c20000.axi_dynclk'),
    ('i2c', 'wm8960', '0-001a'),
]
BIND = list(reversed(UNBIND))

journal = {'firmware': str(FW), 'stage': 'start', 'steps': [], 'done': False}
paused_listeners = []
mixer_saved = False


def save():
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.write_text(json.dumps(journal, indent=2, ensure_ascii=False) + '\n')


def step(name, ok=True, note=''):
    journal['stage'] = name
    journal['steps'].append({'stage': name, 'ok': ok, 'note': note})
    save()
    print('STAGE %s %s %s' % (name, 'OK' if ok else 'FAIL', note), flush=True)
    if not ok:
        raise RuntimeError('%s: %s' % (name, note))


def run(command):
    result = subprocess.run(command, capture_output=True, text=True)
    lines = (result.stdout + result.stderr).strip().splitlines()
    return result.returncode, (lines[-1][:180] if lines else '')


def driver_root(bus, driver):
    return Path('/sys/bus') / bus / 'drivers' / driver


def change_binding(action, bus, driver, device):
    root = driver_root(bus, driver)
    bound = (root / device).exists()
    if action == 'unbind' and not bound:
        return 'already unbound'
    if action == 'bind' and bound:
        return 'already bound'
    try:
        (root / action).write_text(device)
    except OSError as exc:
        # A driver may auto-probe between the write and this check.
        expected = action == 'bind'
        if (root / device).exists() == expected:
            return 'state reached after write error: %s' % exc
        raise
    expected = action == 'bind'
    if (root / device).exists() != expected:
        raise RuntimeError('%s state not reached for %s/%s' %
                           (action, driver, device))
    return 'ok'


def pause_listener():
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cmd = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(
                errors='replace')
        except OSError:
            continue
        if 'music-button-listener' in cmd:
            os.kill(int(entry.name), signal.SIGSTOP)
            paused_listeners.append(int(entry.name))
        elif cmd.startswith('aplay') or 'aplay ' in cmd:
            os.kill(int(entry.name), signal.SIGKILL)


def capture_has_signal(path):
    # S24_LE is carried in 32-bit little-endian words on this ALSA device.
    data = path.read_bytes()[44:]
    if len(data) < 4096:
        return False, 'capture too short: %d bytes' % len(data)
    peak = 0
    nonzero = 0
    for offset in range(0, len(data) - 3, 4):
        value = int.from_bytes(data[offset:offset + 4], 'little', signed=True)
        peak = max(peak, abs(value))
        nonzero += value != 0
    return nonzero > 0, 'bytes=%d nonzero_words=%d peak=%d' % (
        len(data) + 44, nonzero, peak)


def main():
    global mixer_saved
    step('preflight', FW.is_file() and TONE.is_file(),
         'firmware=%s tone=%s' % (FW.is_file(), TONE.is_file()))
    journal['state_before'] = Path(
        '/sys/class/fpga_manager/fpga0/state').read_text().strip()

    pause_listener()
    step('listener_paused', note='pids=%s' % paused_listeners)
    rc, note = run(['alsactl', '-f', str(RUN / 'mixer_before.state'), 'store', '0'])
    step('mixer_saved', rc == 0, note)
    mixer_saved = True

    for bus, driver, device in UNBIND:
        step('unbind_%s_%s' % (driver, device), note=change_binding(
            'unbind', bus, driver, device))

    rc, note = run(['fpgautil', '-b', str(FW), '-f', 'Full'])
    step('bitstream_loaded', rc == 0, note)
    state = Path('/sys/class/fpga_manager/fpga0/state').read_text().strip()
    step('fpga_operating', state == 'operating', state)

    for bus, driver, device in BIND:
        step('bind_%s_%s' % (driver, device), note=change_binding(
            'bind', bus, driver, device))
        time.sleep(0.2)

    deadline = time.monotonic() + 15.0
    while not Path('/dev/snd/controlC0').exists() and time.monotonic() < deadline:
        time.sleep(0.2)
    step('soundcard_ready', Path('/dev/snd/controlC0').exists())

    rc, note = run(['alsactl', '-f', str(RUN / 'mixer_before.state'), 'restore', '0'])
    step('mixer_restored', rc == 0, note)
    rc, note = run(['aplay', '-D', 'default', str(TONE)])
    step('play_command', rc == 0, note)

    if CAPTURE.exists():
        CAPTURE.unlink()
    rc, note = run(['arecord', '-D', 'hw:0,1', '-f', 'S24_LE', '-r', '32000',
                    '-c', '2', '-d', '2', str(CAPTURE)])
    step('capture_command', rc == 0, note)
    has_signal, note = capture_has_signal(CAPTURE)
    step('capture_nonzero', has_signal, note)
    journal['done'] = True
    step('finished')


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        journal['exception'] = repr(exc)
        save()
        raise
    finally:
        if mixer_saved:
            subprocess.run(['alsactl', '-f', str(RUN / 'mixer_before.state'),
                            'restore', '0'], capture_output=True)
        for listener_pid in paused_listeners:
            try:
                os.kill(listener_pid, signal.SIGCONT)
            except OSError:
                pass
        save()
