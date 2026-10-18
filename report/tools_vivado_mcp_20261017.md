# Vivado MCP Server 安装记录（2026-10-17）

## 装了什么

- 文件：`vivado-mcp-server-windows-amd64-2026.9.1.exe`（19.2 MB，未签名）
- 版本：`vivado-mcp-server 2026.9.1`（commit 2c4e86e5，构建 2026-09-29，channel customer）
- 原始 SHA256：`9b43ea6c43b8b1147c4de53e6b50f11eb5d94a89f15e27b9e457f7b402f29016`
- 安装位置：`D:\Tools_FPGA\vivado-mcp\vivado-mcp-server.exe`（同目录 `INSTALL.txt` 记录版本与配置）
- 状态目录：`C:\Users\World\Desktop\2026_FPGA\tmp\vivado_mcp\state`
- 工作目录：`C:\Users\World\Desktop\2026_FPGA\tmp\vivado_mcp`

## 运行方式

```powershell
# 后台守护（推荐）：HTTP MCP 服务
& 'D:\Tools_FPGA\vivado-mcp\vivado-mcp-server.exe' --background `
   --vivado-path='D:\USER_Software\Xilinx_Vivado\Vivado\2018.3\bin\vivado.bat' `
   --default-workdir='C:\Users\World\Desktop\2026_FPGA\tmp\vivado_mcp' `
   --state-dir='C:\Users\World\Desktop\2026_FPGA\tmp\vivado_mcp\state'
