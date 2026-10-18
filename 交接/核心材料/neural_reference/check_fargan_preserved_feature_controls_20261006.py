"""Oracle teacher-feature controls isolate source energy/periodicity assumptions."""
from pathlib import Path
import numpy as np,json,subprocess,soundfile as sf
base=Path(__file__).resolve().parent;budget=base.parent/'board_budget_20261005';native=base.parent/'board_support/native_llvc_20261005'
manifest=json.loads((budget/'fargan_corpus/manifest.json').read_text(encoding='utf-8'))
for name,preserve in [('fargan_teacher_source_energy',[0]),('fargan_teacher_source_energy_periodicity',[0,19])]:
    out=budget/name;out.mkdir(exist_ok=True);rows=[]
    for row in [r for r in manifest['files'] if r['split']=='validation']:
        x=np.fromfile(row['source_features'],dtype='float32').reshape(-1,20);y=np.fromfile(row['teacher_features'],dtype='float32').reshape(-1,20)
        y=np.pad(y,((0,max(0,len(x)-len(y))),(0,0)),mode='edge')[:len(x)].copy()
        for col in preserve:y[:,col]=x[:,col]
        stem=Path(row['filename']).stem;features=out/(stem+'.f32');pcm=out/(stem+'.pcm');y.tofile(features)
        subprocess.run([str(native/'fargan_probe_host.exe'),'--synthesis',str(features),str(pcm),str(out/(stem+'.json'))],check=True)
        wave=np.fromfile(pcm,dtype='<i2').astype('float32')/32768;path=out/(stem+'_student.wav');sf.write(path,wave,16000,subtype='FLOAT');rows.append(dict(row,student_path=str(path)))
    (out/'decision.json').write_text(json.dumps(dict(complete=True,heldout_outputs=rows,oracle_teacher_features=True,control_only=True,not_actual_voice_conversion=True,preserved_source_features=preserve,recognizer_used_as_loss=False,auxiliary_speaker_loss_used=False,quality_accepted=False),ensure_ascii=False,indent=2),encoding='utf-8')
for name in ['evaluate_board_phonetic_naturalness_20261005.py','screen_board_phonetic_pilot_20261005.py']:
    p=base/name;s=p.read_text(encoding='utf-8')
    if "'fargan_teacher_source_energy'" not in s:s=s.replace("'fargan_mapper_pitchaware']","'fargan_mapper_pitchaware','fargan_teacher_source_energy','fargan_teacher_source_energy_periodicity']")
    p.write_text(s,encoding='utf-8')
print('PRESERVED_FEATURE_CONTROLS_READY')
