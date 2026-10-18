"""Relative speaker identity, F0, signal integrity and ASR-content diagnostics.
Scores are not perceptual identity/naturalness acceptance. Target Track5-8 are
references; Track9 is diagnostic only, already repeatedly auditioned by user.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys
import numpy as np
import soundfile as sf
import torch
import run_rvc_pilot as pilot
from pronunciation_review_gate import annotate_report

BASE=Path(__file__).resolve().parent
ROOT=BASE/'RVC'
OUT=Path('D:/总进度/目标人物分析/自动评估与改进')
TARGET=Path('D:/总进度/目标人物语音')
COMPARISON=Path('D:/总进度/目标人物分析/现有素材修正训练_中文真人对比')
SAME_TEXT=Path('D:/总进度/目标人物分析/素材同文本普通声转换对比')

def audio16(path):
    import librosa
    x,sr=sf.read(path,dtype='float32')
    if x.ndim==2: x=x.mean(axis=1)
    if not np.isfinite(x).all() or np.max(np.abs(x))==0: raise RuntimeError('Invalid '+str(path))
    return librosa.resample(x,orig_sr=sr,target_sr=16000) if sr!=16000 else x

def initial_items():
    records=[]
    for label,name in [('ordinary_same_text','普通声_转换前.wav'),('e60_same_text','普通声_转换成目标人物.wav'),
                       ('target9_same_text_diagnostic','目标人物原声_试听.wav')]:
        records.append(dict(label=label,path=str(SAME_TEXT/name),text_origin='ASR-derived target text',
            expected_text=(SAME_TEXT/'素材前15秒_识别文本.txt').read_text(encoding='utf-8').strip()))
    previous=json.loads((COMPARISON/'对比记录.json').read_text(encoding='utf-8-sig'))
    for item in previous['files']:
        if item['sample'] not in ['BAC009S0002W0122','BAC009S0003W0121']: continue
        records.append(dict(label=item['model_label']+'_'+item['sample'],path=item['path'],
                            expected_text=item['text'],text_origin='AISHELL supplied transcript'))
    strength=Path('D:/总进度/目标人物分析/音色参考强度对比_修正60轮/对比记录.json')
    if strength.exists():
        for item in json.loads(strength.read_text(encoding='utf-8'))['files']:
            prior=next(x for x in previous['files'] if x['sample']==item['sample'])
            records.append(dict(label=item['label']+'_'+item['sample'],path=item['path'],
                                expected_text=prior['text'],text_origin='AISHELL supplied transcript'))
    return records

def edit_distance(a,b):
    row=list(range(len(b)+1))
    for i,left in enumerate(a,1):
        next_row=[i]
        for j,right in enumerate(b,1):
            next_row.append(min(next_row[-1]+1,row[j]+1,row[j-1]+(left!=right)))
        row=next_row
    return row[-1]

def mfcc_dtw_distance(path,reference):
    # Same text only. This is an MFCC feature distance, not calibrated MCD/MOS.
    import librosa
    features=[]
    for item in [path,reference]:
        x=audio16(item)
        x=x/max(float(np.sqrt(np.mean(x*x))),1e-8)*.04
        features.append(librosa.feature.mfcc(y=x,sr=16000,n_mfcc=21,n_fft=512,
                        hop_length=160,n_mels=64)[1:])
    distances,path_indices=librosa.sequence.dtw(X=features[0],Y=features[1],metric='euclidean')
    frame_distances=[float(np.linalg.norm(features[0][:,i]-features[1][:,j])) for i,j in path_indices]
    return dict(mean_mfcc1_20_euclidean=float(np.mean(frame_distances)),
                median_mfcc1_20_euclidean=float(np.median(frame_distances)),
                alignment_path_frames=len(path_indices),
                interpretation='Same-text spectral/prosodic diagnostic; not calibrated perceptual likeness')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--items',type=Path)
    parser.add_argument('--name',default='baseline')
    parser.add_argument('--skip-asr',action='store_true')
    args=parser.parse_args()
    pilot.settings()
    sys.path.insert(0,str(ROOT))
    os.chdir(ROOT)
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((BASE/'speaker_evaluator_manifest.json').read_text())
    from transformers import Wav2Vec2FeatureExtractor,WavLMForXVector
    extractor=Wav2Vec2FeatureExtractor.from_pretrained(manifest['local_path'])
    model=WavLMForXVector.from_pretrained(manifest['local_path'],local_files_only=True).to('cuda').eval()
    cache=OUT/'embedding_cache'
    cache.mkdir(exist_ok=True)
    def embed(path):
        digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        stored=cache/(manifest['revision']+'_'+digest+'.npy')
        if stored.is_file(): return np.load(stored)
        x=audio16(path)
        vectors=[]
        for start in range(0,len(x),96000):
            clip=x[start:start+96000]
            if len(clip)<24000 or np.sqrt(np.mean(clip*clip))<.001: continue
            inputs=extractor(clip,sampling_rate=16000,return_tensors='pt')
            with torch.inference_mode():
                vector=model(**{k:v.to('cuda') for k,v in inputs.items()}).embeddings
                vector=torch.nn.functional.normalize(vector,dim=-1).cpu().numpy()[0]
            vectors.append(vector)
        if not vectors: raise RuntimeError('No evaluable segment '+str(path))
        vector=np.mean(vectors,axis=0)
        vector/=np.linalg.norm(vector)
        np.save(stored,vector)
        return vector
    targets=[TARGET/f'Track {n}.wav' for n in range(5,9)]
    references=np.stack([embed(p) for p in targets])
    centroid=references.mean(axis=0)
    centroid/=np.linalg.norm(centroid)
    same_person=[float(references[i]@references[j]) for i in range(4) for j in range(i+1,4)]
    items=json.loads(args.items.read_text(encoding='utf-8')) if args.items else initial_items()
    for item in items:
        path=Path(item['path'])
        vector=embed(path)
        raw,sr=sf.read(path)
        item.update(target_centroid_cosine=float(vector@centroid),
                    target_reference_mean_cosine=float(np.mean(references@vector)),
                    target_reference_min_cosine=float(np.min(references@vector)),
                    duration_seconds=len(raw)/sr,nonfinite_samples=int(np.sum(~np.isfinite(raw))),
                    peak=float(np.max(np.abs(raw))),rms=float(np.sqrt(np.mean(raw*raw))),
                    clipped_fraction=float(np.mean(np.abs(raw)>=.9999)),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        if item.get('same_text_target') or item['text_origin']=='ASR-derived target text':
            reference=item.get('same_text_target',str(SAME_TEXT/'目标人物原声_试听.wav'))
            item['same_text_spectral_distance']=mfcc_dtw_distance(path,reference)
        print('Speaker metric '+item['label']+' '+str(round(item['target_centroid_cosine'],4)),flush=True)
    del model
    torch.cuda.empty_cache()
    from infer.rmvpe import RMVPE
    pitch_model=RMVPE(str(ROOT/'assets/rmvpe/rmvpe.pt'),is_half=True,device='cuda')
    def f0(path):
        values=pitch_model.infer_from_audio(audio16(path),thred=.03)
        positive=values[(values>0)&np.isfinite(values)]
        if not len(positive): return dict(median_hz=None,positive_raw_f0_fraction=0)
        return dict(median_hz=float(np.median(positive)),p10_hz=float(np.percentile(positive,10)),
                    p90_hz=float(np.percentile(positive,90)),positive_raw_f0_fraction=float(len(positive)/len(values)))
    target_pitch=[dict(path=str(p),**f0(p)) for p in targets]
    for item in items: item['raw_rmvpe_pitch']=f0(item['path'])
    del pitch_model
    torch.cuda.empty_cache()
    if not args.skip_asr:
        from transformers import WhisperProcessor,WhisperForConditionalGeneration
        from opencc import OpenCC
        transcribe=json.loads((SAME_TEXT/'转写记录.json').read_text(encoding='utf-8'))
        from huggingface_hub import snapshot_download
        whisper_path=snapshot_download(transcribe['transcription_model'],revision=transcribe['revision'],local_files_only=True)
        processor=WhisperProcessor.from_pretrained(whisper_path)
        asr=WhisperForConditionalGeneration.from_pretrained(whisper_path,torch_dtype=torch.float16,
                    use_safetensors=True,local_files_only=True).to('cuda').eval()
        asr.generation_config.forced_decoder_ids=None
        converter=OpenCC('t2s')
        def canonical(text): return re.sub(r'[^\u4e00-\u9fffA-Za-z0-9]','',converter.convert(text)).lower()
        for item in items:
            inputs=processor(audio16(item['path']),sampling_rate=16000,return_tensors='pt',return_attention_mask=True)
            with torch.inference_mode():
                ids=asr.generate(inputs.input_features.to('cuda',dtype=torch.float16),
                        attention_mask=inputs.attention_mask.to('cuda'),language='zh',task='transcribe',num_beams=5,max_new_tokens=200)
            text=processor.batch_decode(ids,skip_special_tokens=True)[0].strip()
            expected=canonical(item['expected_text'])
            observed=canonical(text)
            item.update(asr_text=text,asr_character_error_rate=edit_distance(expected,observed)/max(1,len(expected)))
            print('Content metric '+item['label']+' '+str(round(item['asr_character_error_rate'],4)),flush=True)
        del asr
    report=dict(evaluator=manifest,target_reference_files=[str(p) for p in targets],
                target_internal_pairwise_cosines=same_person,target_reference_pitch=target_pitch,
                board_deployed=False,subjective_acceptance=False,
                limitations=['Cosine is not percent likeness or calibrated identity acceptance.',
                             'Verification model domain/language can differ from Mandarin microphone data.',
                             'Track9 held out from training/index but already heard and not pristine test data.',
                             'ASR CER includes recognition errors; same-text ground truth was machine transcribed.',
                             'Clipping/finite checks are signal integrity, not a naturalness MOS.'],files=items)
    annotate_report(report)
    dest=OUT/(args.name+'_评估记录.json')
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Report '+str(dest),flush=True)

if __name__=='__main__': main()
