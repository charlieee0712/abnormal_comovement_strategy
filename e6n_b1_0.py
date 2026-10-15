# -*- coding: utf-8 -*-
"""E6n B1-0：第一道分钟测量（brief A2 / A3、§1.4；plan §6.1 / §7.2 / §2.3；附录 S4 / D）。只两推导段；只在 Stage B 冻结之后、任何推导段账户之前；
结果只给 G 账本 probe_result 打标签（A2 真值表），不改任何对象 / 阈值 / 频率（plan §2.2）。
域（MEMBERS × DOMAINS × SCOPES）：
  POOL0；CLEAN（全 clean 格，含 clean\pool0；QGOOD 只在 pool0 定义 → 只 ALL）；A4b_CVRv5 原生形成最终名单；Q0|A4b_CVRv5|α.25|HG10 形成最终名单（主域）；
  两者相对 pool0 的拒绝集；其余五形态的原生 / Q0|α.25|HG10 形成名单（迁移读法）。作用域 QGOOD（主）/ ALL（桥）。
标签：E6m B3 事件表（stageN/B3_prelim/work/events_<段>__POOL0 / CLEAN；FWD_SOURCE 逐字调用源前向函数，ENDPOINT / LINEAR 为桥）h1 / h3 / h5 / h10 / h20，
  单位 bp（持有期累计）；本表另列 bp_per_h。子域标签 = 同一前向收益减去本域当日均值（pool0 基准在域内差里约去）。
统计（plan §6.1）：诊断三分 u = (#更小 + 0.5·#相等)/n，组 = min(2, floor(3u))（全等 → 中组，两尾差不可算 ≠ 0）；先形成日内组等权 → 两组同时可估日求差 →
  跨形成日等权；n = 有效配对形成日；股票事件数另列；DEV 资本加权（门内域）另列；HAC（Newey–West，lag = H）se 只作列。
匹配（plan §7.2）：同日 / 同 Q 诊断组（域内 kQ 三分）/ 同一级行业内，低组对高组无放回；L1 距离，坐标尺度 = 当日域内两端候选 IQR（0 → range，全同 → 0）；
  层 1 = log_mcap、log(过去 20 日有限成交额均值，含 T)；层 2 = 层 1 + kQ、k0、log(H/L)；GAP 桥 = 层 2 + log(O/lclose)；
  scipy linear_sum_assignment（先最大配对数 = min(a, b)，再最小总距离；行列按 ticker 升序 → 并列解确定）。
A2 标签（主域 = QGOOD ∩ Q0|A4b_CVRv5|α.25|HG10 形成集，FWD_SOURCE h5 低 − 高）：见 label_a2（规则在 Stage B 冻结前登记于 registry/b1_0_manifest_E6n.csv 的 a2_rule）。
输出 results/b1_0/b1_0_{cells,pairs,matched,moderators,bridges,regimes}.csv + probe_ledger.csv + registration/seal_B1_0.json。"""
import os
import sys
import json
import time
import pickle
import argparse
import multiprocessing as mp

import numpy as np
import pandas as pd

import e6n_core as N

E6M_W = N.E6M_WORK
HS = (1, 3, 5, 10, 20)
LABELS = ('FWD_SOURCE', 'FWD_ENDPOINT', 'FWD_LINEAR')
FORMS6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
MAIN_DOMAIN = 'GATE_A4b_CVRv5_Q0HG10'
# 成员：(id, 类, meas/full 网格名, meas/<段> 单元列, 工作方向 +1 = 高坏 / 0 = 无登记方向, 卡)
MEMBERS = [
    ('PL_REL20_f5', 'FACET_REL', 'PL_REL20_5', 'raw_PL_REL20_f5', 1, 'H03'),
    ('PL_5', 'FACET_RAW', 'PL_5', 'col_PL_5', 1, 'H03'),
    ('TAIL_PUSH', 'FACET_REL', 'TAIL_PUSH', 'raw_TAIL_PUSH_f5', 1, 'H05'),
    ('L_TAIL', 'FACET_RAW', 'L_TAIL', 'col_L_TAIL', 1, 'H05'),
    ('TAIL_VOL_REL20', 'FACET_REL', 'TAIL_VOL_REL20', 'raw_TAIL_VOL_REL20_f5', 1, 'H06'),
    ('S_TAIL', 'FACET_RAW', 'S_TAIL', 'col_S_TAIL', 1, 'H06'),
    ('JSD_PROFILE20', 'FACET_REL', 'JSD_PROFILE20', 'raw_JSD_PROFILE20_f5', 1, 'H06'),
    ('RV_REL20_f5', 'FACET_REL', 'RV_REL20_5', 'raw_RV_REL20_f5', 1, 'H08'),
    ('RV_5', 'FACET_RAW', 'RV_5', 'col_RV_5', 1, 'H08'),
    ('PL_REL20_f1', 'FREQ_BRIDGE', 'PL_REL20_1', 'raw_PL_REL20_f1', 1, 'H08'),
    ('PL_REL20_f10', 'FREQ_BRIDGE', 'PL_REL20_10', 'raw_PL_REL20_f10', 1, 'H08'),
    ('RV_REL20_f1', 'FREQ_BRIDGE', 'RV_REL20_1', 'raw_RV_REL20_f1', 1, 'H08'),
    ('RV_REL20_f10', 'FREQ_BRIDGE', 'RV_REL20_10', 'raw_RV_REL20_f10', 1, 'H08'),
    ('h_path_f5', 'ADAPTED_RAW', 'h_path_5', 'comp_h_path_f5', 1, 'H04'),
    ('h_close', 'ADAPTED_RAW', 'h_close', 'comp_h_close_f5', 1, 'H07'),
    ('sqrtRV_f5', 'RAW_CONTROL', 'sqrtRV_5', 'comp_sqrtRV_f5', 1, 'H04'),
    ('log_hl', 'RAW_CONTROL', 'LOG_HL', 'comp_log_hl_f5', 1, 'H04'),
    ('u_close', 'RAW_CONTROL', 'h_close_level', 'comp_h_close_level_f5', 1, 'H07'),
    ('K_RANGE_SOURCE', 'OHLC_BRIDGE', '', 'raw_K_RANGE_SOURCE_f5', 1, 'H08'),
    ('CLV20_SOURCE', 'OHLC_BRIDGE', '', 'raw_CLV20_SOURCE_f5', 1, 'H08'),
] + [(n, 'SRC481_BRIDGE', n, 'col_' + n, 0, 'H08') for n in (
    'SRC481_PATH_EFF_1M', 'SRC481_HIGH_TIMING_1M', 'SRC481_VSDS_K8', 'SRC481_VSDS_K5', 'SRC481_VOLUME_ENTROPY_1D', 'SRC481_VOLUME_HHI_1D',
    'SRC481_VOLUME_HHI_NORM_1D', 'SRC481_VSDS_KL_1D', 'SRC481_SESSION_VOLUME_DEVIATION_MAX', 'SRC481_CLOSING_30MIN_VOLUME_RATIO')]
