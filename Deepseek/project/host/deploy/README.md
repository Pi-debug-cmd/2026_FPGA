# host/deploy — 上板部署（串口）

## 1. 内容

| 文件 | 作用 | 已验证 |
|---|---|---|
| `serial_lib.ps1` | 串口会话库：连接、`Invoke-BoardCmd`、`Close-Board`（恢复 `stty echo` 与 PS1） | ✅ 板上跑过 |
| `upload_board.ps1` | base64 分块上传 + 逐块 SHA + 失败回滚重试（块变小） | ✅ 848 s 传完 6.59 MB，双端 SHA 一致 |
| `download_board.ps1` | 从 `/tmp` 回读文件（base64 走控制台）+ SHA 校验 | ✅ |
| `board_preflight.ps1` | 系统事实、声卡状态、停演示服务、建 `/tmp/vc` | ✅ |
| `board_upload_all.ps1` | 一次传二进制 + 权重 + 输入 | ✅ |
| `board_run.ps1` | 跑主链 + `--nopitch` 对照 + dump 遥测 | ✅ |
| `board_download_results.ps1` | 批量回读结果 | ✅ |
| `run_vc.ps1` | 主机侧跑 `vc_stream_host.exe` 的小封装 | ✅ |
| `load_pl_2018.py` | 板端：记录状态 → 解绑 18 个旧 PL 消费者 → 加载位流 → 回绑音频 | ✅ |
| `prepare_recovery.py` | 板端：从启动分区**只读**生成回滚镜像 | ✅ |
| `pitch_dma_mem.c` | 板端：用户态 AXI DMA 驱动 + 变调核跑数（含缓存一致性处理） | ✅ SHA `fe312bb1…` 与板上二进制逐字节相同 |
| `gpio_check.c` | 板端：AXI GPIO ratio 写读校验 | ✅ |
| `bin/` | 预编译的静态 ARM 可执行（`pitch_dma_mem`、`gpio_check`、`regtool`、`dma_roundtrip`） | ✅ 由 SDK 2018.3 GCC 7.3.1 编译 |
| `stage.ps1` | 组装脚本期望的目录布局（**不改一行已验证脚本**） | 新增 |
| `deploy_all.ps1` | 依次调用 preflight → upload → run → download | 新增，**未端到端复跑** |

## 2. 为什么需要 `stage.ps1`

已验证的脚本假定的工作目录是：

```
<root>\tools\*.ps1     <root>\build\vc_stream_arm
<root>\data\*.blob     <root>\logs\
```

参赛包里的位置是 `host/deploy`、`host/app/build`、`host/model`、`metrics/logs`。
为了**不改动已验证脚本的路径常量**（这样它们的 SHA 还能与原始版本对照），
`stage.ps1` 把文件复制成上面那个布局：

```powershell
.\host\deploy\stage.ps1                     # -> D:\vc_stage_20261026
.\host\deploy\stage.ps1 -Stage D:\stage_try # 自定义目标
```

## 3. 完整上板流程

```powershell
# 0) 先有二进制（没有的话先编译）
.\host\app\build_arm.ps1

# 1) 组装 staging
.\host\deploy\stage.ps1

# 2) 关掉任何串口终端（COM8 独占），确认板子已上电

# 3) 一键（preflight → upload → run → download）
.\host\deploy\deploy_all.ps1 -Stage D:\vc_stage_20261026

# 或者逐步：
cd D:\vc_stage_20261026
.\tools\board_preflight.ps1
.\tools\board_upload_all.ps1
.\tools\board_run.ps1
.\tools\board_download_results.ps1
```

## 4. 加 PL 的那一套（可选）

```powershell
cd D:\vc_stage_20261026
# 传位流（gzip 后 332 KB，约 42 s）
.\tools\upload_board.ps1 -LocalFile .\tools\bin\audio_pitch_dma_2018_swap.bin.gz `
                        -RemotePath /tmp/pl_2018/audio_pitch_dma_2018_swap.bin.gz
# 传板端脚本与静态工具
.\tools\upload_board.ps1 -LocalFile .\tools\load_pl_2018.py -RemotePath /tmp/pl_2018/load_pl_2018.py
.\tools\upload_board.ps1 -LocalFile .\tools\prepare_recovery.py -RemotePath /tmp/pl_2018/prepare_recovery.py
.\tools\upload_board.ps1 -LocalFile .\tools\bin\regtool -RemotePath /tmp/pl_2018/regtool
.\tools\upload_board.ps1 -LocalFile .\tools\bin\pitch_dma_mem -RemotePath /tmp/pl_2018/pitch_dma_mem

# 板上（串口）：加载 + 寄存器验收 + DMA 往返
cd /tmp/pl_2018
gunzip -c audio_pitch_dma_2018_swap.bin.gz > audio_pitch_dma_2018_swap.bin
python3 prepare_recovery.py /tmp/pl_2018
python3 load_pl_2018.py /tmp/pl_2018 /tmp/pl_2018/audio_pitch_dma_2018_swap.bin
./regtool --base 0x41200000 --check 0x00:18:86856,65536,131072,32768,86856 --check 0x08:1:0,1
./pitch_dma_mem input_s24_stereo.raw out.raw 86856 s24
```

## 5. 恢复现场（必做）

```powershell
# 板上
alsactl -f /tmp/vc/mixer_before.state restore 0
stty echo
/etc/init.d/world-voice start        # 需要演示时
rm -rf /tmp/vc /tmp/pl_2018          # 撤离时
```

## 6. 注意

- `upload_board.ps1` 只允许写 `/tmp/<name>`（正则强制），不会碰系统文件。
- 串口 7.8 KB/s：4.6 MB 权重约 10.3 min。**日常迭代请用主机侧构建**。
- `deploy_all.ps1` 是新增的编排脚本，**没有在打包后端到端复跑**；
  它只调用已单独验证过的四个脚本，失败时会明确停在某一步。
- `stage.ps1` 不在 staging 里保留自己，避免复制自身造成递归。
