# -*- coding: utf-8 -*-
"""E6o 证券级触发面板（plan §4.1–§4.4；brief §3.2 冻结定义）。不读策略收益。全程交易日 × 全部列，int8：1 = TRUE / 0 = FALSE / −1 = UNKNOWN。
  T1a        生产否决合同在当日的 CVR_20d 坏状态（e6o_source.t1a_panel；段内源池 + 同 (α, β, cut) 池外延伸）；持续状态
  T1b        SOURCE_B2_TRIGGER = E6n B2 / E6m B6 的 CVR_JUMP（源面板原样）
  T1b_LEVEL  当日日 CVR 在 clean 经验分布位置 ≥ .90（同源合同）；持续状态
  T1b_EDGE   显式跨界：今日 ≥ .90 且昨日已知 < .90；昨日未知 → UNKNOWN（前态未知不当非坏）
  T1b_OWNCHANGE  昨日参考合同固定：今日 / 昨日日 CVR 都在昨日 clean 参考里定位，昨日 < .90 → 今日 ≥ .90
  T3{a,b,c}{15,20}[_X|_XR]  量比 V_T / mean(V_{T−20…T−1})（≥ 10 有效、不含 T、停牌 = 未知、基线 0 = 未知）≥ 1.5 / 2.0；a：r < 0；b：r > 0；c：不限符号；
             _X：X1_RANK 豁免（行业 = T−1 冻结一级行业；行业收益 = clean 等权当日 r_day；行业名次 pct ≤ .2 豁免 a、≥ .8 豁免 b、任一尾端豁免 c）；
             _XR：XR 豁免（DOWN：名次 ≤ .2 ∧ 同行 < 0 ∧ 本股 < 同行 → 豁免 a；UP：名次 ≥ .8 ∧ 同行 > 0 ∧ 本股 ≥ 同行 → 豁免 b；c = 两者并集）；
             同行 = 同行业其余 clean 股等权（≥ 2）；行业状态未知 → 不额外豁免
  T4a        尾盘 CVR = C / VWAP_tail − 1（VWAP_tail = 14:30–15:00 额 / 量）在当日 pool0 经验分布位置 ≥ .90 的显式跨界（昨日已知 < .90）；分钟 2013-08-01 起
  T4b        log(C 官方 / 14:57 前最后连续成交价) > 0 且在当日同交易所 pool0 经验分布位置 ≥ .90；持续状态；沪市 2018-08-20 前无收盘竞价 → UNKNOWN
  T5         尾盘额份额 − 前 20 日同制度均值（≥ 10 个完整日）≥ .05
另出：pool0 全程掩码、T3 受公司行为影响标记计数、各触发 1 / 0 / −1 份额事实（按段 × 持仓无关的 clean 域）。用法：python3 e6o_triggers.py"""
import os
import sys
import json
import time
import resource

import numpy as np
import pandas as pd

import e6o_core as O

SH_REFORM = '2018-08-20'


def lag1(a, fill):
    out = np.full(a.shape, fill, a.dtype)
    out[1:] = a[:-1]
    return out


def ecdf_vs(v, ref_mask):
    """逐日：v 在当日参考（ref_mask ∧ v 有限）经验分布中的位置 #ref ≤ v / n；参考空或 v 缺 → NaN。"""
    out = np.full(v.shape, np.nan)
    for t in range(v.shape[0]):
        r = v[t][ref_mask[t] & np.isfinite(v[t])]
        if not len(r):
            continue
        s = np.sort(r)
        f = np.isfinite(v[t])
        out[t, f] = np.searchsorted(s, v[t][f], side='right') / float(len(s))
    return out


def ecdf_cross(v_now, v_ref, ref_mask_prev):
    """今日值 v_now[t] 在昨日参考 v_ref[t−1]（ref_mask_prev[t−1]）中的位置。"""
    out = np.full(v_now.shape, np.nan)
    for t in range(1, v_now.shape[0]):
        r = v_ref[t - 1][ref_mask_prev[t - 1] & np.isfinite(v_ref[t - 1])]
        if not len(r):
            continue
        s = np.sort(r)
        f = np.isfinite(v_now[t])
        out[t, f] = np.searchsorted(s, v_now[t][f], side='right') / float(len(s))
    return out


def tri(true, known):
    out = np.full(true.shape, -1, np.int8)
    out[known] = 0
    out[known & true] = 1
    return out


def edge(pct, tail=0.90):
    kn = np.isfinite(pct)
    hi = kn & (pct >= tail)
    kp = lag1(kn, False)
    hp = lag1(hi, False)
    out = np.full(pct.shape, -1, np.int8)
    both = kn & kp
    out[both] = 0
    out[both & hi & ~hp] = 1
    return out


