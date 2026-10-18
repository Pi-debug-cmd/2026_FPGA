"""Frozen original + accepted synthesis + timing-only diagnostic, separate.

Track9 remains diagnostic: never reference conditioning or training supervision.
The new timing candidate is not an actual male-to-target or student output.
"""
from prepare_aligned_teacher_pilot_20261004 import ctc_centers, warp_pitch_preserving, meaningful_checks, sha, hanzi, read_audio
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker, FRONT
from pathlib import Path
import json, shutil
import numpy as np, torch, soundfile as sf, sentencepiece as spm

OLD=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
OUT=Path('D:/总进度/目标人物分析/固定原台词_分开试听_2026-10-04')
OUT.mkdir(exist_ok=True)
TEXT='我的校园很美，走近大门就能看见宽阔的操场。'
EXPECTED=hanzi(TEXT)

def main():
    meaningful_checks()
    for sr in [16000,24000]:
        w=(.1*np.sin(2*np.pi*200*np.arange(sr)/sr)).astype('float32')
        y=warp_pitch_preserving(w,sr,[0,1],[0,1],sample_rate=sr)
        assert np.linalg.norm(y-w)/np.linalg.norm(w)<1e-5
    provenance=json.loads((OLD/'audition_provenance.json').read_text(encoding='utf8'))
    first,second=provenance['clips'][:2]
    for row in [first,second]:assert sha(row['preview_path'])==row['preview_sha256']
    p1=OUT/'①目标人物原声.wav';p2=OUT/'②之前认可的同文本合成声.wav';p3=OUT/'③同文本_仅节奏对齐.wav'
    shutil.copy2(first['preview_path'],p1);shutil.copy2(second['preview_path'],p2)
    source,sr=sf.read(p1,dtype='float32');teacher,tr=sf.read(p2,dtype='float32')
    assert sr==tr==24000 and source.ndim==teacher.ndim==1
    checker=PinyinChecker();tokenizer=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
    probe=json.loads((OUT/'pinyin_probe.json').read_text(encoding='utf8'))
    expected_pinyin=probe[0]['decoded']
    assert expected_pinyin==probe[1]['decoded'] and len(expected_pinyin)==19
    ids=[checker.vocabulary[t] for t in expected_pinyin]
    def acoustic(path,forced=False):
        x=read_audio(path);x=x/(float(np.max(np.abs(x)))+1e-8)
        torch.manual_seed(20261004)
        with torch.inference_mode():feats,lens=checker.frontend(torch.from_numpy(x).unsqueeze(0),torch.tensor([len(x)]))
        lp,pp,lengths=checker.session.run(['hanzi_log_probs','pinyin_log_probs','encoder_lens'],dict(feats=feats.numpy().astype('float32'),feats_lens=lens.numpy().astype('int32')))
        lp=lp[:int(lengths[0]),0];assert len(lp)==int(lens[0])
        pp=pp[:int(lengths[0]),0]
        tokens=[];previous=0
        for frame in lp:
            token=int(frame.argmax())
            if token and token!=previous:tokens.append(token)
            previous=token
        text=tokenizer.decode(tokens)
        ptokens=[];previous=0
        for frame in pp:
            token=int(frame.argmax())
            if token and token!=previous:ptokens.append(checker.id2token[token])
            previous=token
        if forced and ptokens!=expected_pinyin:raise ValueError('Free pinyin differs before timing alignment')
        # Literal original ASR uses 走进 versus controlled 走近, a homophone.
        # Preserve that discrepancy; align only the independently matching
        # acoustic pinyin sequences, never rewrite original Hanzi recognition.
        return dict(free_hanzi=text,literal_hanzi_matches_expected=hanzi(text)==EXPECTED,
                    free_pinyin=ptokens,pinyin_matches_original=ptokens==expected_pinyin,
                    centers=ctc_centers(pp,ids) if forced else None)
    a,b=acoustic(p1,True),acoustic(p2,True)
    sc=[r['seconds'] for r in a['centers']];tc=[r['seconds'] for r in b['centers']]
    leading=sc[0]-tc[0]
    assert leading>=0
    end=min(len(source)/sr,sc[-1]+len(teacher)/tr-tc[-1])
    source_knots=[leading]+sc+[end];teacher_knots=[0]+tc+[len(teacher)/tr]
    assert np.all(np.diff(source_knots)>0) and np.all(np.diff(teacher_knots)>0)
    print('LANDMARK_RATES',np.diff(teacher_knots)/np.diff(source_knots),flush=True)
    warped=warp_pitch_preserving(teacher,len(source),source_knots,teacher_knots,sample_rate=24000)
    warped*=min(.04/max(float(np.sqrt(np.mean(warped*warped))),1e-12),.95/max(float(np.max(np.abs(warped))),1e-12))
    assert np.isfinite(warped).all()
    sf.write(p3,warped,24000,subtype='PCM_16')
    c=acoustic(p3)
    phonetic=[]
    for path in [p1,p2,p3]:
        result=checker.predict(path)
        phonetic.append(dict(path=str(path),decoded=result['decoded'],human_pronunciation_acceptance=False))
    decision=dict(status='same_text_separate_diagnostic_ready',text=TEXT,
        clips=[dict(order=1,path=str(p1),sha256=sha(p1),seconds=len(source)/sr,role='Original target speaker recording; frozen previous preview',byte_exact_previous_preview=sha(p1)==first['preview_sha256']),
               dict(order=2,path=str(p2),sha256=sha(p2),seconds=len(teacher)/tr,role='Previously accepted text-to-target synthesis, unchanged',byte_exact_previous_preview=sha(p2)==second['preview_sha256']),
               dict(order=3,path=str(p3),sha256=sha(p3),seconds=len(warped)/sr,role='Timing-only modification of clip2; not neural or live conversion',human_acceptance=False)],
        free_hanzi=[a,b,c],phonetic_screening=phonetic,
        pinyin_candidate_matches_baseline=phonetic[1]['decoded']==phonetic[2]['decoded'],
        source_knots=source_knots,teacher_knots=teacher_knots,
        original_synthesis_and_candidate_not_concatenated=True,original_target_not_changed=True,
        model_reference_still_track6=True,target_track9_diagnostic_only=True,
        target_track9_not_used_for_training=True,no_training=True,board_deployed=False,
        no_actual_source_to_student_output=True,automatic_pronunciation_acceptance=False,
        supersedes_previous_changed_text_audition_request=True)
    (OUT/'decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf8')
    print('SEPARATE SAME-TEXT FILES READY; pinyin_matches_baseline=',decision['pinyin_candidate_matches_baseline'],flush=True)

if __name__=='__main__':main()
