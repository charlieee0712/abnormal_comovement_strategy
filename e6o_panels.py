# -*- coding: utf-8 -*-
"""E6o 全程日频面板（plan §4.3、§5.3–§5.5、§7.1；brief §1.2）。只读行情特征（不读任何策略收益）；读取接口 = e6m_stage0_full.load_full（E7 截止守卫）。
输出 <cache>/panels/*.npy（全程交易日 × 全部列，可 mmap）：
  dates / codes；pv（后复权 VWAP，缺 = NaN）/ pv_ff（前向填充，估值用）/ pv_age（距最近有效 VWAP 的天数）；pc / pc_ff（后复权收盘）；
  r_vwap（源 C.vwap_daily_return 同式）/ clean（e6l_state.clean_full：源 clean 同式、全程不按段清零）/ bench（clean 等权 r_vwap）；
  is_open / sellable / buyable（E6n B2 / E6m B6 同式：可卖 = 开盘 ∧ 非全天一字跌停（high ≤ 跌停价）；可买 = 开盘 ∧ 非全天一字涨停（low ≥ 涨停价））；
  cvr1d = close / vwap − 1（开盘、价格为正）；cvr_pct = 当日 clean 截面经验分布位置（#ref ≤ v / n，B2 源同式）；
  r_day = close / lclose − 1（前收盘已按除权除息调整的日简单收益）；sig20（T−20…T−1 r_day 标准差，≥ 10 有效，不含 T）；
  vol / amt（原始量 / 额，停牌 = NaN；已开盘量 0 保留）；adv20（T−20…T−1 成交额均值，≥ 10）；
  ind（一级行业 industry_zx1 的整数码，−1 = 未知）/ indL（T−1 冻结）；zsize（形成日 T 收盘市值在当日 clean 的 rank pct）；
  adjjump（复权因子单日跳升 ≥ 1.15 的股票日 = 疑似送转，T3 受影响标记，不据以改量）。
另：与 E6n b2/triggers_full.npz 的 sell / buy / cvr_pct 逐格对照（事实写 panel_facts.json）。用法：python3 e6o_panels.py"""
import os
import sys
import json
import time
import resource

import numpy as np
import pandas as pd

import e6o_core as O


def rolling_prev(x, k, minp, how):
    """逐列 T−k…T−1（不含 T）的有效值统计；有效数 < minp → NaN。"""
    df = pd.DataFrame(x)
    sh = df.shift(1)
    if how == 'std':
        r = sh.rolling(k, min_periods=minp).std(ddof=1)
    else:
        r = sh.rolling(k, min_periods=minp).mean()
    return r.to_numpy()


