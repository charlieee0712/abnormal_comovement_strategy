# -*- coding: utf-8 -*-
"""E6m B6 触发面板（plan §8.4；附录 A1-5 G17 / A3-14）。只用行情特征与云机状态缓存，不读任何策略收益；全程网格（全部列）上算，
持有票离开 pool0 / clean 后照样有定义（plan §8.4"使用当时可见 clean 参考与既定秩延伸 / raw 定义"）。
B6 账户读法（vintage 早退反事实：停止该批未来 gross、释放资金记现金、受限库存延续、右删失）另在 e6m_b6_accounts.py（阶段 S4，post_gate 后）。
每格 int8：1 = 触发 / 0 = 未触发 / −1 = UNKNOWN（不借未来补齐）。
  PRICE_BREAK            |r_T| ≥ 2·σ20,T−1。r = log(C / lclose)（开盘且价格为正的有效日）；σ20,T−1 = T−20…T−1 有效 r 的样本标准差（ddof = 1，≥ 12 个）；
                         r 或 σ 缺、σ = 0 → UNKNOWN
  CVR_JUMP               cvr_1d = close / vwap − 1（E6e intraday_cvr_1d；roles：高 = 坏）。百分位 = 当日 clean 截面原值的经验分布函数
                         （#{clean 值 ≤ v} / n_clean；clean 与非 clean 同一把尺 = 既定秩延伸）；高尾 = 百分位 ≥ .90。
                         今日高尾且昨日已知且不在高尾 → 1；今昨都已知且非上式 → 0；今日可得、昨日不可得 → 0（另记下一列）；今日不可得 → UNKNOWN
  CVR_FIRST_VISIBLE_HIGH 昨日不可得、今日可得且在高尾 → 1（不捏造"跳升"，另报；plan §8.4）
  TREND_DOWN             个股 Trend3（云机状态缓存 trend：2 UP / 1 MIXED / 0 DOWN / −1 UNKNOWN；ANCHOR_PENDING 至 A4-3）今日 DOWN 且昨日已知非 DOWN → 1；
                         今昨都已知且非上式 → 0；任一未知 → UNKNOWN
  TREND_ANY_CHANGE       今昨都已知且不同 → 1；都已知且相同 → 0；否则 UNKNOWN（范围桥，不称市场级信息）
入口：load() = e6m_stage0_full.load_full（E7 截止守卫；A1-5 G17 攻击此入口）。输出 <out>/b6_triggers_full.npz + b6_trigger_facts.csv。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M

TREND = dict(UP=2, MIXED=1, DOWN=0, UNKNOWN=-1)
NAMES = ('PRICE_BREAK', 'CVR_JUMP', 'CVR_FIRST_VISIBLE_HIGH', 'TREND_DOWN', 'TREND_ANY_CHANGE')


def load():
    import e6m_stage0_full as SF
    return SF.load_full()


def price_break(r):
    sig = pd.DataFrame(r).shift(1).rolling(20, min_periods=12).std(ddof=1).to_numpy()
    out = np.full(r.shape, -1, np.int8)
    k = np.isfinite(r) & np.isfinite(sig) & (sig > 0)
    out[k] = (np.abs(r[k]) >= 2.0 * sig[k]).astype(np.int8)
    return out


def ecdf_pct(v, ref):
    """逐日：v 在当日参考值（ref 有限者）经验分布中的位置 #{ref ≤ v} / n_ref；参考为空或 v 缺 → NaN。"""
    out = np.full(v.shape, np.nan)
    for t in range(v.shape[0]):
        s = np.sort(ref[t][np.isfinite(ref[t])])
        if not len(s):
            continue
        x = v[t]
        f = np.isfinite(x)
        out[t, f] = np.searchsorted(s, x[f], side='right') / float(len(s))
    return out


def cvr_triggers(pct, tail=0.90):
    T, N = pct.shape
    jump = np.full((T, N), -1, np.int8)
    first = np.zeros((T, N), np.int8)
    kn = np.isfinite(pct)
    hi = kn & (pct >= tail)
    jump[0] = np.where(kn[0], 0, -1)
    first[0] = hi[0].astype(np.int8)
    both = kn[1:] & kn[:-1]
    j = both & hi[1:] & ~hi[:-1]
    jump[1:] = np.where(kn[1:], np.where(both, j.astype(np.int8), 0), -1)
    first[1:] = (kn[1:] & ~kn[:-1] & hi[1:]).astype(np.int8)
    return jump, first