MEMBER_IDS = [m[0] for m in MEMBERS]
MATCH_MEMBERS = ('PL_REL20_f5', 'TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20', 'RV_REL20_f5', 'h_path_f5', 'h_close', 'sqrtRV_f5', 'log_hl', 'u_close')
MOD_MEMBERS = ('PL_REL20_f5', 'TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20', 'RV_REL20_f5', 'h_path_f5', 'h_close')
BRIDGE_OF = {'PL_REL20_f5': ('K_RANGE_SOURCE', 'log_hl'), 'RV_REL20_f5': ('K_RANGE_SOURCE', 'log_hl'), 'h_path_f5': ('K_RANGE_SOURCE', 'log_hl'),
             'TAIL_PUSH': ('CLV20_SOURCE',), 'h_close': ('CLV20_SOURCE',), 'TAIL_VOL_REL20': ('CLV20_SOURCE',), 'JSD_PROFILE20': ('CLV20_SOURCE',)}
SAME_SIZE = 0.25          # A2「同向同量」= 桥的低 − 高与成员同号且 |桥 − 成员| ≤ 25%·|成员|（Stage B 冻结前登记）
VANISH = 0.25             # 匹配后「差消失」= 匹配差 ≤ 0（原生 > 0 时）或 |匹配差| < 25%·|原生差|


def domains():
    d = [('POOL0', 'pool0 全部格'), ('CLEAN', 'clean 全部格（含 clean\\pool0；QGOOD 不适用）')]
    for f in FORMS6:
        d.append(('GATE_%s_NATIVE' % f, '%s 原生（α = 0）形成最终名单' % f))
        d.append(('GATE_%s_Q0HG10' % f, 'Q0|%s|α.25|HG10 形成最终名单' % f))
    d.append(('REJ_A4b_CVRv5_NATIVE', 'pool0 \\ A4b_CVRv5 原生形成最终名单'))
    d.append(('REJ_A4b_CVRv5_Q0HG10', 'pool0 \\ Q0|A4b_CVRv5|α.25|HG10 形成最终名单'))
    return d


def manifest():
    """registry/b1_0_manifest_E6n.csv：成员 × 域 × 作用域 × 表 × 列（Stage B 冻结件）。"""
    rows = []
    for mid, kind, grid, cell, dr, card in MEMBERS:
        for dom, desc in domains():
            for scope in ('QGOOD', 'ALL'):
                if dom == 'CLEAN' and scope == 'QGOOD':
                    continue
                tabs = ['b1_0_cells', 'b1_0_pairs']
                if mid in MATCH_MEMBERS and (dom in ('POOL0', MAIN_DOMAIN, 'REJ_A4b_CVRv5_Q0HG10', 'GATE_A4b_CVRv5_NATIVE')):
                    tabs.append('b1_0_matched')
                if mid in MOD_MEMBERS and dom in ('POOL0', MAIN_DOMAIN, 'REJ_A4b_CVRv5_Q0HG10') and scope == 'QGOOD':
                    tabs += ['b1_0_moderators', 'b1_0_regimes']
                if mid in BRIDGE_OF:
                    tabs.append('b1_0_bridges')
                rows.append(dict(member=mid, member_kind=kind, card=card, direction=dr, domain=dom, domain_desc=desc, scope=scope, tables='|'.join(tabs),
                                 labels='|'.join(LABELS), H='|'.join(str(h) for h in HS), segments='|'.join(N.DERIV_SEGS),
                                 columns='member|domain|scope|segment|label|H|tercile|stat|value|unit|n_days|n_events|status|query_id',
                                 a2_rule=('主域 %s ∩ QGOOD、FWD_SOURCE h5 低 − 高：两段 n 加权 > 0 且两段同号 → 支持；> 0 但异号 → mixed（跨时代不稳定）；≤ 0 → 不支持（方向 miss）；'
                                          'pool0∩QGOOD > 0 而主域 ≤ 0 → 加注 池子层面读法；层 1 / 层 2 匹配后差 ≤ 0 或 |匹配| < %.0f%%·|原生| → 加注 混杂候选；'
                                          '对应桥同号且 |桥 − 成员| ≤ %.0f%%·|成员| → 加注 分钟未多出信息；分钟未覆盖 → 未检验；方向未登记（源桥）→ 只报数不打方向标签'
                                          % (MAIN_DOMAIN, VANISH * 100, SAME_SIZE * 100)) if (dom == MAIN_DOMAIN and scope == 'QGOOD') else 'NOT_APPLICABLE'))
    return pd.DataFrame(rows)


# ====================================================================== 数据
def terc_mid_groups(x, key):
    """按 key（单元已按 key 排序）分组的中分布三分：有限值 → 0 / 1 / 2；缺 → −1。全等组 → 中组 1。"""
    out = np.full(len(x), -1, np.int64)
    ok = np.isfinite(x)
    if not ok.any():
        return out
    k = np.asarray(key)[ok].astype(np.int64)
    r = group_avg_rank(k, x[ok])                         # 平均秩 = #更小 + 0.5·#相等 + 0.5
    n = np.bincount(k)[k].astype(float)
    u = (r - 0.5) / n
    out[ok] = np.minimum(2, np.floor(3 * u)).astype(np.int64)
    return out


