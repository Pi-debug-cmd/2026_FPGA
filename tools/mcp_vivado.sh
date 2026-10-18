#!/usr/bin/env bash
# Vivado MCP 客户端（WSL 侧调用 Windows 上的 MCP 服务）。
#
#   ./tools/mcp_vivado.sh status            列出会话
#   ./tools/mcp_vivado.sh exec "TCL..."     在最近一个会话执行 TCL
#   ./tools/mcp_vivado.sh start             启动新会话（TCL 模式）
#   ./tools/mcp_vivado.sh stop <session_id> 停止会话
#
# 说明：MCP 服务监听 Windows 的 127.0.0.1:18090，WSL 是 NAT 网络到不了，
# 因此走 Windows 的 curl.exe（互操作）。JSON 由 python3 生成，避免引号被吃。
set -uo pipefail
URL=${MCP_URL:-http://127.0.0.1:18090/mcp}
ROOT=/mnt/c/Users/World/Desktop/2026_FPGA
TMP="$ROOT/tmp"
WORK_WIN='C:\Users\World\Desktop\2026_FPGA\tmp\vivado_mcp'
mkdir -p "$TMP"

_curl() { curl.exe -s -m "${2:-180}" -X POST "$URL" -H 'Content-Type: application/json' \
            -H 'Accept: application/json, text/event-stream' \
            -H "Mcp-Session-Id: $SID" --data-binary "@$(wslpath -w "$1")" 2>&1 | tail -1; }

_init() {
  python3 - > "$TMP/.mcp_init.json" <<'PY'
import json
print(json.dumps({"jsonrpc":"2.0","id":1,"method":"initialize","params":{
  "protocolVersion":"2025-06-18","capabilities":{},
  "clientInfo":{"name":"wsl-mcp-client","version":"1"}}}))
PY
  local hdr
  hdr=$(curl.exe -s -i -m 30 -X POST "$URL" -H 'Content-Type: application/json' \
          -H 'Accept: application/json, text/event-stream' \
          --data-binary "@$(wslpath -w "$TMP/.mcp_init.json")" 2>&1)
  SID=$(printf '%s' "$hdr" | tr -d '\r' | awk -F': ' 'tolower($1)=="mcp-session-id"{print $2}')
  [ -n "${SID:-}" ] || { echo "MCP 初始化失败（服务没起？先启动守护进程）" >&2; exit 1; }
}

_call() { # _call <name> <python 表达式返回 arguments dict 的代码>
  local name="$1" args="$2"
  NAME="$name" ARGS="$args" python3 - > "$TMP/.mcp_req.json" <<'PY'
import json, os
print(json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
  "name": os.environ["NAME"], "arguments": eval(os.environ["ARGS"])}}))
PY
  _curl "$TMP/.mcp_req.json"
}

case "${1:-status}" in
  status|sessions)
    _init; _call vivado_list_sessions '{}' ;;
  exec)
    [ $# -ge 2 ] || { echo "用法: $0 exec \"TCL\"" >&2; exit 2; }
    _init
    sid=$(_call vivado_list_sessions '{}' | grep -oE 'vivado-2026[0-9-]+-[0-9a-f]{8}' | head -1)
    [ -n "$sid" ] || { echo "没有活动会话，先 $0 start" >&2; exit 1; }
    CMD="$2" SID_V="$sid" python3 - > "$TMP/.mcp_req.json" <<'PY'
import json, os
print(json.dumps({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
  "name":"vivado_execute",
  "arguments":{"session_id": os.environ["SID_V"], "command": os.environ["CMD"]}}}))
PY
    _curl "$TMP/.mcp_req.json" ;;
  start)
    _init; _call vivado_start "{\"session_type\":\"general\",\"working_dir\":r\"$WORK_WIN\"}" ;;
  stop)
    [ $# -ge 2 ] || { echo "用法: $0 stop <session_id>" >&2; exit 2; }
    _init; _call vivado_stop "{\"session_id\":\"$2\"}" ;;
  *)
    sed -n '2,12p' "$0"; exit 2 ;;
esac
