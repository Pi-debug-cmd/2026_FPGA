from pathlib import Path
base=Path(__file__).resolve().parent;native=base.parent/'board_support/native_llvc_20261005'
header=(native/'fargan_mapper_v8.h').read_text(encoding='utf-8')
header=header.replace('OWN_FARGAN_MAPPER_V8_H','OWN_FARGAN_MAPPER_CONTEXT_H').replace('OwnMapperV8','OwnMapperContext').replace('fm8_','fm9_').replace('FMAP008','FMAP009')
header=header.replace('mean[21],std[21],pre_w[2688]','mean[39],std[39],pre_w[4992]')
header=header.replace('float history[151],correction;int count,slot,quiet;','float history[151],correction;int count,slot,quiet;\n double context_history[200][17],context_total[17];int context_count,context_slot,context_quiet;')
header=header.replace('sizes[]={21,21,2688','sizes[]={39,39,4992')
header=header.replace('i<21','i<39').replace('x[21],norm[21]','x[39],norm[39]')
needle='x[20]=input[18];'
assert header.count(needle)==1
header=header.replace(needle,needle+'''
 if(input[0]>-7){
  m->context_quiet=0;
  if(m->context_count<200){
   for(int j=0;j<17;j++){double v=input[j+1];m->context_history[m->context_count][j]=v;m->context_total[j]+=v;}
   m->context_count++;
  }else{
   for(int j=0;j<17;j++){m->context_total[j]-=m->context_history[m->context_slot][j];double v=input[j+1];m->context_history[m->context_slot][j]=v;m->context_total[j]+=v;}
   m->context_slot=(m->context_slot+1)%200;
  }
 }else if(input[0]<-9||input[19]<-.2f){
  if(++m->context_quiet>80){m->context_count=m->context_slot=0;memset(m->context_total,0,sizeof(m->context_total));}
 }
 for(int j=0;j<17;j++)x[21+j]=m->context_count?(float)(m->context_total[j]/m->context_count):0;
 x[38]=m->context_count/200.f;
''')
header=header.replace('m->pre_w+i*21,norm,21','m->pre_w+i*39,norm,39')
header=header.replace('compatible FMAP009 tensors.','compatible FMAP009 tensors, past-only39-feature context.')
(native/'fargan_mapper_context.h').write_text(header,encoding='utf-8')
for src,dst in [('fargan_mapper_probe_v8.c','fargan_mapper_probe_context.c'),('native_fargan_v8_pipeline.c','native_fargan_context_pipeline.c')]:
    text=(native/src).read_text(encoding='utf-8').replace('fargan_mapper_v8.h','fargan_mapper_context.h').replace('OwnMapperV8','OwnMapperContext').replace('fm8_','fm9_')
    (native/dst).write_text(text,encoding='utf-8')
build=(base/'build_native_fargan_v8_20261006.ps1').read_text(encoding='utf-8').replace('native_fargan_v8','native_fargan_context')
build+='''
& 'D:\\Vivado\\Vivado\\2018.3\\tps\\mingw\\6.2.0\\win64.o\\nt\\bin\\gcc.exe' '-O3' '-std=gnu99' '-static' '-mavx2' '-mfma' (Join-Path $taskNative 'fargan_mapper_probe_context.c') '-lm' '-o' (Join-Path $taskNative 'fargan_mapper_probe_context_host.exe')
if($LASTEXITCODE -ne 0){throw 'Context mapper host build failed'}
& 'D:\\Vivado\\SDK\\2018.3\\gnu\\aarch32\\nt\\gcc-arm-linux-gnueabi\\bin\\arm-linux-gnueabihf-gcc.exe' '-O3' '-std=gnu99' '-static' '-mcpu=cortex-a9' '-mfpu=neon' '-mfloat-abi=hard' (Join-Path $taskNative 'fargan_mapper_probe_context.c') '-lm' '-o' (Join-Path $taskNative 'fargan_mapper_probe_context_arm')
if($LASTEXITCODE -ne 0){throw 'Context mapper ARM build failed'}
'''
(base/'build_native_fargan_context_20261006.ps1').write_text(build,encoding='utf-8')
print('CONTEXT_NATIVE_PREPARED')
