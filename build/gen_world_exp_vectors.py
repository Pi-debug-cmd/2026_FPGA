"""Bit-exact integer model; generates 96 frames including fixed-point boundaries."""
from __future__ import annotations

from pathlib import Path

import numpy as np

N = 1024
TWO_PI = 2.0 * np.pi
LOG2 = np.log(2.0)
TWO_PI_Q18 = int(round(TWO_PI * (1 << 18)))       # 1647099
LN2_Q18 = int(round(LOG2 * (1 << 18)))            # 181704
INV_LN2_Q16 = int(round((1 << 16) / LOG2))        # 94548
# 插值位置用 26 位小数，避免常数近似导致“插值落在错误区间”
S_FRAC = 26
INV_EXP = int(round(256.0 / (LOG2 * (1 << 18)) * (1 << S_FRAC)))
INV_ANG = int(round(1024.0 / (TWO_PI * (1 << 18)) * (1 << S_FRAC)))

EXP_LUT = np.array([int(round(np.exp(i * LOG2 / 256.0) * 65536)) for i in range(256)],
                   dtype=np.int64)                # Q2.16, 256 项
ANG = np.arange(N) * TWO_PI / N
COS_LUT = np.array([int(round(np.cos(t) * 131072)) for t in ANG], dtype=np.int64)
SIN_LUT = np.array([int(round(np.sin(t) * 131072)) for t in ANG], dtype=np.int64)
# Q1.17 有符号 18 位无法表示 +1.0（131072），clamp 到 131071；误差 ≤1 LSB，可忽略
COS_LUT = np.clip(COS_LUT, -131072, 131071)
SIN_LUT = np.clip(SIN_LUT, -131072, 131071)


def model(a_int: np.ndarray, b_int: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """整数模型：输入 (A,B) 24 位有符号，输出 (Y_RE,Y_IM) Q2.17。"""
    A = a_int.astype(np.int64)
    B = b_int.astype(np.int64)
    B = np.where(B < 0, B + TWO_PI_Q18, B)

    K = (A * INV_LN2_Q16) >> 34
    R = A - K * LN2_Q18
    # 越界修正（模型与 RTL 一致）
    R2 = np.where(R < 0, R + LN2_Q18, R)
    K2 = np.where(R < 0, K - 1, K)
    R3 = np.where(R2 >= LN2_Q18, R2 - LN2_Q18, R2)
    K3 = np.where(R2 >= LN2_Q18, K2 + 1, K2)
    R, K = R3, K3

    U = R * INV_EXP
    IDX = np.clip(U >> S_FRAC, 0, 255)
    FRAC = (U & ((1 << S_FRAC) - 1)) >> (S_FRAC - 16)
    LO = EXP_LUT[IDX]
    HI = np.where(IDX == 255, 2 * EXP_LUT[0], EXP_LUT[np.minimum(IDX + 1, 255)])
    E_Q16 = LO + (((HI - LO) * FRAC) >> 16)

    SH = -(K + 1)
    E_Q17 = np.where(SH >= 0, E_Q16 >> np.maximum(SH, 0),
                     E_Q16 << np.maximum(-SH, 0))

    V = B * INV_ANG
    J = np.clip(V >> S_FRAC, 0, N - 1)
    F = (V & ((1 << S_FRAC) - 1)) >> (S_FRAC - 16)
    COS = COS_LUT[J] + (((COS_LUT[(J + 1) & (N - 1)] - COS_LUT[J]) * F) >> 16)
    SIN = SIN_LUT[J] + (((SIN_LUT[(J + 1) & (N - 1)] - SIN_LUT[J]) * F) >> 16)

    Y_RE = (E_Q17 * COS + 131072) >> 17
    Y_IM = (E_Q17 * SIN + 131072) >> 17
    Y_RE = np.clip(Y_RE, -524288, 524287)
    Y_IM = np.clip(Y_IM, -524288, 524287)
    return Y_RE, Y_IM


def q_rnd(x, frac):
    return np.floor(np.asarray(x) * (1 << frac) + 0.5).astype(np.int64)


def main():
    import argparse, json
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--dump',type=Path)
    args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    if args.dump:
        rec=np.fromfile(args.dump,dtype='<f8').reshape(-1,4)
        a,b=rec[:,0],rec[:,1]
    else:
        rng=np.random.default_rng(20261027)
        a=rng.uniform(-13.8,0.1,96*513)
        b=rng.uniform(-np.pi,np.pi,96*513)
        a[:8]=[-13.8,-1e-8,0,.1,-np.log(2),-1,-2,-8]
        b[:8]=[0,-np.pi,np.pi,-1e-8,0,np.pi/2,-np.pi/2,1]
    aq,bq=q_rnd(a,18),q_rnd(b,18)
    yr,yi=model(aq,bq)
    packed_in=((bq.astype(np.uint64)&0xffffff)<<24)|(aq.astype(np.uint64)&0xffffff)
    packed_out=((yi.astype(np.uint64)&0xfffff)<<20)|(yr.astype(np.uint64)&0xfffff)
    for name,data in [('input',packed_in),('expected',packed_out)]:
        (args.out/('exp_'+name+'.hex')).write_text(''.join('%016x\n'%int(x) for x in data),encoding='ascii')
        data.astype('<u8').tofile(args.out/('exp_'+name+'.bin'))
    err=np.abs((yr+1j*yi)/131072-np.exp(a+1j*b))
    result={'bins':len(a),'calls':len(a)//513,'max_complex_error':float(err.max()),
            'rms_complex_error':float(np.sqrt(np.mean(err**2))),'seed':20261027}
    (args.out/'vectors.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__': main()
