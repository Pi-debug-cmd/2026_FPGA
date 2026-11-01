# 05 工具链与环境陷阱：11 条花了时间的坑，现在每条一句

日期：2026-10-09 ~ 2026-10-26
相关：`board_c_20261025.md` §11（16 条）、`board_c_20261025_stage2.md` §8、
`pl_build_20261025.md` §5

## 1. 这一轮要解决什么

不是算法问题，是"明明代码没错但跑不起来/结果对不上"的环境问题。
这类问题的特征是**报错误导**（或者根本不报错），所以值得逐条记下来。

## 2. 提示词要点

> "把这次踩的坑写成'现象 → 根因 → 修法'三列，**只写你自己踩过的**，
> 不要写网上抄来的通用建议。"

## 3. 坑清单（按代价排序）

### 3.1 faiss 无法打开中文路径 —— 整个索引构建失败

- **现象**：`IndexIVFFlat.read_index()` / 写索引时失败，报错信息指向文件不存在，
  但文件明明存在。
- **根因**：faiss 的 C++ 文件层用窄字符路径，Windows 中文路径（GBK/UTF-8 之间的转换）
  在传递过程中被破坏。
- **修法**：**索引的构建与读取全部放在纯 ASCII 路径**（我们用了 `D:\rvc_tmp_rvc20\`），
  建完再搬回项目目录。代码注释里直接写明这条（`build_index_rvc20.py` 的首行注释：
  "Build the faiss index at a pure-ASCII path (faiss cannot open the Chinese path)"）。
- **泛化**：任何 C/C++ 第三方库 + Windows 中文路径都可能中招。
  参赛包"文件名必须纯英文"这条纪律，本质上也是同一个坑的预防。

### 3.2 Applio / RVC 的 filelist 编码不一致 —— 训练集被读成乱码路径

- **现象**：filelist 里路径看着正常，训练侧却报大量文件不存在，或者只加载到一部分。
- **根因**：写 filelist 的一端用 UTF-8（或带 BOM），读的一端按系统默认 ANSI/GBK 解码；
  中文路径在两边不一致时静默丢行。
- **修法**：① 路径全 ASCII；② 写读两端显式指定编码；③ 训练前先 `wc -l` 核对行数。
- **泛化**：本项目后来所有"清单类"文件（manifest、SHA256SUMS、consumers.txt）
  都强制 ASCII 路径 + 显式 UTF-8。

### 3.3 串口独占 —— 一个进程占住 COM8，后面全部超时

- **现象**：`Invoke-BoardCmd` 超时，板子"没反应"；或上一条命令的引号没闭合，
  板端 shell 停在续行状态，把后续输入全吃了。
- **根因**：串口是独占资源；板端 shell 的续行状态会跨命令保留。
- **修法**：① 用前先确认没有别的进程占用 COM8；② 板端命令**只用单引号/无引号**的简单形式；
  ③ 卡住时先发 Ctrl-C，再 `stty echo`；④ 测试完必须 `stty echo` 并恢复 `PS1`。
- **纪律**：本包的 `docs/hardware_setup.md` 把这条写成了操作前置检查。

### 3.4 Windows 文本模式把 0x1A 当 EOF —— 原始流被截断

- **现象**：读 S24 裸流只读到 11414 B 就报 `short input`。
- **根因**：Windows 的 stdin 默认文本模式，`0x1A`(Ctrl-Z) 被当作文件结束。
- **修法**：`_setmode(_fileno(stdin), _O_BINARY)`（`vc_stream.cpp` 的 `main` 开头）。

### 3.5 `dump_f32` 用 `sizeof(float)` 写 `double` 数组 —— dump 全是 NaN

- **现象**：中间量 dump 出来是雪花，但 stdout 波形一直是对的（差点误判算法）。
- **根因**：只写了一半字节，重新解释成 float 就是 NaN。
- **修法**：加 `double → float` 的重载，显式窄化。

### 3.6 dump 目录 == 输入目录 —— 程序覆盖自己的 stdin

- **现象**：同一份代码两次运行结果不同。
- **根因**：`--dump` 指到了输入文件所在目录，输出把输入覆盖了，下一次读到垃圾。
- **修法**：输入与 dump 分目录（现在是硬性约定）。

### 3.7 `S24_LE` 是 4 字节容器，不是 3 字节

- **现象**：长度对不上（1,024,000 vs 768,000）。
- **根因**：ALSA 的 `S24_LE` 是 32-bit 容器 + 24 位有效位**左对齐**。
- **修法**：`x = (int32 >> 8) / 8388608.0`；打包时 `<<8`。

### 3.8 板端 python 没有 `mmap` 模块

- **现象**：`import mmap` → `ModuleNotFoundError`，寄存器校验脚本跑不了。
- **修法**：写静态 C 版（`regtool.c` / `gpio_check.c`）。
  这也是 `skill/overlay_load_and_verify` 同时提供 `.py` 和 `.c` 两个实现的原因。

### 3.9 静态链接 + pthread：`std::thread` 直接 terminate

- **现象**：双核版一启动就 `terminate`，`pthread_create` 返回垃圾错误码。
- **根因**：静态 glibc 里 libpthread 的 stub 被优先链接。
- **修法**：裸 pthread API + `-Wl,--whole-archive -lpthread -Wl,--no-whole-archive`，
  并保留失败回退串行（遥测里 `threaded:false`）。

### 3.10 PowerShell 的四个坑

| 坑 | 现象 | 修法 |
|---|---|---|
| 原生命令的 stderr 被当异常 | 编译"失败"其实只是警告 | 检查 `$LASTEXITCODE`，不靠异常 |
| 不支持 `<` 重定向 | 命令语法错 | `cmd /c` 包一层 |
| `-replace` 替换串里 `$'` 有特殊含义 | 正则被悄悄吞掉 | 用 `[regex]::Replace` 或转义 |
| `Set-Content` 默认 ANSI | UTF-8 报告里的中文被毁 | 显式 `-Encoding utf8` 或用 write 工具 |

### 3.11 板端 `world-voice` 演示服务占着声卡

- **现象**：`aplay -l` 显示 `Subdevices: 1/1`，新进程拿不到 PCM。
- **修法**：测试前 `/etc/init.d/world-voice stop`，结束后 `start` 恢复。
  （这是**改板子状态**的操作，必须记录并在结束时还原。）

## 4. 沉淀

1. **报错误导时，先怀疑"环境/编码/资源独占"这三类**，而不是代码逻辑。
2. **路径一律 ASCII**：这是本包"文件名纯英文"纪律的真实来源，不是格式洁癖。
3. **每一步都留原始日志**：上面 11 条里有 8 条是靠原始日志（而不是靠回忆）定位的。
4. **恢复现场是流程的一部分**：`stty echo`、mixer restore、服务 start、
   临时文件清理——写进脚本，不靠记性。
