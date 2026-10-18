#!/usr/bin/env python3
"""Temporary raw UART transfer. Always restore saved115200 terminal settings."""
import os,sys,time,select,hashlib,termios
class Args:pass
options=dict(zip(sys.argv[1::2],sys.argv[2::2]));args=Args()
args.bytes=int(options['--bytes']);args.sha=options['--sha']
args.path=options['--path'];args.baud=int(options.get('--baud','921600'))
assert 0<args.bytes<=32*1024*1024 and len(args.sha)==64
assert args.path.startswith('/home/root/native_llvc_trial_20261005/') and '..' not in args.path
fd=sys.stdin.fileno();saved=termios.tcgetattr(fd)
def say(s):
    sys.stdout.write(s+'\n');sys.stdout.flush()
def exact(n):
    result=bytearray()
    while len(result)<n:
        if not select.select([fd],[],[],15)[0]:raise TimeoutError('no UART input for15s')
        b=os.read(fd,n-len(result))
        if not b:raise EOFError('input ended')
        result.extend(b)
    return bytes(result)
try:
    speed=getattr(termios,'B'+str(args.baud))
    say('SWITCH_BAUD_'+str(args.baud));termios.tcdrain(fd);time.sleep(.25)
    attrs=termios.tcgetattr(fd)
    attrs[0]&=~(termios.BRKINT|termios.ICRNL|termios.INPCK|termios.ISTRIP|termios.IXON|termios.IXOFF|termios.INLCR|termios.IGNCR)
    attrs[1]&=~termios.OPOST;attrs[2]=(attrs[2]&~(termios.CSIZE|termios.PARENB))|termios.CS8
    attrs[3]&=~(termios.ECHO|termios.ICANON|termios.IEXTEN|termios.ISIG)
    attrs[6][termios.VMIN]=1;attrs[6][termios.VTIME]=0
    attrs[4]=speed;attrs[5]=speed
    termios.tcsetattr(fd,termios.TCSANOW,attrs)
    termios.tcflush(fd,termios.TCIFLUSH)
    hello=exact(5)
    if hello!=b'HELLO':raise RuntimeError('bad handshake '+repr(hello)+' tty_speeds='+repr(termios.tcgetattr(fd)[4:6]))
    say('TRANSFER_READY')
    digest=hashlib.sha256();received=0
    with open(args.path+'.part','wb') as f:
        while received<args.bytes:
            b=exact(min(65536,args.bytes-received));f.write(b);digest.update(b);received+=len(b)
            say('ACK '+str(received))
        f.flush();os.fsync(f.fileno())
    actual=digest.hexdigest()
    if actual!=args.sha:raise RuntimeError('SHA256 mismatch '+actual)
    os.replace(args.path+'.part',args.path)
    say('TRANSFER_DONE '+actual);termios.tcdrain(fd);time.sleep(.25)
except Exception as e:
    open('/home/root/native_llvc_trial_20261005/uart_last_error.txt','w').write(repr(e))
    say('TRANSFER_ERROR '+str(e));termios.tcdrain(fd);time.sleep(.25)
finally:
    termios.tcsetattr(fd,termios.TCSANOW,saved)