def trend_triggers(tr):
    T, N = tr.shape
    down = np.full((T, N), -1, np.int8)
    chg = np.full((T, N), -1, np.int8)
    kn = tr >= 0
    both = kn[1:] & kn[:-1]
    down[1:] = np.where(both, ((tr[1:] == TREND['DOWN']) & (tr[:-1] != TREND['DOWN'])).astype(np.int8), -1)
    chg[1:] = np.where(both, (tr[1:] != tr[:-1]).astype(np.int8), -1)
    return down, chg


def build(data):
    import e6l_state as LS
    close = data['close'].astype(float)
    idx, cols = close.index, close.columns
    g = lambda k: data[k].reindex(index=idx, columns=cols).astype(float).to_numpy()
    is_open = (data['is_open'].reindex(index=idx, columns=cols) == 1).to_numpy()
    c, lc, vw = g('close'), g('lclose'), g('vwap')
    with np.errstate(all='ignore'):
        r = np.where(is_open & (c > 0) & (lc > 0), np.log(c / lc), np.nan)
        cvr = np.where(is_open & (vw > 0) & (c > 0), c / vw - 1.0, np.nan)
    clean = LS.clean_full(data).reindex_like(close).fillna(0.0).to_numpy() == 1
    pct = ecdf_pct(cvr, np.where(clean, cvr, np.nan))
    jump, first = cvr_triggers(pct)
    zs = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)
    sd = {str(d)[:10]: i for i, d in enumerate(zs['dates'])}
    sc = {str(x): j for j, x in enumerate(zs['columns'])}
    ri = np.array([sd.get(str(d)[:10], -1) for d in idx])
    cj = np.array([sc.get(str(x), -1) for x in cols])
    tr = np.full(close.shape, -1, np.int8)
    okr, okc = ri >= 0, cj >= 0
    tr[np.ix_(okr, okc)] = zs['trend'][np.ix_(ri[okr], cj[okc])]
    down, chg = trend_triggers(tr)
    P = dict(PRICE_BREAK=price_break(r), CVR_JUMP=jump, CVR_FIRST_VISIBLE_HIGH=first, TREND_DOWN=down, TREND_ANY_CHANGE=chg)
    return P, clean, idx, cols, dict(state_rows_unmatched=int((~okr).sum()), state_cols_unmatched=int((~okc).sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    od = a.out or M.P('stageS_dev', 'b6')
    os.makedirs(od, exist_ok=True)
    data, before, cd = load()
    M.assert_index_ok(data['close'].index, 'B6 triggers')
    P, clean, idx, cols, info = build(data)
    import e6m_stage0_full as SF
    p0 = SF.pool0_mask(data['close'])
    dates = pd.to_datetime(pd.Index(idx).astype(str))
    rows = []
    for s in SF.SEG:
        m = SF.seg_rows(dates, s)
        for nm in NAMES:
            for dom, D in (('pool0', p0), ('clean', clean)):
                x = P[nm][m][D[m]]
                n = max(len(x), 1)
                rows.append(dict(segment=s, trigger=nm, domain=dom, cells=int(len(x)), share_1=float((x == 1).sum() / n), share_0=float((x == 0).sum() / n),
                                 share_unknown=float((x == -1).sum() / n)))
    F = pd.DataFrame(rows)
    p1 = os.path.join(od, 'b6_triggers_full.npz')
    M.atomic_write_npz(p1, dates=np.array([str(d)[:10] for d in idx]), columns=np.array([str(x) for x in cols]), status=np.array(['ANCHOR_PENDING']),
                       **P)
    p2 = os.path.join(od, 'b6_trigger_facts.csv')
    M.atomic_write_csv(p2, F)
    T = dict(wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2),
             cache_dir_unchanged=sorted(os.listdir(cd)) == before, **info)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_b6_triggers'), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__],
                    note='B6 触发面板（行情特征，不读策略收益）', **T)
    print(json.dumps(T, ensure_ascii=False), flush=True)
    print(F[F.domain == 'pool0'].pivot_table(index='trigger', columns='segment', values='share_1').round(4).to_string(), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
