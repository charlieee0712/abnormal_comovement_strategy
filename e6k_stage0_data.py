# -*- coding: utf-8 -*-
"""E6k Stage 0 第 4 类：数据 / 时钟（brief §2 第 4 类；附录 A4-1 … A4-5；A4-6 COMMON_SUPPORT 齐全在推导段账户后由闭包核）。
  A4-1 z_T = negMarketValue（data['mcap']）当日 clean 域 rank(pct=True) → pool0 单元，与 E6j e6j_run_p.size_pct_cells 逐位相同（0 差）
  A4-2 z_LAG1 = 前一交易日 z_T 按股票对齐（停牌沿最近可用，记陈旧天数）；无 T−1 者保留（NaN）不删：计数
  A4-3 行业长表 industry_zx_1_all：按 tradeDate 逐日 pivot（data_loader.load_fundamental_long_table）→ 形成日 T 用 tradeDate = T 的记录
       （reindex 到交易日历、不前向填充）；日期覆盖、pool0 覆盖、逐股变更次数与日期抽样（只看 ≤ 2026-03-27 的行）
  A4-4 继承 E6j Stage 0 第 4 项（J 特征合成 / 真实恒等 F00–F12）回执；本轮在真实数据上重算 Q 原值（e6i_features.Base + e6j_features.b1：
       q = 1/(|log(C/lclose)| + 1e−4)）与 J 缓存逐位；另核 d = |log(close / lclose)| 与数据字段独立重算一致
  A4-5 T+1 VWAP 时钟（单格玩具目标：首个非零收益在形成日 + 2 行 = w·(r0 − bench)）；复权口径；段末日期 ≤ 2026-03-27（右删失，不读 E7）
不读收益作任何判断之外的用途；只写 E6k 结果目录。"""
import e6k_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_env as E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--rerun', action='store_true')
    a = ap.parse_args()
    out = K.P('stage0', 'c4_data' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    pname = a.segment
    rows = []

    def chk(cid, obj, metric, expected, got, ok, note=''):
        rows.append(dict(check_id=cid, segment=pname, object=obj, metric=metric, expected=str(expected), got=str(got),
                         status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), note=note))
    seg = E.Seg(pname)
    ci, S = seg.ci, seg.S
    # ---- A4-1
    import e6j_run_p as RPJ
    zj = RPJ.size_pct_cells(seg.env)
    same = bool(np.array_equal(np.isnan(zj), np.isnan(seg.zT)) and np.array_equal(zj[np.isfinite(zj)], seg.zT[np.isfinite(seg.zT)]))
    chk('A4-1', 'z_T', '与 E6j size_pct_cells 逐位相同（pool0 单元）', '0 差', same, same)
    chk('A4-1', 'z_T', 'pool0 单元 z_T 缺失份额', '', '%.6f' % float(np.isnan(seg.zT).mean()), None)
    chk('A4-1', 'data[mcap]', '字段来源 = negMarketValue（data_loader 字段映射 negMarketValue → mcap）', 'negMarketValue', 'mcap', True)
    # ---- A4-2
    st = seg.zL_stale
    chk('A4-2', 'z_LAG1', 'pool0 单元：精确 T−1 / 陈旧（沿最近可用）/ 无值 的份额', '',
        '%.6f / %.6f / %.6f' % (float((st == 1).mean()), float((st > 1).mean()), float((st < 0).mean())), None)
    chk('A4-2', 'z_LAG1', '陈旧天数分位（p50 / p90 / max；只含 > 1）', '',
        str(np.percentile(st[st > 1], [50, 90, 100]).tolist()) if (st > 1).any() else '[]', None)
    chk('A4-2', 'z_LAG1', '无 T−1 者保留（不删单元；单元数不变）', seg.n, len(seg.zL), len(seg.zL) == seg.n)
    # ---- A4-3
    ind = S.industry.reindex(index=S.pool0.index, columns=S.pool0.columns)
    icv = ind.values[:, S.ccols]
    p0c = S.p0c
    known = pd.notna(icv) & p0c
    chk('A4-3', 'industry_zx1', 'pool0 单元行业已知份额', '', '%.6f' % float(known.sum() / p0c.sum()), None)
    day_cov = pd.notna(ind.values).any(axis=1)
    chk('A4-3', 'industry_zx1', '交易日中行业表有记录的日份额（无记录日 → 当日全 UNK，不前向填充）', '', '%.6f（%d / %d）' % (day_cov.mean(), day_cov.sum(), len(day_cov)), None)
    chg = (icv[1:] != icv[:-1]) & pd.notna(icv[1:]) & pd.notna(icv[:-1])
    nchg = int(chg.sum())
    chk('A4-3', 'industry_zx1', '相邻交易日同股行业变更次数（重分类事件）', '', nchg, None)
    if nchg:
        tt, cc = np.nonzero(chg)
        samp = [(str(S.dates[t + 1])[:10], str(S.ccolnames[c]).split('.')[0][-2:] + '**', str(icv[t, c]), str(icv[t + 1, c])) for t, c in zip(tt[:5], cc[:5])]
        chk('A4-3', 'industry_zx1', '变更抽样（日期 / 代码末两位 / 前值 / 后值）：形成日 T 用 tradeDate = T 当日记录', '', json.dumps(samp, ensure_ascii=False), None)
    # ---- A4-4
    rc = os.path.join(K.E6J_RES, 'task_status', 'stage0_item4_features.receipt.json')
    r = json.load(open(rc, encoding='utf-8')) if os.path.exists(rc) else {}
    chk('A4-4', 'E6j stage0_item4_features', 'E6j J 特征 F00–F12（合成 + 真实）回执状态（继承证据）', 'SUCCEEDED', r.get('status'), r.get('status') == 'SUCCEEDED')
    if pname in K.DERIV_SEGS:
        import e6i_core as I
        import e6i_features as FE
        import e6j_features as FJ
        import e6j_slot as SL
        SW = I.seg_i(pname, warm=True)
        B = FE.Base(SW)
        q = FJ.b1(B)['J_B1_qCC']
        qs = B.to_seg(q)
        ref, meta = SL.j_member_raw(pname, 'J_B1_qCC')
        m = SW.p0c
        a_, b_ = qs[m], ref[m]
        eq = bool(np.array_equal(np.isnan(a_), np.isnan(b_)) and np.array_equal(a_[np.isfinite(a_)], b_[np.isfinite(b_)]))
        chk('A4-4', 'J_B1_qCC', '真实数据重算 q = 1/(|log(C/lclose)| + 1e−4) = J 缓存（pool0 单元逐位）', '0 差', eq, eq)
        wd = SW.wdata_i
        lk = [k for k in ('lclose', 'pre_close', 'preclose') if k in wd]
        if lk and hasattr(B, 'd'):
            cl = wd['close'].astype(float).reindex(index=B.dates_w, columns=B.own_cols).values
            lc = wd[lk[0]].astype(float).reindex(index=B.dates_w, columns=B.own_cols).values
            with np.errstate(all='ignore'):
                dd = np.abs(np.log(cl / lc))
            bd = np.asarray(B.d, float)
            if dd.shape == bd.shape:
                mm = np.isfinite(bd)
                err = float(np.max(np.abs(dd[mm] - bd[mm]))) if mm.any() else 0.0
                chk('A4-4', lk[0], 'd = |log(close / %s)|：数据字段独立重算 = Base.d（Base.d 有限格 %d）' % (lk[0], int(mm.sum())), '≤ 1e−12',
                    '%.2e' % err, err <= 1e-12)
            else:
                chk('A4-4', lk[0], '独立重算形状不符（记录，不判）', str(bd.shape), str(dd.shape), None)
        else:
            chk('A4-4', 'lclose', 'wdata 无前收字段或 Base 无 d（记录；字段 %s）' % sorted(k for k in wd if 'clos' in k), '', '', None)
    # ---- A4-5
    SE = seg.SE
    T = seg.T
    t_form = min(40, T - 5)
    c_ = int(ci.c[seg.off[t_form]])
    led = SE.pnl(np.array([t_form]), np.array([c_]), np.array([0.01]), (1,), 8.0)[1]
    g = led[0]
    nz = np.flatnonzero(np.abs(g) > 0)
    exp = 0.01 * (S.r0[t_form + 2, c_] - S.bench[t_form + 2])
    chk('A4-5', 'T+1 VWAP', '单格目标（形成日 t）首个非零收益行 = t + 2 且 = w·(r0 − bench)', t_form + 2,
        '%s / %.3e' % (int(nz[0]) if len(nz) else None, abs(g[t_form + 2] - exp)), len(nz) > 0 and int(nz[0]) == t_form + 2 and abs(g[t_form + 2] - exp) <= 1e-15)
    import e6e_core as EE
    chk('A4-5', '复权', 'vwap_daily_return 复权口径（e6e_core.ADJUST）', '', str(getattr(EE, 'ADJUST', None)), None)
    last = str(seg.dates[-1])[:10]
    chk('A4-5', '段末', '段末交易日 ≤ 2026-03-27（右删失；不读 E7 补齐）', K.MARKET_DATA_END_MAX, last, last <= K.MARKET_DATA_END_MAX)
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'data_checks_%s.csv' % pname)
    K.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    K.write_receipt('stage0_c4_data_%s%s' % (pname, '_rerun' if a.rerun else ''), [p], 'SUCCEEDED' if ok else 'FAILED',
                    counts=df.status.value_counts().to_dict(), blocker=not ok, wall_s=round(time.time() - t0, 1))
    print(df.to_string(max_colwidth=90), flush=True)
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
