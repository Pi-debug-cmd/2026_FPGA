from pathlib import Path
base=Path(__file__).resolve().parent
source=(base/'train_feature_phone_ctc_20261006.py').read_text(encoding='utf-8')
source=source.replace('from fargan_feature_phone_ctc_20261006 import FeaturePhoneCTC,collapse','from fargan_feature_phone_cmn_20261006 import FeaturePhoneCMN,collapse').replace('FeaturePhoneCTC(','FeaturePhoneCMN(').replace('fargan_phone_ctc','fargan_phone_cmn').replace('PHONE_CTC','PHONE_CMN').replace('20261006+217','20261006+251')
source=source.replace('if n<blocks:x=torch.nn.functional.pad(x,(0,0,0,6*(blocks-n)))','if n<blocks:\n            x=torch.nn.functional.pad(x,(0,0,0,6*(blocks-n)));x[n*6:,0]=-12;x[n*6:,19]=-.5')
(base/'train_feature_phone_cmn_20261006.py').write_text(source,encoding='utf-8')
qual=(base/'qualify_feature_phone_ctc_20261006.py').read_text(encoding='utf-8')
qual=qual.replace('from fargan_feature_phone_ctc_20261006 import FeaturePhoneCTC','from fargan_feature_phone_cmn_20261006 import FeaturePhoneCMN').replace('FeaturePhoneCTC(','FeaturePhoneCMN(').replace('fargan_phone_ctc','fargan_phone_cmn')
(base/'qualify_feature_phone_cmn_20261006.py').write_text(qual,encoding='utf-8')
