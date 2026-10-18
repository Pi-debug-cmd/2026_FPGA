from run_sensevoice_pinyin_validation_20261004 import PinyinChecker,FRONT
from prepare_aligned_teacher_pilot_20261004 import read_audio,sha,hanzi
from pathlib import Path
import json,torch,numpy as np,sentencepiece as spm,onnxruntime as ort
import torchaudio.compliance.kaldi as kaldi
BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/原台词_模型直接转换检查_2026-10-04')
OLD=Path('D:/总进度/目标人物分析/固定原台词_分开试听_2026-10-04')

def main():
    d=json.loads((OUT/'decision.json').read_text(encoding='utf8'));before=json.loads((OUT/'before_inference.json').read_text(encoding='utf8'))
    checker=PinyinChecker();sp=spm.SentencePieceProcessor(model_file=str(FRONT/'chn_jpn_yue_eng_ko_spectok.bpe.model'))
    manifest=json.loads((BASE/'cross_evaluators/manifest.json').read_text(encoding='utf8'))
    weights=next(r for r in manifest if r['evaluator'].startswith('WeSpeaker'))['weight'];assert sha(weights['path'])==weights['sha256']
    opts=ort.SessionOptions();opts.intra_op_num_threads=4;opts.inter_op_num_threads=1
    speaker=ort.InferenceSession(weights['path'],sess_options=opts,providers=['CPUExecutionProvider'])
    def embed(path):
        x=read_audio(path);vectors=[];sizes=[]
        for start in range(0,len(x),96000):
            part=x[start:start+96000]
            if len(part)<24000:continue
            part=part*.04/max(float(np.sqrt(np.mean(part*part))),1e-8)
            feats=kaldi.fbank(torch.from_numpy(part*32768)[None],num_mel_bins=80,frame_length=25,frame_shift=10,sample_frequency=16000,window_type='hamming',dither=0.)
            feats=(feats-feats.mean(dim=0))[None].numpy().astype('float32')
            v=speaker.run(None,{'feats':feats})[0][0];v/=max(float(np.linalg.norm(v)),1e-8)
            vectors.append(v);sizes.append(len(part))
        v=np.average(vectors,axis=0,weights=sizes);return v/np.linalg.norm(v)
    target=np.mean([embed(f'D:/总进度/目标人物语音/Track {n}.wav') for n in [5,6,7,8]],axis=0);target/=np.linalg.norm(target)
    files=[dict(kind='original_target_diagnostic',path=str(OLD/'①目标人物原声.wav')),
           dict(kind='accepted_text_target_baseline',path=str(OLD/'②之前认可的同文本合成声.wav')),
           dict(kind='ordinary_male_input',path=before['cropped_source']),dict(kind='native_conversion',path=d['path'])]
    rows=[]
    for r in files:
        x=read_audio(r['path']);x/=float(np.max(np.abs(x)))+1e-8;torch.manual_seed(20261004)
        with torch.inference_mode():f,l=checker.frontend(torch.from_numpy(x)[None],torch.tensor([len(x)]))
        hp,pp,lengths=checker.session.run(['hanzi_log_probs','pinyin_log_probs','encoder_lens'],dict(feats=f.numpy().astype('float32'),feats_lens=l.numpy().astype('int32')))
        decoded=[]
        for probs in [hp,pp]:
            ids=[];previous=0
            for frame in probs[:int(lengths[0]),0]:
                token=int(frame.argmax())
                if token and token!=previous:ids.append(token)
                previous=token
            decoded.append(ids)
        text=sp.decode(decoded[0]);pin=[checker.id2token[t] for t in decoded[1]]
        rows.append(dict(r,sha256=sha(r['path']),free_hanzi=text,pinyin=pin,
            wespeaker_raw_cosine_to_target=float(embed(r['path'])@target),phonetic_acceptance=False,human_acceptance=False))
        print(r['kind'],round(rows[-1]['wespeaker_raw_cosine_to_target'],4),pin,flush=True)
    ordinary=next(r for r in rows if r['kind']=='ordinary_male_input');native=next(r for r in rows if r['kind']=='native_conversion')
    check=dict(status='native_same_text_machine_screening_complete',files=rows,
        native_pinyin_matches_ordinary_input=ordinary['pinyin']==native['pinyin'],
        native_hanzi_matches_ordinary_input=hanzi(ordinary['free_hanzi'])==hanzi(native['free_hanzi']),
        speaker_score_not_human_similarity_acceptance=True,asr_not_human_pronunciation_acceptance=True,
        source_same_text=True,source_registration=False,board_deployed=False,not_causal_input=True)
    (OUT/'screening.json').write_text(json.dumps(check,ensure_ascii=False,indent=2),encoding='utf8')
    print('SCREENING COMPLETE',check['native_pinyin_matches_ordinary_input'],check['native_hanzi_matches_ordinary_input'],flush=True)

if __name__=='__main__':main()
