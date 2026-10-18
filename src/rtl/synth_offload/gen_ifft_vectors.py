#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WORLD 合成卸载（增量 1）：1024 点 IFFT RTL 的参考实现与黄金向量生成器。

本脚本做三件事（纯 numpy，无第三方 WORLD 依赖）：

1. 按 WORLD 合成链路的同构方式构造测试频谱：
   - 513 个复数频点 X[0..512]（DC / Nyquist 强制为实数）；
   - RTL 内部按厄米对称补齐 X[1024-k] = conj(X[k])（k = 1..511），
     再做 1024 点逆 DFT：x[n] = (1/1024) * sum_k X[k] * exp(+j*2*pi*k*n/1024)。
2. 生成 RTL 的黄金向量（RTL 与 testbench 的接口约定见下）：
   - caseK_input.hex    : 513 行，每行 8 位十六进制 = {imag_q15[15:0], real_q15[15:0]}；
   - caseK_expected.hex : 1024 行，每行 8 位十六进制 = x[n] 的 Q1.17 定点值（32 位符号扩展）；
   - vectors.json       : 事件元数据、输入余量、定点模型误差等证据。
3. 生成 1024 点 IFFT 旋转因子 ROM 的 Verilog 源文件（512 项，Q3.15）。

定点格式（与 RTL 一一对应，RTL 见 ifft1024_stream.v）：
- 输入        ：Q1.15（16 位有符号，|X| <= 32767/32768）；
- 内部数据    ：Q1.17（18 位有符号），输入左移 2 位无损扩展；
- 旋转因子    ：Q3.15（18 位有符号，1.0 = 32768，cos/sin 可精确表示 ±1.0）；
- 每级蝶形缩放 1/2（共 10 级，总缩放 1/1024，等价 numpy ifft），
  逐级缩放保证内部不会溢出；
- 乘积      ：18x18 -> 36 位 Q4.32，加 2^14 四舍五入后右移 15 位 -> Q4.17，
              再饱和到 18 位 Q1.17（正常数据不会触发饱和）；
- 和/差     ：19 位，加 1 后算术右移 1 位（四舍五入）-> 18 位 Q1.17；
- 输出        ：Q1.17（18 位有符号），RTL 在 32 位 tdata 上做符号扩展。

输入无溢出契约：对每一帧，主机需保证
    ( |X[0]| + |X[512]| + 2 * sum_{k=1..511} |X[k]| ) / 1024 <= 0.99
这样 IFFT 输出必然落在 (-1, 1)，内部 Q1.17 不会饱和。真实 WORLD 语音的
sqrt(包络) 频点幅度可达 3.0 左右（16 kHz/fft1024/10 ms 帧实测），因此 PS 侧
送数前需要按帧做 2^-e 归一化，并在后续增量里把 e 传给 OLA 增益；本增量先按
"输入已归一化"的契约验证 IFFT 核本身。

用法：
    python gen_ifft_vectors.py                 # 生成向量 + ROM（默认路径）
    python gen_ifft_vectors.py --no-rom        # 只生成向量
    python gen_ifft_vectors.py --check-only    # 只跑模型自检，不写文件
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
N = 1024            # IFFT 点数 / 时域帧长
HB = N // 2 + 1     # 频点个数 513
Q_IN = 15           # 输入小数位
Q_DATA = 17         # 内部/输出数据小数位
TW_FRAC = 15        # 旋转因子小数位（Q3.15）
TW_ONE = 1 << TW_FRAC
SAT_MAX = (1 << (Q_DATA + 1)) - 1    # 131071
SAT_MIN = -(1 << (Q_DATA + 1))       # -131072

ROOT = Path(__file__).resolve().parents[3]      # 仓库根目录
DEFAULT_OUT = ROOT / "build" / "generated" / "pl_synth_offload"
DEFAULT_ROM = Path(__file__).resolve().parent / "twiddle_rom_1024.v"


