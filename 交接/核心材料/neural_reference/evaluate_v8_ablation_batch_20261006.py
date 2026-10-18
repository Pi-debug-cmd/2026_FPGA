from pathlib import Path
import subprocess, os, json

base=Path(__file__).resolve().parent
variants=['fargan_v8_pitch_smooth','fargan_v8_source_voicing','fargan_v8_pitch_smooth_source_voicing']
for filename in ('screen_board_phonetic_pilot_20261005.py','evaluate_board_phonetic_naturalness_20261005.py'):
    path=base/filename;text=path.read_text(encoding='utf-8')
    if "'fargan_v8_pitch_smooth'" not in text:
        needle="'fargan_mapper_expanded_v8']"
        assert text.count(needle)==1
        text=text.replace(needle,"'fargan_mapper_expanded_v8',"+','.join(repr(v) for v in variants)+']')
        path.write_text(text,encoding='utf-8')
env=os.environ.copy();env['PYTHONIOENCODING']='utf-8'
env['TMP']=env['TEMP']='D:/Tools_codex/temp'
for variant in variants:
    print('EVALUATING',variant,flush=True)
    subprocess.run([str(base/'cosyvoice_env/Scripts/python.exe'),str(base/'screen_board_phonetic_pilot_20261005.py'),'--outname',variant,'--validation-only'],env=env,check=True)
    subprocess.run([str(base/'rvc_env/Scripts/python.exe'),str(base/'evaluate_board_phonetic_naturalness_20261005.py'),'--candidate',variant],env=env,check=True)
print('ALL_ABLATIONS_EVALUATED',flush=True)