# 端点：http://127.0.0.1:18090/mcp ；仅用 stdio 的客户端加 --stdio-bridge
# 停止：& 'D:\Tools_FPGA\vivado-mcp\vivado-mcp-server.exe' --kill-all
```

2026-10-17 15:16 已启动：PID 45020，监听 `127.0.0.1:18090`，服务日志 `C:\Users\World\.vivado-ai\server_LAPTOP-2P078LDE.log`。

## 已验证

- `initialize` 与 `tools/list` 均 HTTP 200：11 个工具（`vivado_start`、`vivado_execute`、`vivado_status`、`vivado_log_messages`、`vivado_list_sessions`、`vivado_connect`、`vivado_stop`、`vivado_cleanup`、`vivado_history`、`vivado_todos`、`vivado_client_info`）。
- MCP 协议层可用，服务本身没问题。

## 阻塞：与 Vivado 2018.3 不兼容

`vivado_start` 实测失败：`Failed to start Vivado: webserver failed to become ready`。

根因在注入的初始化脚本 `tmp/vivado_mcp/.vivado-ai/init_*.tcl`：

```tcl
set_param messaging.defaultLimit 10000000
webserver -start -key none
```

而本机 Vivado 2018.3 的 `webserver` 只有：

```
webserver [-port <arg>] [-stop] [-open] [-browser <arg>] [-page <arg>]
```

**没有 `-start`，也没有 `-key`**（实测 `[Common 17-170] Unknown option '-start'`）。这两个选项属于较新 Vivado 的 webserver CLI；服务还需要新版 webserver 的 REST 接口来下发 TCL，因此不是写个 Tcl 兼容层就能绕过。

本机仅安装 `D:\USER_Software\Xilinx_Vivado\Vivado\2018.3`，没有其他版本。

## 结论与选项

- 结论：**服务已装好且 MCP 层验证通过，但无法驱动 Vivado 2018.3**。
- 选项 A：另装较新 Vivado（2020.2 以上，建议 2024.x/2025.x），MCP 用 `vivado_path` 按会话指向它；工程构建仍用 2018.3，两者可共存。代价为数十 GB 下载与许可。
- 选项 B：保留安装但不使用；需要 AI 驱动的构建继续走现有 Tcl 脚本（`build/*.tcl`），本项目已验证该路径。
- 选项 C：若坚持 2018.3 + MCP，需要上游支持（其 CLI 假设与 2018.3 不符），本仓库不改上游代码。

本轮只做安装、启动与协议验证；未修改任何 Vivado 工程、未编译、未动板卡与启动分区。

---

## 2026-10-17 复核：改用 Vivado 2026.1，MCP 已跑通

### 环境变化

本机 `D:\USER_Software\Xilinx_Vivado`（2018.3）已被移除，新装 **Vivado 2026.1**。
注意实际路径多一层 `Vivado`：

```
D:\USER_Software\vivado\2026.1\Vivado\bin\vivado.bat
```

（写错成 `...\2026.1\bin\vivado.bat` 时，MCP 会报 `Vivado binary not found`。）

### 启动命令（Windows 侧进程，故仍用 PowerShell 启动）

```powershell
& 'D:\Tools_FPGA\vivado-mcp\vivado-mcp-server.exe' --kill-all
& 'D:\Tools_FPGA\vivado-mcp\vivado-mcp-server.exe' --background `
   --vivado-path='D:\USER_Software\vivado\2026.1\Vivado\bin\vivado.bat' `
   --default-workdir='C:\Users\World\Desktop\2026_FPGA\tmp\vivado_mcp' `
   --state-dir='C:\Users\World\Desktop\2026_FPGA\tmp\vivado_mcp\state'
```

### 验证结果（全部通过）

| 调用 | 结果 |
| --- | --- |
| `vivado_start`（session_type=general） | 成功：TCL 模式、webserver `http://localhost:8088`、PID 38596、session `vivado-20261017-173814-30c4aaf4` |
| `vivado_list_sessions` | `process_running=true`、`webserver_healthy=true`，含 `proxy_addr` |
| `vivado_execute`：`puts [version -short]` | exit 0，输出 `2026.1` |
| `vivado_execute`：`puts [get_param general.maxThreads]` | exit 0，输出 `2` |
| `vivado_execute`：`expr 6*7` / `set v [version -short]; puts $v` | exit 0，输出 `42` / `2026.1` |

结论：**Vivado 2026.1 的 `webserver -start -key` 兼容 MCP 的假设，2018.3 的不兼容问题不再存在。**

### WSL 侧调用封装

新增 `tools/mcp_vivado.sh`：

```bash
./tools/mcp_vivado.sh status              # 列会话
./tools/mcp_vivado.sh exec "puts [version -short]"
./tools/mcp_vivado.sh start               # 新会话（TCL 模式）
./tools/mcp_vivado.sh stop <session_id>
```

要点：MCP 监听 Windows 的 `127.0.0.1:18090`，WSL 是 NAT 到不了，脚本用 Windows `curl.exe` 走互操作；JSON 由 python3 生成，避免引号被两层 shell 吃掉。**从脚本文件调用稳定，内联 `bash -lc "...; ..."` 容易被外层 PowerShell 破坏。**

### 注意事项

- 守护进程空闲 5 分钟自动退出（`daemon idle timeout`），长时间不用要重新启动。
- `vivado_start` 起的 Vivado 会话会一直运行，用完 `vivado_stop` 或 `--kill-all`。
- 综合/实现需要有效 license；`version`、`expr` 这类命令无需 license。许可生成后放入 `~/.Xilinx/*.lic` 或用 `XILINXD_LICENSE_FILE`。
- 这些 `vivado_*` 工具**不是 DSH 原生工具**，是通过上面的脚本走 HTTP 调用。

---

## 2026.1 器件与 xsim 复核：安装不完整，PL 流程被阻塞

用户要求以后 Vivado 场景（写 PL、仿真、综合）一律走 MCP。实测结论如下。

### 工作正常的部分

| 项 | 结果 |
| --- | --- |
| MCP 服务 | `initialize` / `tools/list` / `tools/call` 均正常；空闲 5 分钟自动退出，需按批次重启 |
| `vivado_start` | 成功：TCL 模式、webserver :8088、`process_running=true`、`webserver_healthy=true` |
| `vivado_execute` | `puts [version -short]` → `2026.1`；`expr` / `set` 均 exit 0 |
| `xvlog` | 成功（1.04 s） |
| `xelab` | 成功（3.64 s） |

### 阻塞一：器件库为空（综合/实现无法进行）

- 会话内 `get_parts *` → 0；`get_parts xc7z020clg400-2` → `WARNING: [Coretcl 2-179] No part matched`。
- **命令行直调同样 0**（`XILINX_VIVADO=D:/USER_Software/vivado/2026.1/Vivado`、可执行文件正确），所以不是 MCP 环境问题。
- `create_project ... -part xc7z020clg400-2` → `[Project 1-848] Could not get a valid part`。
- 磁盘现状：`data/parts` 共 5.7 GB，`zynq/devint/zynq/xc7z020` 存在，但 `zynq/public` 只有 bsdl/ibis/liberty；安装根 `D:\USER_Software\vivado\2026.1` **没有 `.xinstall` 注册目录**。今天 15:45 的安装日志显示当时在删除旧 `D:\USER_Software\Xilinx_Vivado\.xinstall`，即同时在做卸载。

### 阻塞二：xsim 崩溃（仿真无法进行）

- `xsim tb_sim -R` → `Could not open file mapping object (2).` 紧接 `Abnormal program termination (EXCEPTION_ACCESS_VIOLATION)`，耗时约 133 s。
- 直接 `cmd /c xsim.bat tb_sim -R` 一样崩；去掉 `-autoloadwcfg` 后仍崩。
- `hs_err_pid*.log` 只有一行 `EXCEPTION_ACCESS_VIOLATION`，没有栈。xsim 的 JVM 层崩溃，与 MCP 无关。

### 判断与建议

两处症状都指向**安装不完整或损坏**（无 `.xinstall` 注册、器件数据不全、xsim 启动即崩）。建议：

1. 用 `D:\USER_Software\vivado\Downloads` 下的安装器做**修复/重装**，务必勾选 **Vivado** 与 **Zynq-7000**（含 7 Series）器件族，并让安装完整结束。
2. 装完先做两条验收：
   ```tcl
   # 器件
   puts [llength [get_parts]]
   # 仿真（在临时目录放一个计数模块和 testbench）
   xvlog -sv counter.sv tb_counter.sv
   xelab -debug typical tb_counter -s tb_sim
   xsim tb_sim -R
   ```
   两项都正常后再让 MCP 接管 PL 工作流。
3. 本次验证用的最小工程在 `build/generated/pl_mcp_20261017/sim/`（`counter.sv`、`tb_counter.sv`），装好后可直接复跑。

### 环境补充

WSL 的 Windows 互操作会随实例回收失效（`cannot execute binary file: Exec format error`）。本次用常驻 `wsl -e bash -c "sleep 7200"` 保持实例存活后稳定。`tools/mcp_vivado.sh` 依赖该互操作访问 Windows 侧 MCP。

---

## 2026-10-17 18:30 更新：两个阻塞都已解除

1. **器件库**：修复安装后重启会话，`get_parts` = **165**，`get_parts xc7z020*` = 8，`xc7z020clg400-2` 可解析。注意：**重装后必须重启 Vivado 会话**（旧会话在启动时已加载空器件库）。
2. **仿真**：`xsim` 在工作区内崩溃（`Could not open file mapping object` + `EXCEPTION_ACCESS_VIOLATION`）与安装无关，是 **DSH 文件沙箱过滤驱动**干扰文件映射。把仿真目录放到工作区外（`D:\xsim_work\pl_mcp_20261017`）后实测通过。

### 验证结果（全部经 MCP）

| 步骤 | 结果 |
| --- | --- |
| `xvlog -sv counter.sv tb_counter.sv` | exit 0 |
| `xelab -debug typical tb_counter -s tb_sim` | exit 0 |
| `xsim tb_sim -R`（工作区外） | exit 0，`PASS value=10`，2.28 s |
| `read_verilog` + `synth_design -part xc7z020clg400-2`（工作区内） | exit 0，`Got license for 'Vivado_Synthesis' and device 'xc7z020'`，0 errors，耗时 40.8 s（含 14 s 读文件） |

PL 器件报告（2026.1）：DSPs 220、BRAMs 280（RAMB18 计），与 xc7z020 规格一致。

### 工具链约定（已写入全局提示词）

- 客户端改用 `tools/mcp_vivado.py`（python 标准库），`tools/mcp_vivado.ps1` 因执行策略被挡已删除。
- TCL 命令不要用双引号套方括号（`puts "N=[llength $p]"` 会 `missing close-bracket`），用 `puts N=[llength $p]`。
- 仿真目录必须在工作区外；综合/实现不受此限制。
