"""Unprompted decoding of same Chinese B; compare baseline separately."""
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,FRONT
from prepare_aligned_teacher_pilot_20261004 import read_audio,hanzi
from check_phasefree_student_20261004 import distance
from pathlib import Path
import torch,numpy as np,json,sentencepiece as spm,onnxruntime as ort
import torchaudio.compliance.kaldi as kaldi
base=Path(__file__).resolve().parent;out=base.parent/'board_budget_20261005/fargan_v8_fullchain_verification';checker=PinyinChecker();sp=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
opts=ort.SessionOptions();opts.intra_op_num_threads=4;speaker=ort.InferenceSession(str(base/'cross_evaluators/cnceleb_resnet34_LM.onnx'),sess_options=opts,providers=['CPUExecutionProvider'])
def embedding(path):
    x=read_audio(path);x=x*.04/max(float(np.sqrt(np.mean(x*x))),1e-8);f=kaldi.fbank(torch.from_numpy(x*32768)[None],num_mel_bins=80,frame_length=25,frame_shift=10,sample_frequency=16000,window_type='hamming',dither=0.);f=(f-f.mean(0))[None].numpy().astype('float32');v=speaker.run(None,{'feats':f})[0][0];return v/np.linalg.norm(v)
reference=embedding('D:/总进度/目标人物分析/SeedVC下一阶段/inputs/target_t6_8s.wav');expected='我的校园很美，走近大门就能看见宽阔的操场。';rows=[]
paths=[('source','B_普通男声_同一句中文.wav'),('baseline','D_现有基线_同一句中文.wav'),('candidate','C_新版转换_同一句中文.wav')]
if (out/'E_板端计算_同一句中文.wav').exists():paths.append(('board','E_板端计算_同一句中文.wav'))
for kind,name in paths:
    path=out/name;x=read_audio(path);x=x/max(float(np.max(np.abs(x))),1e-8)
    with torch.inference_mode():f,l=checker.frontend(torch.from_numpy(x)[None],torch.tensor([len(x)]))
    h,p,n=checker.session.run(['hanzi_log_probs','pinyin_log_probs','encoder_lens'],dict(feats=f.numpy().astype('float32'),feats_lens=l.numpy().astype('int32')));ids=[];phones=[]
    for scores,dest in [(h,ids),(p,phones)]:
        old=0
        for frame in scores[:int(n[0]),0]:
            k=int(frame.argmax())
            if k and k!=old:dest.append(k)
            old=k
    text=sp.decode(ids);rows.append(dict(kind=kind,path=str(path),decoded=text,pinyin=[checker.id2token[k] for k in phones],hanzi_edits=distance(hanzi(text),hanzi(expected)),target_cosine=float(embedding(path)@reference)))
for row in rows:row['pinyin_edits_to_source']=distance(row['pinyin'],rows[0]['pinyin'])
report=dict(rows=rows,expected_only_used_after_decode=True,source_enrollment=False,human_acceptance=False,baseline_recognizer_and_speaker_used_as_losses=True,candidate_recognizer_and_speaker_not_used_as_losses=True,development_case_not_blind_test=True)
(out/'same_text_screen.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=True),flush=True)
