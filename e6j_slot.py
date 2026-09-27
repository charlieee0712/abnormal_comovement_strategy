# -*- coding: utf-8 -*-
"""E6j P 块 SLOT 算子（生产坐标；brief W05、plan §4.1 / §4.1a / §4.2）。
坐标（SRC = 生产约定，与 E6i NS pct 同式）：成员原值在 pool0 内当日 log 市值 OLS（`C.precompute_neutralized_factor`）→
方向（'hi' 高 = 坏：s.rank(pct=True)；'lo' 低 = 坏：(−s).rank(pct=True)，真实反序，不用 1 − pct）→ 混合 → 源分箱。
FALLBACK（plan §4.1）：
  单臂  q = (1−a)·q0 + a·q_new（q_new 缺失处 = q0，逐位取 q0，与 e6i_ops._blend 同式）
  SM    q = (1−a)·q0 + (a/2)·c_S + (a/2)·c_M，c_X = q_X 或（缺失时）q0；两者都缺 = q0；不放大另一分量
不对 q 再做市值 OLS 或再 rank。α = 0 在读取任何新成员之前短路回母体（e6j_prod.form_masks(ctx)）。
新成员原值复用 E6i 成员缓存（`<E6I_RES>/cache/<seg>/<mid>__OBS.npy`，sidecar sha 校验；E6i 按预热数据算、取 pool0 网格）。"""
import os
import json

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import comprehensive_factor_diagnosis as C

E6I_CACHE = os.path.join(J.E6I_RES, 'cache')


def ccols_of(ctx):
    return np.where(ctx['p0'].any(axis=0))[0]


def e6i_member_raw(pname, mid, policy='OBS'):
    """E6i 成员原值 (T, Nc) float64 + sidecar；sha 不符 / 形状不符 / 特征日越界即抛错。"""
    base = os.path.join(E6I_CACHE, pname, '%s__%s' % (mid, policy))
    meta = json.load(open(base + '.json', encoding='utf-8'))
    got = J.sha_file(base + '.npy')
    if meta.get('sha256') != got:
        raise RuntimeError('E6i 成员缓存 sha 不符: %s/%s' % (pname, mid))
    arr = np.load(base + '.npy', allow_pickle=False)
    if list(arr.shape) != list(meta['shape']) or arr.dtype != np.float64:
        raise RuntimeError('E6i 成员缓存形状 / 类型不符: %s/%s' % (pname, mid))
    J.assert_end_ok(str(meta['max_feature_date']).replace('-', ''), 'member %s/%s max_feature_date' % (pname, mid))
    return arr, meta


J_CACHE = os.path.join(J.RES, 'cache')


def j_member_raw(pname, mid):
    """E6j J 成员原值 (T, Nc) + sidecar（Stage 0 第 4 项写入）；sha / 形状 / 特征截止日校验，越界抛错。"""
    base = os.path.join(J_CACHE, pname, mid)
    meta = json.load(open(base + '.json', encoding='utf-8'))
    if meta.get('sha256') != J.sha_file(base + '.npy'):
        raise RuntimeError('J 成员缓存 sha 不符: %s/%s' % (pname, mid))
    J.assert_end_ok(str(meta['max_feature_date']).replace('-', ''), 'J member %s/%s max_feature_date' % (pname, mid))
    arr = np.load(base + '.npy', allow_pickle=False)
    if list(arr.shape) != list(meta['shape']) or arr.dtype != np.float64:
        raise RuntimeError('J 成员缓存形状 / 类型不符: %s/%s' % (pname, mid))
    return arr, meta


def e6i_member_pct_table(pname, mid, direction, policy='OBS'):
    """E6i 已存 NS pct 表 (T, Nc)（只作特征合同比对）。"""
    return np.load(os.path.join(E6I_CACHE, pname, '%s__%s__NS%s.npy' % (mid, policy, direction)), allow_pickle=False)


def full_frame(ctx, arr_c):
    """(T, Nc) → 全市场宽 DataFrame（ccols 之外 NaN），按位置对回 pool0 网格。"""
    pool0 = ctx['pool0']; cc = ccols_of(ctx)
    if arr_c.shape != (pool0.shape[0], len(cc)):
        raise RuntimeError('成员网格与 pool0 不符: %s vs %s' % (arr_c.shape, (pool0.shape[0], len(cc))))
    out = np.full(pool0.shape, np.nan)
    out[:, cc] = arr_c
    return pd.DataFrame(out, index=pool0.index, columns=pool0.columns)


def neu_of(ctx, raw_df):
    return C.precompute_neutralized_factor(raw_df, ctx['pool0'], ctx['log_mcap'])


