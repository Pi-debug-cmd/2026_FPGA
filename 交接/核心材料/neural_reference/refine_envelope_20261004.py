"""One controlled strength change after partial human improvement; no retraining."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,soundfile as sf,torch
from run_rvc_pilot import settings
settings()
BASE=Path(__file__).resolve().parent;ROOT=BASE/'Seed-VC'
OLD=Path('D:/总进度/目标人物分析/局部音色包络校正')
OUT=OLD/'2026-10-04_校正细化';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def feedback():
 d=read(OLD/'decision.json')
 d.update(status='human_partial_improvement_not_accepted',hearing_result='partial_improvement',
  human_feedback='好一些，但还是差一点',human_feedback_date='2026-10-04',subjective_acceptance=False,
  preferred_comparison_baseline='Smoothed envelope 0.2, human partial improvement only',
  overall_improvement_demonstrated=False,
  next_step='Same four inputs/model/pool/40ms EMA, controlled strength 0.2 to 0.3; no board acceptance.')
 save(OLD/'decision.json',d);save(OUT/'human_feedback.json',dict(feedback=d['human_feedback'],
  selected=d['selected'],hearing_result='partial_improvement',subjective_acceptance=False,date='2026-10-04'))
 p=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');s=p.read_text(encoding='utf-8')
 heading='## 最新反馈与细化：2026-10-04'
 if heading not in s:
  insert=heading+'\n\n用户对平滑0.2音色校正明确反馈“好一些，但还是差一点”。保存为有局部改善、仍未通过验收的新比较基线；完整V2退步仍保持拒绝。下一轮固定相同四输入、个人V1第300步/CFG0.3、目标5—8检索库及40ms平滑，只比较0.2与0.3校正强度。没有重新训练、源人物注册或板卡部署。以下历史待0.2试听的文字已经过时。电脑细化中，用户暂不需要上电、接线或补录。完成后保存评估与一次短对照；不能把单条试听改善称作任意人实时转换完成。\n\n'
  s=s.replace('更新时间：2026-10-03','更新时间：2026-10-04',1)
  s=s.replace('## 最新工程进展：',insert+'## 最新工程进展：',1);p.write_text(s,encoding='utf-8')
 p=BASE.parent/'PROJECT_STATUS.md';s=p.read_text(encoding='utf-8');heading='## Latest: partial human improvement; controlled envelope refinement — 2026-10-04'
 if heading not in s:
  first,rest=s.split('\n',1);s=first+'\n\n'+heading+'\n\nHuman feedback: 好一些，但还是差一点. Smoothed envelope 0.2 becomes a partially improved, still unaccepted comparison baseline. V2 remains rejected. Next preserve four sources, personal V1 checkpoint/CFG, target pool and 40ms EMA; only change strength to 0.3. No training/source enrollment/board or realtime acceptance. PC refinement in progress; historical pending 0.2 audition is superseded.\n'+rest;p.write_text(s,encoding='utf-8')
def main():
 feedback();print('FEEDBACK SAVED',flush=True)
 torch.set_num_threads(4)
 sys.path.insert(0,str(ROOT));from modules.bigvgan.bigvgan import BigVGAN
 asset=next(r for r in read(ROOT/'checkpoints/pinned/strong_manifest.json') if r['repository']=='nvidia/bigvgan_v2_22khz_80band_256x')
 for f in asset['files']:assert sha(f['path'])==f['sha256']
 model=BigVGAN.from_pretrained(asset['local'],use_cuda_kernel=False);model.remove_weight_norm();model=model.to('cuda').eval()
 old=read(OLD/'smoothed_items.json');rows=[];checks=[];alpha=1-np.exp(-256/22050/.04)
 for row in old:
  for key,hkey in [('path','sha256'),('source_path','source_sha256'),('prepared_source_path','prepared_source_sha256')]:assert sha(row[key])==row[hkey]
  assert sha(row['checkpoint']['path'])==row['checkpoint']['sha256']
  d=np.load(OLD/(row['test_name']+'_mel_diagnostics.npz'));base=d['baseline_mel'];residual=d['bounded_residual']
  filtered=np.empty_like(residual);state=np.zeros(residual.shape[0],dtype='float32')
  for t in range(residual.shape[1]):state+=alpha*(residual[:,t]-state);filtered[:,t]=state
  for amount in [.2,.3]:
   corrected=base+amount*filtered
   with torch.inference_mode():y=model(torch.from_numpy(corrected).unsqueeze(0).to('cuda')).squeeze().cpu().numpy()
   assert np.isfinite(y).all() and np.sqrt(np.mean(y*y))>1e-6
   y*=min(.04/float(np.sqrt(np.mean(y*y))),.95/float(np.max(np.abs(y))))
   folder=OUT/('reproduction_0.2' if amount==.2 else 'smoothed_envelope_0.3');folder.mkdir(exist_ok=True)
   dest=folder/(row['test_name']+'.wav');sf.write(dest,y,22050,subtype='PCM_24')
   x,sr=sf.read(dest);assert sr==22050 and np.isfinite(x).all() and np.max(np.abs(x))<.999
   if amount==.2:
    previous,psr=sf.read(row['path']);assert psr==sr and previous.shape==x.shape
    err=float(np.max(np.abs(x-previous)));assert err<=2/8388608,err
    checks.append(dict(test_name=row['test_name'],max_sample_error=err,previous_sha256=row['sha256'],reproduction_sha256=sha(dest)))
   else:
    rows.append(dict(row,label='smoothed_envelope_0.3_'+row['test_name'],group='smoothed_envelope_0.3',amount=.3,
     path=str(dest),sha256=sha(dest),human_feedback=None,subjective_acceptance=False,
     parent_baseline_path=row['path'],parent_baseline_sha256=row['sha256'],mel_diagnostics_sha256=sha(OLD/(row['test_name']+'_mel_diagnostics.npz'))))
   print(row['test_name'],amount,'COMPLETE',flush=True)
 save(OUT/'conversion_items.json',rows);save(OUT/'baseline_reproductions.json',checks)
 save(OUT/'generation_manifest.json',dict(script_sha256=sha(__file__),changed_variable='envelope strength 0.2 to 0.3',
  four_fixed_inputs=True,ema_seconds=.04,causal_streaming=False,board_deployed=False,training_performed=False,
  original_baseline_preserved=all(sha(r['path'])==r['sha256'] for r in old)))
 print('GENERATION COMPLETE',flush=True)
if __name__=='__main__':main()
