"""Separate measured diagnostics from phonetic acceptance; no phoneme model.

Human failures bind to exact waveform hashes. An absence of failure, ASR match,
high identity cosine, or MOS never automatically validates pronunciation.
"""
from pathlib import Path
import hashlib
import json

REGISTRY=Path('D:/总进度/目标人物分析/发音审核修正_2026-10-04/pronunciation_reviews.json')

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while block:=f.read(4*1024*1024): h.update(block)
 return h.hexdigest()

def load_reviews(path=REGISTRY):
 if not Path(path).exists(): return []
 data=json.loads(Path(path).read_text(encoding='utf-8'))
 if data.get('version')!=1 or not isinstance(data.get('reviews'),list):
  raise ValueError('Malformed pronunciation review registry')
 for r in data['reviews']:
  if r.get('result') not in ['failed','partial','passed'] or len(r.get('audio_sha256',''))!=64:
   raise ValueError('Malformed pronunciation review')
 return data['reviews']

def assess(item,reviews):
 actual=digest(item['path'])
 if item.get('sha256') and actual!=item['sha256']:
  raise ValueError('Audio hash changed: '+item['path'])
 matching=[r for r in reviews if r['audio_sha256']==actual]
 if any(r['result']=='failed' for r in matching): status='failed_human_review'
 elif any(r['result']=='partial' for r in matching): status='partial_human_review_not_accepted'
 elif matching: status='passed_specific_human_review_only'
 else: status='not_assessed'
 return dict(audio_sha256=actual,status=status,human_reviews=matching,
  automatically_verified_phonemes=False,asr_word_match_proves_correct_pronunciation=False,
  speaker_or_mos_score_proves_correct_pronunciation=False,can_auto_approve=False,
  scope='Only exact reviewed waveform and listening scope, not all source speakers, all syllables, streaming or board acceptance.',
  limitation='This gate records evidence/blocks misinterpretation; it does not detect, align or repair phonemes.')

def annotate_report(report,registry=REGISTRY):
 reviews=load_reviews(registry)
 for item in report['files']:
  item['pronunciation_review']=assess(item,reviews)
 statuses=[r['pronunciation_review']['status'] for r in report['files']]
 report['pronunciation_audit']=dict(registry_path=str(registry),
  failed_human_reviews=statuses.count('failed_human_review'),
  not_assessed=statuses.count('not_assessed'),
  validated_automatic_phone_evaluator=False,automatic_pronunciation_approval=False,
  overall_candidate_approved=False,
  instruction='Keep pronunciation independent from ASR transcript, speaker identity, MOS and signal integrity. Any human failure stays a failure regardless of scores.')
 return report