class SegData(object):
    """一个推导段：pool0 单元（测量单元）与 clean 单元两个宇宙；成员值、标签、调节变量、匹配坐标、域掩码。"""

    def __init__(self, seg):
        import e6n_vars as VR
        import e6n_meas as ME
        self.seg = seg
        B = VR.Base(seg)
        self.B = B
        S = ME.SegM(seg)
        self.S = S
        ctx = S.ctx
        dates = B.get('dates')
        codes = B.get('codes')
        self.dates = dates
        N.assert_end_ok(str(int(dates.max())), 'B1-0 %s' % seg)
        # ---- pool0 宇宙（测量单元）
        U = {}
        U['t'], U['c'] = B.t, B.c
        U['code'] = codes[B.c]
        U['qgood'] = B.qgood
        U['kQ'] = B.kQ
        U['k0'] = B.get('k0')
        lm = S.cells(ctx['log_mcap'].reindex(index=S.pool0.index, columns=S.pool0.columns).to_numpy(float)[:, S.ccols])
        U['log_mcap'] = lm
        amt = ctx['data']['amount'].astype(float).reindex(index=S.pool0.index, columns=S.pool0.columns)
        am20 = amt.where(np.isfinite(amt) & (amt > 0)).rolling(20, min_periods=1).mean()
        with np.errstate(all='ignore'):
            U['log_amt20'] = S.cells(np.log(am20.to_numpy(float))[:, S.ccols])
        U['log_hl'] = B.get('col_LOG_HL')
        U['gap'] = B.get('col_GAP')
        ind = ctx['industry'].reindex(index=S.pool0.index, columns=S.pool0.columns).to_numpy(float)[:, S.ccols]
        U['ind'] = S.cells(np.where(np.isfinite(ind), ind, -1)).astype(np.int64)
        for mid, kind, grid, cell, dr, card in MEMBERS:
            U['m:' + mid] = B.get(cell)
        self.U = U
        self.n = len(B.t)
        # ---- 标签与调节变量（E6m B3 POOL0 事件 → 单元）
        self.Y, self.mod = self._labels('POOL0', U)
        # ---- 域掩码（pool0 宇宙）
        self.dom = {'POOL0': np.ones(self.n, bool)}
        for f in FORMS6:
            z = np.load(N.P('masks', seg, '%s.npz' % f), allow_pickle=False)
            keys = [str(k) for k in z['mask_keys']]
            n = int(z['n_cells'][0])
            nat = np.unpackbits(z['final_bits'][keys.index('NONE|a0|NATIVE')])[:n].astype(bool)
            q0h = np.unpackbits(z['final_bits'][keys.index('HG10|a0.25|Q0')])[:n].astype(bool)
            self.dom['GATE_%s_NATIVE' % f] = nat
            self.dom['GATE_%s_Q0HG10' % f] = q0h
        self.dom['REJ_A4b_CVRv5_NATIVE'] = ~self.dom['GATE_A4b_CVRv5_NATIVE']
        self.dom['REJ_A4b_CVRv5_Q0HG10'] = ~self.dom['GATE_A4b_CVRv5_Q0HG10']
        # ---- clean 宇宙（含 clean\pool0；成员值取 meas/full；OHLC 桥只在源缓存网格内）
        self.C = self._clean_universe(ctx, dates, codes)

    def _labels(self, dom, U):
        z = np.load(os.path.join(E6M_W, 'stageN', 'B3_prelim', 'work', 'events_%s__%s.npz' % (self.seg, dom)), allow_pickle=False)
        ed = np.array([int(str(x).replace('-', '')) for x in z['dates']], np.int64)
        di = {int(d): i for i, d in enumerate(self.dates)}
        tt = np.array([di.get(int(ed[t]), -1) for t in z['t']], np.int64)
        key = {}
        for i, (a, b) in enumerate(zip(U['t'], U['code'])):
            key[(int(a), str(b))] = i
        ix = np.array([key.get((int(a), '%06d' % int(b)), -1) for a, b in zip(tt, z['tick'])], np.int64)
        ok = ix >= 0
        n = len(U['t'])
        Y = np.full((n, len(z['ycols'])), np.nan)
        Y[ix[ok]] = z['Y'][ok]
        mod = {}
        for k in ('pos', 'act20', 'vol3', 'trend', 'size3', 'k3', 'cash'):
            v = np.full(n, -9, np.int64)
            v[ix[ok]] = np.asarray(z[k])[ok].astype(np.int64)
            mod[k] = v
        self.label_cols = [str(c) for c in z['ycols']]
        self.label_cover = dict(events=int(len(ix)), mapped=int(ok.sum()), cells=n, cells_with_label=int(np.isfinite(Y).any(1).sum()))
        return Y, mod

    def _clean_universe(self, ctx, dates, codes_seg):
        import e6n_meas as ME
        fd = N.P('meas', 'full')
        fdates = np.load(os.path.join(fd, 'dates.npy'))
        fcodes = np.load(os.path.join(fd, 'codes.npy'))
        cl = ctx['clean'].reindex(index=self.S.pool0.index).fillna(0)
        rr, cc = np.nonzero(cl.to_numpy() == 1)
        ccode = np.array([str(x)[:6] for x in cl.columns])[cc]
        ri = pd.Index(fdates).get_indexer(dates[rr])
        cj = pd.Index(fcodes).get_indexer(ccode)
        ok = (ri >= 0)
        rr, ccode, ri, cj = rr[ok], ccode[ok], ri[ok], cj[ok]
        o = np.lexsort((ccode, rr))
        rr, ccode, ri, cj = rr[o], ccode[o], ri[o], cj[o]
        C = dict(t=rr, code=ccode)
        pc = {(int(a), str(b)): i for i, (a, b) in enumerate(zip(self.U['t'], self.U['code']))}
        for mid, kind, grid, cell, dr, card in MEMBERS:
            if grid:
                A = np.load(os.path.join(fd, grid + '.npy'), mmap_mode='r')
                v = np.full(len(rr), np.nan)
                m = cj >= 0
                v[m] = np.asarray(A[ri[m], cj[m]])
                C['m:' + mid] = v
            else:
                v = np.full(len(rr), np.nan)
                src = self.U['m:' + mid]
                for i, (a, b) in enumerate(zip(rr, ccode)):
                    j = pc.get((int(a), str(b)))
                    if j is not None:
                        v[i] = src[j]
                C['m:' + mid] = v
        Yc, modc = self._labels('CLEAN', C)
        C['Y'] = Yc
        C['mod'] = modc
        C['n'] = len(rr)
        return C


