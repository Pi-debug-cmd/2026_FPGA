# 第一级固定输入者采集规范

本规范只用于保底阶段固定输入者素材，不是第二级陌生人校准，也不是第三级目标注册。

## 数据角色

每名固定输入者使用五个互不重叠的文件：

| 角色 | 用途 | 是否可选参 |
| --- | --- | --- |
| `train1`、`train2`、`train3` | 建立该输入者的专用模型或配置 | 可以 |
| `validation` | 选择模型、阈值和超参数 | 可以，但不得并入训练 |
| `holdout` | 冻结模型后的客观评价和试听 | 不可以 |

第一级要求同一输入者的句子/录制会话隔离。`holdout` 必须使用训练和验证中未出现的新句；最终验收再增加一次冻结模型后的新会话句。第二级才要求测试说话人与训练说话人完全隔离。

## 朗读内容

每段自然朗读约 20 秒，保持正常音量和距离，不刻意升高音调。

- `train1`：今天早上，我打开窗户，看见外面的阳光很好。桌上放着一杯温水，还有几本刚刚整理好的书。我们先检查设备，再开始今天的工作。
- `train2`：傍晚的街道比平时安静，路边的树叶被风轻轻吹动。前方的车辆慢慢停下，行人依次穿过路口，然后继续向前走。
- `train3`：请确认文件已经保存，网络连接保持正常。如果程序出现提示，我们先记录现象，再按照步骤重新检查，不要跳过中间过程。
- `validation`：周末我准备整理房间，把不用的物品分类收好。天气合适的时候，也想去附近走一走，看看有没有新的变化。
- `holdout`：远处传来清楚的广播声，提醒大家带好随身物品。列车到站以后，请先让里面的人出来，再有序上车。

## 板端采集

每次采集都是独立现场测试，开始前必须取得当次操作者准备确认。脚本先播放两声提示音，播放结束并等待 150 ms 后才开启录音；提示音不会进入录音。

```sh
python3 /tmp/capture_source_mapping.py --run --speaker fixed_b --role train1 --seconds 20
python3 /tmp/capture_source_mapping.py --run --speaker fixed_b --role train2 --seconds 20
python3 /tmp/capture_source_mapping.py --run --speaker fixed_b --role train3 --seconds 20
python3 /tmp/capture_source_mapping.py --run --speaker fixed_b --role validation --seconds 20
python3 /tmp/capture_source_mapping.py --run --speaker fixed_b --role holdout --seconds 20
```

每轮必须保存 `capture_manifest.json`、`capture.wav.gz`、原始 SHA、WAV SHA、削顶比例和 mixer 恢复状态。真人音频不会自动提交 Git；维护者确认后才放入受控目录并把 SHA 写入资产清单。
