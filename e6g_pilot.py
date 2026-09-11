#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 阶段 0-g: 计时试点 (brief §13)。固定配方, 在【最长段】与【最短段】各跑一遍,
   报每个动作的秒数与本进程线程数, 不用最短段线性外推。"""
import os, sys, json, time, threading
import numpy as np
import pandas as pd
from fractions import Fraction

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6g_core as G
import e6g_desc as GD

T = {}


class tic(object):
    def __init__(self, name):
        self.n = name

    def __enter__(self):
        self.t = time.time()
        return self

    def __exit__(self, *a):
        T[self.n] = round(time.time() - self.t, 3)
        print('  %-34s %7.3fs  (线程 %d)' % (self.n, T[self.n], threading.active_count()
                                            + len(os.listdir('/proc/self/task'))), flush=True)


def nthreads():
    try:
        return len(os.listdir('/proc/self/task'))
    except OSError:
        return -1


def main(pname):
    print('=== 试点 %s ===' % pname, flush=True)
    t0 = time.time()
    with tic('00_段构建(取数+70键特征+池+基准)'):
        S = G.seg(pname, 'legacy_all', verbose=False)
    ctx = GD.GCtx(S)
    print('  T=%d Nc=%d pool0日均%.1f 线程%d' % (S.T, S.Nc, S.p0.sum(1).mean(), nthreads()),
          flush=True)

    with tic('01_单腿pct(NS, 含中性化缓存)'):
        Pk = G.get_pct_g(S, D.DK, 'NS', 'hi', 'identity')
    with tic('02_单腿pct(已缓存)'):
        _ = G.get_pct_g(S, D.DK, 'NS', 'hi', 'identity')
    with tic('03_三腿核KTC_mean@25(SRC)'):
        m_src, sc, _ = ctx.build_core_g(GD.parse_core('KTC_mean@25'))
    with tic('04_同核QEDGE'):
        _ = G.keep_QEDGE(sc, S.p0c, 25)
    with tic('05_同核RANKBUDGET(d=22.5)'):
        _ = G.keep_RANKBUDGET(sc, S.p0c, 22.5)
    with tic('06_否决栈(cvr_1d:k10+cr5:k10)'):
        dr = ctx.build_veto_drop_g(GD.parse_veto('cvr_1d:k10+cr5:k10'),
                                   GD.parse_core('KTC_mean@25'))
    with tic('07_DEV权重'):
        idx, val = F.dev_from_dense(S, m_src & ~dr)
    with tic('08_引擎sparse_pnl_H(H=5)'):
        pnl = F.sparse_pnl_H(S, idx, val, 5, F.COST)
    with tic('09_引擎(H=20)'):
        _ = F.sparse_pnl_H(S, idx, val, 20, F.COST)
    with tic('10_变换zprior60(全帧)'):
        _ = G.tf_apply(G.build_raw_g(S, D.DT_), 'zprior60')
    with tic('11_第四腿加权核(alpha=1/8)'):
        c4 = GD.mk_core_g('KTC_mean', 'mean', s=25,
                          keys=[K.FK, K.FT, K.FC, 'realized_vol_20d'],
                          ws=[Fraction(7, 24)] * 3 + [Fraction(1, 8)])
        m4, _, _ = ctx.build_core_g(c4)
    with tic('12_完整配置端到端(掩码->DEV->引擎)'):
        _ = ctx.run(GD.parse_cfg('KTC_mean@30|cvr_1d:k10+cr5:k10'))

    # 条件否决一条路径 (H3 的单位成本)
    with tic('13_条件否决单条(状态分层+毒尾交集+DEV+引擎)'):
        Pt = G.get_pct_g(S, D.DT_, 'NS', 'hi', 'identity')
        st = np.zeros((S.T, S.Nc), bool)
        for t in range(S.T):
            v = np.where(S.p0c[t] & np.isfinite(Pt[t]))[0]
            if len(v):
                st[t, v] = Pt[t, v] >= np.nanmedian(Pt[t, v])
        Q = m_src.copy()
        tox = F.drop_mask_dense(G.get_pct_g(S, D.DB5, 'NS', 'hi', 'identity'), S.p0c, 10)
        cond = Q & ~(tox & st)
        i2, v2 = F.dev_from_dense(S, cond)
        _ = F.sparse_pnl_H(S, i2, v2, 5, F.COST)

    # 随机路径一批 (H3 / K2 的单位成本)
    with tic('14_随机路径x8(行业内重排状态标签)'):
        rng = np.random.default_rng(11)
        for _ in range(8):
            stp = np.zeros_like(st)
            for t in range(0, S.T, 1):
                v = np.where(S.p0c[t])[0]
                if len(v) < 2:
                    continue
                lab = st[t, v].copy()
                rng.shuffle(lab)
                stp[t, v] = lab
            c2 = Q & ~(tox & stp)
            i3, v3 = F.dev_from_dense(S, c2)
            _ = F.sparse_pnl_H(S, i3, v3, 5, F.COST)

    with tic('15_bootstrap x200 (stationary, 块长20)'):
        x = np.nan_to_num(pnl[3], nan=0.0)
        n = len(x)
        rng = np.random.default_rng(3)
        out = np.empty(200)
        for b in range(200):
            idxs = []
            while len(idxs) < n:
                s0 = rng.integers(0, n)
                L = rng.geometric(1 / 20.0)
                idxs.extend(range(s0, min(n, s0 + L)))
            out[b] = x[np.asarray(idxs[:n])].mean()
        _ = float(out.std())

    with tic('16_写盘(逐日账本 parquet)'):
        df = pd.DataFrame(dict(gross=pnl[0], pos=pnl[1], turn=pnl[2], net8=pnl[3]),
                          index=pd.DatetimeIndex(S.dates))
        p = os.path.join(G.RES, 'H0', '_pilot_%s.parquet' % pname)
        df.to_parquet(p)
        os.remove(p)

    T['_total'] = round(time.time() - t0, 3)
    T['_threads_peak'] = nthreads()
    T['_T'] = S.T
    T['_Nc'] = S.Nc
    T['_rss_gb'] = round(int(open('/proc/self/statm').read().split()[1]) * 4096 / 2 ** 30, 2)
    with open(os.path.join(G.RES, 'H0', 'pilot_%s.json' % pname), 'w') as fh:
        json.dump(T, fh, indent=1, ensure_ascii=False)
    print('  合计 %.1fs, 峰值线程 %d, RSS %.2f GB' % (T['_total'], T['_threads_peak'],
                                                     T['_rss_gb']), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