# ====================================================================== 统计
def nw_se(x, lag):
    """Newey–West（Bartlett）均值标准误；x 已去 NaN。"""
    x = np.asarray(x, float)
    n = len(x)
    if n < 3:
        return np.nan
    e = x - x.mean()
    s = e @ e / n
    for l in range(1, min(lag, n - 1) + 1):
        w = 1.0 - l / (lag + 1.0)
        s += 2.0 * w * (e[l:] @ e[:-l]) / n
    return float(np.sqrt(s / n)) if s > 0 else np.nan


def group_avg_rank(key, v):
    """组（key）内平均秩（1 起；并列取平均）——pandas rank(method='average') 的分组向量版。"""
    n = len(v)
    if n == 0:
        return np.zeros(0)
    o = np.lexsort((v, key))
    ks, vs = key[o], v[o]
    newk = np.r_[True, ks[1:] != ks[:-1]]
    gstart = np.maximum.accumulate(np.where(newk, np.arange(n), 0))
    pos = np.arange(n) - gstart
    newt = np.r_[True, (ks[1:] != ks[:-1]) | (vs[1:] != vs[:-1])]
    tid = np.cumsum(newt) - 1
    avg = np.bincount(tid, weights=pos) / np.bincount(tid)
    r = np.empty(n)
    r[o] = avg[tid] + 1.0
    return r


def daily_spearman(t, x, y, nmin=10):
    """逐日 Spearman（秩的 Pearson；t 已排序、x / y 有限）→ 有效日的 IC 数组（日内 ≥ nmin 且两边秩方差 > 0）。"""
    if not len(t):
        return np.zeros(0)
    rx, ry = group_avg_rank(t, x), group_avg_rank(t, y)
    T = int(t.max()) + 1
    n = np.bincount(t, minlength=T).astype(float)
    sx, sy = np.bincount(t, rx, T), np.bincount(t, ry, T)
    sxx, syy, sxy = np.bincount(t, rx * rx, T), np.bincount(t, ry * ry, T), np.bincount(t, rx * ry, T)
    with np.errstate(all='ignore'):
        cov = sxy / n - (sx / n) * (sy / n)
        vx = sxx / n - (sx / n) ** 2
        vy = syy / n - (sy / n) ** 2
        ic = cov / np.sqrt(vx * vy)
    ok = (n >= nmin) & (vx > 1e-12) & (vy > 1e-12) & np.isfinite(ic)
    return ic[ok]


def day_stats(t, g, y, w=None):
    """逐日：各组均值（等权或权重 w）与域当日均值。返回 (days, mean[3], n[3], dom_mean)。t 已排序。"""
    days = np.unique(t)
    T = int(t.max()) + 1 if len(t) else 0
    fin = np.isfinite(y)
    ww = np.ones(len(y)) if w is None else w
    dm_n = np.bincount(t[fin], weights=ww[fin], minlength=T)
    dm_s = np.bincount(t[fin], weights=(ww * np.where(fin, y, 0))[fin], minlength=T)
    with np.errstate(all='ignore'):
        dom = dm_s / dm_n
    M = np.full((T, 3), np.nan)
    Nn = np.zeros((T, 3), np.int64)
    for k in range(3):
        m = fin & (g == k)
        s = np.bincount(t[m], weights=(ww * y)[m], minlength=T)
        c = np.bincount(t[m], weights=ww[m], minlength=T)
        Nn[:, k] = np.bincount(t[m], minlength=T)
        with np.errstate(all='ignore'):
            M[:, k] = np.where(c > 0, s / c, np.nan)
    return days, M, Nn, dom


