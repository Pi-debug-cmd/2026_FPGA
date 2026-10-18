from pathlib import Path
import ast,json,time,hashlib
from load_llvc_audit_model import load_model,SOURCE,BASE,digest
from llvc_online_stream import LLVCAudioStream
import torch,numpy as np,soundfile as sf
OUT=Path('D:/Tools_FPGA/workspace/voice_conversion_zynq7020/board_budget_20261004/causal_stream_audit');OUT.mkdir(exist_ok=True)
torch.set_num_threads(4);model,config=load_model();source=BASE/'public_chinese_validation/fleurs_test_row0_id1906.wav';wave,sr=sf.read(source,dtype='float32');assert sr==16000 and wave.ndim==1
text=(SOURCE/'infer.py').read_text();fun=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='infer_stream');ns=dict(torch=torch,np=np,time=time);exec(compile(ast.Module(body=[fun],type_ignores=[]),str(SOURCE/'infer.py')+'::infer_stream','exec'),ns)
reference,_,_=ns['infer_stream'](model,torch.from_numpy(wave),1,sr);reference=reference.numpy().reshape(-1);rows=[]
for sizes in [[1],[256],[1000,17,31,208]]:
 stream=LLVCAudioStream(model);outputs=[];offset=0;i=0;start=time.perf_counter();first=None
 while offset<len(wave):
  n=sizes[i%len(sizes)];part=wave[offset:offset+n];offset+=len(part);i+=1;new=stream.feed(part)
  if new and first is None:first=dict(input_received_samples=stream.received,algorithm_required_samples=stream.chunk_samples+stream.L)
  outputs.extend(new)
 outputs.extend(stream.finish());actual=np.concatenate(outputs);diff=float(np.max(np.abs(actual-reference)))
 assert len(actual)==len(wave) and diff==0.,(sizes,diff,len(actual))
 rows.append(dict(feed_sizes=sizes,output_samples=len(actual),max_sample_difference_from_official_chunk_reference=diff,first_output=first,pc_wall_seconds=time.perf_counter()-start))
 print('PASS fragmentation',sizes,diff,flush=True)
# A suffix is never supplied to the model until its own block is due.
a=wave.copy();b=wave.copy();rng=np.random.default_rng(20261004);b[224:]=rng.normal(0,.03,len(b)-224)
sa=LLVCAudioStream(model);sb=LLVCAudioStream(model);ya=np.concatenate(sa.feed(a));yb=np.concatenate(sb.feed(b));assert np.array_equal(ya[:208],yb[:208])
first=LLVCAudioStream(model);assert first.feed(wave[:223])==[];assert len(first.feed(wave[223:224])[0])==208
for n in [0,1,16,207,208,209,224,416]:
 stream=LLVCAudioStream(model);result=stream.feed(wave[:n])+stream.finish();assert sum(len(v) for v in result)==n
 try:stream.feed(np.zeros(1));raise AssertionError('Closed stream accepted data')
 except RuntimeError:pass
status=dict(status='pretrained_reference_strict_load_bounded_online_adapter_verified',source_path=str(source),source_sha256=digest(source),checkpoint_sha256=digest(BASE/'llvc_pretrained_audit/G_500000.pth'),model_parameter_count=sum(p.numel() for p in model.parameters()),official_reference_function_sha256=hashlib.sha256(ast.get_source_segment(text,fun).encode()).hexdigest(),fragmentation_checks=rows,first_output_required_raw_samples=224,first_output_audio_samples=208,algorithmic_availability_ms=14,suffix_mutation_after_224_samples_does_not_change_first_208_output=True,empty_partial_exact_chunk_and_eof_length_checks=True,official_checkpoint_not_user_target=True,target_voice_trained=False,pc_only=True,board_deployed=False,actual_microphone_test=False,no_source_enrollment=True)
(OUT/'decision.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
print('ONLINE ADAPTER COMPLETE',flush=True)
