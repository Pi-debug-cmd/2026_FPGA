# 外接麦克风实时直通：已确认配置

日期：2026-10-03。

用户确认：现在讲话时音箱同步输出当前声音。先前听到重复旧录音的现象在此次配置后消失，但不能仅凭进程状态或该现象推定完整根因。

## 已确认的状态

- 外接麦克风：粉色3.5 mm口。
- 音箱：绿色3.5 mm口。
- 串口：本次COM8，115200，root/root。
- 原设备树仅含RINPUT1/RINPUT2到MICB的供电路由，尚未替换设备树。
- 录音过程中检查MICB为On，左右ADC/输入混音器可工作。
- 新采集文件的SHA256不同于旧文件，首8192字节不出现在旧录音PCM中；这只能排除该片段逐字节重放，不能代替语音听感或音质测试。
- 当前实时管道运行，音乐按键监听通过 `/etc/init.d/music-button stop` 临时停止，重启后仍按原开机配置启动。

## 当前有效混音设置

```sh
amixer sset 'Left Boost Mixer LINPUT1' on
amixer sset 'Left Input Mixer Boost' on
amixer sset 'Left Boost Mixer LINPUT2' off
amixer sset 'Left Input Boost Mixer LINPUT2' 0
amixer sset 'Left Input Boost Mixer LINPUT1' 1
amixer sset 'Right Boost Mixer RINPUT1' on
amixer sset 'Right Input Mixer Boost' on
amixer sset 'Capture' 35,35 cap
amixer sset 'ADC PCM' 190,190
amixer cset name='ADC Data Output Select' 1
```

右输入路径保持开启，以利用现有设备树供电路由保持MICB供电；实际数字输出仅选择左ADC并复制到两个声道。不要在现有设备树下随意关闭右路径后宣称麦克风仍获供电，应检查DAPM状态。

## 当前实时管道

```sh
arecord -q -D capture -t raw -f S24_LE -r 44100 -c 2 --period-size=256 --buffer-size=1024 | aplay -q -D default -t raw -f S24_LE -r 44100 -c 2 --period-size=256 --buffer-size=1024
```

该管道直接传输采样数据，不读取之前的WAV。256帧是5.805 ms音频，1024帧缓冲容量是23.22 ms；实际缓冲占用变化，且还有采集、播放和设备延迟，端到端总延迟未测。

本次检查进程PID为arecord=9397、aplay=9398；PID只用于历史记录，后续不要复用，须重新查询。

## 停止当前音频

```sh
for p in $(pidof arecord aplay 2>/dev/null); do kill -9 "$p"; done
```

这会停止所有arecord/aplay，操作前应确认没有其他需要保留的音频任务。完成关机前应先停音频，再执行Linux安全关机。

## 下一步

用户已有目标人物WAV。先获得本地路径，分析时长、采样率、声道、响度、削波、背景噪声与语音特征，再设计可运行在7020上的首版转换。目标人物相似度、算法可实时性、PL加速和端到端延迟均未完成。