def member_tables(sd, seg, mid, dr, dom_name, scope, univ):
    """一个 (成员, 域, 作用域, 段)：cells / pairs 行（全部标签 × H）。"""
    if univ == 'CLEAN':
        C = sd.C
        t, x, Y = C['t'], C['m:' + mid], C['Y']
        mask = np.ones(len(t), bool)
        w = None
    else:
        U = sd.U
        t, x, Y = U['t'], U['m:' + mid], sd.Y
        mask = sd.dom[dom_name].copy()
        if scope == 'QGOOD':
            mask &= U['qgood']
        w = sd.capw.get(dom_name)
    tt = t[mask]
    xx = x[mask]
    g = terc_mid_groups(xx, tt)
    rows_c, rows_p = [], []
    unest = int(len(np.unique(tt[np.isfinite(xx)]))) - int(len(np.unique(tt[(g == 0) | (g == 2)]))) if len(tt) else 0
    atom0 = float((xx[np.isfinite(xx)] == 0).mean()) if np.isfinite(xx).any() else np.nan
    cover = float(np.isfinite(xx).mean()) if len(xx) else np.nan
    base = dict(member=mid, domain=dom_name, scope=scope, segment=seg)
    for j, col in enumerate(sd.label_cols if univ != 'CLEAN' else sd.label_cols):
        lab, hh = col.rsplit('_h', 1)
        H = int(hh)
        y = Y[mask, j]
        days, M, Nn, dmean = day_stats(tt, g, y)
        rel = M - dmean[:, None]
        for k, nm in enumerate(('LOW', 'MID', 'HIGH')):
            ok = np.isfinite(rel[:, k])
            v = float(np.mean(rel[ok, k])) if ok.any() else np.nan
            rows_c.append(dict(base, label=lab, H=H, tercile=nm, stat='mean_rel_domain_bp', value=v, unit='bp', n_days=int(ok.sum()),
                               n_events=int(Nn[ok, k].sum()), status='COMPUTED' if ok.any() else 'NOT_COMPUTABLE'))
            rows_c.append(dict(base, label=lab, H=H, tercile=nm, stat='mean_rel_domain_bp_per_h', value=v / H if ok.any() else np.nan, unit='bp_per_h',
                               n_days=int(ok.sum()), n_events=int(Nn[ok, k].sum()), status='COMPUTED' if ok.any() else 'NOT_COMPUTABLE'))
        dd = M[:, 0] - M[:, 2]
        ok = np.isfinite(dd)
        v = float(dd[ok].mean()) if ok.any() else np.nan
        se = nw_se(dd[ok], H) if ok.sum() > 2 else np.nan
        st = 'COMPUTED' if ok.any() else 'NOT_COMPUTABLE'
        ne = int((Nn[ok, 0] + Nn[ok, 2]).sum())
        for stat, val, unit in (('low_minus_high_bp', v, 'bp'), ('low_minus_high_bp_per_h', v / H if ok.any() else np.nan, 'bp_per_h'),
                                ('low_minus_high_hac_se_bp', se, 'bp'), ('low_minus_high_t_hac', v / se if (ok.any() and se and np.isfinite(se)) else np.nan, 'decimal')):
            rows_p.append(dict(base, label=lab, H=H, tercile='LOW_MINUS_HIGH', stat=stat, value=val, unit=unit, n_days=int(ok.sum()), n_events=ne, status=st))
        if w is not None:
            daysw, Mw, Nw, dmw = day_stats(tt, g, y, w[mask])
            dw = Mw[:, 0] - Mw[:, 2]
            okw = np.isfinite(dw)
            rows_p.append(dict(base, label=lab, H=H, tercile='LOW_MINUS_HIGH', stat='low_minus_high_capw_bp', value=float(dw[okw].mean()) if okw.any() else np.nan,
                               unit='bp', n_days=int(okw.sum()), n_events=int((Nw[okw, 0] + Nw[okw, 2]).sum()), status='COMPUTED' if okw.any() else 'NOT_COMPUTABLE'))
        # 连续 rank 关系（逐日 Spearman，域内；只 FWD_SOURCE）
        if lab == 'FWD_SOURCE':
            fin = np.isfinite(xx) & np.isfinite(y)
            ics = daily_spearman(tt[fin], xx[fin], y[fin])
            rows_p.append(dict(base, label=lab, H=H, tercile='CONTINUOUS', stat='rank_ic_mean', value=float(np.mean(ics)) if len(ics) else np.nan, unit='decimal',
                               n_days=int(len(ics)), n_events=int(fin.sum()), status='COMPUTED' if len(ics) else 'NOT_COMPUTABLE'))
    for stat, val, unit in (('member_coverage_share', cover, 'decimal'), ('atom_zero_share', atom0, 'decimal'), ('two_tail_unestimable_days', unest, 'count')):
        rows_p.append(dict(base, label='NOT_APPLICABLE', H=0, tercile='DIAG', stat=stat, value=val, unit=unit, n_days=0, n_events=int(len(xx)),
                           status='COMPUTED' if np.isfinite(val) else 'NOT_COMPUTABLE'))
    return rows_c, rows_p


def moderator_tables(sd, seg, mid, dom_name):
    """主域 / pool0 / 拒绝集 × QGOOD × FWD_SOURCE h5：低 − 高在调节格内（位置 / 活动 / 九格 / Vol3 / Trend / size3 / 旧 K3）与制度期。"""
    U = sd.U
    mask = sd.dom[dom_name] & U['qgood']
    j = sd.label_cols.index('FWD_SOURCE_h5')
    t, x, y = U['t'][mask], U['m:' + mid][mask], sd.Y[mask, j]
    g = terc_mid_groups(x, t)
    mod = {k: v[mask] for k, v in sd.mod.items()}
    code = U['code'][mask]
    ex = np.where(np.char.startswith(code.astype(str), '6'), 'SH', 'SZ')
    dts = sd.dates[t]
    regime = np.where(ex == 'SZ', 'SZ', np.where(dts >= 20180820, 'SH_POST', 'SH_PRE'))
    cats = {'pos': mod['pos'], 'act20': mod['act20'], 'pos_x_act20': mod['pos'] * 10 + mod['act20'], 'vol3': mod['vol3'], 'trend': mod['trend'],
            'size3': mod['size3'], 'k3': mod['k3']}
    rows, rg = [], []
    base = dict(member=mid, domain=dom_name, scope='QGOOD', segment=seg, label='FWD_SOURCE', H=5)
    for mname, mv in cats.items():
        for cv in np.unique(mv):
            if cv < 0:
                continue
            m = mv == cv
            if m.sum() < 30:
                continue
            days, M, Nn, dm = day_stats(t[m], g[m], y[m])
            dd = M[:, 0] - M[:, 2]
            ok = np.isfinite(dd)
            rows.append(dict(base, moderator=mname, cell=int(cv), stat='low_minus_high_bp', value=float(dd[ok].mean()) if ok.any() else np.nan, unit='bp',
                             n_days=int(ok.sum()), n_events=int((Nn[ok, 0] + Nn[ok, 2]).sum()), status='COMPUTED' if ok.any() else 'NOT_COMPUTABLE'))
    for rv in ('SH_PRE', 'SH_POST', 'SZ'):
        m = regime == rv
        if not m.any():
            rg.append(dict(base, regime=rv, stat='low_minus_high_bp', value=np.nan, unit='bp', n_days=0, n_events=0, status='NOT_COVERED'))
            continue
        days, M, Nn, dm = day_stats(t[m], g[m], y[m])
        dd = M[:, 0] - M[:, 2]
        ok = np.isfinite(dd)
        rg.append(dict(base, regime=rv, stat='low_minus_high_bp', value=float(dd[ok].mean()) if ok.any() else np.nan, unit='bp', n_days=int(ok.sum()),
                       n_events=int((Nn[ok, 0] + Nn[ok, 2]).sum()), status='COMPUTED' if ok.any() else 'NOT_COMPUTABLE'))
    return rows, rg


