"""SHA-verified raw UART transfer, returning tty to115200 after completion."""
from pathlib import Path
import sys,time,argparse,hashlib,json
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT/'transport_lib'))
import serial
a=argparse.ArgumentParser()
a.add_argument('file');a.add_argument('remote');a.add_argument('--port',default='COM8');a.add_argument('--baud',type=int,default=921600)
args=a.parse_args();source=Path(args.file);size=source.stat().st_size;sha=hashlib.sha256(source.read_bytes()).hexdigest()
assert args.remote.startswith('/home/root/native_llvc_trial_20261005/') and '..' not in args.remote
port=serial.Serial(args.port,115200,timeout=.2,write_timeout=10)
def collect(seconds):
    data=bytearray();end=time.monotonic()+seconds
    while time.monotonic()<end:data.extend(port.read(max(1,port.in_waiting)))
    return bytes(data)
def line_until(prefix,seconds=12):
    end=time.monotonic()+seconds;buf=bytearray()
    while time.monotonic()<end:
        b=port.read(1)
        if b:
            buf.extend(b)
            if b==b'\n':
                line=bytes(buf).strip();buf.clear()
                if line.startswith(b'TRANSFER_ERROR'):raise RuntimeError(line.decode(errors='replace'))
                if line.startswith(prefix):return line
    raise TimeoutError('expected '+prefix.decode()+', last '+bytes(buf).decode(errors='replace'))
try:
    port.write(b'\r');data=collect(1)
    if b'root@' not in data:raise RuntimeError('root shell is not ready')
    cmd='python3 -u /home/root/native_llvc_trial_20261005/uart_receiver.py --bytes %d --sha %s --path %s --baud %d\r'%(size,sha,args.remote,args.baud)
    port.write(cmd.encode('ascii'));line_until(('SWITCH_BAUD_'+str(args.baud)).encode(),5)
    time.sleep(.5);port.baudrate=args.baud;port.write(b'HELLO');line_until(b'TRANSFER_READY',5)
    begin=time.monotonic();sent=0;last=begin
    with source.open('rb') as f:
        while sent<size:
            block=f.read(min(65536,size-sent))
            port.write(block);port.flush();sent+=len(block)
            ack=line_until(b'ACK ',8)
            if ack!=('ACK '+str(sent)).encode():raise RuntimeError('ACK mismatch')
            now=time.monotonic()
            if now-last>=5 or sent==size:
                print(json.dumps(dict(sent=sent,total=size,percent=round(100*sent/size,1),elapsed_seconds=round(now-begin,1))),flush=True);last=now
    done=line_until(b'TRANSFER_DONE',15)
    assert done==('TRANSFER_DONE '+sha).encode()
    time.sleep(.4);port.baudrate=115200;port.write(b'\r');shell=collect(1)
    result=dict(source=str(source),remote=args.remote,sha256=sha,bytes=size,seconds=time.monotonic()-begin,
                full_sha_verified=True,baud_restored_115200=True,root_shell_visible=b'root@' in shell)
    (OUT/(source.name+'.transport_result.json')).write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result),flush=True)
finally:
    port.baudrate=115200;port.close()