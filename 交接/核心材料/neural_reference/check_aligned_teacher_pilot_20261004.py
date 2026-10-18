"""Free acoustic screening of alignment outputs; never human acceptance."""
from prepare_aligned_teacher_pilot_20261004 import OUT, hanzi, read_audio, sha, ctc_centers
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker, FRONT
import json, torch, numpy as np, sentencepiece as spm

checker=PinyinChecker()
tokenizer=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
decision=json.loads((OUT/'decision.json').read_text(encoding='utf8'))
results=[]
for row in decision['cases']:
    p=row['aligned_teacher_path'];assert sha(p)==row['aligned_teacher_sha256']
    x=read_audio(p);normalized=x/(float(np.max(np.abs(x)))+1e-8)
    torch.manual_seed(20261004)
    with torch.inference_mode():feats,lens=checker.frontend(torch.from_numpy(normalized).unsqueeze(0),torch.tensor([len(x)]))
    lp,lengths=checker.session.run(['hanzi_log_probs','encoder_lens'],dict(feats=feats.numpy().astype('float32'),feats_lens=lens.numpy().astype('int32')))
    tokens=[];previous=0
    for frame in lp[:int(lengths[0]),0]:
        token=int(frame.argmax())
        if token and token!=previous:tokens.append(token)
        previous=token
    text=tokenizer.decode(tokens)
    new_centers=ctc_centers(lp[:int(lengths[0]),0],tokenizer.encode(hanzi(row['unmodified_actual_asr_text'])))
    old_centers=row['alignments'][0]['centers']
    landmark_errors=[abs(a['seconds']-b['seconds']) for a,b in zip(old_centers,new_centers)]
    old=checker.predict(row['path']);new=checker.predict(p)
    results.append(dict(label=row['label'],path=p,sha256=sha(p),unconstrained_hanzi=text,
                        hanzi_matches_input=hanzi(text)==hanzi(row['unmodified_actual_asr_text']),
                        teacher_pinyin=old['decoded'],aligned_pinyin=new['decoded'],
                        pinyin_unchanged=old['decoded']==new['decoded'],
                        coarse_ctc_landmark_max_error_seconds=max(landmark_errors),
                        coarse_ctc_landmark_mean_error_seconds=float(np.mean(landmark_errors)),
                        ctc_landmarks_not_phone_boundaries=True,
                        human_acceptance=False,phonetic_approval=False))
    print('CHECKED',row['label'],'hanzi_match',results[-1]['hanzi_matches_input'],'pinyin_unchanged',results[-1]['pinyin_unchanged'],flush=True)
(OUT/'free_acoustic_screening.json').write_text(json.dumps(dict(status='screening_only',cases=results,expected_text_not_input=True,
    known_pronunciation_blind_spots=True,automatic_training_pair_acceptance=False),ensure_ascii=False,indent=2),encoding='utf8')