def match_task(args):
    """(段, 成员, 域, 作用域, 层) → 匹配低 − 高（全部标签 × H）+ 平衡 / 覆盖。子进程（fork 共享 SD）。"""
    seg, mid, dom_name, scope, layer = args
    from scipy.optimize import linear_sum_assignment
    sd = SD[seg]
    U = sd.U
    mask = sd.dom[dom_name].copy()
    if scope == 'QGOOD':
        mask &= U['qgood']
    idx = np.flatnonzero(mask)
    t, x = U['t'][idx], U['m:' + mid][idx]
    g = terc_mid_groups(x, t)
    qg = terc_mid_groups(U['kQ'][idx], t)
    coords = ['log_mcap', 'log_amt20'] + (['kQ', 'k0', 'log_hl'] if layer in ('L2', 'GAP') else []) + (['gap'] if layer == 'GAP' else [])
    X = np.column_stack([U[c][idx] for c in coords])
    ind = U['ind'][idx]
    code = U['code'][idx]
    pairs_d, pairs_lo, pairs_hi = [], [], []
    bal_pre, bal_post, cost_tot, n_cand = [], [], 0.0, 0
    bnd = np.flatnonzero(np.r_[True, t[1:] != t[:-1], True]) if len(t) else np.array([0])
    for a, b in zip(bnd[:-1], bnd[1:]):
        gd = g[a:b]
        ends = (gd == 0) | (gd == 2)
        Xd = X[a:b]
        okc = np.isfinite(Xd).all(1)
        cand = ends & okc
        n_cand += int(ends.sum())
        if not (gd[cand] == 0).any() or not (gd[cand] == 2).any():
            continue
        sc = np.ones(X.shape[1])
        for k in range(X.shape[1]):
            v = Xd[cand, k]
            q75, q25 = np.percentile(v, 75), np.percentile(v, 25)
            iqr = q75 - q25
            sc[k] = iqr if iqr > 0 else (v.max() - v.min())
        sc_ = np.where(sc > 0, sc, np.inf)
        for qv in np.unique(qg[a:b][cand]):
            for iv in np.unique(ind[a:b][cand]):
                ss = cand & (qg[a:b] == qv) & (ind[a:b] == iv)
                lo = np.flatnonzero(ss & (gd == 0))
                hi = np.flatnonzero(ss & (gd == 2))
                if not len(lo) or not len(hi):
                    continue
                lo = lo[np.argsort(code[a:b][lo], kind='stable')]
                hi = hi[np.argsort(code[a:b][hi], kind='stable')]
                D = (np.abs(Xd[lo][:, None, :] - Xd[hi][None, :, :]) / sc_[None, None, :]).sum(-1)
                r, c = linear_sum_assignment(D)
                cost_tot += float(D[r, c].sum())
                pairs_d.extend([t[a]] * len(r))
                pairs_lo.extend(list(idx[a + lo[r]]))
                pairs_hi.extend(list(idx[a + hi[c]]))
        pre_lo, pre_hi = Xd[cand & (gd == 0)], Xd[cand & (gd == 2)]
        bal_pre.append(np.abs(pre_lo.mean(0) - pre_hi.mean(0)) / np.where(np.isfinite(sc_), sc_, 1.0))
    pairs_d = np.asarray(pairs_d, np.int64)
    pl = np.asarray(pairs_lo, np.int64)
    ph = np.asarray(pairs_hi, np.int64)
    rows = []
    base = dict(member=mid, domain=dom_name, scope=scope, segment=seg, layer=layer)
    if len(pl):
        Xa = np.column_stack([U[c] for c in coords])
        post = np.abs(Xa[pl] - Xa[ph]).mean(0)
    for j, col in enumerate(sd.label_cols):
        lab, hh = col.rsplit('_h', 1)
        H = int(hh)
        if not len(pl):
            rows.append(dict(base, label=lab, H=H, stat='matched_low_minus_high_bp', value=np.nan, unit='bp', n_days=0, n_pairs=0, status='NOT_COMPUTABLE'))
            continue
        yv = sd.Y[pl, j] - sd.Y[ph, j]
        ok = np.isfinite(yv)
        T = int(pairs_d.max()) + 1
        s = np.bincount(pairs_d[ok], weights=yv[ok], minlength=T)
        c = np.bincount(pairs_d[ok], minlength=T)
        dm = s[c > 0] / c[c > 0]
        rows.append(dict(base, label=lab, H=H, stat='matched_low_minus_high_bp', value=float(dm.mean()) if len(dm) else np.nan, unit='bp',
                         n_days=int(len(dm)), n_pairs=int(ok.sum()), status='COMPUTED' if len(dm) else 'NOT_COMPUTABLE'))
    extra = dict(base, label='NOT_APPLICABLE', H=0, stat='match_cost_total', value=cost_tot, unit='decimal', n_days=int(len(np.unique(pairs_d))),
                 n_pairs=int(len(pl)), status='COMPUTED')
    rows.append(extra)
    rows.append(dict(base, label='NOT_APPLICABLE', H=0, stat='match_coverage_share', value=(2 * len(pl) / n_cand) if n_cand else np.nan, unit='decimal',
                     n_days=int(len(np.unique(pairs_d))), n_pairs=int(len(pl)), status='COMPUTED' if n_cand else 'NOT_COMPUTABLE'))
    if len(pl):
        for k, cn in enumerate(coords):
            rows.append(dict(base, label='NOT_APPLICABLE', H=0, stat='balance_abs_diff_post_%s' % cn, value=float(post[k]), unit='raw_unit',
                             n_days=int(len(np.unique(pairs_d))), n_pairs=int(len(pl)), status='COMPUTED'))
    if bal_pre:
        bp_ = np.nanmean(np.vstack(bal_pre), axis=0)
        for k, cn in enumerate(coords):
            rows.append(dict(base, label='NOT_APPLICABLE', H=0, stat='balance_std_diff_pre_%s' % cn, value=float(bp_[k]), unit='decimal',
                             n_days=len(bal_pre), n_pairs=0, status='COMPUTED'))
    return rows


SD = {}


def capital_weights(sd):
    """门内域 DEV 资本权重（源 DEV：e6k_acct.Acct.target）：单元 → 形成日目标权重。"""
    import e6l_env as V
    import e6k_acct as AC
    seg = V.SegL(sd.seg, state=False)
    if not (np.array_equal(seg.ci.t, sd.B.t) and np.array_equal(seg.ci.c, sd.B.c)):
        raise RuntimeError('段单元坐标不一致')
    acct = AC.Acct(seg, impact=False)
    out = {}
    for k, m in sd.dom.items():
        if not k.startswith('GATE_'):
            continue
        tg = acct.target(m)
        w = np.zeros(sd.n)
        w[tg['ids']] = tg['w']
        out[k] = w
    return out


