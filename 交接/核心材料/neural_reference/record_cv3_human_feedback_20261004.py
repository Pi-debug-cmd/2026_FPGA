from pathlib import Path
import json,hashlib
BASE=Path('D:/总进度/目标人物分析/中文文字到目标音色对照_2026-10-04')
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
feedback={'date':'2026-10-04','verbatim':'2像1，自然是自然，也挺像，但是感觉变得更正式了，节奏有点不一样，3会好一些，但还是会','audition_path':str(BASE/'新方案短对照_原目标声_同台词生成_真人识别生成.wav'),'clip2':{'likeness':'positive_user_feedback','naturalness':'positive_user_feedback','remaining_issue':'more formal delivery and different rhythm','pronunciation_fully_accepted':False},'clip3':{'improved':True,'remaining_issue':'user says 还是会, exact character and substitution clarification pending','fully_accepted':False},'does_not_prove_all_speakers_or_board_realtime':True}
save(BASE/'human_feedback_20261004.json',feedback)
d=read(BASE/'decision.json');d.update(status='human_partial_improvement_remaining_articulation_and_rhythm',subjective_acceptance=False,candidate_promoted=False,human_feedback_path=str(BASE/'human_feedback_20261004.json'),required_user_help='Optional localization of clip3 remaining problematic character; no new audition or recording required now.',next_action='Measure cached reference streaming and latency; repair articulation before full quality acceptance.');save(BASE/'decision.json',d)
rp=Path('D:/总进度/目标人物分析/发音审核修正_2026-10-04/pronunciation_reviews.json');r=read(rp)
p=BASE/'试听3.wav'
if not any(x['audio_sha256']==sha(p) for x in r['reviews']):r['reviews'].append(dict(audio_path=str(p),audio_sha256=sha(p),result='partial',date='2026-10-04',reviewer='human user',feedback=feedback['verbatim'],listening_scope='Third complete segment in14s composite, same normalized/faded waveform as 试听3.wav; original generated parent is not assigned exact review by hash.',issue='Improved but remaining issue unspecified, clarification pending.',error_reproduced_by_validated_phone_model=False))
save(rp,r)
text='\n\n## 2026-10-04 最新用户听感与正在进行的测量\n\n用户对新14秒对照反馈：②像①，较自然、较像，但更正式、节奏不同；③好一些，但仍有问题，具体字待定位。保留逐字反馈与音频哈希，不把机器拼音匹配当作咬字通过。当前进行固定目标人物条件缓存与分块输出速度测量。输入仍是完整预录音；这不是麦克风因果实时处理，更不是7020部署。无需开板或补录。\n'
for p in [Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md'),Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/PROJECT_STATUS.md')]:
 with p.open('a',encoding='utf8') as f:f.write(text)
print('HUMAN PARTIAL FEEDBACK RECORDED')
