"""Fetch small board trial artifacts with base64/SHA; never emit media bytes."""
from pathlib import Path
import sys,time,re,base64,hashlib,json,uuid
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'transport_lib'))
import serial
if len(sys.argv)!=3:raise SystemExit('usage: serial_fetch_file.py REMOTE_PATH LOCAL_PATH')
remote=sys.argv[1];local=Path(sys.argv[2]).resolve()
assert re.fullmatch(r'/home/root/native_llvc_trial_20261005/[a-zA-Z0-9_.-]+',remote)
assert local.drive.lower()=='d:' and local.parent.exists()
token=uuid.uuid4().hex;start='FILE_BEGIN_'+token;end='FILE_END_'+token
port=serial.Serial('COM8',115200,timeout=.2,write_timeout=5)
try:
    port.write(b'\r');time.sleep(.3);initial=port.read(port.in_waiting)
    if b'root@' not in initial:raise RuntimeError('root shell not ready')
    code="import base64,hashlib; b=open('%s','rb').read(); print('%s'); print(base64.b64encode(b).decode()); print('FILE_SHA_'+hashlib.sha256(b).hexdigest()); print('%s')"%(remote,start,end)
    # Path validated above; code contains no shell single quote.
    escaped=code.replace("'","'\"'\"'")
    port.write(("python3 -c '"+escaped+"'\r").encode())
    buf=bytearray();lines=[];started=False;deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        buf.extend(port.read(max(1,port.in_waiting)))
        while b'\n' in buf:
            line,sep,tail=buf.partition(b'\n');buf=bytearray(tail);line=line.strip()
            if not started:
                if line==start.encode():started=True
            elif line==end.encode():
                sha_line=next(x for x in lines if x.startswith(b'FILE_SHA_'))
                payload=b''.join(x for x in lines if not x.startswith(b'FILE_SHA_'))
                data=base64.b64decode(payload,validate=True);digest=hashlib.sha256(data).hexdigest()
                assert sha_line==('FILE_SHA_'+digest).encode()
                local.write_bytes(data)
                print(json.dumps(dict(remote=remote,local=str(local),bytes=len(data),sha256=digest,verified=True)),flush=True)
                raise SystemExit(0)
            else:lines.append(line)
    raise TimeoutError('artifact download did not finish')
finally:port.close()