def label_a2(P, M, BR):
    """probe_ledger（A2 真值表）：每成员主域标签。P = pairs，M = matched，BR = bridges 汇总。"""
    rows = []
    sel = lambda D, **kw: D[np.logical_and.reduce([D[k] == v for k, v in kw.items()])] if len(D) else D
    for mid, kind, grid, cell, dr, card in MEMBERS:
        r = dict(idea_id='G-%s' % card, member=mid, domain=MAIN_DOMAIN, table='results/b1_0/b1_0_pairs.csv',
                 cell='scope=QGOOD|label=FWD_SOURCE|H=5|stat=low_minus_high_bp')
        v = {}
        nn = {}
        for s in N.DERIV_SEGS:
            x = sel(P, member=mid, domain=MAIN_DOMAIN, scope='QGOOD', segment=s, label='FWD_SOURCE', H=5, stat='low_minus_high_bp')
            v[s] = float(x.value.iloc[0]) if len(x) and np.isfinite(float(x.value.iloc[0])) else np.nan
            nn[s] = int(x.n_days.iloc[0]) if len(x) else 0
        s1, s2 = N.DERIV_SEGS
        r.update(seg1_value=v[s1], seg2_value=v[s2], n_seg1=nn[s1], n_seg2=nn[s2], n=nn[s1] + nn[s2])
        fin = [s for s in N.DERIV_SEGS if np.isfinite(v[s]) and nn[s] > 0]
        if not fin:
            r.update(overall=np.nan, same_sign='NOT_COMPUTABLE', label='未检验（分钟未覆盖 / 不可算）', miss_root_hypotheses='NOT_APPLICABLE')
            rows.append(r)
            continue
        ov = sum(v[s] * nn[s] for s in fin) / sum(nn[s] for s in fin)
        same = (len(fin) == 2) and (np.sign(v[s1]) == np.sign(v[s2]))
        r.update(overall=ov, same_sign=bool(same) if len(fin) == 2 else 'ONE_SEGMENT_ONLY')
        if dr == 0:
            lab = '只报数（源桥无登记方向）'
        elif ov > 0 and same:
            lab = '支持'
        elif ov > 0:
            lab = 'mixed（跨时代不稳定）'
        else:
            lab = '不支持（方向 miss）'
        notes = []
        pv = []
        for s in fin:
            x = sel(P, member=mid, domain='POOL0', scope='QGOOD', segment=s, label='FWD_SOURCE', H=5, stat='low_minus_high_bp')
            if len(x):
                pv.append((float(x.value.iloc[0]), int(x.n_days.iloc[0])))
        if pv and dr != 0:
            pov = sum(a * b for a, b in pv) / max(1, sum(b for _, b in pv))
            if pov > 0 and ov <= 0:
                notes.append('池子层面读法（pool0∩QGOOD %+.2f bp 而主域 %+.2f bp）' % (pov, ov))
        if len(M) and dr != 0:
            for layer in ('L1', 'L2'):
                mv = []
                for s in fin:
                    x = sel(M, member=mid, domain=MAIN_DOMAIN, scope='QGOOD', segment=s, layer=layer, label='FWD_SOURCE', H=5, stat='matched_low_minus_high_bp')
                    if len(x) and np.isfinite(float(x.value.iloc[0])):
                        mv.append((float(x.value.iloc[0]), int(x.n_days.iloc[0])))
                if mv and ov > 0:
                    mo = sum(a * b for a, b in mv) / max(1, sum(b for _, b in mv))
                    if mo <= 0 or abs(mo) < VANISH * abs(ov):
                        notes.append('混杂候选（匹配 %s 后 %+.2f bp）' % (layer, mo))
        if mid in BRIDGE_OF and len(BR) and dr != 0:
            for bmid in BRIDGE_OF[mid]:
                bv = []
                for s in fin:
                    x = sel(P, member=bmid, domain=MAIN_DOMAIN, scope='QGOOD', segment=s, label='FWD_SOURCE', H=5, stat='low_minus_high_bp')
                    if len(x) and np.isfinite(float(x.value.iloc[0])):
                        bv.append((float(x.value.iloc[0]), int(x.n_days.iloc[0])))
                if bv:
                    bo = sum(a * b for a, b in bv) / max(1, sum(b for _, b in bv))
                    if np.sign(bo) == np.sign(ov) and abs(bo - ov) <= SAME_SIZE * abs(ov):
                        notes.append('分钟未多出信息（桥 %s %+.2f bp）' % (bmid, bo))
        r.update(label=lab + ('；' + '；'.join(notes) if notes else ''),
                 miss_root_hypotheses=('待区分：(a) 门内域已被 Q0 / K / T / CVR 吸收；(b) 日内路径信号在该制度期反向（承接 vs 争夺）；(c) 覆盖 / 剂量效应（2010-14 分钟仅 1/3 覆盖）'
                                       if lab.startswith('不支持') or lab.startswith('mixed') else 'NOT_APPLICABLE'))
        rows.append(r)
    return pd.DataFrame(rows)


