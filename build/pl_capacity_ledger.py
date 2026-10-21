#!/usr/bin/env python3
"""PL 资源账本与加速预算计算（第 2 步：PL 评估的准备）。

输入：2026.1 实现后的利用率报告（真实工程）。
输出：report/pl_capacity_ledger_20261019.json + 控制台表格。

用途：任何音色候选交来后，用同一口径判断其 PL 资源/周期可行性：
- 权重放哪（BRAM/LUTRAM/DDR 流式）
- 每 200 ms 参数块的周期预算是否够
- DSP 数量是否够 MAC 吞吐
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTIL = ROOT / 'report/audio_pitch_dma_2026_impl_utilization.txt'
OUT = ROOT / 'report/pl_capacity_ledger_20261019.json'

CLOCK_MHZ = 100.0          # FCLK_CLK0
FRAME_MS = 10.0            # 参数帧周期
UPDATE_MS = 200.0          # 实时链路参数更新周期
AUDIO_RATE = 32000         # 实时链路 32 kHz
AUDIO_CH = 2
AUDIO_BITS = 32


def parse_utilization(text: str) -> dict:
    def grab(name: str) -> tuple[int, int] | None:
        # 2026.1 行格式：| 名称 | used | - | - | available | pct% |
        # 2018.3 行格式：| 名称 | used | - | available | pct% |
        for line in text.splitlines():
            if not line.startswith('|'):
                continue
            fields = [f.strip() for f in line.split('|') if f.strip()]
            if len(fields) < 4 or fields[0] != name:
                continue
            try:
                return (int(fields[1]), int(fields[-2]))
            except ValueError:
                continue
        return None

    out = {}
    for key, label in [('lut', 'Slice LUTs'), ('ff', 'Slice Registers'),
                       ('bram', 'Block RAM Tile'), ('dsp', 'DSPs')]:
        got = grab(label)
        if got:
            out[key] = {'used': got[0], 'available': got[1]}
    return out


def main() -> None:
    used = parse_utilization(UTIL.read_text(encoding='utf-8'))
    if len(used) != 4:
        raise SystemExit(f'未能解析全部资源: {used}')

    # 每 200 ms 与每 10 ms 的周期预算
    cycles_per_ms = CLOCK_MHZ * 1000.0
    budget = {
        'clock_mhz': CLOCK_MHZ,
        'cycles_per_frame': int(cycles_per_ms * FRAME_MS),
        'cycles_per_update': int(cycles_per_ms * UPDATE_MS),
        'frames_per_update': int(UPDATE_MS / FRAME_MS),
    }

    # 实时音频带宽（PL 侧 AXI-Stream / AXI4）
    audio_bytes_per_s = AUDIO_RATE * AUDIO_CH * (AUDIO_BITS / 8)
    # 参数块：513 bin × (sp, ap, f0) × 8 字节，10 ms 一帧
    param_bytes_per_frame = 513 * 3 * 8
    param_bytes_per_s = param_bytes_per_frame * (1000.0 / FRAME_MS)

    # BRAM 容量：1 个 BRAM36 = 36 kb = 4.5 KB；1 个 RAMB18 = 2.25 KB
    bram_total_kb = used['bram']['available'] * 4.5
    bram_used_kb = used['bram']['used'] * 4.5

    # DSP 吞吐参考：每 DSP48E1 每 2 拍一次 25x18 乘加（保守按 0.5 MAC/cycle/DSP）
    dsp_free = used['dsp']['available'] - used['dsp']['used']
    dsp_mac_per_cycle = dsp_free * 0.5
    macs_per_update = dsp_mac_per_cycle * budget['cycles_per_update']

    ledger = {
        'kind': 'pl_capacity_ledger',
        'date': '2026-10-19',
        'source': str(UTIL.relative_to(ROOT)).replace('\\', '/'),
        'device': 'xc7z020clg400-2',
        'tool': 'Vivado 2026.1（实现后报告）',
        'resources': {
            k: {'used': v['used'], 'available': v['available'],
                'free': v['available'] - v['used'],
                'used_pct': round(100.0 * v['used'] / v['available'], 2)}
            for k, v in used.items()
        },
        'timing': {'clock_mhz': CLOCK_MHZ, 'wns_ns': 1.696, 'failing_endpoints': 0,
                   'note': '实现后 WNS，来自 report/audio_pitch_dma_2026_impl_timing.txt'},
        'cycle_budget': budget,
        'bandwidth': {
            'audio_bytes_per_s': int(audio_bytes_per_s),
            'audio_mbit_per_s': round(audio_bytes_per_s * 8 / 1e6, 3),
            'param_bytes_per_frame': param_bytes_per_frame,
            'param_mbit_per_s': round(param_bytes_per_s * 8 / 1e6, 3),
            'note': '音频与参数流量相对 HP 端口带宽可忽略；PL 加速的约束是计算与存储，不是带宽。',
        },
        'memory': {
            'bram_total_kb': round(bram_total_kb, 1),
            'bram_used_kb': round(bram_used_kb, 1),
            'bram_free_kb': round(bram_total_kb - bram_used_kb, 1),
            'note': 'BRAM36 按 4.5 KB 计；实际可用还受布线/时钟域分布影响，保守按 80% 折算。',
        },
        'compute': {
            'dsp_total': used['dsp']['available'],
            'dsp_free': dsp_free,
            'macs_per_update_at_half_rate': int(macs_per_update),
            'macs_per_frame_at_half_rate': int(dsp_mac_per_cycle * budget['cycles_per_frame']),
            'note': '只按当前工程空闲 DSP 计算，并按每 DSP 0.5 MAC/cycle 保守估算。',
        },
        'verdict_rules': {
            'weights': '权重 ≤ 可用 BRAM 的 80% 视为可静态驻留；超出则需 DDR 流式或 LUTRAM 分片。',
            'cycles': '每 200 ms 参数块的计算必须 ≤ cycles_per_update；超了就降频次或换算法。',
            'dsp': 'MAC 数 ≤ macs_per_update_at_half_rate 视为吞吐可行。',
            'latency': '单帧处理延迟需远小于 200 ms（建议 ≤ 20 ms）才能保住实时余量。',
        },
    }
    OUT.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8')

    print('== PL 资源账本 ==')
    for k, v in ledger['resources'].items():
        print(f"  {k:5s} used {v['used']:>6} / {v['available']:>6}  free {v['free']:>6}  ({v['used_pct']}%)")
    print('== 周期预算 ==')
    print(f"  每帧 {FRAME_MS}ms: {budget['cycles_per_frame']:,} cycles")
    print(f"  每更新 {UPDATE_MS}ms: {budget['cycles_per_update']:,} cycles ({budget['frames_per_update']} 帧)")
    print('== 带宽 ==')
    print(f"  音频 {ledger['bandwidth']['audio_mbit_per_s']} Mbit/s, 参数 {ledger['bandwidth']['param_mbit_per_s']} Mbit/s")
    print('== 存储与算力 ==')
    print(f"  BRAM 空闲 {ledger['memory']['bram_free_kb']} KB")
    print(f"  MACs/update（保守）: {ledger['compute']['macs_per_update_at_half_rate']:,}")
    print('wrote', OUT.name)


if __name__ == '__main__':
    main()
