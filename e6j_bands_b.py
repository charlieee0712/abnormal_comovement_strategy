# -*- coding: utf-8 -*-
"""E6j B 块同时带（plan §8.4 第二、三层）：主配置 α .25 × H5 的全部研究描述符（子 − 同 H 研究母体，8bp 日配对，四段按有效日合并 FULL）。
  第二层：每个有明确问题的研究块（B1–B7 各一族，含全部母体与方向）；第三层：全部 B 主配置描述符一张探索参考。
平稳块自助与 P 包共享同一组日期 draw（同键 'P-main'、同段长与日期，脚本核对），块均长 20 / 60、各 2,000 次；
max-t 同时带（SE = bootstrap sd；零 sd 列不入族，另报）与逐点 ±1.96·sd 并列；不设新 FWER 门。
读后段账户：须 B_post 封存核对通过。写 results_B/simultaneous_bands_B.csv。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_stats as ST
import e6j_bands as BD

ACC_B = os.path.join(J.RES, 'accounts', 'B')
ACC_P = os.path.join(J.RES, 'accounts', 'P')
OUT = os.path.join(J.RES, 'results_B')
SEGS = list(J.SEGMENTS)
N_DRAWS = 2000


def main_config_series():
    """{段: (日期, {描述符: d 日序列})}；只取 α .25 × H5。"""
    out = {}
    for s in SEGS:
        pz = np.load(os.path.join(ACC_B, s, 'parents.npz'), allow_pickle=False)
        par = {str(k): i for i, k in enumerate(pz['keys'])}
        series = {}
        for p in sorted(glob.glob(os.path.join(ACC_B, s, '*__*.npz'))):
            if os.path.basename(p).startswith('masks_'):
                continue
            mother = os.path.basename(p)[:-4].split('__')[0]
            z = np.load(p, allow_pickle=False)
            net = None
            for i, did in enumerate(z['desc']):
                did = str(did)
                if not did.endswith('|a=0.25|H5'):
                    continue
                if net is None:
                    net = z['net8']
                series[did] = ST.paired(net[i], pz['net8'][par['%s|H5' % mother]])[0]
        out[s] = (np.array([str(x)[:10] for x in pz['dates']]), series)
    return out


def run():
    import e6j_seal as SEAL
    ok, bad = SEAL.verify('B_post')
    if not ok:
        raise RuntimeError('B_post 封存核对未过（%d 项）' % len(bad))
    ser = main_config_series()
    # 与 P 包同一日期 draw：段长与日期逐日相同
    for s in SEGS:
        pd_ = np.load(os.path.join(ACC_P, s, 'A4b_CVRv5.npz'), allow_pickle=False)['dates']
        if not np.array_equal(np.array([str(x)[:10] for x in pd_]), ser[s][0]):
            raise RuntimeError('B 与 P 日期不一致：%s' % s)
    keys = sorted(set.intersection(*[set(ser[s][1]) for s in SEGS]))
    X = {s: np.column_stack([ser[s][1][k] for k in keys]) for s in SEGS}
    lens = {s: len(ser[s][0]) for s in SEGS}; dates = {s: ser[s][0] for s in SEGS}
    real = np.array([ST.full_g4([ST.seg_D(X[s][:, j])[0] for s in SEGS], [ST.seg_D(X[s][:, j])[1] for s in SEGS])[0] for j in range(len(keys))])
    block = np.array([k.split('|')[1] for k in keys])
    rows = {k: dict(descriptor_id=k, block=b, FULL=float(v)) for k, b, v in zip(keys, block, real)}
    for L in (20, 60):
        cm = BD.count_mats(lens, dates, L, N_DRAWS, 'P-main')
        rs = BD.resample(cm, X)
        F = BD.full(rs, SEGS)
        q3, sd, plo, phi, slo3, shi3, fam3 = BD.max_t_band(F, real)
        for j, k in enumerate(keys):
            rows[k].update({'boot_sd_L%d' % L: float(sd[j]), 'point_lo_L%d' % L: float(plo[j]), 'point_hi_L%d' % L: float(phi[j]),
                            'allB_maxt_q95_L%d' % L: q3, 'allB_simul_lo_L%d' % L: float(slo3[j]), 'allB_simul_hi_L%d' % L: float(shi3[j]),
                            'in_family_L%d' % L: bool(fam3[j])})
        for b in sorted(set(block)):
            ix = np.flatnonzero(block == b)
            q2, sd2, _, _, slo2, shi2, _ = BD.max_t_band(F[:, ix], real[ix])
            for jj, j in enumerate(ix):
                rows[keys[j]].update({'block_maxt_q95_L%d' % L: q2, 'block_simul_lo_L%d' % L: float(slo2[jj]), 'block_simul_hi_L%d' % L: float(shi2[jj])})
        del cm, rs
    df = pd.DataFrame(list(rows.values()))
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'simultaneous_bands_B.csv')
    if os.path.exists(p):
        raise RuntimeError('只增不删：%s 已存在' % p)
    J.atomic_write_csv(p, df)
    J.write_receipt('bands_B', [p], 'SUCCEEDED', n=len(df), blocks=int(len(set(block))))
    print('bands_B', len(df))
    return 0


if __name__ == '__main__':
    sys.exit(run())
