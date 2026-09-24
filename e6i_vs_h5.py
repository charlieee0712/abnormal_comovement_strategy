#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 相对生产 H5 的完整增量 (plan §5.5: "每个 H 都同时给相对同 H 母体的结构增量, 以及相对生产参照 H5 的完整增量;
两种比较不能合并")。逐日配对: 子账户 net8 (其自身 H) − 同母体 H5 net8; 均值与 NW(lag = 子的 H) 标准误, 分段与 full
(段间不拼接)。母体 H5 逐日序列 = 该母体任一 H5 描述符的 (net8 − dnet8)。输出 statistics/vs_prodH5.csv。
Stage 3 技术修复 (记 hash): 另列相对 R1@H5 / R2@H5 (brief §8) —— 原有列与数值不变;
--post: 两后段 + 后段合并 (vs_prodH5_post_full.csv) + 四段合并 (vs_prodH5_all4.csv, 段间不拼接)。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_stats as ST

MAIN = ('RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL', 'TPAIR', 'FOURARM')
REFS = ('R1', 'R2')


def load_seg(seg):
    od = os.path.join(I.RES, 'accounts', seg)
    idx = pd.read_csv(os.path.join(od, 'merged_index.csv'))
    meta = pd.concat([pd.read_csv(os.path.join(od, 'merged_%s.csv' % r), low_memory=False)
                      for r in idx.route.unique()], ignore_index=True)
    meta = meta[meta.status == 'SUCCEEDED'].set_index('descriptor_id')
    net, dnet = {}, {}
    for f, g in idx.groupby('npz'):
        # 每个 npz 只解压一次; 逐行 copy, 使整块数组在本循环后释放 (NpzFile 每次 z[key] 都重新读整块, 行视图会把整块留在内存)
        with np.load(os.path.join(od, f)) as z:
            N_, D_ = z['net8'], z['dnet8']
        for did, row in zip(g.descriptor_id, g.row):
            net[did] = N_[row].copy()
            dnet[did] = D_[row].copy()
        del N_, D_
    par5 = {}
    for did in net:
        if did in meta.index and int(meta.loc[did, 'H']) == 5 and meta.loc[did, 'route_id'] in MAIN:
            mo = meta.loc[did, 'mother_id']
            if mo not in par5:
                par5[mo] = net[did] - dnet[did]
    return meta, net, par5


def nw1(x, H):
    mu, se, n = ST.nw_se_masked(x[:, None], H)
    return float(mu[0]) * I.ANN, float(se[0]) * I.ANN, int(n[0])


def merged(parts, H):
    """段间不拼接: 各段 NW 按有效日加权合并均值与方差。parts = [x_seg1, x_seg2, ...]。"""
    ms, ss, cs = [], [], []
    for x in parts:
        m_, s_, c_ = ST.nw_se_masked(x[:, None], H)
        ms.append(m_[0]), ss.append(s_[0]), cs.append(c_[0])
    ms, ss, cs = np.asarray(ms), np.asarray(ss), np.asarray(cs)
    with np.errstate(all='ignore'):                       # 与原两段合并公式逐字一致 (任一段无有效日 -> NaN)
        mu = float(np.sum(cs * ms) / np.sum(cs))
        se = float(np.sqrt(np.sum((cs * ss) ** 2) / np.sum(cs) ** 2))
    return mu * I.ANN, se * I.ANN


def main():
    t0 = time.time()
    post = '--post' in sys.argv[1:]
    segs = list(I.POST_SEGS if post else I.DERIV_SEGS)
    out = {}
    for seg in segs:
        meta, net, par5 = load_seg(seg)
        rows = []
        for did, x in net.items():
            if did not in meta.index:
                continue
            mo, H = meta.loc[did, 'mother_id'], int(meta.loc[did, 'H'])
            if mo not in par5:
                continue
            dser = x - par5[mo]
            m_, s_, n_ = nw1(dser, H)
            rec = dict(descriptor_id=did, mother_id=mo, H=H, n_days=n_, d_vs_prodH5_ann=m_, se_nwH=s_)
            refs = {}
            for ref in REFS:
                if ref in par5:
                    dr = x - par5[ref]
                    refs[ref] = dr
                    m2_, s2_, _ = nw1(dr, H)
                    rec['d_vs_%sH5_ann' % ref] = m2_
                    rec['se_vs_%sH5_nwH' % ref] = s2_
            rows.append(rec)
            out.setdefault(did, {})[seg] = (dser, refs, H)
        d = pd.DataFrame(rows)
        d['segment'] = seg
        I.atomic_write_csv(os.path.join(I.RES, 'statistics', 'vs_prodH5_%s.csv' % seg), d)
        print('[%s] %d 描述符; 母体 H5 序列 %s; %.0fs' % (seg, len(d), sorted(par5), time.time() - t0), flush=True)
    rows = []
    for did, dct in out.items():
        if len(dct) < len(segs):
            continue
        H = dct[segs[0]][2]
        rec = dict(descriptor_id=did, H=H)
        rec['d_vs_prodH5_ann'], rec['se_nwH'] = merged([dct[s][0] for s in segs], H)
        for ref in REFS:
            if all(ref in dct[s][1] for s in segs):
                rec['d_vs_%sH5_ann' % ref], rec['se_vs_%sH5_nwH' % ref] = merged([dct[s][1][ref] for s in segs], H)
        rows.append(rec)
    I.atomic_write_csv(os.path.join(I.RES, 'statistics', 'vs_prodH5_%s.csv' % ('post_full' if post else 'full')),
                       pd.DataFrame(rows))
    print('%s %d; %.0fs' % ('post_full' if post else 'full', len(rows), time.time() - t0), flush=True)
    if post:
        # 四段合并 (段间不拼接): 推导两段的逐日序列在此重载
        for seg in I.DERIV_SEGS:
            meta, net, par5 = load_seg(seg)
            for did, x in net.items():
                if did not in out or did not in meta.index:
                    continue
                mo, H = meta.loc[did, 'mother_id'], int(meta.loc[did, 'H'])
                if mo not in par5:
                    continue
                out[did][seg] = (x - par5[mo], {r: x - par5[r] for r in REFS if r in par5}, H)
        rows = []
        for did, dct in out.items():
            if not all(s in dct for s in I.SEGMENTS):
                continue
            H = dct[I.SEGMENTS[0]][2]
            rec = dict(descriptor_id=did, H=H)
            rec['d_vs_prodH5_ann'], rec['se_nwH'] = merged([dct[s][0] for s in I.SEGMENTS], H)
            for ref in REFS:
                if all(ref in dct[s][1] for s in I.SEGMENTS):
                    rec['d_vs_%sH5_ann' % ref], rec['se_vs_%sH5_nwH' % ref] = merged(
                        [dct[s][1][ref] for s in I.SEGMENTS], H)
            rows.append(rec)
        I.atomic_write_csv(os.path.join(I.RES, 'statistics', 'vs_prodH5_all4.csv'), pd.DataFrame(rows))
        print('all4 %d; %.0fs' % (len(rows), time.time() - t0))


if __name__ == '__main__':
    main()
