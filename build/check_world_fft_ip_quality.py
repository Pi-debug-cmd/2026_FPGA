"""Check locally generated AMD FFT C-model and full WORLD PCM16 regression."""
import argparse
import ctypes as ct
import hashlib
import json
import os
from pathlib import Path
import subprocess
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('--sdk', type=Path, required=True)
p.add_argument('--exe', type=Path, required=True)
p.add_argument('--xci', type=Path, required=True)
p.add_argument('--input', type=Path, action='append', required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--vectors-only', action='store_true', help='Generate RTL vectors without repeating speech tests')
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
names = ['C_NFFT_MAX','C_ARCH','C_HAS_NFFT','C_USE_FLT_PT','C_INPUT_WIDTH',
         'C_TWIDDLE_WIDTH','C_HAS_SCALING','C_HAS_BFP','C_HAS_ROUNDING','C_NSSR','C_SYSTOLICFFT_INV']
values = [11,3,1,1,32,25,1,0,0,1,0]
xci = json.loads(a.xci.read_text())['ip_inst']['parameters']
for k, v in zip(names, values):
    if k in xci['model_parameters']:
        assert int(xci['model_parameters'][k][0]['value']) == v, k
class Generics(ct.Structure):
    _fields_ = [(k,ct.c_int) for k in names]
class Inputs(ct.Structure):
    _fields_ = [('nfft',ct.c_int),('re',ct.POINTER(ct.c_double)),('re_size',ct.c_int),
                ('im',ct.POINTER(ct.c_double)),('im_size',ct.c_int),
                ('scaling',ct.POINTER(ct.c_int)),('scaling_size',ct.c_int),('direction',ct.c_int)]
class Outputs(ct.Structure):
    _fields_ = [('re',ct.POINTER(ct.c_double)),('re_size',ct.c_int),
                ('im',ct.POINTER(ct.c_double)),('im_size',ct.c_int),('exponent',ct.c_int),('overflow',ct.c_int)]
dll_dir = os.add_dll_directory(str(a.sdk.resolve()))
lib = ct.CDLL(str((a.sdk/'libIp_xfft_v9_1_bitacc_cmodel.dll').resolve()))
create = lib.xilinx_ip_xfft_v9_1_create_state
create.argtypes, create.restype = [Generics], ct.c_void_p
simulate = lib.xilinx_ip_xfft_v9_1_bitacc_simulate
simulate.argtypes, simulate.restype = [ct.c_void_p,Inputs,ct.POINTER(Outputs)], ct.c_int
destroy = lib.xilinx_ip_xfft_v9_1_destroy_state
destroy.argtypes = [ct.c_void_p]
state = create(Generics(*values))
assert state
result = {'kind':'world_fft_ip_quality','generics':dict(zip(names,values)),
          'exe_sha256':hashlib.sha256(a.exe.read_bytes()).hexdigest(),
          'xci_sha256':hashlib.sha256(a.xci.read_bytes()).hexdigest(),'unit':[],'speech':[]}
rng = np.random.default_rng(20261027)
input_words, output_words = [], []
compact_input, compact_output = [], []
def Words(re, im):
    pairs = np.column_stack((re,im)).astype('<f4')
    return pairs.view('<u8').reshape(-1).tolist()
ptr = lambda x: x.ctypes.data_as(ct.POINTER(ct.c_double))
try:
    for n in [1024,2048,1024]:
        random = rng.normal(size=n)+1j*rng.normal(size=n)
        for label, x in [('zero',np.zeros(n)),('impulse',np.eye(1,n)[0]),
                         ('constant',np.ones(n)*0.125),('random',random),('quiet',random*1e-12)]:
            re = np.ascontiguousarray(x.real.astype('float32').astype('float64'))
            im = np.ascontiguousarray(x.imag.astype('float32').astype('float64'))
            for direction in [1,0]:
                out_re, out_im = np.empty(n), np.empty(n)
                scaling = (ct.c_int*6)()
                inp = Inputs(int(np.log2(n)),ptr(re),n,ptr(im),n,scaling,6,direction)
                out = Outputs(ptr(out_re),n,ptr(out_im),n,0,0)
                assert simulate(state,inp,ct.byref(out)) == 0
                input_words += [int(np.log2(n)) | (direction<<8)] + Words(re,im)
                output_words += Words(out_re,out_im)
                ref = np.fft.fft(re+1j*im) if direction else np.fft.ifft(re+1j*im)*n
                err = out_re+1j*out_im-ref
                relative = float(np.linalg.norm(err)/max(np.linalg.norm(ref),1e-30))
                result['unit'].append(dict(size=n,case=label,direction=direction,relative_l2=relative))
                assert relative < 1e-5, result['unit'][-1]
                if direction==1:
                    # Independently generate a real-input version of every case.
                    zero_im=np.zeros(n)
                    compact_in=Inputs(int(np.log2(n)),ptr(re),n,ptr(zero_im),n,scaling,6,1)
                    assert simulate(state,compact_in,ct.byref(out)) == 0
                    compact_input += [int(np.log2(n)) | 0x300] + re.astype('<f4').view('<u8').tolist()
                    compact_output += Words(out_re[:n//2+1],out_im[:n//2+1])
finally:
    destroy(state)
(a.out/'input.mem').write_text(''.join(f'{v:016x}\n' for v in input_words))
(a.out/'output.mem').write_text(''.join(f'{v:016x}\n' for v in output_words))
(a.out/'compact_input.mem').write_text(''.join(f'{v:016x}\n' for v in compact_input))
(a.out/'compact_output.mem').write_text(''.join(f'{v:016x}\n' for v in compact_output))
for file in ([] if a.vectors_only else a.input):
    pcm = file.read_bytes()
    assert len(pcm)%32000 == 0
    seconds = len(pcm)//32000
    ref = None
    for mode in ['cpu','d4c','analysis','render','all']:
        env = dict(os.environ,WORLD_EXP='cpu',WORLD_FFT_MODEL=mode,
                   PATH=str(a.sdk.resolve())+os.pathsep+os.environ['PATH'])
        r = subprocess.run([str(a.exe.resolve()),str(seconds),'pcm16','0','39322'],input=pcm,
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=300)
        stem = file.parent.name+'_'+mode
        (a.out/(stem+'.raw')).write_bytes(r.stdout)
        (a.out/(stem+'.log')).write_bytes(r.stderr)
        assert r.returncode == 0, r.stderr.decode(errors='replace')
        y = np.frombuffer(r.stdout,dtype='<i2').astype(float)
        assert len(y) == seconds*16000
        if ref is None:
            ref = y
        err = ref-y
        snr = float(10*np.log10(max(np.dot(ref,ref),1)/max(np.dot(err,err),1e-30)))
        row = dict(input=str(file),input_sha256=hashlib.sha256(pcm).hexdigest(),mode=mode,
                   output_sha256=hashlib.sha256(r.stdout).hexdigest(),snr_db=snr,
                   max_pcm16_error=float(abs(err).max()),
                   telemetry=[json.loads(s) for s in r.stderr.decode().splitlines() if s.startswith('{')])
        result['speech'].append(row)
        assert snr >= 80 and row['max_pcm16_error'] <= 4, row
        print(file.parent.name,mode,snr,flush=True)
result['passed'] = True
(a.out/'quality.json').write_text(json.dumps(result,indent=2)+'\n')