def run(workers):
    import e6n_gate as GT
    t0 = time.time()
    fz = N.P('registration', GT.FREEZE)
    if not os.path.exists(fz):
        raise RuntimeError('B1-0 先于 Stage B 冻结：拒绝')
    if os.path.exists(N.P('registration', GT.SEAL_B10)):
        raise RuntimeError('seal_B1_0 已存在（只增不覆盖；复跑属复现，另写 results/b1_0_rerun）')
    acc = N.P('accounts')
    if os.path.isdir(acc) and any(os.scandir(acc)):
        raise RuntimeError('已有账户产物：B1-0 必须先于任何推导段账户')
    od = N.P('results', 'b1_0')
    os.makedirs(od, exist_ok=True)
    cells, pairs, mods, regs = [], [], [], []
    facts = {}
    for seg in N.DERIV_SEGS:
        sd = SegData(seg)
        sd.capw = capital_weights(sd)
        SD[seg] = sd
        facts[seg] = sd.label_cover
        for mid, kind, grid, cell, dr, card in MEMBERS:
            for dom, desc in domains():
                for scope in ('QGOOD', 'ALL'):
                    if dom == 'CLEAN' and scope == 'QGOOD':
                        continue
                    c, p = member_tables(sd, seg, mid, dr, dom, scope, 'CLEAN' if dom == 'CLEAN' else 'POOL0')
                    cells += c
                    pairs += p
            if mid in MOD_MEMBERS:
                for dom in ('POOL0', MAIN_DOMAIN, 'REJ_A4b_CVRv5_Q0HG10'):
                    m_, r_ = moderator_tables(sd, seg, mid, dom)
                    mods += m_
                    regs += r_
        N.log('B1-0 %s：表行 cells %d / pairs %d（%.0f s）' % (seg, len(cells), len(pairs), time.time() - t0))
    jobs = [(seg, mid, dom, scope, layer) for seg in N.DERIV_SEGS for mid in MATCH_MEMBERS
            for dom in ('POOL0', MAIN_DOMAIN, 'REJ_A4b_CVRv5_Q0HG10', 'GATE_A4b_CVRv5_NATIVE') for scope in ('QGOOD', 'ALL') for layer in ('L1', 'L2', 'GAP')]
    matched = []
    with mp.get_context('fork').Pool(workers) as pool:
        for r in pool.imap_unordered(match_task, jobs, chunksize=2):
            matched += r
    N.log('B1-0 匹配：%d 任务（%.0f s）' % (len(jobs), time.time() - t0))
    Cc, Pp, Mm, Md, Rg = (pd.DataFrame(x) for x in (cells, pairs, matched, mods, regs))
    # 桥并排：成员 vs 对应 OHLC / range 桥（同域同作用域同段，FWD_SOURCE 全 H）
    br = []
    for mid, bridges in BRIDGE_OF.items():
        for bmid in bridges:
            a = Pp[(Pp.member == mid) & (Pp.stat == 'low_minus_high_bp')]
            b = Pp[(Pp.member == bmid) & (Pp.stat == 'low_minus_high_bp')]
            m = a.merge(b, on=['domain', 'scope', 'segment', 'label', 'H'], suffixes=('', '_bridge'))
            for r in m.itertuples():
                br.append(dict(member=mid, bridge=bmid, domain=r.domain, scope=r.scope, segment=r.segment, label=r.label, H=r.H, stat='low_minus_high_bp',
                               value=r.value, value_bridge=r.value_bridge, same_sign=bool(np.sign(r.value) == np.sign(r.value_bridge)) if np.isfinite(r.value) and np.isfinite(r.value_bridge) else 'NOT_COMPUTABLE',
                               rel_gap=(abs(r.value_bridge - r.value) / abs(r.value)) if (np.isfinite(r.value) and r.value != 0 and np.isfinite(r.value_bridge)) else np.nan,
                               unit='bp', n_days=r.n_days, n_events=r.n_events, status='COMPUTED' if np.isfinite(r.value) and np.isfinite(r.value_bridge) else 'NOT_COMPUTABLE'))
    Br = pd.DataFrame(br)
    for D, q in ((Cc, 'E6N-B10-CELLS'), (Pp, 'E6N-B10-PAIRS'), (Mm, 'E6N-B10-MATCHED'), (Md, 'E6N-B10-MODERATORS'), (Rg, 'E6N-B10-REGIMES'), (Br, 'E6N-B10-BRIDGES')):
        D['query_id'] = q
    G = label_a2(Pp, Mm, Br)
    outs = []
    for nm, D in (('b1_0_cells', Cc), ('b1_0_pairs', Pp), ('b1_0_matched', Mm), ('b1_0_moderators', Md), ('b1_0_regimes', Rg), ('b1_0_bridges', Br)):
        p = os.path.join(od, nm + '.csv')
        N.atomic_write_csv(p, N.to_status(D))
        outs.append(p)
    pl = N.P('registration', 'probe_ledger.csv')
    N.atomic_write_csv(pl, N.to_status(G))
    outs.append(pl)
    fj = os.path.join(od, 'b1_0_facts.json')
    N.atomic_write_json(fj, dict(label_cover=facts, workers=workers, wall_s=round(time.time() - t0, 1)))
    outs.append(fj)
    seal = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=len(outs), queued_missing=0, n_receipts=1,
                sha256_manifest={N.rel(p): N.sha_file(p) for p in outs}, first_stage_status='SEALED_BEFORE_ANY_DERIV_ACCOUNT',
                segments=list(N.DERIV_SEGS), freeze_sha256=N.sha_file(fz), labels_a2=G.label.value_counts().to_dict(),
                note='B1-0 只打标签，不改任何对象 / 阈值 / 频率（plan §2.2）；后续复跑同格属复现')
    sp = N.P('registration', GT.SEAL_B10)
    N.atomic_write_json(sp, seal)
    N.write_receipt('E6n_b1_0', outs + [sp], code=[__file__], wall_s=round(time.time() - t0, 1), rows=dict(cells=len(Cc), pairs=len(Pp), matched=len(Mm),
                                                                                                        moderators=len(Md), regimes=len(Rg), bridges=len(Br)))
    print(json.dumps(dict(rows=dict(cells=len(Cc), pairs=len(Pp), matched=len(Mm), moderators=len(Md), regimes=len(Rg), bridges=len(Br)),
                          labels=seal['labels_a2'], wall_s=round(time.time() - t0, 1)), ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['manifest', 'run'])
    ap.add_argument('--workers', type=int, default=32)
    a = ap.parse_args()
    if a.step == 'manifest':
        M = manifest()
        p = N.P('registry', 'b1_0_manifest_E6n.csv')
        N.atomic_write_csv(p, M)
        N.write_receipt('E6n_b1_0_manifest', [p], code=[__file__], rows=len(M))
        print(len(M))
        return 0
    run(a.workers)
    return 0


if __name__ == '__main__':
    sys.exit(main())