# ---------------------------------------------------------------------------
# 定点工具
# ---------------------------------------------------------------------------
def rev10(v: int) -> int:
    """10 位下标按位倒序（1024 点 DIT 需要按位倒序装载输入）。"""
    return int(format(v & 0x3FF, "010b")[::-1], 2)


def q_round(x, frac: int) -> np.ndarray:
    """四舍五入到 frac 位小数（round half up），返回 int64。"""
    return np.floor(np.asarray(x, dtype=np.float64) * (1 << frac) + 0.5).astype(np.int64)


def clip_int(v: np.ndarray, lo: int, hi: int) -> np.ndarray:
    return np.clip(v, lo, hi)


def sat18(v: int) -> int:
    return SAT_MIN if v < SAT_MIN else (SAT_MAX if v > SAT_MAX else v)


def twiddle_table() -> tuple[list[int], list[int]]:
    """返回 (cos_q15, sin_q15)，长度 512，角度 +2*pi*j/1024（IFFT 正号）。"""
    cos_v, sin_v = [], []
    for j in range(N // 2):
        ang = 2.0 * math.pi * j / N
        cos_v.append(int(math.floor(math.cos(ang) * TW_ONE + 0.5)))
        sin_v.append(int(math.floor(math.sin(ang) * TW_ONE + 0.5)))
    return cos_v, sin_v


# ---------------------------------------------------------------------------
# 逐位对应的定点 IFFT 模型（与 RTL 完全同序，可用来预测 RTL 误差）
# ---------------------------------------------------------------------------
def fixed_ifft(x_q15: np.ndarray, cos_q15: list[int], sin_q15: list[int]) -> dict:
    """输入 513 点复数 Q1.15，输出 1024 点实数 Q1.17（与 RTL 同序同舍入）。

    返回 dict：out（int64 数组）、sat_count（饱和次数，正常应为 0）。
    """
    # 1) 厄米对称补齐 + 按位倒序装载（RTL 在写 BRAM 时完成）
    data = [0j] * N
    x_re = x_q15[:, 0].astype(np.int64)
    x_im = x_q15[:, 1].astype(np.int64)
    for k in range(HB):
        # Q1.15 -> Q1.17 左移 2 位；-32768 左移后仍是 -131072（18 位补码可表示）
        data[rev10(k)] = complex(int(x_re[k]) << 2, int(x_im[k]) << 2)
        if 0 < k < N // 2:
            # X[1024-k] = conj(X[k])
            data[rev10(N - k)] = complex(int(x_re[k]) << 2, -int(x_im[k]) << 2)

    re = np.array([int(c.real) for c in data], dtype=np.int64)
    im = np.array([int(c.imag) for c in data], dtype=np.int64)
    sat_count = 0

    # 2) 10 级 radix-2 DIT（输入按位倒序 -> 输出自然序）
    for s in range(1, 11):
        length = 1 << s
        half = length >> 1
        for bf in range(N // 2):
            group = bf >> (s - 1)
            j = bf & (half - 1)
            a = (group << s) | j
            b = a | half
            tw = j << (10 - s)
            c, sn = cos_q15[tw], sin_q15[tw]

            # t = v * w，乘积 Q4.32 -> 加 2^14 后算术右移 15 -> Q4.17 -> 饱和
            v_re, v_im = int(re[b]), int(im[b])
            p_re = v_re * c - v_im * sn
            p_im = v_re * sn + v_im * c
            t_re_raw = (p_re + (1 << 14)) >> 15
            t_im_raw = (p_im + (1 << 14)) >> 15
            t_re = sat18(t_re_raw)
            t_im = sat18(t_im_raw)
            if t_re != t_re_raw or t_im != t_im_raw:
                sat_count += 1

            u_re, u_im = int(re[a]), int(im[a])
            # (u +/- t) / 2，加 1 后算术右移 1 位（四舍五入）
            re[a] = (u_re + t_re + 1) >> 1
            im[a] = (u_im + t_im + 1) >> 1
            re[b] = (u_re - t_re + 1) >> 1
            im[b] = (u_im - t_im + 1) >> 1

    return {"out": re.copy(), "sat_count": sat_count}


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------
def _zero_spectrum() -> np.ndarray:
    return np.zeros(HB, dtype=np.complex128)


def _normalize_headroom(spec: np.ndarray, target: float) -> np.ndarray:
    """归一化到 IFFT 无溢出区间。

    同时满足两个约束（取更严格者）：
    1. 最坏情况输出上界 (|X0|+|X512|+2*sum|X1..511|)/1024 <= target；
    2. 单个频点 |X[k]| <= 0.95，保证 Q1.15 输入不削顶（|X| <= 32767/32768）。
    """
    bound = (abs(spec[0]) + abs(spec[-1]) + 2.0 * np.abs(spec[1:-1]).sum()) / N
    peak = float(np.max(np.abs(spec)))
    scale = target / bound if bound > 0 else 1.0
    if peak > 0:
        scale = min(scale, 0.95 / peak)
    return spec * scale


def _dc_nyquist_real(spec: np.ndarray) -> np.ndarray:
    spec = spec.copy()
    spec[0] = complex(spec[0].real, 0.0)
    spec[-1] = complex(spec[-1].real, 0.0)
    return spec


def build_cases() -> list[dict]:
    rng = np.random.default_rng(20261018)
    cases: list[dict] = []

    # case0：全频带实数谱，IFFT 后是 n=0 处的冲激（幅度 0.45），检查满量程与对称性
    spec = np.full(HB, 0.45 + 0j)
    cases.append({
        "name": "impulse_full_band",
        "desc": "513 个频点全为实数 0.45，IFFT 后应为 x[0]=0.45、其余≈0 的冲激",
        "spec": spec,
    })

    # case1：8 个实频点单音叠加，检查正/负频率配对与幅度（输出峰值约 0.014）
    spec = _zero_spectrum()
    for k in (37, 64, 128, 200, 313, 400, 456, 489):
        spec[k] = 0.9 + 0j
    cases.append({
        "name": "multi_tone",
        "desc": "8 个幅度 0.9 的实频点，检查厄米配对与叠加幅度",
        "spec": spec,
    })

    # case2：WORLD 合成同构频谱（sqrt(包络) + 最小相位），最接近真实语音合成输入
    k = np.arange(HB, dtype=np.float64)
    amp = (0.25
           + 2.4 * np.exp(-((k - 16.0) / 9.0) ** 2)
           + 1.6 * np.exp(-((k - 48.0) / 13.0) ** 2)
           + 0.9 * np.exp(-((k - 110.0) / 24.0) ** 2)
           + 0.45 * np.exp(-((k - 250.0) / 70.0) ** 2))
    amp[0] *= 0.5
    amp[-1] *= 0.5
    log_amp = np.log(np.maximum(amp, 1e-9))
    log_full = np.concatenate([log_amp, log_amp[-2:0:-1]])
    cep = np.fft.ifft(log_full).real
    idx = np.arange(N)
    cep_min = np.where(idx == 0, cep,
                       np.where(idx < N // 2, 2.0 * cep,
                                np.where(idx == N // 2, cep, 0.0)))
    min_spec = np.fft.fft(cep_min)[:HB]
    spec = _normalize_headroom(_dc_nyquist_real(min_spec), 0.85)
    cases.append({
        "name": "world_like_minphase",
        "desc": "sqrt(包络)（300 Hz~4 kHz 四个共振峰）+ 最小相位，按 0.85 上界归一化",
        "spec": spec,
    })

    # case3：随机相位宽带谱，按 0.85 上界归一化（WORLD 非周期/混合相位一类的压力测试）
    amp3 = 0.05 + 0.85 * rng.random(HB)
    ph3 = rng.uniform(-math.pi, math.pi, HB)
    spec3 = amp3 * np.exp(1j * ph3)
    spec3 = _normalize_headroom(_dc_nyquist_real(spec3), 0.85)
    cases.append({
        "name": "random_broadband",
        "desc": "随机相位、随机幅度宽带谱（0.85 上界），检查复数通路的随机压力",
        "spec": spec3,
    })

    # case4：只有 Nyquist 频点，输出应为 (-1)^n 交替序列（检查符号与边界频点）
    spec4 = _zero_spectrum()
    spec4[-1] = 0.9 + 0j
    cases.append({
        "name": "nyquist_alternating",
        "desc": "仅 X[512]=0.9，输出应为幅度 0.9/1024 的 (-1)^n 交替序列",
        "spec": spec4,
    })

    # case5：只有 DC，输出应为常量 0.9/1024（检查 DC 与最小幅度分辨率）
    spec5 = _zero_spectrum()
    spec5[0] = 0.9 + 0j
    cases.append({
        "name": "dc_only",
        "desc": "仅 X[0]=0.9，输出应为常量 0.9/1024，检查 DC 与低幅度量化",
        "spec": spec5,
    })

    return cases


# ---------------------------------------------------------------------------
# 生成与校验
# ---------------------------------------------------------------------------
def hermitian_full(spec: np.ndarray) -> np.ndarray:
    full = np.zeros(N, dtype=np.complex128)
    full[:HB] = spec
    for k in range(1, N // 2):
        full[N - k] = np.conj(spec[k])
    return full


def quantize_input(spec: np.ndarray) -> np.ndarray:
    re = clip_int(q_round(spec.real, Q_IN), -(1 << Q_IN), (1 << Q_IN) - 1)
    im = clip_int(q_round(spec.imag, Q_IN), -(1 << Q_IN), (1 << Q_IN) - 1)
    return np.stack([re, im], axis=1)


def write_hex_words(path: Path, words: np.ndarray) -> None:
    with path.open("w", encoding="ascii", newline="\n") as fh:
        for w in words:
            fh.write("%08x\n" % (int(w) & 0xFFFFFFFF))


def word_input(q: np.ndarray) -> np.ndarray:
    re = q[:, 0].astype(np.int64) & 0xFFFF
    im = q[:, 1].astype(np.int64) & 0xFFFF
    return (im << 16) | re


def word_expected(v: np.ndarray) -> np.ndarray:
    # Q1.17 的 32 位符号扩展表示：低 18 位保留，bit31..18 按符号补 1/0
    v = v.astype(np.int64)
    return (v & 0x3FFFF) | np.where(v < 0, 0xFFFC0000, 0)


def decode_expected(word: np.ndarray) -> np.ndarray:
    """把 32 位十六进制字还原成有符号整数（生成器自检用）。"""
    w = word.astype(np.int64) & 0xFFFFFFFF
    return np.where(w >= (1 << 31), w - (1 << 32), w)


def rom_verilog(cos_v: list[int], sin_v: list[int]) -> str:
    lines = [
        "`timescale 1ns/1ps",
        "// ===========================================================================",
        "// 自动生成，请勿手改：由 src/rtl/synth_offload/gen_ifft_vectors.py 生成。",
        "// 1024 点 IFFT 旋转因子 ROM：512 项，每项 {sin_q15[17:0], cos_q15[17:0]}。",
        "// cos/sin 采用 Q3.15 定点（1.0 = 32768，可精确表示 ±1.0），",
        "// 角度 +2*pi*j/1024（IFFT 用正号），j = 0..511。",
        "// ===========================================================================",
        "module twiddle_rom_1024 (",
        "    input  wire        clk,",
        "    input  wire [8:0]  addr,",
        "    output reg  [35:0] data",
        ");",
        "    (* rom_style = \"block\" *) reg [35:0] rom [0:511];",
        "    initial begin",
    ]
    for j in range(N // 2):
        word = ((sin_v[j] & 0x3FFFF) << 18) | (cos_v[j] & 0x3FFFF)
        lines.append("        rom[%3d] = 36'h%09x;" % (j, word))
    lines += [
        "    end",
        "    always @(posedge clk) data <= rom[addr];",
        "endmodule",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="向量输出目录")
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM, help="旋转因子 ROM 输出文件")
    parser.add_argument("--no-rom", action="store_true", help="不生成旋转因子 ROM")
    parser.add_argument("--check-only", action="store_true", help="只做模型自检，不写文件")
    args = parser.parse_args()

    cos_v, sin_v = twiddle_table()
    cases = build_cases()
    report = {
        "generated_by": "src/rtl/synth_offload/gen_ifft_vectors.py",
        "n_fft": N,
        "input_bins": HB,
        "format": {
            "input": "513 行 8 位十六进制，{imag_q15[15:0], real_q15[15:0]}（Q1.15）",
            "expected": "1024 行 8 位十六进制，x[n] 的 Q1.17 32 位符号扩展",
            "output_contract": "x[n] = (1/1024) * sum X[k] * exp(+j2pi k n /1024)，实数部分",
            "headroom_rule": "(|X0|+|X512|+2*sum|X1..511|)/1024 <= 0.99",
        },
        "cases": [],
    }

    max_model_err = 0.0
    for ci, case in enumerate(cases):
        spec = case["spec"]
        bound = float((abs(spec[0]) + abs(spec[-1]) + 2.0 * np.abs(spec[1:-1]).sum()) / N)
        peak_in = float(np.max(np.abs(spec)))
        if bound > 0.99:
            raise SystemExit("case%d 输入无溢出上界 %.4f 超限" % (ci, bound))
        if peak_in * (1 << Q_IN) > (1 << Q_IN) - 1:
            raise SystemExit("case%d 输入频点峰值 %.4f 超出 Q1.15 范围" % (ci, peak_in))
        full = hermitian_full(spec)
        ref = np.fft.ifft(full).real
        x_q = quantize_input(spec)
        expected_q17 = clip_int(q_round(ref, Q_DATA), SAT_MIN, SAT_MAX)
        model = fixed_ifft(x_q, cos_v, sin_v)
        model_err = float(np.max(np.abs(model["out"] - expected_q17)) / (1 << Q_DATA))
        max_model_err = max(max_model_err, model_err)

        input_words = word_input(x_q)
        expected_words = word_expected(expected_q17)
        # 自检：黄金向量文件编码必须能无损还原 Q1.17 期望值
        if not np.array_equal(decode_expected(expected_words), expected_q17):
            raise SystemExit("case%d 黄金向量 32 位符号扩展编码自检失败" % ci)
        case_meta = {
            "index": ci,
            "name": case["name"],
            "desc": case["desc"],
            "input_hex": "case%d_input.hex" % ci,
            "expected_hex": "case%d_expected.hex" % ci,
            "input_peak_abs": round(peak_in, 6),
            "input_headroom_bound": round(bound, 6),
            "ref_peak_abs": round(float(np.max(np.abs(ref))), 8),
            "ref_rms": round(float(np.sqrt(np.mean(ref ** 2))), 8),
            "expected_q17_min": int(expected_q17.min()),
            "expected_q17_max": int(expected_q17.max()),
            "model_vs_float_max_abs_err": round(model_err, 9),
            "model_saturations": int(model["sat_count"]),
        }
        report["cases"].append(case_meta)
        print("case%d %-22s bound=%.4f peak=%.6f model_err=%.3e sat=%d"
              % (ci, case["name"], bound, np.max(np.abs(ref)), model_err,
                 model["sat_count"]))
        if not args.check_only:
            args.out.mkdir(parents=True, exist_ok=True)
            write_hex_words(args.out / case_meta["input_hex"], input_words)
            write_hex_words(args.out / case_meta["expected_hex"], expected_words)

    report["model_max_abs_err"] = round(max_model_err, 9)
    report["tolerance"] = 1e-3
    if not args.check_only:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "vectors.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.no_rom:
            args.rom.write_text(rom_verilog(cos_v, sin_v), encoding="utf-8", newline="\n")
            print("写入旋转因子 ROM:", args.rom)
        print("写入向量目录:", args.out)
    print("模型自检：定点模型 vs numpy ifft 最大绝对误差 = %.3e（容差 1e-3）"
          % max_model_err)
    if max_model_err > 1e-3:
        raise SystemExit("定点模型误差超出容差，检查定点格式")


if __name__ == "__main__":
    main()
