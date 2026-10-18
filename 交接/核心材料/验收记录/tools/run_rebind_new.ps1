$DR = '/sys/bus/platform/drivers'
$cmd = (@(
  'echo "== unbind =="',
  "echo xlnx_snd_card.0.auto > $DR/xlnx_snd_card/unbind 2>&1",
  "echo 43c40000.audio_formatter > $DR/xlnx_formatter_pcm/unbind 2>&1",
  "echo 43c50000.i2s_receiver > $DR/xlnx_i2s/unbind 2>&1",
  "echo 43c60000.i2s_transmitter > $DR/xlnx_i2s/unbind 2>&1",
  "echo 43c20000.axi_dynclk > $DR/dglnt-dynclk/unbind 2>&1",
  'sleep 1',
  'echo "== bind dynclk =="',
  "echo 43c20000.axi_dynclk > $DR/dglnt-dynclk/bind 2>&1",
  'sleep 1',
  'echo "== bind i2s rx/tx =="',
  "echo 43c50000.i2s_receiver > $DR/xlnx_i2s/bind 2>&1",
  "echo 43c60000.i2s_transmitter > $DR/xlnx_i2s/bind 2>&1",
  'sleep 1',
  'echo "== bind formatter =="',
  "echo 43c40000.audio_formatter > $DR/xlnx_formatter_pcm/bind 2>&1",
  'sleep 2',
  'echo "== bind card =="',
  "echo xlnx_snd_card.0.auto > $DR/xlnx_snd_card/bind 2>&1",
  'sleep 2',
  'echo "== pcm list =="; aplay -l 2>&1',
  'echo "== dynclk 00/04 =="; devmem 0x43C20000; devmem 0x43C20004',
  'echo "== dmesg tail =="; dmesg | tail -n 6'
) -join '; ')
& 'D:\总进度\7020验收记录\tools\serial_run.ps1' -Command $cmd -TimeoutSeconds 70 -LogPath 'D:\总进度\7020验收记录\B_PL音频\45_rebind_new.log'
