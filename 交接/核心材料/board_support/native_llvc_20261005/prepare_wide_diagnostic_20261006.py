"""RAM diagnostic hooks only; no waveform/model change and no disk IO while streaming."""
from pathlib import Path
import re, subprocess, os, json, hashlib
r=Path(__file__).resolve().parent
s=(r/'native_llvc_wide192_shallow2_meter.cpp').read_text(encoding='utf-8')
old=(r/'native_llvc_small96_diag120.cpp').read_text(encoding='utf-8')
code=old[old.index('static const size_t DIAG_KEEP='):old.index('static volatile sig_atomic_t streaming=')]
code=code.replace('"realtime_output_not_delayed_by_ring"','"realtime_output_not_delayed_by_ring"')
for before,after in [
 ('static volatile sig_atomic_t streaming=1;',code+'\nstatic volatile sig_atomic_t streaming=1;'),
 ('size_t got=read_pcm(input,CHUNK+LOOK),received=got,produced=0,chunks=0,late=0;','size_t got=read_pcm(input,CHUNK+LOOK),received=got,produced=0,chunks=0,late=0;diag_read(input,got);'),
 ('produced+=valid;','produced+=valid;diag_write(output,valid);'),
 ('got=read_pcm(input,CHUNK);received+=got;eof=got<CHUNK;','got=read_pcm(input,CHUNK);diag_read(input,got);received+=got;eof=got<CHUNK;'),
 ('status(status_path,received,produced,chunks,total,maximum,late,true);','diag_dump();status(status_path,received,produced,chunks,total,maximum,late,true);')]:
 assert s.count(before)==1,before
 s=s.replace(before,after)
(r/'native_llvc_wide192_diag120.cpp').write_text(s,encoding='utf-8')
helper=(r/'board_neural_wide192.sh').read_text(encoding='utf-8')
helper=helper.replace('# Reversible live trial only. No boot changes, no files of user speech.','# Diagnostic RAM ring; explicit finish saves latest 120s after live processing stops.')
helper=helper.replace('native_llvc_wide192_shallow2_meter_arm','native_llvc_wide192_diag120_arm')
helper=helper.replace('RUN=/run/voice-neural-live','RUN=/run/voice-neural-live\nexport LLVC_DIAG_TRIGGER="$RUN/wide_diag_dump.flag"\nexport LLVC_DIAG_PREFIX="$DIR/mic_wide_diagnostic_20261006"')
helper=helper.replace('mkdir -p "$RUN"','mkdir -p "$RUN"\n        rm -f "$LLVC_DIAG_TRIGGER"')
# Stop capture first: model drains buffered samples and dumps only on EOF, avoiding blocking live output on SD IO.
finish='''    finish)
        touch "$LLVC_DIAG_TRIGGER"
        for role in watchdog capture; do
            [ ! -f "$RUN/$role.pid" ] || kill "$(cat "$RUN/$role.pid")" 2>/dev/null || true
        done
        for attempt in 1 2 3 4 5 6 7 8; do
            [ -e "$LLVC_DIAG_TRIGGER" ] || break
            sleep 1
        done
        if [ -e "$LLVC_DIAG_TRIGGER" ]; then echo DIAGNOSTIC_DUMP_NOT_COMPLETED >&2; exit 1; fi
        stop_live
        sh "$DIR/board_neural_wide192.sh" start
        echo DIAGNOSTIC_SAVED_BASELINE_RESTORED
        ;;
'''
helper=helper.replace('    status)\n',finish+'    status)\n')
(r/'board_neural_wide_diag120.sh').write_text(helper,encoding='utf-8',newline='\n')
env=os.environ.copy();env['TEMP']=env['TMP']='D:/Tools_codex/temp'
host='D:/Vivado/Vivado/2018.3/tps/mingw/6.2.0/win64.o/nt/bin/g++.exe'
arm='D:/Vivado/SDK/2018.3/gnu/aarch32/nt/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-g++.exe'
flags=['-std=c++11','-O3','-static','-pthread']
src=str(r/'native_llvc_wide192_diag120.cpp')
subprocess.run([host,*flags,src,'-o',str(r/'native_llvc_wide192_diag120_host.exe')],check=True,env=env)
subprocess.run([arm,*flags,'-mcpu=cortex-a9','-mfpu=neon','-mfloat-abi=hard',src,'-Wl,--whole-archive','-lpthread','-Wl,--no-whole-archive','-o',str(r/'native_llvc_wide192_diag120_arm')],check=True,env=env)
# Compile the unmodified source identically for meaningful output parity.
subprocess.run([host,*flags,str(r/'native_llvc_wide192_shallow2_meter.cpp'),'-o',str(r/'native_llvc_wide192_meter_parity_host.exe')],check=True,env=env)
print('Diagnostic and reference builds complete')
