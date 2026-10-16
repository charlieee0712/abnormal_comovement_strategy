# -*- coding: utf-8 -*-
"""E6m N8 · B3 先行 · 事件表构建（合同 stageN/B3_prelim/B3_run_contract.md §1–§3 + 附录 1 B3_run_contract_addendum.md）。
任务：
  masks --seg <段>：源上下文（tmp/ctx_<段>.pkl）→ pool0 / clean / A4b_CVRv5 门内（e6j_prod.form_masks）/ 拒绝集、CVR k5 坏尾、pcond、kQ、log_mcap，
        写 stageN/B3_prelim/work/masks_<段>.npz（段坐标 + col_ids / date_ids）；门内名单对 N5 pool2 部件逐格核成员。
  events：全程数据（2010-01-04 → 2026-03-27）算特征与标签（FWD_SOURCE 逐字调用 comprehensive_factor_diagnosis.compute_forward_5d_excess），
        分类在参考域（POOL0 / 门内 / 拒绝 → 当日 pool0；CLEAN → 当日 clean）上算，按段 × 域写事件表 stageN/B3_prelim/work/events_<段>__<域>.npz。
执行端不读数值：日志与回执只有行数、计数、耗时。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import pickle
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M

SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
DOMAINS = ('POOL0', 'CLEAN', 'A4B_CVRV5_GATE_IN', 'A4B_CVRV5_REJECTED')
LABELS = ('FWD_SOURCE', 'FWD_ENDPOINT', 'FWD_LINEAR')
HS = (1, 3, 5, 10, 20)
YCOLS = ['%s_h%d' % (lb, h) for lb in LABELS for h in HS]          # 15 列：标签 × h（bp / h 日）
# 码表（事件表 int8）
ACT = {'LOW': 0, 'MID': 1, 'HIGH': 2}
PR_ = {'QUIET': 0, 'UP': 1, 'DOWN': 2}
POS = {'LOW': 0, 'MID': 1, 'HIGH': 2}
VOL = {'LOW': 0, 'MID': 1, 'HIGH': 2}                                # e6l_state.tercile
TREND = {'UP': 2, 'DOWN': 0, 'MIXED': 1}                             # e6l_state.compute trend 码
PEERQ = {'STOCK_WEAK_PEER_STRONG': 0, 'STOCK_WEAK_PEER_WEAK': 1, 'STOCK_STRONG_PEER_STRONG': 2, 'STOCK_STRONG_PEER_WEAK': 3}
GAP = {'GAP_UP': 0, 'GAP_DOWN': 1, 'GAP_ZERO': 2}
CVR = {'CVR_BAD_TAIL': 1, 'CVR_NON_BAD': 0}


def wdir(*p):
    return M.P('stageN', 'B3_prelim', 'work', *p)


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 ** 2


def dict_dense(cache, pool0):
    """dict 日期 → Series（列 = ticker）→ 段坐标稠密阵（缺 = NaN）。"""
    out = np.full(pool0.shape, np.nan)
    di = {d: i for i, d in enumerate(pool0.index)}
    cp = {c: j for j, c in enumerate(pool0.columns)}
    for d, s in cache.items():
        if d not in di:
            continue
        pos = np.fromiter((cp.get(x, -1) for x in s.index), int, len(s))
        ok = pos >= 0
        out[di[d], pos[ok]] = s.to_numpy(float)[ok]
    return out


# ---------------------------------------------------------------- masks
def task_masks(seg):
    import e6j_prod as PR
    t0 = time.time()
    with open(M.P('tmp', 'ctx_%s.pkl' % seg), 'rb') as fh:
        ctx = pickle.load(fh)
    pool0, p0 = ctx['pool0'], ctx['p0']
    T = dict(load_s=round(time.time() - t0, 1))
    clean = ctx['clean'].reindex_like(pool0).fillna(0.0).to_numpy() == 1
    t1 = time.time()
    masks = PR.form_masks(ctx)
    T['form_masks_s'] = round(time.time() - t1, 1)
    gate = masks['A4b_CVRv5']
    rej = p0 & ~gate
    cvr_bad = PR.drop_mask(ctx['neu_cvr'], pool0, 5)
    pcond = dict_dense(ctx['pcond'], pool0)
    z = np.load(M.P('stage0', 'cache_cloud', 'kq_%s.npz' % seg), allow_pickle=False)
    if list(z['dates']) != [str(d)[:10] for d in pool0.index]:
        raise RuntimeError('kq 日期轴与 ctx 不一致')
    cpos = {str(c): j for j, c in enumerate(pool0.columns)}
    kq = np.full(pool0.shape, np.nan)
    kq[:, [cpos[c] for c in z['ccols']]] = z['kq']
    lm = ctx['log_mcap'].reindex_like(pool0).to_numpy(float)
    # 门内名单对 N5 pool2 部件（A4b_cvrveto）逐格核成员
    pq = pd.read_parquet(M.P('stage0', 'c2_rebuild_parts', seg, 'pool2_%s.parquet' % PR.FNAME['A4b_CVRv5']))
    di = {str(d)[:10]: i for i, d in enumerate(pool0.index)}
    ci = {int(c): j for j, c in enumerate(ctx['col_ids'])}
    wcol = [c for c in pq.columns if c not in ('ticker', 'tradeDate')][0]
    r_ = pq.tradeDate.astype(str).str[:10].map(di)
    c_ = pq.ticker.astype(int).map(ci)
    okp = r_.notna() & c_.notna()
    part = np.zeros(pool0.shape, bool)
    part[r_[okp].astype(int).to_numpy(), c_[okp].astype(int).to_numpy()] = (pq[wcol][okp].to_numpy(float) > 0)
    chk = dict(rows_unmapped=int((~okp).sum()), part_not_gate=int((part & ~gate).sum()), gate_not_part=int((gate & ~part).sum()),
               zero_weight_rows=int((pq[wcol].to_numpy(float) <= 0).sum()), gate_cells=int(gate.sum()), p0_cells=int(p0.sum()),
               clean_cells=int(clean.sum()), p0_not_clean=int((p0 & ~clean).sum()), cvr_bad_cells=int(cvr_bad.sum()),
               cvr_bad_outside_p0=int((cvr_bad & ~p0).sum()), pcond_finite_in_p0=int(np.isfinite(pcond[p0]).sum()),
               kq_finite_in_p0=int(np.isfinite(kq[p0]).sum()), lm_finite_in_clean=int(np.isfinite(lm[clean]).sum()))
    out = wdir('masks_%s.npz' % seg)
    M.atomic_write_npz(out, date_ids=np.array([str(d)[:10] for d in pool0.index]), col_ids=np.asarray(ctx['col_ids'], np.int64),
                       pool0=p0, clean=clean, gate=gate, rej=rej, cvr_bad=cvr_bad, pcond=pcond, kq=kq, log_mcap=lm)
    T['total_s'] = round(time.time() - t0, 1)
    T['rss_peak_gb'] = round(rss_gb(), 2)
    ok = chk['rows_unmapped'] == 0 and chk['part_not_gate'] == 0 and chk['gate_not_part'] == 0 and chk['cvr_bad_outside_p0'] == 0
    M.write_receipt(os.environ.get('E6M_TASK', 'N8_b3_masks_%s' % seg), [out], status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, M.__file__], timing=T, checks=chk)
    print(json.dumps(dict(seg=seg, ok=ok, **chk, **T), ensure_ascii=False), flush=True)
    return 0 if ok else 1


# ---------------------------------------------------------------- 分类工具（码与 e6m_b3_tools 同口径；test 对拍）
def mid_pct(v):
    """有限值的中点百分位 (#< + .5·#=)/n；非有限 → NaN。"""
    out = np.full(len(v), np.nan)
    ok = np.isfinite(v)
    if ok.any():
        w = v[ok]
        s = np.sort(w)
        lo = np.searchsorted(s, w, 'left')
        hi = np.searchsorted(s, w, 'right')
        out[ok] = (lo + 0.5 * (hi - lo)) / len(w)
    return out


def terc_ref(v, ref):
    """参考域 ref（bool）内有限值算中点百分位三分；返回全体（len(v)）码，ref 外 / 非有限 = −1。"""
    out = np.full(len(v), -1, np.int8)
    ix = np.flatnonzero(ref & np.isfinite(v))
    if len(ix):
        p = mid_pct(v[ix])
        out[ix] = np.where(p <= 1 / 3, 0, np.where(p <= 2 / 3, 1, 2)).astype(np.int8)
    return out


def react_ref(r, ref):
    """价格反应（参考域 ref 内）：先核 r 有限；QUIET = d 中点百分位 ≤ 1/3 或 r = 0；其余 UP / DOWN；无效 −1。"""
    out = np.full(len(r), -1, np.int8)
    ix = np.flatnonzero(ref & np.isfinite(r))
    if len(ix):
        rr = r[ix]
        p = mid_pct(np.abs(rr))
        out[ix] = np.where((p <= 1 / 3) | (rr == 0), 0, np.where(rr > 0, 1, 2)).astype(np.int8)
    return out


def qgood_ref(kq, ref):
    """Q 优：kQ 在参考域内中点百分位 ≤ 1/3 → 1；有限且 > 1/3 → 0；缺失 / 域外 → −1（不把缺失当好或坏）。"""
    out = np.full(len(kq), -1, np.int8)
    ix = np.flatnonzero(ref & np.isfinite(kq))
    if len(ix):
        out[ix] = (mid_pct(kq[ix]) <= 1 / 3).astype(np.int8)
    return out


# ---------------------------------------------------------------- events
def load_full_data():
    import e6m_stage0_full as SF
    return SF.load_full()


def shift_up(a, k):
    """out[t] = a[t + k]（越界 NaN）。"""
    out = np.full_like(a, np.nan)
    if k < a.shape[0]:
        out[:a.shape[0] - k] = a[k:]
    return out


def task_events():
    import comprehensive_factor_diagnosis as C
    import e6l_state as LS
    T = {}
    t0 = time.time()
    data, before, cd = load_full_data()
    T['load_full_s'] = round(time.time() - t0, 1)
    close = data['close'].astype(float)
    dstr = np.array([str(d)[:10] for d in close.index])
    TT, NN = close.shape
    cols = close.columns
    tick = np.array([int(c) for c in cols], np.int64)
    g = lambda k: data[k].reindex(index=close.index, columns=cols).astype(float).to_numpy()
    is_open = (data['is_open'].reindex(index=close.index, columns=cols) == 1).to_numpy()
    o, h, l, c, lc = g('open'), g('high'), g('low'), g('close'), g('lclose')
    with np.errstate(all='ignore'):
        valid = is_open & (o > 0) & (h > 0) & (l > 0) & (c > 0) & (lc > 0)
        valid &= (l <= np.minimum(o, c) + 1e-9) & (h >= np.maximum(o, c) - 1e-9)
        r = np.where(valid, np.log(c / lc), np.nan)
        gapv = np.where(valid, np.log(o / lc), np.nan)
    gap = np.where(np.isfinite(gapv), np.where(gapv > 0, 0, np.where(gapv < 0, 1, 2)), -1).astype(np.int8)
    x = g('turnover_rate')
    x = np.where(is_open & np.isfinite(x) & (x >= 0), x, np.nan)
    X = pd.DataFrame(x)
    act = {}
    for w, mo in ((20, 12), (5, 3), (60, 36)):
        b = X.shift(1).rolling(w, min_periods=mo).mean().to_numpy()
        with np.errstate(all='ignore'):
            act[w] = np.where(np.isfinite(x) & np.isfinite(b) & (b > 0), x / b, np.nan)
    del X
    A = C.adjust_factor(data).reindex(index=close.index, columns=cols).to_numpy()
    with np.errstate(all='ignore'):
        ca = c * A
    ca = np.where(np.isfinite(ca) & (ca > 0), ca, np.nan)
    pre20 = np.full(ca.shape, np.nan)
    with np.errstate(all='ignore'):
        pre20[21:] = ca[20:-1] / ca[:-21] - 1.0
    rmax = pd.DataFrame(ca).rolling(20, min_periods=16).max().to_numpy()
    dd = np.full(ca.shape, np.nan)
    with np.errstate(all='ignore'):
        dd[1:] = ca[:-1] / rmax[:-1] - 1.0
    T['features_s'] = round(time.time() - t0 - T['load_full_s'], 1)
    # 行业（全程 industry_zx1，T 日值）与同业 / 市场（T−1 clean，e6l_state.clean_full，同 N5 task_peer）
    t1 = time.time()
    ind = data['industry_zx1'].reindex(index=close.index, columns=cols)
    codes, _ = pd.factorize(pd.Series(ind.to_numpy().ravel()))
    ind_code = codes.reshape(ind.shape).astype(np.int32)
    del ind
    clean_e6l = LS.clean_full(data).reindex_like(close).fillna(0.0).to_numpy() == 1
    prevclean = np.zeros_like(clean_e6l)
    prevclean[1:] = clean_e6l[:-1]
    del clean_e6l
    K = int(ind_code.max()) + 1
    sstrong = np.full((TT, NN), -1, np.int8)
    pstrong = np.full((TT, NN), -1, np.int8)
    for t in range(TT):
        v = pre20[t]
        k = ind_code[t]
        mem = prevclean[t] & np.isfinite(v) & (k >= 0)
        if not mem.any():
            continue
        mkt = v[mem].mean()
        cnt = np.bincount(k[mem], minlength=K)
        sm = np.bincount(k[mem], weights=v[mem], minlength=K)
        kk = np.maximum(k, 0)
        n_oth = np.where(k >= 0, cnt[kk] - mem.astype(np.int64), 0)
        s_oth = np.where(k >= 0, sm[kk] - np.where(mem, v, 0.0), 0.0)
        with np.errstate(all='ignore'):
            peer = np.where(n_oth > 0, s_oth / np.maximum(n_oth, 1), np.nan)
        known = (k >= 0) & (n_oth > 0) & np.isfinite(v) & np.isfinite(peer) & np.isfinite(mkt)
        sstrong[t] = np.where(known, (v > peer).astype(np.int8), -1)
        pstrong[t] = np.where(known, (peer > mkt).astype(np.int8), -1)
    peerq = np.where(sstrong < 0, -1, np.where(sstrong == 0, np.where(pstrong == 1, 0, 1), np.where(pstrong == 1, 2, 3))).astype(np.int8)
    del prevclean
    T['peer_s'] = round(time.time() - t1, 1)
    # 状态（云机重建，ANCHOR_PENDING）
    z = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)
    if list(z['dates']) != list(dstr):
        raise RuntimeError('状态日期轴与全程数据不一致')
    zc = {int(s): j for j, s in enumerate(z['columns'])}
    tmap = np.array([zc.get(int(s), -1) for s in cols])
    trend = np.full((TT, NN), -1, np.int8)
    ok = tmap >= 0
    trend[:, ok] = z['trend'][:, tmap[ok]]
    vol3 = z['vol_state'].astype(np.int8)
    T['state_cols_unmapped'] = int((~ok).sum())
    # 域掩码 → 全程网格
    t1 = time.time()
    col_of = {int(s): j for j, s in enumerate(tick)}
    day_of = {s: i for i, s in enumerate(dstr)}
    G = {k: np.zeros((TT, NN), bool) for k in ('pool0', 'clean', 'gate', 'rej', 'cvr_bad')}
    F = {k: np.full((TT, NN), np.nan) for k in ('pcond', 'kq', 'log_mcap')}
    segrow = np.full(TT, -1, np.int8)
    for si, seg in enumerate(SEGS):
        zz = np.load(wdir('masks_%s.npz' % seg), allow_pickle=False)
        rows = np.array([day_of[s] for s in zz['date_ids']])
        cmap = np.array([col_of.get(int(x), -1) for x in zz['col_ids']])
        okc = cmap >= 0
        if (~okc).any() and any(zz[k][:, ~okc].any() for k in ('pool0', 'clean')):
            raise RuntimeError('段列有域成员但不在全程列中：%s' % seg)
        segrow[rows] = si
        for k in G:
            G[k][np.ix_(rows, cmap[okc])] = zz[k][:, okc]
        for k in F:
            F[k][np.ix_(rows, cmap[okc])] = zz[k][:, okc]
    T['domain_grid_s'] = round(time.time() - t1, 1)
    # 标签
    t1 = time.time()
    rv = C.vwap_daily_return(data, True).reindex(index=close.index, columns=cols).to_numpy()
    va = C.adjusted_prices(data, ('vwap',))['vwap'].reindex(index=close.index, columns=cols).to_numpy()
    va = np.where(np.isfinite(va) & (va > 0), va, np.nan)
    vraw = g('vwap')
    entry_ok = np.zeros((TT, NN), bool)
    entry_ok[:-1] = is_open[1:] & np.isfinite(vraw[1:]) & (vraw[1:] > 0)
    del vraw
    ENDP, LIN = {}, {}
    va1 = shift_up(va, 1)
    for hh in HS:
        with np.errstate(all='ignore'):
            ENDP[hh] = (shift_up(va, 1 + hh) / va1 - 1.0) * 1e4
        acc = np.zeros((TT, NN))
        for k in range(2, 2 + hh):
            acc = acc + shift_up(rv, k)
        LIN[hh] = acc * 1e4
    del va1
    T['endpoint_linear_s'] = round(time.time() - t1, 1)
    t1 = time.time()
    dom_full = {'POOL0': G['pool0'], 'CLEAN': G['clean'], 'A4B_CVRV5_GATE_IN': G['gate'], 'A4B_CVRV5_REJECTED': G['rej']}
    FWD = {}
    for dn, msk in dom_full.items():
        bp = pd.DataFrame(msk.astype(float), index=close.index, columns=cols)
        for hh in HS:
            FWD[(dn, hh)] = C.compute_forward_5d_excess(data, bp, hold_days=hh, adjust=True).reindex(index=close.index, columns=cols).to_numpy()
        del bp
    T['fwd_source_s'] = round(time.time() - t1, 1)
    T['rss_after_labels_gb'] = round(rss_gb(), 2)
    # 逐段 × 域抽事件行
    t1 = time.time()
    order_cols = np.argsort(tick, kind='mergesort')
    counts = []
    for dn in DOMAINS:
        refm = G['clean'] if dn == 'CLEAN' else G['pool0']
        dm = dom_full[dn]
        for si, seg in enumerate(SEGS):
            days = np.flatnonzero((segrow == si) & dm.any(1))
            parts = {k: [] for k in ('t', 'tick', 'ind', 'size3', 'k3', 'act20', 'act5', 'act60', 'pr', 'pos', 'posdd', 'vol3', 'trend', 'peerq',
                                     'sstrong', 'pstrong', 'cvr', 'gap', 'qgood', 'd', 'cash', 'Y', 'YB')}
            ndom = np.zeros(TT, np.int64)
            for t in days:
                ref = refm[t][order_cols]
                mem = dm[t][order_cols]
                cix = order_cols[mem]
                n = len(cix)
                ndom[t] = n
                rr = r[t][order_cols]
                cl = lambda codes_full: codes_full[mem]
                parts['t'].append(np.full(n, t, np.int32))
                parts['tick'].append(tick[cix])
                parts['ind'].append(ind_code[t, cix])
                parts['size3'].append(cl(terc_ref(F['log_mcap'][t][order_cols], ref)))
                parts['k3'].append(cl(terc_ref(F['pcond'][t][order_cols], ref)) if dn != 'CLEAN' else np.full(n, -1, np.int8))
                parts['act20'].append(cl(terc_ref(act[20][t][order_cols], ref)))
                parts['act5'].append(cl(terc_ref(act[5][t][order_cols], ref)))
                parts['act60'].append(cl(terc_ref(act[60][t][order_cols], ref)))
                parts['pr'].append(cl(react_ref(rr, ref)))
                parts['pos'].append(cl(terc_ref(pre20[t][order_cols], ref)))
                parts['posdd'].append(cl(terc_ref(dd[t][order_cols], ref)))
                parts['vol3'].append(np.full(n, vol3[t], np.int8))
                parts['trend'].append(trend[t, cix])
                parts['peerq'].append(peerq[t, cix])
                parts['sstrong'].append(sstrong[t, cix])
                parts['pstrong'].append(pstrong[t, cix])
                parts['cvr'].append(G['cvr_bad'][t, cix].astype(np.int8) if dn == 'POOL0' else np.full(n, -1, np.int8))
                parts['gap'].append(gap[t, cix] if dn == 'POOL0' else np.full(n, -1, np.int8))
                parts['qgood'].append(cl(qgood_ref(F['kq'][t][order_cols], ref)) if dn != 'CLEAN' else np.full(n, -1, np.int8))
                parts['d'].append(np.abs(r[t, cix]))
                parts['cash'].append(~entry_ok[t, cix])
                own = np.empty((n, len(YCOLS)))
                brg = np.empty((n, len(YCOLS)))
                j = 0
                for lb in LABELS:
                    for hh in HS:
                        if lb == 'FWD_SOURCE':
                            own[:, j] = FWD[(dn, hh)][t, cix]
                            brg[:, j] = FWD[('POOL0', hh)][t, cix]
                        else:
                            raw = (ENDP if lb == 'FWD_ENDPOINT' else LIN)[hh][t]
                            v = raw[cix]
                            fin = np.isfinite(v)
                            b_own = v[fin].mean() if fin.any() else np.nan
                            pv = raw[G['pool0'][t]]
                            pf = np.isfinite(pv)
                            b_p0 = pv[pf].mean() if pf.any() else np.nan
                            own[:, j] = v - b_own
                            brg[:, j] = v - b_p0
                        j += 1
                parts['Y'].append(own)
                parts['YB'].append(brg)
            out = {k: (np.concatenate(v) if len(v) else np.zeros((0, len(YCOLS)) if k in ('Y', 'YB') else 0)) for k, v in parts.items()}
            if dn == 'POOL0':
                out.pop('YB')                                          # POOL0 的桥 = 自身
            p = wdir('events_%s__%s.npz' % (seg, dn))
            M.atomic_write_npz(p, ycols=np.array(YCOLS), ndom=ndom, dates=dstr, segment=np.array([seg]), domain=np.array([dn]),
                               status=np.array(['ANCHOR_PENDING']), **out)
            counts.append(dict(segment=seg, domain=dn, days=len(days), events=int(len(out['t'])), file=os.path.basename(p)))
    T['events_s'] = round(time.time() - t1, 1)
    T['cache_dir_unchanged'] = sorted(os.listdir(cd)) == before
    T['rss_peak_gb'] = round(rss_gb(), 2)
    cdf = pd.DataFrame(counts)
    M.atomic_write_csv(wdir('events_counts.csv'), cdf)
    outs = [wdir('events_counts.csv')] + [wdir(x) for x in cdf.file]
    ok = bool(T['cache_dir_unchanged'])
    M.write_receipt(os.environ.get('E6M_TASK', 'N8_b3_events'), outs, status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__],
                    timing=T)
    print(cdf.to_string(index=False), flush=True)
    print(json.dumps(T, ensure_ascii=False), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['masks', 'events'])
    ap.add_argument('--seg')
    a = ap.parse_args()
    os.makedirs(wdir(), exist_ok=True)
    sys.exit(task_masks(a.seg) if a.task == 'masks' else task_events())
