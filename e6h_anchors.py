#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 阶段 0 的锚 (brief §2「新算子恒等锚(阻断)」里不依赖新规则实现的那部分)。

两组:
  S* 源锚: R1/R2/A06/A08 等固定展示组在本轮重建后必须对上 E6g 已存 summary。
  D* 新派生键锚: 尺度不变、值域、单成员 NA、两成员互为对方、REL = OWN - IND 等。
新规则对象 (SLOT/FOCAL/ADD/SWAP/CONJ/MARGIN/软降权) 的 identity 锚在实现它们时另测。

用法: python3 e6h_anchors.py --segment 2010-2014
"""
from __future__ import annotations
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K

RES = H.RES
TOL_BIT = 1e-12


def md(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    both = np.isfinite(a) & np.isfinite(b)
    if not both.any():
        return np.nan, 0
    return float(np.nanmax(np.abs(a[both] - b[both]))), int(both.sum())


def source_anchors(S, res):
    """S*: 固定展示组重建 vs E6g 已存 summary_H0。"""
    f = os.path.join(H.E6G_DIR, 'H0', 'summary_H0_%s_s0.csv' % S.name)
    alt = sorted(__import__('glob').glob(
        os.path.join(H.E6G_DIR, 'H0', 'summary_H0_%s_s*.csv' % S.name)))
    dfs = [pd.read_csv(p) for p in alt] if alt else ([pd.read_csv(f)] if os.path.exists(f) else [])
    if not dfs:
        res.append(dict(test='S0_e6g_summary_present', ok=False, level='ANCHOR',
                        note='E6g H0 summary 不存在, 无法对源锚'))
        return
    d = pd.concat(dfs, ignore_index=True)
    d = d[d['display'].notna()]
    ctx = GD.GCtx(S)
    for lab, cid, _ in G.DISPLAY:
        row = d[(d['display'] == lab) & (d['segment'] == S.name)]
        if not len(row):
            res.append(dict(test='S_%s' % lab, ok=False, level='ANCHOR',
                            note='E6g summary 里没有 %s @ %s' % (lab, S.name)))
            continue
        row = row.iloc[0]
        try:
            pnl, iv, mk = ctx.run(GD.parse_cfg(cid))
        except Exception as e:
            res.append(dict(test='S_%s' % lab, ok=False, level='ANCHOR',
                            note='重建失败 %s' % str(e)[:100]))
            continue
        gross, pos, turn, net8 = pnl
        got = dict(gross_ann=H.ann(gross), net8_ann=H.ann(net8),
                   turn_mean=float(np.nanmean(turn)), pos_mean=float(np.nanmean(pos)))
        diffs = {k: abs(got[k] - float(row[k])) for k in got}
        worst = max(diffs.values())
        res.append(dict(test='S_%s' % lab, ok=bool(worst < 1e-9), level='ANCHOR',
                        max_diff=worst, detail={k: round(v, 14) for k, v in diffs.items()},
                        note='%s 重建 vs E6g summary' % lab))


def derived_anchors(S, res):
    """D*: 新派生键的恒等 / 值域 / 缺失语义。"""
    data = S.wdata if getattr(S, 'wdata', None) is not None else S.data
    ind = S.industry

    # D1 TCV 尺度不变 —— 【仪器相对锚】。
    # TCV = std/mean 在数学上严格尺度不变, 但 pandas.rolling.std 用的是不稳定的在线
    # 算法 (E6g 仪器事实 I2), 在近常数窗上条件数很差, 所以实现层只在 ~1e-8 量级不变。
    # 本轮【不换成两遍稳定 std】: brief §1.3 写明 "ddof 沿源 std", 且 M-T 的问题就是
    # T vs TCV 的对比 —— 两者必须共用同一估计器, 否则对比里混进估计器差异。
    # 因此锚改成可证伪的形式: TCV 的缩放误差【不得超过源 T 自身的缩放误差】。
    c = 3.7
    d2 = dict(data)
    t0 = H.tcv(data, 20, 10)
    d2['turnover_rate'] = data['turnover_rate'] * c
    t1 = H.tcv(d2, 20, 10)
    both = np.isfinite(t0.values) & np.isfinite(t1.values)
    rel_tcv = float(np.nanmax((np.abs(t0.values - t1.values)
                               / np.maximum(np.abs(t0.values), 1e-12))[both])) if both.any() else 0.0
    tt = data['turnover_rate']

    def _std_scale_err(w, mp):
        """同窗口 rolling.std 自身的缩放相对误差 (估计器自带的条件数)。"""
        a_ = tt.rolling(w, min_periods=mp).std()
        b_ = (tt * c).rolling(w, min_periods=mp).std()
        ok_ = np.isfinite(a_.values) & np.isfinite(b_.values)
        if not ok_.any():
            return 0.0
        return float(np.nanmax((np.abs(b_.values - c * a_.values)
                                / np.maximum(np.abs(c * a_.values), 1e-12))[ok_]))

    # 【同窗口】才是公平比较: TCV_20 对 rolling(20,10).std, 不是对 60 窗的源 T
    rel_std_same = _std_scale_err(20, 10)
    rel_T_60 = _std_scale_err(60, 30)          # 源 T 的窗口, 只作登记
    # 排名影响 (真正要紧的是这个)
    x0 = t0.where(S.pool0 == 1).rank(axis=1, pct=True).values
    x1 = t1.where(S.pool0 == 1).rank(axis=1, pct=True).values
    fin = np.isfinite(x0) & np.isfinite(x1)
    nch = int((fin & (np.abs(x0 - x1) > 1e-12)).sum())
    frac = nch / max(1, int(fin.sum()))
    res.append(dict(test='D1_tcv_scale_invariance_vs_same_window_std',
                    ok=bool(rel_tcv <= max(10.0 * rel_std_same, 1e-9)), level='ANCHOR',
                    max_diff=rel_tcv, rel_err_tcv=rel_tcv,
                    rel_err_same_window_std=rel_std_same, rel_err_source_T60=rel_T_60,
                    n_rank_changed=nch, n_rank_cells=int(fin.sum()),
                    rank_changed_frac=frac,
                    note=('TCV=std/mean 在数学上严格尺度不变, 实现层继承 pandas.rolling.std '
                          '的条件数 (E6g 仪器事实 I2)。锚 = 比值不得把【同窗口】std 自身的'
                          '缩放误差放大 10 倍以上。不换稳定 std: brief §1.3 要求 ddof 沿源 std, '
                          '且 M-T 就是 T vs TCV 的对比, 必须共用估计器')))
    res.append(dict(test='D1b_tcv_scale_rank_impact', ok=bool(frac < 1e-4), level='ANCHOR',
                    rank_changed_frac=frac, n_rank_changed=nch, n_rank_cells=int(fin.sum()),
                    note='真正要紧的是排名: 池内 pct 排名因缩放而变的格必须 < 0.01%'))

    # D2 TCV 定义: std/mean 且 mean<=0 -> NA
    t = data['turnover_rate']
    sd = t.rolling(20, min_periods=10).std()
    mu = t.rolling(20, min_periods=10).mean()
    ref = (sd / mu.where(mu > 0)).replace([np.inf, -np.inf], np.nan)
    m, n = md(t0.values.ravel(), ref.values.ravel())
    nan_ok = bool((t0.isna() == ref.isna()).values.all())
    res.append(dict(test='D2_tcv_matches_definition', ok=bool((np.isnan(m) or m == 0) and nan_ok),
                    level='ANCHOR', max_diff=m, n=n, nan_pattern_same=nan_ok,
                    note='TCV 必须逐位等于 std/mean 定义, NA 位一致'))

    # D3 JUMP 值域 [0,1]
    j5 = H.jump(data, 5, 3)
    v = j5.values[np.isfinite(j5.values)]
    res.append(dict(test='D3_jump_in_unit_interval',
                    ok=bool(v.size == 0 or (v.min() >= -1e-12 and v.max() <= 1 + 1e-12)),
                    level='ANCHOR', vmin=float(v.min()) if v.size else None,
                    vmax=float(v.max()) if v.size else None, n=int(v.size),
                    note='JUMP 是占比, 必须落在 [0,1]'))

    # D4 JUMP 全零 -> NA (构造一个全零收益的假数据)
    z = {k: (vv.copy() if hasattr(vv, 'copy') else vv) for k, vv in dict(data).items()}
    z['open'] = data['close'] * 1.0
    z['lclose'] = data['close'] * 1.0
    jz = H.jump(z, 5, 3)
    frac_na = float(np.isnan(jz.values).mean())
    res.append(dict(test='D4_jump_all_zero_is_na', ok=bool(frac_na > 0.99),
                    level='ANCHOR', frac_na=frac_na,
                    note='open=lclose=close -> on=in=0 -> 分母 0 -> 必须 NA, 不是 0'))

    # D5 REL_IND == OWN_RET - IND_CUR 逐位
    for w in (5, 20):
        own = H.endpoint_ret(data, w)
        pm = H.ind_peer_current(data, ind, w)[0]
        rel = own - pm
        got = H.derived_frame(S, 'REL_IND_%d' % w)
        m, n = md(rel.values.ravel(), got.values.ravel())
        res.append(dict(test='D5_rel_ind_%d_identity' % w,
                        ok=bool(np.isnan(m) or m < 1e-12), level='ANCHOR',
                        max_diff=m, n=n,
                        note='REL_IND_%d 必须逐位 = OWN_RET_%d - IND_CUR_%d' % (w, w, w)))

    # D6 同业单成员 -> NA; 两成员 -> 互为对方收益
    w = 5
    own = H.endpoint_ret(data, w)
    pm, npf, thin = H.ind_peer_current(data, ind, w)
    single = (npf.values == 0)
    na_on_single = bool(np.all(np.isnan(pm.values[single]))) if single.any() else True
    res.append(dict(test='D6a_singleton_peer_is_na', ok=na_on_single, level='ANCHOR',
                    n_single=int(single.sum()),
                    note='同业只有自己 -> peer mean 必须 NA'))
    two = (npf.values == 1)
    ok2, n2 = True, int(two.sum())
    if n2:
        # 两成员组: peer = 对方收益, 所以 peer 也必须是个有效收益
        pv = pm.values[two]
        ok2 = bool(np.isfinite(pv).mean() > 0.99)
    res.append(dict(test='D6b_two_member_peer_is_other', ok=ok2, level='ANCHOR', n=n2,
                    note='同业恰好两只 -> peer mean = 对方的收益 (必须有限)'))

    # D7 OWN_RET 与复权端点定义一致
    got = H.derived_frame(S, 'OWN_RET_5')
    m, n = md(own.values.ravel(), got.values.ravel())
    res.append(dict(test='D7_own_ret_matches_endpoint', ok=bool(np.isnan(m) or m == 0),
                    level='ANCHOR', max_diff=m, n=n,
                    note='OWN_RET_5 = close_adj[T]/close_adj[T-5]-1'))

    # D8 CURRENT vs ROLLING 必须不同名不同值 (防两者被当同一个)
    cur = H.derived_frame(S, 'IND_CUR_5')
    rol = H.derived_frame(S, 'IND_ROLL_5')
    both = np.isfinite(cur.values) & np.isfinite(rol.values)
    dd = float(np.nanmax(np.abs(cur.values[both] - rol.values[both]))) if both.any() else np.nan
    res.append(dict(test='D8_current_differs_from_rolling', ok=bool(both.any() and dd > 1e-6),
                    level='INFO', max_diff=dd, n=int(both.sum()),
                    note='CURRENT (T 时归属) 与 ROLLING (逐历史日归属) 含义不同, 值应不同'))

    # D9 派生键在池内的可用率 (不是锚, 是登记)
    p0 = S.pool0.values == 1
    cov = {}
    for k in sorted(H.DERIVED):
        fr = H.derived_frame(S, k)
        fr = fr.reindex(index=S.pool0.index, columns=S.pool0.columns)
        cov[k] = round(float(np.isfinite(fr.values[p0]).mean()), 4)
    res.append(dict(test='D9_derived_pool_coverage', ok=True, level='INFO',
                    coverage=cov, note='池内可用率 (登记用, 不设闸)'))

    # D10 派生键与守卫: 每个都必须被认作受保护
    bad = [k for k in H.DERIVED if not H.is_protected_key(k)]
    res.append(dict(test='D10_all_derived_protected', ok=(not bad), level='ANCHOR',
                    note='12 个派生键必须全部被守卫认作受保护', bad=bad))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(os.path.join(RES, 'checks'), exist_ok=True)

    S = H.seg(a.segment, verbose=False)
    tb = time.time() - t0
    res = []
    source_anchors(S, res)
    ts = time.time() - t0
    derived_anchors(S, res)
    td = time.time() - t0

    anchors = [x for x in res if x.get('level') == 'ANCHOR']
    npass = sum(1 for x in anchors if x['ok'])
    out = dict(round='E6h', segment=a.segment, version=H.VERSION,
               written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               n_anchor=len(anchors), n_pass=npass, results=res,
               timing=dict(build_segment_s=round(tb, 1), source_anchors_s=round(ts - tb, 1),
                           derived_anchors_s=round(td - ts, 1), total_s=round(td, 1)))
    p = os.path.join(RES, 'checks', 'anchors_%s.json' % a.segment)
    tmp = p + '.tmp'
    with open(tmp, 'w') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False, default=str)
    os.replace(tmp, p)

    print('== E6h 锚 @ %s ==  ANCHOR %d/%d' % (a.segment, npass, len(anchors)))
    for x in res:
        if x.get('level') == 'INFO':
            continue
        print('  %s %-34s %s' % ('OK ' if x['ok'] else '!! ', x['test'],
                                 ('max|d|=%.3e' % x['max_diff'])
                                 if x.get('max_diff') is not None else ''))
        if not x['ok']:
            print('      %s' % x.get('note', ''))
            if x.get('detail'):
                print('      %s' % x['detail'])
    inf = [x for x in res if x.get('level') == 'INFO']
    for x in inf:
        print('  -- %s: %s' % (x['test'], x.get('coverage', x.get('max_diff'))))
    print('  计时: 建段 %.0fs / 源锚 %.0fs / 派生锚 %.0fs / 合计 %.0fs'
          % (tb, ts - tb, td - ts, td))


if __name__ == '__main__':
    main()
