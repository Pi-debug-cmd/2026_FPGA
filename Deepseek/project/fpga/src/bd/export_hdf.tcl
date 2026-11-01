open_project D:/g_build/pl_20261025/build/generated/audio_pitch_dma/voice7020.xpr
open_run impl_1
set root D:/g_build/pl_20261025
write_hwdef -force -file [file join $root audio_pitch.hwdef]
write_sysdef -hwdef [file join $root audio_pitch.hwdef] -bitfile [file join $root build generated audio_pitch_dma voice7020.runs impl_1 zynq_wrapper.bit] -file [file join $root audio_pitch.hdf]
puts HDF_EXPORTED
exit
