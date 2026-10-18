"""No winner from numerical controls; one short component-isolation question."""
from pathlib import Path
from math import gcd
import json,hashlib,shutil
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from finalize_post_rejection_phase import summaries
BASE=Path(__file__).resolve().parent;OUT=Path('D:/总进度/目标人物分析/自然度与鼻音排查_2026-10-04')
OLD=Path('D:/总进度/目标人物分析/局部音色包络校正');DIAG=Path('D:/总进度/目标人物分析/V1音色来源排查')
V2=Path('D:/总进度/目标人物分析/SeedVC完整V2对照')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 items=[r for r in read(OUT/'evaluation_items.json') if r['group']!='input_controls']
 groups,metrics=summaries(read(OUT/'naturalness_cross_eval.json'),read(OUT/'naturalness_content_eval.json'),items)
 checks=[]
 for r in items:
  assert sha(r['path'])==r['sha256'] and sha(r['source_path'])==r['source_sha256']
  x,sr=sf.read(r['path']);assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6 and np.max(np.abs(x))<.999
  checks.append(dict(label=r['label'],sha256=r['sha256'],seconds=len(x)/sr,peak=float(np.max(np.abs(x))),clipped_fraction=0))
 save(OUT/'audio_integrity.json',checks);save(OUT/'matched_summary.json',dict(groups=groups,files=metrics))
 row=next(r for r in read(DIAG/'roundtrip_items.json') if r['test_name']=='track9')
 assert sha(row['path'])==row['sha256'] and sha(row['source_path'])==row['source_sha256']
 manifest=read(DIAG/'reference_manifest.json');ref=next(r for r in manifest['references'] if 'track9_' in r['path'])
 assert ref['role']=='diagnostic only; excluded from conditioning' and sha(ref['original'])==ref['original_sha256']
 p1=OUT/'1_目标人物原声_6秒.wav';shutil.copy2(V2/'1_目标人物原声_6秒.wav',p1)
 y,sr=sf.read(row['path'],dtype='float32');y=resample_poly(y,24000//gcd(sr,24000),sr//gcd(sr,24000))[:144000]
 assert len(y)==144000;y*=min(.04/float(np.sqrt(np.mean(y*y))),.95/float(np.max(np.abs(y))))
 y[:120]*=np.linspace(0,1,120);y[-120:]*=np.linspace(1,0,120)
 p2=OUT/'2_诊断专用_同原声经声码器重建_6秒.wav';sf.write(p2,y,24000,subtype='PCM_16')
 a,ar=sf.read(p1,dtype='float32');b,br=sf.read(p2,dtype='float32');assert ar==br==24000 and len(a)==len(b)==144000
 audition=OUT/'12秒定位_目标原声_仅声码器重建.wav';sf.write(audition,np.concatenate([a,np.zeros(4800,dtype='float32'),b]),24000,subtype='PCM_16')
 save(OUT/'audition_provenance.json',dict(path=str(audition),sha256=sha(audition),seconds=12.2,
  clips=[dict(order=1,role='original target comparator',path=str(p1),sha256=sha(p1),source_original=ref['original'],source_original_sha256=ref['original_sha256']),
   dict(order=2,role='DIAGNOSTIC ONLY: target waveform to native mel to frozen BigVGAN, not voice conversion',
    path=str(p2),sha256=sha(p2),reconstruction=row)],
  target9_used_for_training_or_conditioning=False,second_clip_is_conversion_result=False,
  no_personal_cfm_or_retrieval_correction_in_second_clip=True,manual_pitch_or_speed_change=False,
  preview_processing='same RMS.04 cap.95, 24k resampling, first6s, 5ms endpoint fades; clip1 directly reused'))
 save(OUT/'decision.json',dict(status='awaiting_vocoder_component_isolation_only',human_feedback=read(OUT/'human_feedback.json')['feedback'],
  subjective_acceptance=False,candidate_promoted=False,nasal_cause_confirmed=False,groups=groups,
  audition=str(audition),audition_is_not_conversion_demo=True,new_conversions=8,
  board_deployed=False,causal_streaming=False,board_latency_measured=False,audio_uploaded=False,active_jobs=0,
  question='Does target-only reconstruction clip2 have the same unnatural nasal quality compared to original clip1?',
  next_if_reconstruction_nasal='Investigate waveform/mel/vocoder reconstruction first; do not assume CFM alone is responsible.',
  next_if_reconstruction_natural='Investigate generated acoustics and target adaptation; no further envelope-strength tuning.',
  limits=['Human nasal judgment is not inferred from raw cosine, MOS or CER.',
   'Natural reconstruction of native target mel cannot prove vocoder has no artifacts on generated mel.',
   'Numerical controls change raw V1 acoustics; their nose quality is unassessed, not claimed repaired.',
   'Previously partial0.2 timbre improvement retained historically, both0.2/0.3 still unacceptable.',
   'Track9 excluded from conditioning/training, repeatedly diagnostic, not pristine holdout.']))
 table='\n'.join(f"|{r['group']}|{r['count']}|{r['mean_cosine']:.4f}|{r['mean_predicted_mos']:.3f}|{r['mean_cer']:.4f}|" for r in groups)
 report=f'''# 自然度与鼻音来源排查

日期：2026-10-04。最新用户反馈：{read(OUT/'human_feedback.json')['feedback']}。0.3未改进；0.2此前相对未校正版“好一些”，但当前确认两版都不自然、均未验收。停止包络强度微调，保留历史相对改善，不把它改写成自然度通过。

## 实际排查

两版共用同一V1声学模型、BigVGAN及局部校正，单凭两版均有鼻音不能确认哪层产生问题。重新生成去除局部校正的控制：相同个人V1第300步/CFG0.3/参考Track6前8秒/随机种子20261003，固定4份原准备PCM，FP32＋30步与FP32＋120步，各4条。没有重新训练、文字合成、变调或输入人物注册。8条新转换仅排查计算精度和采样精细度，尚未经过人耳鼻音确认，不宣称消除鼻音。更慢PC推理不是低延迟部署方案。

|组别|匹配输入数|中文声纹原始余弦均值|自然度预测均值|ASR CER均值|
|---|---:|---:|---:|---:|
{table}

保存逐条指标和完整性；数字不代表相似百分比或人耳自然度，“后鼻音”仍是用户听感而非已确认的鼻腔共振故障。此前5份目标原声只经过声码器重建，原片段与重建的声纹余弦约0.994—0.997；这只能提供身份变化较小的诊断，不能证明不存在鼻音。

## 必要的一次组件定位（非新变声成果）

`{audition}`，共12.2秒：①目标原声6秒，②同一原声的频谱经冻结BigVGAN重新合成6秒。②完全绕开人物声学转换模型和局部校正，只测试原声→频谱→声音重建。该重建在此前已经生成，本轮只提取短预览；不能把直接重建目标素材当任意人转换演示。原声预览复用已听过的①，音量、采样率与端点处理规则固定，无手动变调或变速。Track9仍只用于诊断对照，未入训练/参考库。

当前需要用户仅判断②是否也有刚才不自然的鼻音。若有，优先排查声音重建；若自然，优先排查声学模型生成频谱及人物适配。即使原生频谱重建自然，也不能断言声码器在模型生成的频谱上没有失真。

## 工程状态

8条新输出、原输入及重建文件SHA、非静音、有限值、削波检查完成。无后台作业、音频上传、板卡或SD改动。无需上电、接线或补录。完整转换仍非因果，无任意人实时、7020或端到端延迟验收。全部原声和候选保留；当前任务只需一次12秒组件定位，避免继续让用户听相近的调参版本。
'''
 (OUT/'鼻音排查与当前任务.md').write_text(report,encoding='utf-8')
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 phrase='此条覆盖历史待0.3试听状态。';addition='已完成8条无额外校正的精度/采样控制及匹配诊断，没有确认鼻音消失，也没有推广新版本。当前唯一用户动作是一次12.2秒组件定位：`'+str(audition)+'`，①原声、②同原声仅经过声码器重建（不是转换成果）；判断②是否也有鼻音。若②自然，优先检查声学模型；若②也不自然，优先检查重建环节。所有工作结束，无后台任务。详见`'+str(OUT/'鼻音排查与当前任务.md')+'`。'+phrase
 assert phrase in s;s=s.replace(phrase,addition,1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');phrase='Overrides historical pending0.3 audition.'
 assert phrase in s;s=s.replace(phrase,'Completed8 raw numerical/sampling controls and matched diagnostics, no demonstrated nasal repair or candidate promotion. Only pending action:12.2s original target→same target native-mel/BigVGAN reconstruction, diagnostic only (never any-to-one evidence), to locate unnatural quality. All jobs complete. Artifacts D:\\总进度\\目标人物分析\\自然度与鼻音排查_2026-10-04. '+phrase,1);p.write_text(s,encoding='utf-8')
 print('FINALIZED',str(audition),flush=True)
if __name__=='__main__':main()
