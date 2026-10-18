"""One low-impact waveform clarity control, not acoustic retraining/phoneme repair."""
from pathlib import Path
from math import gcd
import numpy as np,soundfile as sf
from scipy.signal import lfilter,freqz,resample_poly
from run_knn_controls import read,save,sha,BASE
OLD=Path('D:/总进度/目标人物分析/自然真实输入基线_2026-10-04')
CONTROL=Path('D:/总进度/目标人物分析/真实输入与评价复核_2026-10-04')
OUT=Path('D:/总进度/目标人物分析/真实输入轻度清晰度检查_2026-10-04');OUT.mkdir(exist_ok=True)
CLARIFICATION='字基本没错，但声母、字与字的边界有点糊'
def shelf(sr,fc=2400,gain_db=2):
 A=10**(gain_db/40);w=2*np.pi*fc/sr;c=np.cos(w);alpha=np.sin(w)/2*np.sqrt(2);t=2*np.sqrt(A)*alpha
 b=A*np.array([(A+1)+(A-1)*c+t,-2*((A-1)+(A+1)*c),(A+1)+(A-1)*c-t])
 a=np.array([(A+1)-(A-1)*c+t,2*((A-1)-(A+1)*c),(A+1)-(A-1)*c-t])
 return b/a[0],a/a[0]
def main():
 manifest=read(OLD/'baseline_manifest.json');row=manifest['converted'];source=manifest['source']
 for r in [row,source]:assert sha(r['path'])==r['sha256']
 x,sr=sf.read(row['path']);assert sr==22050 and x.ndim==1
 b,a=shelf(sr);poles=np.roots(a);assert np.max(np.abs(poles))<1
 frequencies,response=freqz(b,a,worN=4096,fs=sr);gain=20*np.log10(np.maximum(np.abs(response),1e-12))
 assert abs(gain[0])<1e-6 and np.max(gain)<=2.001 and gain[-1]>1.99
 y=lfilter(b,a,x);assert np.isfinite(y).all() and np.sqrt(np.mean(y*y))>1e-6
 loudness_factor=min(float(np.sqrt(np.mean(x*x))/np.sqrt(np.mean(y*y))),.95/float(np.max(np.abs(y))))
 y*=loudness_factor;dest=OUT/'真实男声转换_轻度清晰度增强.wav';sf.write(dest,y,sr,subtype='PCM_24')
 reread,rs=sf.read(dest);assert rs==sr and len(reread)==len(x) and np.max(np.abs(reread))<.999
 record=dict(row,label='real_male300_env02_gentle_clarity2dB',group='gentle_clarity_control',path=str(dest),sha256=sha(dest),
  expected_text=source['expected_text'],text_origin=source['text_origin'],waveform_clarity_postfilter=True,
  filter_kind='single stable causal high-shelf biquad',high_shelf_fc_hz=2400,high_shelf_gain_db=2,
  parent_conversion_path=row['path'],parent_conversion_sha256=row['sha256'],subjective_acceptance=False,
  postfilter_only_causal=True,causal_streaming=False,source_speaker_enrollment=False,board_deployed=False,
  no_acoustic_retraining=True,manual_pitch_or_speed_change=False)
 baseline=dict(row,label='real_male300_env02_natural_baseline',group='natural_baseline',
  expected_text=source['expected_text'],text_origin=source['text_origin'])
 save(OUT/'evaluation_items.json',[baseline,record]);save(OUT/'conversion_item.json',record)
 save(OUT/'filter_manifest.json',dict(date='2026-10-04',human_clarification=CLARIFICATION,
  script_sha256=sha(__file__),b=b.tolist(),a=a.tolist(),pole_max_radius=float(np.max(np.abs(poles))),
  max_response_gain_db=float(np.max(gain)),dc_gain_db=float(gain[0]),loudness_factor=loudness_factor,
  new_outputs=1,model_changed=False,original_preserved=sha(row['path'])==row['sha256'],
  frame_lookahead_added=0,full_teacher_still_noncausal=True,not_a_phoneme_reconstruction_method=True,
  no_actual_naturalness_or_clarity_gain_claimed=True,no_board_write=True))
 m=read(OLD/'baseline_manifest.json');m.update(human_clarification=CLARIFICATION,
  articulation_issue_type='Consonant/word boundaries blurry, words basically correct',clarification_date='2026-10-04')
 save(OLD/'baseline_manifest.json',m)
 for f in ['architecture_choice.json','decision.json']:
  m=read(CONTROL/f);m.update(human_clarification=CLARIFICATION,clarification_date='2026-10-04');save(CONTROL/f,m)
 print('ONE GENTLE CLARITY CONTROL READY',flush=True)
if __name__=='__main__':main()
