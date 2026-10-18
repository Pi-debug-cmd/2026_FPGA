from pathlib import Path
base=Path(__file__).resolve().parent
source=(base/'qualify_feature_phone_guidance_20261006.py').read_text(encoding='utf-8')
source=source.replace('from fargan_feature_phone_model_20261006 import FeaturePhoneNet','from fargan_feature_phone_ctc_20261006 import FeaturePhoneCTC').replace('FeaturePhoneNet(','FeaturePhoneCTC(')
source=source.replace("out=budget/'fargan_phone_guidance'","out=budget/'fargan_phone_ctc'")
source=source.replace('feature_phone_step3000.pt','feature_phone_ctc_step10000.pt')
source=source.replace("(out/'body_vocabulary.json')","(budget/'fargan_phone_guidance/body_vocabulary.json')")
source=source.replace("summary[0]['accuracy']>=.65 and summary[1]['accuracy']>=.55","summary[0]['sequence_error_rate']<=.25 and summary[1]['sequence_error_rate']<=.25")
source=source.replace('thresholds=dict(source_accuracy=.65,teacher_accuracy=.55)','thresholds=dict(source_sequence_error_rate_max=.25,teacher_sequence_error_rate_max=.25)')
(base/'qualify_feature_phone_ctc_20261006.py').write_text(source,encoding='utf-8')
