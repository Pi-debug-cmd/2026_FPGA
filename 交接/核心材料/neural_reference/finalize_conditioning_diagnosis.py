from pathlib import Path
from collections import defaultdict
import json,hashlib
import numpy as np,soundfile as sf
BASE=Path(__file__).resolve().parent;OUT=Path('D:/总进度/目标人物分析/V1音色来源排查')
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 cross=read(OUT/'conditioning_cross_eval.json');content=read(OUT/'conditioning_content_eval.json')
 by={r['label']:r for r in content['files']};metrics={r['label']:r for r in cross['files']}
 wes=next(r for r in cross['models'] if r['evaluator'].startswith('WeSpeaker'));ut=next(r for r in cross['models'] if r['evaluator'].startswith('UTMOS'))
 prefix=hashlib.sha256((cross['protocol']+wes['weight']['sha256']+ut['weight']['sha256']+cross['utmos_source_sha256']).encode()).hexdigest()[:16]
 cache=Path('D:/总进度/目标人物分析/中文交叉评估/cache')
 def vec(p):return np.load(cache/(prefix+'_'+sha(p)+'.npz'))['vector']
 pairs=[]
 for row in read(OUT/'roundtrip_items.json'):
  pairs.append(dict(track=row['test_name'],matched_source_to_reconstruction_raw_cosine=float(vec(row['source_path'])@vec(row['path'])),
   source_mos=metrics['vocoder_input_'+row['test_name']]['utmos_predicted'],
   reconstruction_mos=metrics[row['label']]['utmos_predicted'],
   role='Signal reconstruction diagnostic only; not converted arbitrary speech'))
 group=defaultdict(list);integrity=[]
 for r in read(OUT/'cross_items.json'):
  assert sha(r['path'])==r['sha256'];x,sr=sf.read(r['path']);assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6
  integrity.append(dict(label=r['label'],sha256=r['sha256'],seconds=len(x)/sr,clipped_fraction=float(np.mean(np.abs(x)>=.999))))
  if r['label'] in by and r['group'] not in ['input_controls','reproduce_clip2']:group[r['group']].append(metrics[r['label']])
 summary=[]
 for k,rows in group.items():
  summary.append(dict(group=k,count=len(rows),mean_cosine=float(np.mean([r['wespeaker_raw_cosine_to_centroid'] for r in rows])),
   mean_mos=float(np.mean([r['utmos_predicted'] for r in rows])),mean_cer=float(np.mean([by[r['label']]['asr_character_error_rate'] for r in rows]))))
 baseline=next(r for r in read(Path('D:/总进度/目标人物分析/SeedVC完整V2对照/matched_summary.json'))['groups'] if r['group']=='rejected_personal_v1_matched4')
 summary.append(baseline)
 decision=dict(status='diagnostics_complete_no_new_audition_selected',baseline_reproduction=read(OUT/'baseline_reproduction.json'),
  roundtrip_pairs=pairs,conditioning_groups=summary,preferred_comparison_baseline='personal V1 step300/CFG.3, still not accepted',
  conversions=13,target_reconstruction_diagnostics=5,subjective_acceptance=False,board_deployed=False,
  conclusion='Vocoder paired identity changes are small; no evidence yet that it is dominant cause. Reference/style variations do not consistently improve naturalness/content; none promoted by identity score alone.',
  next_action='Test kNN-VC fixed target feature retrieval on identical source controls; no source enrollment and no more V2 audition.')
 save(OUT/'diagnosis_decision.json',decision);save(OUT/'audio_integrity.json',integrity)
 table='\n'.join(f"|{r['group']}|{r['count']}|{r['mean_cosine']:.4f}|{r['mean_mos']:.3f}|{r['mean_cer']:.4f}|" for r in summary)
 pairs_table='\n'.join(f"|{r['track']}|{r['matched_source_to_reconstruction_raw_cosine']:.4f}|{r['source_mos']:.3f}|{r['reconstruction_mos']:.3f}|" for r in pairs)
 report=f'''# V1音色来源排查

用户明确认为上次对照②好于③，③退步；完整V2候选拒绝。个人V1第300步/CFG0.3保留为比较基线，仍有厚重、不自然问题，未接受。

先用相同权重、固定源音频、随机种子与目标参考复现②。解码采样最大绝对误差为0.0；WAV文件哈希因容器元数据不同而不同，不能误称波形变化。记录见baseline_reproduction.json。

## 还原过程隔离

把目标录音提取频谱后，仅送入原BigVGAN，不执行音色转换。5条重建只用于检查还原过程，绝不能当任意人到目标人物的转换成果。前4条各8秒，Track9前15秒只作诊断，不用于模型训练或人物条件。

|录音|同一源片段→重建原始身份余弦|原片段自然度预测|重建自然度预测|
|---|---:|---:|---:|
{pairs_table}

身份诊断变化小，当前不足以把声码器定为主要问题；自然度预测不能证明厚薄、鼻音和气声都被保留。梅尔范围/采样率/窗函数与固定声码器配置已核对匹配，没有发现需要立即修正的频率配置问题。

## 目标条件隔离

相同V1权重、30步/CFG0.3/固定种子，分别改用Track5前8秒、Track8前8秒，以及保留Track6前8秒频谱提示但用Track5—8前8秒CAMPPlus特征的原始平均人物条件；共12条转换，加1条基线复现为13条。平均条件是实验改动，未宣称官方默认方法；没有训练或改变权重，没有用Track9条件，没有源人物注册。

|版本|相同输入数|中文身份原始余弦均值|自然度预测均值|ASR CER均值|
|---|---:|---:|---:|---:|
{table}

更换参考或平均人物条件未一致保住自然度与内容；平均条件的身份诊断较高，但男声同文本自然度预测反而下降，不因此请求新试听。自动分数不改变用户对②/③的结论，②仍未达到目标。

本轮检查结束，下一步测试官方kNN-VC固定目标语音特征检索：目标库只用Track5—8，固定同一批普通输入；先检查中文内容和人物音色，电脑质量诊断不代表7020实时可行性。原始录音/旧模型/SD均保留，不上传音频。

当前任务：检验固定目标语音特征检索是否比②更适合本项目。
'''
 (OUT/'音色来源排查说明.md').write_text(report,encoding='utf-8')
 print(json.dumps(dict(roundtrip_pairs=pairs,groups=summary,selected_for_audition=False),ensure_ascii=False))
if __name__=='__main__':main()
