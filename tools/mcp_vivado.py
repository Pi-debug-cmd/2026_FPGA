#!/usr/bin/env python3
"""Vivado MCP 客户端（Windows 侧，Python 标准库实现，不受 PowerShell 执行策略限制）。

用法：
  python tools/mcp_vivado.py status
  python tools/mcp_vivado.py start
  python tools/mcp_vivado.py exec "puts [version -short]"
  python tools/mcp_vivado.py stop <session_id>
  python tools/mcp_vivado.py raw <tool> '<json-args>'
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

URL = 'http://127.0.0.1:18090/mcp'
SERVER = r'D:\Tools_FPGA\vivado-mcp\vivado-mcp-server.exe'
VIVADO = r'D:\USER_Software\vivado\2026.1\Vivado\bin\vivado.bat'
WORKDIR = r'C:\Users\World\Desktop\2026_FPGA\tmp\vivado_mcp'
STATEDIR = os.path.join(WORKDIR, 'state')
SESSION_RE = re.compile(r'vivado-2026[0-9-]+-[0-9a-f]{8}')


def port_open(host: str = '127.0.0.1', port: int = 18090, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ensure_server() -> None:
    if port_open():
        return
    subprocess.Popen([SERVER, '--background', f'--vivado-path={VIVADO}',
                      f'--default-workdir={WORKDIR}', f'--state-dir={STATEDIR}'],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        time.sleep(0.5)
        if port_open():
            return
    raise SystemExit('MCP 服务启动失败：18090 未监听')


class Client:
    def __init__(self) -> None:
        ensure_server()
        self.session = None
        self._post({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                    'params': {'protocolVersion': '2025-06-18', 'capabilities': {},
                               'clientInfo': {'name': 'dsh-python', 'version': '1'}}})

    def _post(self, payload: dict) -> dict:
        body = json.dumps(payload).encode('utf-8')
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json, text/event-stream'}
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        request = urllib.request.Request(URL, data=body, headers=headers, method='POST')
        with urllib.request.urlopen(request, timeout=600) as response:
            self.session = response.headers.get('Mcp-Session-Id') or self.session
            text = response.read().decode('utf-8', 'replace')
        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith('{'):
                return json.loads(line)
        return {}

    def call(self, name: str, arguments: dict) -> dict:
        response = self._post({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                               'params': {'name': name, 'arguments': arguments}})
        if 'error' in response:
            return {'error': response['error']}
        try:
            text = response['result']['content'][0]['text']
        except (KeyError, IndexError):
            return response
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {'text': text}

    def session_id(self) -> str | None:
        listing = self.call('vivado_list_sessions', {})
        match = SESSION_RE.search(json.dumps(listing))
        return match.group(0) if match else None


def emit(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> None:
    action = (sys.argv[1] if len(sys.argv) > 1 else 'status').lower()
    client = Client()

    if action == 'status':
        emit(client.call('vivado_list_sessions', {}))
    elif action == 'start':
        emit(client.call('vivado_start', {'session_type': 'general', 'working_dir': WORKDIR}))
    elif action == 'exec':
        if len(sys.argv) < 3:
            raise SystemExit('用法: mcp_vivado.py exec "<TCL>"')
        sid = client.session_id()
        if not sid:
            raise SystemExit('没有活动会话，先执行 start')
        emit(client.call('vivado_execute', {'session_id': sid, 'command': sys.argv[2]}))
    elif action == 'stop':
        if len(sys.argv) < 3:
            raise SystemExit('用法: mcp_vivado.py stop <session_id>')
        emit(client.call('vivado_stop', {'session_id': sys.argv[2]}))
    elif action == 'raw':
        if len(sys.argv) < 3:
            raise SystemExit('用法: mcp_vivado.py raw <tool> \'<json-args>\'')
        arguments = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        emit(client.call(sys.argv[2], arguments))
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main()
