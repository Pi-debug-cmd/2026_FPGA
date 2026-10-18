from pathlib import Path
import tarfile,hashlib,json
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005';p=native/'board_neural_fargan.sh';s=p.read_text(encoding='utf-8')
s=s.replace('--period-size=160 --buffer-size=640','--period-size=208 --buffer-size=832').replace('--start-delay=30000','--start-delay=39000')
line='        python3 "$DIR/audio_affinity.py" > "$RUN/affinity.log" 2>&1\n'
if line not in s:s=s.replace('        echo NEURAL_LIVE_START_REQUESTED\n',line+'        echo NEURAL_LIVE_START_REQUESTED\n')
p.write_text(s,encoding='utf-8',newline='\n');bundle=native/'fargan_v8_audio_helper_patch.tar.gz'
with tarfile.open(bundle,'w:gz') as t:
    for name in ['board_neural_fargan.sh','fargan_live_watchdog.py','audio_affinity.py']:t.add(native/name,arcname=name)
print(json.dumps(dict(bytes=bundle.stat().st_size,sha256=hashlib.sha256(bundle.read_bytes()).hexdigest())))
