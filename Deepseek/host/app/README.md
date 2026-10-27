# host/app — PS 侧主程序（`vc_stream`）

## 1. 内容

| 文件 | 作用 |
|---|---|
| `src/vc_stream.cpp` | 全部算法：S24 解码、32k↔16k 重采样、SoundTouch 升调、WORLD 分析/合成、646 维特征、MLP、包络移植、S24 打包、CLI、遥测、dump |
| `src/stream_mode.inc` | 流式模式（按块切分、跨块滤波器历史、hold-back 交叉淡化、逐块遥测） |
| `src/mlp_int8.inc` | int8 权重量化与 `vmlal.s16` 内核（`--mlp-int8`） |
| `src/st_cpu_stub.cpp` | SoundTouch 在非 x86 平台的 `detectCPUextensions()` 桩 |
| `third_party/world/` | WORLD 源码（与 pyworld 0.3.5 同一份，未改动） |
| `third_party/soundtouch/` | SoundTouch 源码（WSOLA 核心，未改动） |
| `build_arm.ps1` / `build_host.ps1` | 交叉编译（并自动校验 ELF 头） / 主机侧构建 |
| `Makefile` | 同上，供有 make 的环境使用 |
| `export_weights.py` / `ref_port.py` / `make_test_input.py` | 权重导出 / Python oracle / 测试输入生成 |

## 2. 构建

```powershell
# 交叉编译（板上运行）
.\build_arm.ps1                 # 产物 build\vc_stream_arm（静态 ARM ELF）
.\build_arm.ps1 -ExtraFlags "-O3"   # 只用于对照实验

# 主机侧（数值迭代，30 s 一轮）
.\build_host.ps1                # 产物 build\vc_stream_host.exe
```

交叉编译器路径写在 `build_arm.ps1` 里（Vivado SDK 2018.3 的 Linaro GCC 7.3.1）；
若你的 SDK 装在别处，改 `$gccdir` 一行即可。

> **关于 `build/vc_stream_arm`**：本包已附一份 2026-10-26 重编译的产物（804,424 B）。
> 它的大小与板上跑过的那份完全相同，但 **SHA 不同**（C++ 局部静态符号名受输入路径影响）；
> 该产物**未在板上验证**。详见 `build/BUILD_NOTE.md`。

产物校验（脚本自动打印）：

```
magic    : 7f 45 4c 46
e_machine: 0x0028 (ARM)
e_type   : 0x0002 (EXEC)
flags    : 0x05000400 (EABI5 hard-float)
sha256   : ...
```

## 3. 快速自检（不需要板卡）

```powershell
$py = "...\env\venv\Scripts\python.exe"
& $py make_test_input.py                    # 生成 4 s 32 kHz S24 测试输入
build\vc_stream_host.exe 4 native_s24 200 --model ..\model\student_v5.blob `
    < ..\metrics\inputs\test_src_32k_s24.raw > out.raw 2> tel.json
type tel.json                                # 期望 ok:true, samples_out == samples_in
```

> **Windows 注意**：程序内部已经 `_setmode(_O_BINARY)`，但 PowerShell 的 `<`
> 重定向不可用，请用 `cmd /c` 或 `Get-Content -Encoding Byte` 管道。

## 4. 与 Python 参考对齐（重要）

```powershell
# 让 C 吃 oracle dump 出来的同一份 float32，才能排除 1-ulp 输入差
build\vc_stream_host.exe 4 pcm16 0 --model ..\model\student_v5.blob `
    --in-f32-16k --out-f32-16k --nopitch --dump out\c_nopitch `
    < oracle\x16.f32 > out\c_nopitch\y_out.f32 2> err.txt
```

期望与 `ref_port.py` 的 oracle 一致到 **121.7 dB**（16 kHz 源）/ **126.16 dB**（板端 32 kHz 源）。

## 5. 已知限制

- 32 kHz 是硬编码（`kSrIn=32000`、`kSr=16000`、`kChannels=2`）；换采样率要改常量并重新验证。
- SoundTouch 的升调是 WSOLA，与 librosa 的相位声码器**不是同一算法**，
  两者不能做样本级 SNR 比较（只可比包络）。
- 静态链接 + `std::thread` 会崩，必须用裸 `pthread` + `--whole-archive -lpthread`（脚本已处理）。
- 输入长度必须 ≥ 一个 FFT 窗（1024 样本 @16 kHz），否则直接报错退出。