def main():
    import e6m_stage0_full as SF
    import comprehensive_factor_diagnosis as C
    import e6l_state as LS
    import e6m_b6_triggers as BT
    t0 = time.time()
    data, before, cd = SF.load_full()
    close = data['close'].astype(float)
    idx, cols = close.index, close.columns
    O.assert_index_ok(idx, 'panels close')
    dates = np.array([str(d)[:10] for d in idx])
    codes = np.array([str(c) for c in cols])
    O.assert_end_ok(dates[-1], 'panels dates')
    g = lambda k: data[k].reindex(index=idx, columns=cols).astype(float).to_numpy()
    facts = dict(keys=sorted(str(k) for k in data.keys()), T=int(len(idx)), N=int(len(cols)), first=dates[0], last=dates[-1])
    od = os.path.join(O.cache_dir(), 'panels')
    os.makedirs(od, exist_ok=True)

    def save(name, a):
        p = os.path.join(od, name + '.npy')
        tmp = p + '.tmp%d.npy' % os.getpid()
        np.save(tmp, np.ascontiguousarray(a))
        os.replace(tmp, p)

    save('dates', dates)
    save('codes', codes)
    is_open = (data['is_open'].reindex(index=idx, columns=cols) == 1).to_numpy()
    save('is_open', is_open)
    adj = C.adjust_factor(data).reindex(index=idx, columns=cols).astype(float)
    A = adj.to_numpy()
    vw_raw, cl_raw = g('vwap'), g('close')
    pv = np.where(is_open & (vw_raw > 0), vw_raw * A, np.nan)
    pc = np.where(is_open & (cl_raw > 0), cl_raw * A, np.nan)
    import e6k_env as E
    pv_ff, pv_age = E.ffill_age(pv)
    pc_ff, _ = E.ffill_age(pc)
    save('pv', pv)
    save('pc', pc)
    save('close_raw', np.where(is_open & (cl_raw > 0), cl_raw, np.nan))
    save('vwap_raw', np.where(is_open & (vw_raw > 0), vw_raw, np.nan))
    save('pv_ff', pv_ff)
    save('pv_age', pv_age.astype(np.int32))
    save('pc_ff', pc_ff)
    rv = C.vwap_daily_return(data, True).reindex(index=idx, columns=cols).to_numpy(float)
    save('r_vwap', rv)
    clean = (LS.clean_full(data).reindex(index=idx, columns=cols).fillna(0.0).to_numpy() == 1)
    save('clean', clean)
    with np.errstate(all='ignore'):
        bench = np.nanmean(np.where(clean, rv, np.nan), axis=1)
    save('bench', bench)
    hi, ld, lo, lu = g('high'), g('limit_down'), g('low'), g('limit_up')
    with np.errstate(invalid='ignore'):
        sellable = is_open & ~(np.isfinite(ld) & (hi <= ld + 1e-6))
        buyable = is_open & ~(np.isfinite(lu) & (lo >= lu - 1e-6))
        cvr = np.where(is_open & (vw_raw > 0) & (cl_raw > 0), cl_raw / vw_raw - 1.0, np.nan)
    save('sellable', sellable)
    save('buyable', buyable)
    save('limit_known', np.isfinite(ld) & np.isfinite(lu))
    save('adj_known', np.isfinite(A) & (A > 0))
    save('cvr1d', cvr.astype(np.float64))
    cvr_pct = BT.ecdf_pct(cvr, np.where(clean, cvr, np.nan))
    save('cvr_pct', cvr_pct.astype(np.float64))
    lc = g('lclose')
    with np.errstate(all='ignore'):
        r_day = np.where(is_open & (cl_raw > 0) & (lc > 0), cl_raw / lc - 1.0, np.nan)
    save('r_day', r_day)
    save('sig20', rolling_prev(r_day, 20, 10, 'std'))
    vol = np.where(is_open, g('volume'), np.nan)
    amt = np.where(is_open, g('amount'), np.nan)
    save('vol', vol)
    save('amt', amt)
    save('adv20', rolling_prev(amt, 20, 10, 'mean'))
    ind_df = data.get('industry_zx1', data.get('industry')).reindex(index=idx, columns=cols)
    codes_i, uniq = pd.factorize(pd.Series(ind_df.to_numpy().ravel()))
    ind = codes_i.reshape(len(idx), len(cols)).astype(np.int16)
    save('ind', ind)
    indL = np.full(ind.shape, -1, np.int16)
    indL[1:] = ind[:-1]
    save('indL', indL)
    save('ind_names', np.array([str(u) for u in uniq]))
    mc = data['mcap'].reindex(index=idx, columns=cols).astype(float)
    z = mc.where(pd.DataFrame(clean, index=idx, columns=cols)).rank(axis=1, pct=True).to_numpy()
    save('zsize', z)
    save('mcap', mc.to_numpy())
    with np.errstate(all='ignore'):
        jump = np.zeros(A.shape, bool)
        jump[1:] = (A[1:] / A[:-1]) >= 1.15
    save('adjjump', jump)
    # 行业份额（clean 等权个数份额，源 bench_industry_shares 同式）→ 行业上限 = 份额 + 3pp
    G = int(ind.max()) + 1
    share = np.zeros((len(idx), G))
    for t in range(len(idx)):
        m = clean[t] & (ind[t] >= 0)
        tot = int(clean[t].sum())
        if tot:
            share[t] = np.bincount(ind[t][m], minlength=G) / tot
    save('ind_share', share)
    # 与 E6n B2 面板逐格对照
    zb = np.load(O.E6N('b2', 'triggers_full.npz'), allow_pickle=False)
    same_axes = (list(zb['dates']) == list(dates)) and (list(zb['columns']) == list(codes))
    facts['vs_e6n_b2'] = dict(axes_equal=bool(same_axes))
    if same_axes:
        facts['vs_e6n_b2'].update(sell_diff=int((zb['sell'] != sellable).sum()), buy_diff=int((zb['buy'] != buyable).sum()),
                                  cvr_pct_maxabs=float(np.nanmax(np.abs(zb['cvr_pct'].astype(float) - cvr_pct))),
                                  cvr_pct_nan_same=bool(np.array_equal(np.isfinite(zb['cvr_pct']), np.isfinite(cvr_pct))))
        save('cvr_jump_src', zb['CVR_JUMP'].astype(np.int8))
        save('cvr_first_visible_src', zb['CVR_FIRST_VISIBLE_HIGH'].astype(np.int8))
    facts.update(n_industries=G, bench_nan_days=int(np.isnan(bench).sum()), first_bench_day=str(dates[np.flatnonzero(np.isfinite(bench))[0]]),
                 cache_dir_unchanged=sorted(os.listdir(cd)) == before, wall_s=round(time.time() - t0, 1),
                 rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(os.path.join(od, 'panel_facts.json'), facts)
    O.write_receipt('E6o_panels', [os.path.join(od, 'panel_facts.json')], code=[__file__, O.__file__], **{k: v for k, v in facts.items() if not isinstance(v, (dict, list))})
    print(json.dumps({k: v for k, v in facts.items() if k != 'keys'}, ensure_ascii=False, default=str), flush=True)
    print('keys:', facts['keys'], flush=True)


if __name__ == '__main__':
    main()
