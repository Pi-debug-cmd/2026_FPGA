"""Freeze cross-model diagnostics and prepare one short, labeled human audition."""
from pathlib import Path
from importlib.metadata import distributions
import hashlib,json
from math import gcd
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

BASE=Path(__file__).resolve().parent
OUT=Path('D:/总进度/目标人物分析/音色与自然度复查')
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    cross=read(OUT/'review_cross_eval.json');content=read(OUT/'review_content_eval.json')
    items=read(OUT/'all_review_items.json');neural=read(OUT/'neural_control_manifest.json')
    by_path={str(Path(r['path']).resolve()):r for r in content['files']}
    cross_path={str(Path(r['path']).resolve()):r for r in cross['files']}
    wes=next(r for r in cross['models'] if r['evaluator'].startswith('WeSpeaker'))
    ut=next(r for r in cross['models'] if r['evaluator'].startswith('UTMOS'))
    prefix=hashlib.sha256((cross['protocol']+wes['weight']['sha256']+ut['weight']['sha256']+cross['utmos_source_sha256']).encode()).hexdigest()[:16]
    cache=OUT.parent/'中文交叉评估/cache'
    def vector(path):
        data=np.load(cache/(prefix+'_'+sha(path)+'.npz'))
        return data['vector']
    target_vectors=[vector(Path(f'D:/总进度/目标人物语音/Track {n}.wav')) for n in range(5,9)]
    centroid=np.mean(target_vectors,axis=0);centroid/=np.linalg.norm(centroid)
    integrity=[];source_diagnostics=[]
    for row in items:
        path=Path(row['path']);assert sha(path)==row['sha256']
        x,sr=sf.read(path);assert np.isfinite(x).all() and np.sqrt(np.mean(x*x))>1e-6
        check=dict(label=row['label'],sha256=row['sha256'],seconds=len(x)/sr,peak=float(np.max(np.abs(x))),clipped_fraction=float(np.mean(np.abs(x)>=.9999)))
        if row.get('source_path'):
            assert sha(row['source_path'])==row['source_sha256']
            y,ysr=sf.read(row['source_path']);check['duration_error_seconds']=abs(len(x)/sr-len(y)/ysr);assert check['duration_error_seconds']<.1
            source_vector=vector(row['source_path']);output_vector=vector(path)
            source_diagnostics.append(dict(label=row['label'],group=row['group'],source_sha256=row['source_sha256'],
                source_to_target_raw_cosine=float(source_vector@centroid),output_to_target_raw_cosine=float(output_vector@centroid),
                output_to_source_raw_cosine=float(output_vector@source_vector),
                limitation='Embedding diagnostics cannot prove perceptual source-trait removal.'))
        integrity.append(check)
    save(OUT/'source_trait_diagnostics.json',dict(files=source_diagnostics,protocol=cross['protocol']))
    save(OUT/'signal_integrity.json',dict(status='complete',files=integrity))
    new_hashes={r['sha256'] for r in neural['files']}
    groups=['openvoice_mean4_tracks','openvoice_track6_8s','seed_generic_reference','seed_personal300_cfg03','rvc_e120_neural']
    summaries=[]
    for group in groups:
        rows=[r for r in cross['files'] if r.get('group')==group and r.get('source_sha256') in new_hashes]
        assert len(rows)==2
        qualities=[by_path[str(Path(r['path']).resolve())] for r in rows]
        summaries.append(dict(group=group,inputs=2,
            mean_mandarin_raw_cosine=float(np.mean([r['wespeaker_raw_cosine_to_centroid'] for r in rows])),
            minimum_mandarin_raw_cosine=min(r['wespeaker_raw_cosine_to_centroid'] for r in rows),
            mean_predicted_naturalness=float(np.mean([r['utmos_predicted'] for r in rows])),
            mean_asr_cer=float(np.mean([r['asr_character_error_rate'] for r in qualities])),
            mean_same_text_spectral_distance=float(np.mean([r['same_text_spectral_distance']['mean_mfcc1_20_euclidean'] for r in qualities]))))
    choice=next(r for r in items if r['label']=='seed_personal300_cfg03_zm_010')
    ordinary=next(r for r in neural['files'] if r['voice']=='zm_010')
    target=Path(choice['same_text_target']);source=Path(choice['source_path']);converted=Path(choice['path'])
    previews=[];clip_arrays=[]
    for number,label,path in [(1,'目标人物原声',target),(2,'普通中文输入',source),(3,'转换后声音',converted)]:
        x,sr=sf.read(path,dtype='float32')
        if x.ndim==2:x=x.mean(axis=1)
        x=x[:sr*6];factor=gcd(sr,24000);x=resample_poly(x,24000//factor,sr//factor).astype('float32')[:144000]
        assert len(x)==144000
        x*=min(.04/max(float(np.sqrt(np.mean(x*x))),1e-8),.95/max(float(np.max(np.abs(x))),1e-8))
        x[:120]*=np.linspace(0,1,120,dtype='float32');x[-120:]*=np.linspace(1,0,120,dtype='float32')
        output=OUT/f'{number}_{label}_6秒.wav';sf.write(output,x,24000,subtype='PCM_16')
        previews.append(dict(order=number,label=label,source=str(path),source_sha256=sha(path),path=str(output),sha256=sha(output),seconds=6))
        clip_arrays.append(x)
    joined=OUT/'18秒试听_目标原声_普通输入_转换结果.wav'
    gap=np.zeros(4800,dtype='float32');sf.write(joined,np.concatenate([clip_arrays[0],gap,clip_arrays[1],gap,clip_arrays[2]]),24000,subtype='PCM_16')
    save(OUT/'audition_provenance.json',dict(path=str(joined),sha256=sha(joined),seconds=18.4,clips=previews,
        ordinary_input_source=ordinary,selected_conversion=choice,
        target_audio_is_conversion_input=False,text_changed=False,text_representation_note='Same ASR-derived text normalized from traditional to simplified characters; ASR text not human proofread',
        excerpt_note='First6s of each clip; different speaking rates, not word-aligned. Only volume/resampling/end5ms fades, no pitch/speed editing.'))
    selected_score=cross_path[str(converted.resolve())];selected_content=by_path[str(converted.resolve())]
    decision=dict(status='awaiting_one_short_audition',original_rejected_candidate_still_rejected=True,
        selected_candidate=choice,selected_metrics=dict(mandarin_raw_cosine=selected_score['wespeaker_raw_cosine_to_centroid'],
            predicted_naturalness=selected_score['utmos_predicted'],asr_cer=selected_content['asr_character_error_rate'],
            spectral_distance=selected_content['same_text_spectral_distance']['mean_mfcc1_20_euclidean']),
        comparisons_on_same_two_generic_inputs=summaries,conversions=26,generic_source_controls=2,
        hearing_result=None,subjective_acceptance=False,arbitrary_live_speaker_acceptance=False,
        board_deployed=False,board_latency_measured=False,audio_uploaded=False,active_jobs=0,
        user_action='Listen once to18.4s three-part audition:1 target,2 ordinary input,3 conversion. Judge3 against1 for target identity/naturalness.',
        selection_reason='Personal300/.3 balances identity/naturalness/content on both generic inputs; male preset gives clear source-to-target pitch/identity separation, rather than selecting only largest identity score.',
        next_if_accepted='Broaden natural-source/live evaluation and design causal small-student budget; this is not permission to declare7020 feasibility.',
        next_if_rejected='Treat as teacher failure; try source-trait-suppression architecture such as genuine Seed V2 with AR+CFM, rather than more V1 iterations/metrics alone.',
        limitation='New generic inputs are synthetic controls, not new real people; one fixed-target/offline audition cannot establish any-to-one realtime on7020.')
    previous=read(OUT/'review_decision.json') if (OUT/'review_decision.json').exists() else {}
    if previous.get('human_feedback'):
        for key in ['status','hearing_result','subjective_acceptance','human_feedback','next_action']:
            if key in previous:decision[key]=previous[key]
    save(OUT/'review_decision.json',decision)
    (OUT/'environment_freeze.txt').write_text('\n'.join(sorted(f'{d.metadata["Name"]}=={d.version}' for d in distributions()))+'\n',encoding='utf-8')
    table='\n'.join(f"| {r['group']} | {r['mean_mandarin_raw_cosine']:.4f} | {r['mean_predicted_naturalness']:.3f} | {r['mean_asr_cer']:.4f} | {r['mean_same_text_spectral_distance']:.2f} |" for r in summaries)
    report=f'''# 音色与自然度复查：新普通中文输入与另一种转换模型

日期2026-10-03。用户授权持续推进，直到需要协助/试听或完成目标。本轮电脑测试和整理已经完成，当前仅需一次短试听反馈；没有后台任务，最终7020任意人物实时转换未完成。

## 做了什么

之前同文本普通声使用SAPI Kangkang，自然度预测约2.924，可能成为测试干扰因素，但没有证明它是失败的主因。本轮用[官方Kokoro中文模型](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh)在本机生成两个普通预设声音，朗读同一ASR提取的文字。原输入不含目标人物音色条件；没有上传目标录音，也没有把目标原声直接送入转换。文字只是繁简表示归一化，没有改写；机器转写尚未经人工逐字核对。

在相同两个普通新输入上对比：未个人微调的Seed V1、个人300步/CFG0.3、原RVC120轮、OpenVoiceV2两种固定目标参考（四段平均/Track6前8秒）。另外OpenVoice两种参考各测原来8个输入。本轮共26段转换、2段新普通合成输入，总共10个输入音频，不能说10名真人。

## 同一组两个普通新输入上的诊断

| 版本 | 中文身份原始余弦平均 ↑ | 自然度预测平均 ↑ | ASR CER平均 ↓ | 同文本MFCC-DTW平均 ↓ |
|---|---:|---:|---:|---:|
{table}

两个新普通输入自然度预测均值约3.493，身份对目标均值约0.0725。个人Seed均值约0.9341，自然度约3.479，平均ASR CER约0.0678，与两段新原声识别错误均值相同；不能把余弦当“93%像”。它在相同新输入上比未个人微调Seed的身份/自然度诊断更好，但没有听感结果，不是人物音色已合格。RVC同文本频谱距离仍较低，Seed没有全面领先。更自然的普通声可能改善了测试条件，不能把换输入所得全部变化都归因于模型。

OpenVoice两种参考在这些测试上身份分低于Seed，不能凭更换项目名称就取代当前教师。OpenVoice自动从本段输入提取源声特征，无人工注册，但整段提取尚非因果流式。其完整10输入结果在review_cross_eval.json，不能与两个输入的均值混比。

已用同一中文嵌入缓存比较输出→源人、输出→目标、源人→目标，见source_trait_diagnostics.json。此空间的距离不足以判断厚薄/鼻音/气声，也不能证明源人物所有听觉特征已被消除。对于选定新输入，普通声F0中位约113Hz、转换约204Hz；另一普通声约256Hz、转换约206Hz，目标参考约193Hz。只是固定目标下不同输入的一项诊断，不是身份或实时验收。

## 本次只听一条18.4秒对照

文件`18秒试听_目标原声_普通输入_转换结果.wav`：1目标原声6秒、0.2秒间隔、2普通新输入6秒、0.2秒间隔、3个人Seed300步/CFG0.3转换6秒。判断3和1的人物音色及自然度；2展示转换输入不是目标原声。不同语速使各片段末尾未逐词对齐。

只对试听副本做单声道24k、音量匹配、端点5ms淡入淡出；没有升调、变速或改字。完整三段及原始人物录音均保留。来源、生成资产固定版本/SHA256、转换权重SHA256在neural_control_manifest.json、audition_provenance.json和review_decision.json。这里只请求一次选定结果反馈，避免让用户逐版试听。

若仍明显不像，继续教师路线，并考虑真正的Seed V2 AR+CFM等更强源人物特征抑制，不按声纹分继续盲目增加V1轮次。若音色接近可接受，也仍需真实说话人、真实麦克风连续验证以及因果小型学生/PS/PL预算，不能直接宣布7020部署可行。

## 工程完整性与兼容记录

28个转换/输入文件哈希、有限数值、非静音检查通过；26段转换原输入哈希及时长检查通过。削波文件数{sum(r['clipped_fraction']>0 for r in integrity)}。原模型、原人物录音和SD未改变。神经普通声严格核对并重载全部学习参数；PyPI Kokoro实现为旧ONNX导出新增了默认1/0的InstanceNorm仿射项，而固定中文检查点没有它们，本轮恢复affine=False，随后严格加载成功，没有跳过应加载的学习参数。仅绕开无关英语pipeline导入，使用官方KModel及中文G2P数学路径。

新增小型中文G2P依赖放在原D盘虚拟环境，未改Torch/RVC关键版本；环境清单随附。固定TTS仓库版本`01e7505bd6a7a2ac4975463114c3a7650a9f7218`，权重SHA256与官方模型卡一致。目标声音仍仅在本机处理。

当前任务：用户听1/2/3短对照，确认新转换的人物音色与自然度；之后继续对应工程路线。
'''
    (OUT/'复查与试听说明.md').write_text(report,encoding='utf-8')
    entry='''### 自然度干扰排查与新一次短试听（电脑任务已完成）

用户授权继续直到需要协助/试听或完成。已本地生成两种普通神经中文声，沿用同一ASR提取文字（繁简表示归一化、不改写）；对照未微调Seed、300步/CFG0.3、RVC和OpenVoice两参考，合计26个新转换及2个普通源控。OpenVoice另含原8输入，各组输入数不可混比。新个人Seed在同两输入上中文身份均值0.9341、UTMOS3.479、ASR CER0.0678，但仍是诊断，尚未听感验收；旧零样本“明显不像”反馈仍保留。新普通声身份对目标仅约0.0725，不是直接目标→目标重建。

已准备唯一18.4秒1/2/3对照：目标原声6秒→普通新输入6秒→个人300步/CFG0.3转换6秒。当前需要用户听3对1是否接近、是否自然；本次新结果尚无反馈，不要默认已接受或已被否定。路径`D:\\总进度\\目标人物分析\\音色与自然度复查\\18秒试听_目标原声_普通输入_转换结果.wav`，同目录`复查与试听说明.md`、`review_decision.json`。

所有任务结束，无后台工作，原声/模型/SD保留，无音频上传、板卡部署或实时延迟验收。最终仍是任意人麦克风实时转换，普通TTS仅作可重复测试。若仍失败，考虑真正Seed V2源人物抑制/其他教师架构，不无限加V1轮数；若通过，再做真人/连续麦克风与因果学生预算。用户只需短试听，暂不补录或上电。学习线不变。本条优先于下文“当前无试听要求”等历史状态。

'''
    handoff=Path('D:/总进度/ZYNQ7020人声转换项目_总目标与当前进度.md');text=handoff.read_text(encoding='utf-8')
    marker='## 最新工程进展：2026-10-03（优先于下文原有阶段计划）\n\n'
    if entry.split('\n')[0] not in text:handoff.write_text(text.replace(marker,marker+entry,1),encoding='utf-8')
    status=BASE.parent/'PROJECT_STATUS.md';text=status.read_text(encoding='utf-8')
    entry_en='''## Latest: generic-source confound control and single audition requested — 2026-10-03

- Completed26 new conversions and2 locally generated neural Mandarin generic-source controls using same ASR-derived text (script representation normalized, no content rewrite); compare Seed V1 zero-shot/personal300-CFG.3, frozen RVC and2 OpenVoice target profiles. OpenVoice also tested old8 sources; do not mix10-input means with2-input means. On same2 new sources, personal Seed mean Mandarin raw cosine.9341/UTMOS3.479/ASR CER.0678 vs raw sources' identity.0725/MOS3.493. Diagnostics only; no new human acceptance. Older zero-shot audition rejection remains valid. Input/confound changes are not pure model gains. All hashes/finite/non-silent/durations checked; all jobs complete; no audio upload/SD/board changes.
- Prepared18.4s audition:1 target original6s,2 ordinary new generic male preset6s,3 personal300/.3 conversion6s; target not used as conversion input. Need one listener judgment3 vs1. No source enrollment; source embedding in OpenVoice is whole-clip/noncausal. No live/7020 acceptance. If still unlike, investigate true Seed V2 AR+CFM/source-trait suppression rather than endless V1 fine-tuning; if accepted, broaden real/live validation and causal-student PS/PL budget. Artifacts: `D:\\总进度\\目标人物分析\\音色与自然度复查`. No active jobs, user hardware action unnecessary; current action is one short audition. This supersedes earlier no-audition statements.

'''
    if entry_en.split('\n')[0] not in text:status.write_text(text.replace('# Zynq-7020 Low-Latency Voice Conversion Project\n\n','# Zynq-7020 Low-Latency Voice Conversion Project\n\n'+entry_en,1),encoding='utf-8')
    print(json.dumps(dict(status='awaiting_audition',audition=str(joined),seconds=18.4,metrics=summaries,conversions=26),ensure_ascii=False))

if __name__=='__main__':main()
