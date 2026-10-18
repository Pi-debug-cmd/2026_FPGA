"""Two development speakers only; alignment pilot, never training acceptance.

CTC emission centers are coarse content landmarks, not phone boundaries.
Forced alignment is permitted only after unconstrained text agreement. It is
not pronunciation verification. Held-out speakers remain untouched.
"""
from pathlib import Path
import json, re, hashlib
from run_sensevoice_pinyin_validation_20261004 import PinyinChecker, FRONT
import numpy as np, torch, soundfile as sf, sentencepiece as spm, librosa
from scipy.signal import resample_poly
from math import gcd

BASE = Path(__file__).resolve().parent
OUT = Path('D:/总进度/目标人物分析/小模型监督对齐试验_2026-10-04')
OUT.mkdir(exist_ok=True)


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def hanzi(t): return re.sub(r'[^\u4e00-\u9fff]', '', t)


def read_audio(path):
    x, sr = sf.read(path, dtype='float32')
    if x.ndim == 2: x = x.mean(axis=1)
    if sr != 16000: x = resample_poly(x, 16000//gcd(sr,16000), sr//gcd(sr,16000)).astype('float32')
    return x


def ctc_centers(lp, ids):
    assert ids and all(i > 0 for i in ids)
    labels = [0]
    for token in ids: labels.extend([token, 0])
    T, S = len(lp), len(labels)
    scores = np.full((T, S), -np.inf)
    back = np.full((T, S), -1, dtype='int32')
    scores[0, :2] = lp[0, labels[:2]]
    for t in range(1, T):
        for s, label in enumerate(labels):
            candidates = [s]
            if s > 0: candidates.append(s-1)
            if s > 1 and label != 0 and label != labels[s-2]: candidates.append(s-2)
            prev = max(candidates, key=lambda v: scores[t-1, v])
            scores[t,s] = scores[t-1,prev] + lp[t,label]
            back[t,s] = prev
    state = S-1 if scores[-1,S-1] > scores[-1,S-2] else S-2
    if not np.isfinite(scores[-1,state]): raise ValueError('No valid CTC alignment')
    path = np.empty(T, dtype='int32')
    for t in range(T-1,-1,-1):
        path[t] = state
        if t: state = back[t,state]
    centers=[]
    for i, token in enumerate(ids):
        frames=np.where(path == 2*i+1)[0]
        if not len(frames): raise ValueError('Missing token in CTC path')
        # The peak within the forced token state supplies a coarse landmark.
        peak=int(frames[np.argmax(lp[frames,token])])
        centers.append(dict(token=token, peak_frame=peak, seconds=peak*.06,
                            approximate_first_frame=int(frames[0]), approximate_last_frame=int(frames[-1]),
                            posterior=float(np.exp(lp[peak,token]))))
    assert all(b['seconds'] > a['seconds'] for a,b in zip(centers,centers[1:]))
    return centers


def warp_pitch_preserving(wave, target_length, target_anchors, source_anchors, sample_rate=16000):
    # Same STFT phase propagation as a phase vocoder, with a monotone variable
    # analysis-time map. Mapping adjusts rhythm; it does not resample the pitch.
    assert sample_rate in [16000, 24000]
    n_fft, hop = int(sample_rate*.032), int(sample_rate*.008)
    D = librosa.stft(wave, n_fft=n_fft, hop_length=hop)
    output_frames = 1 + target_length//hop
    times = np.arange(output_frames)*hop/sample_rate
    steps = np.interp(times, target_anchors, source_anchors)*sample_rate/hop
    # Floating-point unit maps can yield e.g. 1.9999999999999998. Choosing
    # frame1 again would duplicate its phase increment instead of using frame2.
    nearest=np.round(steps)
    steps=np.where(np.abs(steps-nearest)<1e-9,nearest,steps)
    assert np.all(np.diff(steps)>=0)
    phase_advance = 2*np.pi*hop*np.arange(1+n_fft//2)/n_fft
    phase = np.angle(D[:,0]).astype('float64')
    padded = np.pad(D, ((0,0),(0,2)))
    result = np.zeros((len(phase), len(steps)), dtype=D.dtype)
    for i, step in enumerate(steps):
        if times[i] < target_anchors[0] or times[i] > target_anchors[-1]:
            continue
        t=min(int(step),D.shape[1]-1); fraction=step-int(step)
        a,b=padded[:,t],padded[:,t+1]
        magnitude=(1-fraction)*np.abs(a)+fraction*np.abs(b)
        result[:,i]=magnitude*np.exp(1j*phase)
        delta=np.angle(b)-np.angle(a)-phase_advance
        delta-=2*np.pi*np.round(delta/(2*np.pi))
        phase+=phase_advance+delta
    return librosa.istft(result, hop_length=hop, length=target_length).astype('float32')


def meaningful_checks():
    # Identity reconstruction and pitch preservation under a nonuniform warp.
    wave=(.1*np.sin(2*np.pi*200*np.arange(16000)/16000)).astype('float32')
    same=warp_pitch_preserving(wave,len(wave),[0,1],[0,1])
    assert np.linalg.norm(same-wave)/np.linalg.norm(wave)<1e-5
    stretched=warp_pitch_preserving(wave,24000,[0,.75,1.5],[0,.6,1])
    for lo,hi in [(2000,10000),(14000,22000)]:
        part=stretched[lo:hi]*np.hanning(hi-lo)
        peak=np.argmax(np.abs(np.fft.rfft(part)))*16000/len(part)
        assert abs(peak-200)<3,peak
    # Adjacent identical CTC labels need a blank; impossible paths must fail.
    lp=np.full((5,3),-30.)
    lp[np.arange(5),[0,1,0,1,0]]=0
    c=ctc_centers(lp,[1,1]);assert [r['peak_frame'] for r in c]==[1,3]
    try:ctc_centers(lp[:1],[1,1]);raise AssertionError('Impossible path accepted')
    except ValueError:pass


def main():
    meaningful_checks()
    checker=PinyinChecker()
    tokenizer=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
    rows=json.loads(Path('D:/总进度/目标人物分析/固定人物多说话人中文回归_2026-10-04/evaluation_items.json').read_text(encoding='utf8'))
    plan=[r for r in rows if r['source_split']=='development']
    assert len(plan)==2
    records=[]
    for row in plan:
        assert sha(row['source_path'])==row['source_sha256'] and sha(row['path'])==row['sha256']
        text=hanzi(row['unmodified_actual_asr_text']);ids=tokenizer.encode(text)
        assert hanzi(tokenizer.decode(ids))==text
        waves=[read_audio(row['source_path']),read_audio(row['path'])]
        align=[]
        for role,wave in zip(['source','teacher'],waves):
            normalized=wave/(float(np.max(np.abs(wave)))+1e-8)
            torch.manual_seed(20261004)
            with torch.inference_mode():feats,lens=checker.frontend(torch.from_numpy(normalized).unsqueeze(0),torch.tensor([len(wave)]))
            lp,lengths=checker.session.run(['hanzi_log_probs','encoder_lens'],dict(feats=feats.numpy().astype('float32'),feats_lens=lens.numpy().astype('int32')))
            lp=lp[:int(lengths[0]),0]
            # This exporter invokes the encoder directly: no four query-token
            # prefix is present. Assert encoder length equals acoustic features.
            assert len(lp)==int(lens[0])
            decoded=[];previous=0
            for p in lp:
                token=int(p.argmax())
                if token and token!=previous:decoded.append(token)
                previous=token
            free=tokenizer.decode(decoded)
            assert hanzi(free)==text,(row['label'],role,free,text)
            centers=ctc_centers(lp,ids)
            assert centers[-1]['seconds']<len(wave)/16000
            np.savez_compressed(OUT/(row['label']+'_'+role+'_ctc.npz'),log_probs=lp,token_ids=np.array(ids))
            align.append(dict(role=role,free_decoding=free,centers=centers,seconds=len(wave)/16000))
        source,teacher=waves
        first_source=align[0]['centers'][0]['seconds'];first_teacher=align[1]['centers'][0]['seconds']
        last_source=align[0]['centers'][-1]['seconds'];last_teacher=align[1]['centers'][-1]['seconds']
        leading_padding=first_source-first_teacher
        active_end=last_source+(len(teacher)/16000-last_teacher)
        # Do not stretch the initial syllable to imitate leading silence.
        # Preserve teacher prefix/tail durations and pad the residual silence.
        # This conservative pilot rejects cases that would require trimming.
        assert leading_padding>=0 and active_end<=len(source)/16000
        source_knots=[leading_padding]+[p['seconds'] for p in align[0]['centers']]+[active_end]
        teacher_knots=[0]+[p['seconds'] for p in align[1]['centers']]+[len(teacher)/16000]
        assert np.all(np.diff(source_knots)>0) and np.all(np.diff(teacher_knots)>0)
        aligned=warp_pitch_preserving(teacher,len(source),source_knots,teacher_knots)
        assert len(aligned)==len(source) and np.isfinite(aligned).all()
        gain=min(1.,.95/max(float(np.max(np.abs(aligned))),1e-12));aligned*=gain
        path=OUT/(row['label']+'_aligned_teacher.wav');sf.write(path,aligned,16000,subtype='PCM_24')
        sf.write(OUT/(row['label']+'_original.wav'),source,16000,subtype='PCM_24')
        rates=np.diff(teacher_knots)/np.diff(source_knots)
        records.append(dict(row,aligned_teacher_path=str(path),aligned_teacher_sha256=sha(path),source_seconds=len(source)/16000,
                            teacher_seconds=len(teacher)/16000,alignments=align,source_knots=source_knots,teacher_knots=teacher_knots,
                            local_analysis_rates=rates.tolist(),leading_silence_padding_seconds=leading_padding,
                            trailing_silence_padding_seconds=len(source)/16000-active_end,
                            prefix_and_tail_not_time_stretched=True,gain=gain,human_alignment_acceptance=False,
                            approved_training_pair=False,source_speaker_enrollment=False))
        print('ALIGNED',row['label'],'rate range',float(rates.min()),float(rates.max()),flush=True)
    # One short necessary naturalness review, raw teacher then aligned teacher.
    raw=read_audio(records[0]['path']);warped=read_audio(records[0]['aligned_teacher_path'])
    parts=[]
    for wave in [raw,warped]:
        gain=min(.04/max(float(np.sqrt(np.mean(wave*wave))),1e-12),.95/max(float(np.max(np.abs(wave))),1e-12))
        parts.append(wave*gain)
    preview=OUT/'原目标合成声_对齐后目标声_约8秒.wav'
    sf.write(preview,np.concatenate([parts[0],np.zeros(4800,dtype='float32'),parts[1]]),16000,subtype='PCM_24')
    decision=dict(status='alignment_pilot_ready_for_human_review',cases=records,
                  preview_path=str(preview),preview_sha256=sha(preview),test_identity_nonuniform_pitch_repeated_label_and_impossible_path=True,
                  ctc_landmarks_are_not_exact_phone_boundaries=True,forced_text_not_pronunciation_approval=True,
                  teacher_outputs_not_all_human_accepted=True,student_not_trained=True,heldout_speakers_not_used=True,board_deployed=False)
    (OUT/'decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2),encoding='utf8')
    print('ALIGNMENT PILOT COMPLETE',flush=True)


if __name__=='__main__':main()
