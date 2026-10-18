"""Local ASR only; target audio never uploaded. Text may require correction."""
from pathlib import Path
import hashlib
import json
import os
import numpy as np
import soundfile as sf
import torch
import run_rvc_pilot as pilot

BASE = Path(__file__).resolve().parent
OUT = Path('D:/总进度/目标人物分析/素材同文本普通声转换对比')

def main():
    pilot.settings()
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    from huggingface_hub import snapshot_download, HfApi
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    import librosa
    OUT.mkdir(parents=True, exist_ok=True)
    source = Path('D:/总进度/目标人物语音/Track 9.wav')
    audio, sr = sf.read(source)
    audio = audio[:15 * sr].mean(axis=1).astype(np.float32)
    sf.write(OUT/'目标人物原声_前15秒.wav',audio,sr,subtype='PCM_16')
    repo = 'openai/whisper-small'
    revision = HfApi().model_info(repo).sha
    print('Downloading local transcription model ' + revision, flush=True)
    model_path = snapshot_download(repo,revision=revision,
        allow_patterns=['config.json','generation_config.json','preprocessor_config.json',
                        'tokenizer_config.json','tokenizer.json','vocab.json','merges.txt',
                        'normalizer.json','special_tokens_map.json','added_tokens.json',
                        'model.safetensors'],max_workers=4)
    print('Local transcription model ready', flush=True)
    processor = WhisperProcessor.from_pretrained(model_path)
    model = WhisperForConditionalGeneration.from_pretrained(model_path,
                torch_dtype=torch.float16, use_safetensors=True).to('cuda')
    x = librosa.resample(audio,orig_sr=sr,target_sr=16000)
    inputs = processor(x,sampling_rate=16000,return_tensors='pt',return_attention_mask=True)
    model.generation_config.forced_decoder_ids = None
    with torch.inference_mode():
        ids = model.generate(inputs.input_features.to('cuda',dtype=torch.float16),
                             attention_mask=inputs.attention_mask.to('cuda'),
                             language='zh',task='transcribe',num_beams=5,
                             max_new_tokens=200)
    text = processor.batch_decode(ids,skip_special_tokens=True)[0].strip()
    if not text:
        raise RuntimeError('Empty transcription')
    (OUT/'素材前15秒_识别文本.txt').write_text(text+'\n',encoding='utf-8')
    report = dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  start_seconds=0,end_seconds=15,text=text,
                  transcription_model=repo,revision=revision,
                  audio_uploaded=False,verbatim_accuracy='not human verified',
                  output_folder=str(OUT))
    (OUT/'转写记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__ == '__main__':
    main()