def pct_dir(cache, direction):
    if direction == 'hi':
        return {d: s.rank(pct=True) for d, s in cache.items()}
    if direction == 'lo':
        return {d: (-s).rank(pct=True) for d, s in cache.items()}
    raise ValueError(direction)


def member_pct(ctx, mid, direction, pname=None):
    """E6i 成员 → 生产坐标 pct 缓存（dict 日期 → Series）与中性化残差缓存。"""
    arr, meta = e6i_member_raw(pname or ctx['pname'], mid)
    neu = neu_of(ctx, full_frame(ctx, arr))
    return pct_dir(neu, direction), neu, meta


def dense(ctx, cache):
    """dict 日期 → Series  →  (T, Nc)（ccols 空间，缺 = NaN），用于与 E6i 稠密表比对。"""
    pool0 = ctx['pool0']; cc = ccols_of(ctx)
    colpos = {c: i for i, c in enumerate(pool0.columns[cc])}
    didx = {d: i for i, d in enumerate(pool0.index)}
    out = np.full((pool0.shape[0], len(cc)), np.nan)
    for d, s in cache.items():
        pos = np.fromiter((colpos.get(x, -1) for x in s.index), int, len(s))
        v = pos >= 0
        out[didx[d], pos[v]] = s.to_numpy()[v]
    return out


def blend_q(q0, parts, a):
    """FALLBACK 混合。q0: dict 日期 → Series（K 槽位坏度，定义域 = 母体 K 有效域）；
       parts: [(share, pct_cache)]，share 之和 = 1（单臂 [(1, qS)]；SM [(.5, qS), (.5, qM)]）。"""
    a = float(a)
    out = {}
    for d, s0 in q0.items():
        if len(parts) == 1:
            sn = parts[0][1].get(d)
            sn = pd.Series(np.nan, index=s0.index) if sn is None else sn.reindex(s0.index)
            out[d] = s0.where(sn.isna(), (1 - a) * s0 + a * sn)
            continue
        comps, miss_all = [], np.ones(len(s0), bool)
        for share, pc in parts:
            sn = pc.get(d)
            sn = pd.Series(np.nan, index=s0.index) if sn is None else sn.reindex(s0.index)
            miss_all &= sn.isna().to_numpy()
            comps.append((share, s0.where(sn.isna(), sn)))
        q = (1 - a) * s0
        for share, c in comps:
            q = q + (a * share) * c
        out[d] = s0.where(pd.Series(miss_all, index=s0.index), q)
    return out


def replace_q(qnew, q0):
    """REPLACE α = 1（只作 FALLBACK ≠ REPLACE 恒等锚）：只用新测量，定义域 = 新有效 ∩ pool0（不回退旧腿）。"""
    return {d: s for d, s in qnew.items() if len(s)}


def transport(q0, neu_new, direction):
    """TRANSPORT 诊断（plan §4.1a）：J = 新残差有效 ∩ q0 定义域；在 J 内按新坏度排序，把 J 内 q0 的有序值逐一分给同序位；
       新值平局块取对应 q0 值的均值；J 外保留 q0。同残差、同平局、同支持的复制输入逐值回到 q0。"""
    out = {}
    for d, s0 in q0.items():
        sn = neu_new.get(d)
        if sn is None:
            out[d] = s0.copy(); continue
        sn = sn.reindex(s0.index)
        jm = sn.notna().to_numpy()
        if not jm.any():
            out[d] = s0.copy(); continue
        bad = sn[jm] if direction == 'hi' else -sn[jm]
        old_sorted = np.sort(s0[jm].to_numpy(), kind='mergesort')
        order = np.argsort(bad.to_numpy(), kind='mergesort')
        vals = np.empty(len(order)); vals[order] = old_sorted
        # 新值平局块取对应 q0 有序值的均值
        bv = bad.to_numpy()
        tmp = pd.Series(vals).groupby(bv).transform('mean').to_numpy()
        arr = s0.to_numpy(copy=True)
        arr[jm] = tmp
        out[d] = pd.Series(arr, index=s0.index)
    return out


def arm_masks(ctx, arm, a, members=None):
    """P 块五臂 → 六形态掩码。arm ∈ {'C0','S','M','SM','C1'}；members = {'S': pct, 'M': pct, 'C1': pct}。
       α = 0 或 C0：显式短路（不读新输入）。"""
    if arm == 'C0' or float(a) == 0.0:
        return P.form_masks(ctx)
    q0 = ctx['pcond']
    parts = {'S': [(1.0, members['S'])], 'M': [(1.0, members['M'])], 'C1': [(1.0, members['C1'])],
             'SM': [(0.5, members['S']), (0.5, members['M'])]}[arm]
    return P.form_masks(ctx, kq=blend_q(q0, parts, a))
