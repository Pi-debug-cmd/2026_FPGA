"""Run one prepared 20-second Deepseek PS audio streaming diagnostic."""
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    root = Path('/tmp/codex_deepseek_ds01')
    run = root / ('live_' + str(time.monotonic_ns()))
    run.mkdir()
    record = {'seconds': 20, 'pl_enabled': False, 'block_ms': 300, 'run': str(run)}
    processes, logs = [], []
    saved = False
    def command(argv):
        p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
        record.setdefault('setup', []).append({'command': argv, 'exit': p.returncode, 'output': p.stdout.decode(errors='replace')})
        p.check_returncode()
    try:
        command(['alsactl', '-f', str(run / 'mixer.state'), 'store', '0']); saved = True
        for control in [
            ['Left Input Mixer Boost', 'on'], ['Right Boost Mixer RINPUT1', 'on'],
            ['Right Input Mixer Boost', 'on'], ['Left Boost Mixer LINPUT1', 'on'],
            ['Left Input Boost Mixer LINPUT1', '0'], ['Capture', '31,31', 'cap'],
            ['Left Output Mixer PCM', 'on'], ['Right Output Mixer PCM', 'on'],
            ['Headphone Playback ZC', 'on'], ['Headphone', '127,127'], ['Playback', '255,255']]:
            command(['amixer', 'sset', *control])
        command(['amixer', 'cset', 'name=ADC Data Output Select', '1'])
        command(['aplay', '-D', 'default', '-t', 'raw', '-f', 'S24_LE', '-r', '32000', '-c', '2', str(root / 'cue.raw')])
        time.sleep(.15)
        for name in ('capture', 'convert', 'playback'):
            logs.append((run / (name + '.log')).open('wb'))
        capture_cmd=['arecord', '-D', 'hw:0,1', '-t', 'raw', '-f', 'S24_LE', '-r', '32000', '-c', '2', '--period-size=512', '--buffer-size=4096', '-d', '20']
        convert_cmd=[str(root/'vc_s24fix_arm'), '20', 'native_s24', '200', '39322', '262144', '--model', str(root/'model.blob'), '--preset', 'live', '--stream', '300']
        playback_cmd=['aplay', '-D', 'default', '-t', 'raw', '-f', 'S24_LE', '-r', '32000', '-c', '2', '--period-size=1024', '--buffer-size=16384', '--start-delay=200000']
        record['commands']=[capture_cmd,convert_cmd,playback_cmd]
        before=time.monotonic()
        capture=subprocess.Popen(capture_cmd,stdout=subprocess.PIPE,stderr=logs[0]);processes.append(capture)
        convert=subprocess.Popen(convert_cmd,stdin=capture.stdout,stdout=subprocess.PIPE,stderr=logs[1],env={**os.environ,'VC_PL':'0'});processes.append(convert);capture.stdout.close()
        playback=subprocess.Popen(playback_cmd,stdin=convert.stdout,stdout=subprocess.DEVNULL,stderr=logs[2]);processes.append(playback);convert.stdout.close()
        deadline=time.monotonic()+40
        for p in processes:p.wait(timeout=max(1,deadline-time.monotonic()))
        record['wall_s']=time.monotonic()-before
        record['exit_codes']=[p.returncode for p in processes]
    finally:
        for p in processes:
            if p.poll() is None:p.terminate()
        for p in processes:
            if p.poll() is None:
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)
        for f in logs:f.close()
        for name in ('capture','convert','playback'):
            path=run/(name+'.log')
            if path.exists():record[name+'_log']=path.read_text(errors='replace')
        if saved:
            try:command(['alsactl','-f',str(run/'mixer.state'),'restore','0'])
            except Exception as exc:record['restore_error']=str(exc)
        (run/'report.json').write_text(json.dumps(record,indent=2))
        (root/'live_latest_report.json').write_text(json.dumps(record,indent=2))
        print(json.dumps(record,indent=2))


if __name__ == '__main__':
    main()