def main():
    t0 = time.time()
    cd = O.cache_dir()
    pdir = os.path.join(cd, 'panels')
    L = lambda k: np.load(os.path.join(pdir, k + '.npy'))
    dates, codes = L('dates'), L('codes')
    T, N = len(dates), len(codes)
    di = {d: i for i, d in enumerate(dates)}
    cj = {c: j for j, c in enumerate(codes)}
    facts = dict(T=T, N=N)
    # ---------------- pool0 全程掩码 + T1a（源段）
    pool0 = np.zeros((T, N), bool)
    t1a = np.full((T, N), -1, np.int8)
    for s in O.SEGS:
        z = np.load(os.path.join(cd, 'source', '%s.npz' % s), allow_pickle=False)
        sd = [di[d] for d in z['dates']]
        sc = np.array([cj[c] for c in z['codes']])
        sd = np.array(sd)
        pool0[sd[z['cell_t']], sc[z['cell_c']]] = True
        tc = np.array([cj.get(str(c), -1) for c in z['t1a_cols']])
        ok = tc >= 0
        t1a[np.ix_(sd, tc[ok])] = z['t1a'][:, ok]
        facts['t1a_cols_unmapped_%s' % s] = int((~ok).sum())
    out = dict(T1a=t1a)
    # ---------------- 日 CVR 族
    clean = L('clean')
    cvr = L('cvr1d')
    pct = L('cvr_pct')
    out['T1b'] = L('cvr_jump_src').astype(np.int8)
    out['T1b_LEVEL'] = tri(pct >= 0.90, np.isfinite(pct))
    out['T1b_EDGE'] = edge(pct)
    pprev = ecdf_cross(cvr, cvr, clean)                      # 今日 CVR 在昨日 clean 参考中的位置
    kn_now, kn_prev = np.isfinite(pprev), lag1(np.isfinite(pct), False)
    bad_now = kn_now & (pprev >= 0.90)
    bad_prev = lag1(np.isfinite(pct) & (pct >= 0.90), False)
    own = np.full((T, N), -1, np.int8)
    both = kn_now & kn_prev
    own[both] = 0
    own[both & bad_now & ~bad_prev] = 1
    out['T1b_OWNCHANGE'] = own
    facts['edge_vs_source'] = dict(trig_cells_source=int((out['T1b'] == 1).sum()), trig_cells_edge=int((out['T1b_EDGE'] == 1).sum()),
                                   trig_diff_cells=int(((out['T1b'] == 1) != (out['T1b_EDGE'] == 1)).sum()))
    # ---------------- T3 族
    vol = L('vol')
    r = L('r_day')
    base = pd.DataFrame(vol).shift(1).rolling(20, min_periods=10).mean().to_numpy()
    with np.errstate(all='ignore'):
        vr = np.where(np.isfinite(vol) & (vol >= 0) & np.isfinite(base) & (base > 0), vol / base, np.nan)
    np.save(os.path.join(pdir, 'vr20.npy'), vr)
    indL = L('indL').astype(np.int64)
    G = int(indL.max()) + 1
    # 行业名次与同行收益（clean 域、T−1 冻结行业、当日 r_day）
    valid = clean & (indL >= 0) & np.isfinite(r)
    rank = np.full((T, N), np.nan)
    peer = np.full((T, N), np.nan)
    for t in range(T):
        m = valid[t]
        if not m.any():
            continue
        g = indL[t][m]
        sm = np.bincount(g, weights=r[t][m], minlength=G)
        ct = np.bincount(g, minlength=G).astype(float)
        has = ct > 0
        ir = np.full(G, np.nan)
        ir[has] = sm[has] / ct[has]
        gr = pd.Series(ir[has]).rank(pct=True).to_numpy()
        rk = np.full(G, np.nan)
        rk[np.flatnonzero(has)] = gr
        gi = indL[t]
        okg = gi >= 0
        rank[t, okg] = rk[gi[okg]]
        selfin = m.astype(float)
        cnt_o = np.where(okg, ct[np.maximum(gi, 0)] - selfin, 0.0)
        sum_o = np.where(okg, sm[np.maximum(gi, 0)] - np.where(m, r[t], 0.0), 0.0)
        with np.errstate(all='ignore'):
            peer[t] = np.where(okg & (cnt_o >= 2), sum_o / cnt_o, np.nan)
    np.save(os.path.join(pdir, 'ind_rank.npy'), rank)
    np.save(os.path.join(pdir, 'peer_ret.npy'), peer)
    rk_lo = np.isfinite(rank) & (rank <= 0.2)
    rk_hi = np.isfinite(rank) & (rank >= 0.8)
    xr_dn = rk_lo & np.isfinite(peer) & np.isfinite(r) & (peer < 0) & (r < peer)
    xr_up = rk_hi & np.isfinite(peer) & np.isfinite(r) & (peer > 0) & (r >= peer)
    kv = np.isfinite(vr)
    for th, tag in ((1.5, '15'), (2.0, '20')):
        hit = kv & (vr >= th)
        kr = np.isfinite(r)
        a_true, a_known = hit & kr & (r < 0), kv & (~hit | kr)
        b_true, b_known = hit & kr & (r > 0), kv & (~hit | kr)
        c_true, c_known = hit, kv
        out['T3a' + tag] = tri(a_true, a_known)
        out['T3b' + tag] = tri(b_true, b_known)
        out['T3c' + tag] = tri(c_true, c_known)
        out['T3a%s_X' % tag] = tri(a_true & ~rk_lo, a_known)
        out['T3b%s_X' % tag] = tri(b_true & ~rk_hi, b_known)
        out['T3c%s_X' % tag] = tri(c_true & ~(rk_lo | rk_hi), c_known)
        if tag == '15':
            out['T3a15_XR'] = tri(a_true & ~xr_dn, a_known)
            out['T3b15_XR'] = tri(b_true & ~xr_up, b_known)
            out['T3c15_XR'] = tri(c_true & ~(xr_dn | xr_up), c_known)
    jump = L('adjjump')
    aff = pd.DataFrame(jump.astype(float)).rolling(21, min_periods=1).max().to_numpy() > 0
    facts['t3_corp_action_affected_cells_hit15'] = int((aff & kv & (vr >= 1.5)).sum())
    # ---------------- 分钟族
    md = os.path.join(cd, 'minute')
    Mn = lambda k: np.load(os.path.join(md, k + '.npy'))
    cl_raw_ok = L('is_open')
    tail_amt, tail_vol, all_amt = Mn('tail_amt'), Mn('tail_vol'), Mn('all_amt')
    p1457 = Mn('p1457')
    close_raw = L('close_raw')
    mstart = di[min(d for d in dates if d >= O.MINUTE_START)]
    with np.errstate(all='ignore'):
        vwt = np.where(tail_vol > 0, tail_amt / tail_vol, np.nan)
        tcvr = np.where(cl_raw_ok & (close_raw > 0) & (vwt > 0), close_raw / vwt - 1.0, np.nan)
        jmp = np.where(cl_raw_ok & (close_raw > 0) & (p1457 > 0), np.log(close_raw / p1457), np.nan)
        share = np.where(all_amt > 0, tail_amt / all_amt, np.nan)
    tcvr[:mstart] = np.nan
    jmp[:mstart] = np.nan
    share[:mstart] = np.nan
    sh = np.array([c[:1] == '6' for c in codes])
    reform = di[min(d for d in dates if d >= SH_REFORM)]
    jmp[:reform, sh] = np.nan                                  # 沪市改革前无收盘集合竞价：对象不存在，不当 0
    tpct = ecdf_vs(tcvr, pool0)
    out['T4a'] = edge(tpct)
    # T4b：同交易所 pool0 参考
    exch = np.where(sh, 1, 0)
    jpct = np.full((T, N), np.nan)
    for e in (0, 1):
        cols = exch == e
        jpct[:, cols] = ecdf_vs(jmp[:, cols], pool0[:, cols])
    out['T4b'] = tri((jmp > 0) & (jpct >= 0.90), np.isfinite(jmp) & np.isfinite(jpct))
    # T5：前 20 日同制度均值（沪市改革日前后不跨窗）
    shp = share.copy()
    base5 = np.full((T, N), np.nan)
    for e, cols in ((0, ~sh), (1, sh)):
        x = shp[:, cols].copy()
        if e == 1:
            pre = pd.DataFrame(x[:reform]).shift(1).rolling(20, min_periods=10).mean().to_numpy()
            post = pd.DataFrame(x[reform:]).shift(1).rolling(20, min_periods=10).mean().to_numpy()
            b = np.vstack([pre, post])
        else:
            b = pd.DataFrame(x).shift(1).rolling(20, min_periods=10).mean().to_numpy()
        base5[:, cols] = b
    d5 = shp - base5
    out['T5'] = tri(d5 >= 0.05, np.isfinite(d5))
    np.save(os.path.join(pdir, 'tail_cvr.npy'), tcvr)
    np.save(os.path.join(pdir, 'tail_cvr_pct.npy'), tpct)
    np.save(os.path.join(pdir, 'auction_jump.npy'), jmp)
    np.save(os.path.join(pdir, 'tail_share.npy'), share)
    # ---------------- 写出
    od = os.path.join(cd, 'triggers')
    os.makedirs(od, exist_ok=True)
    np.save(os.path.join(od, 'pool0.npy'), pool0)
    rows = []
    segi = np.array([O.seg_of_date(d) for d in dates])
    for k, v in out.items():
        np.save(os.path.join(od, k + '.npy'), v)
        for s in O.SEGS:
            m = (segi == s)[:, None] & pool0
            x = v[m]
            n = max(len(x), 1)
            rows.append(dict(trigger=k, segment=s, domain='pool0', cells=int(len(x)), share_true=float((x == 1).sum() / n),
                             share_false=float((x == 0).sum() / n), share_unknown=float((x == -1).sum() / n)))
    O.atomic_write_csv(os.path.join(od, 'trigger_shares.csv'), pd.DataFrame(rows))
    facts.update(triggers=sorted(out), minute_start=O.MINUTE_START, sh_reform=SH_REFORM, wall_s=round(time.time() - t0, 1),
                 rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(os.path.join(od, 'trigger_facts.json'), facts)
    O.write_receipt('E6o_triggers', [os.path.join(od, 'trigger_facts.json'), os.path.join(od, 'trigger_shares.csv')], code=[__file__, O.__file__],
                    wall_s=facts['wall_s'])
    print(json.dumps(facts, ensure_ascii=False, default=str), flush=True)


if __name__ == '__main__':
    main()
