# -*- coding: utf-8 -*-
"""E6m B4 签名 1–3（plan §8.1；定义 = registration/delegated_decisions_E6m_S.json 第 22 项与"签名 1–3 定义"，用户 2026-10-05 授权执行端代拟、advisor 复核；
限制登记 L-S3）。阶段 S 真实引擎，一段一个进程（run --seg）；对象 = registry/b4_queries_E6m.csv 的 SIGNATURE 对象（78 个，H5）。
  sig1  入场后 j 日曲线：批次 = 形成日 f 的目标（账户同一 DEV 权重）；e_f(j) = Σ_c w (r0[f+1+j] − bench[f+1+j]) / Σ_c w（按投入资本），累计 = 累加，
        名单持有到 j = 20（超出 H 也照算）；只取窗口完整的批次（f ≤ T − 22），按形成年等权平均：子 / 同 H 原父 / 子 − 父（父对象只报自身）。
        第一天份额 = 年均 CumEx(1) / 年均 CumEx(20)，年均 CumEx(20) ≤ 2·se（批次 CumEx(20) 序列 HAC 滞后 20）时 UNDEFINED。
        账户锚：Σ_f Σ_{j ≤ H} E[f, j] = Σ_t gross[t]·den(t − 2)（den = min(t − 1, H)），与 accounts 的 d_gross 比，相对差 > 1e−12 记 CLOSURE_FAIL。
  sig3  保留 / 剔除特征价差：每个形成日 保留 = 父 ∩ 子、剔除 = 父 \\ 子、新增 = 子 \\ 父；特征 Q = 本对象测量坏度（Q0 / Q_MAX2）、K = 旧 K 坏度 q0、
        size = z_T；组内等权；其后收益 = 每股入场后 H 日累计超额；价差 = 保留 − 剔除、新增 − 剔除，按形成年等权平均；原父对象 NOT_APPLICABLE。
  sig2  同步性：名单 = 形成日 T 的目标名单；收益 = S.dr（VWAP 日收益，无效 = NaN）；截至 T 的 60 日平均两两相关，raw 与剔市场（源基准）/ 同业
        （clean 同业等权、剔自身，industry_zx1）后两版；β 用截至 T 的 120 日、至少 60 对；窗口内完整样本（任一日无效即不进，计数另报）；
        平均相关 = (Σ_k S_k² / 60 − n) / (n(n − 1))，S = Σ 标准化收益（完整样本下 = 两两相关平均，不建矩阵）。
        随机对照：同日 pool0（同一有效规则）、同人数，按格分层无放回 1,024 条：A = 行业 × size3 × 流动性3（T 前 20 日 turnover_rate 均值）、B = 行业 × size3；
        格内不够依次从 行业 × size3 → 行业 → 全池 补（计数另报）；优先序 = e6j_random.uniform（namespace 'E6m.SIG2'，块 = 绝对交易日，对象间共用）。
        只报均值与 sd。
输出 <out>/b4_sig1_<段>.csv / b4_sig3_<段>.csv / b4_sig2_<段>.csv。B2：只跑 selftest（合成）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M

J = 20
W_RAW, W_BETA, MIN_BETA = 60, 120, 60
NPATH = 1024
TOL_REL = 1e-12


# ====================================================================== sig1
def batch_excess(T, t, c, w, x, J_=J):
    """E (T, J)：E[f, j − 1] = Σ_{格 t = f} w·x[f + 1 + j, c]（f + 1 + j ≤ T − 1 才有）；W (T,) = Σ_{格 t = f} w。"""
    E = np.zeros((T, J_))
    for j in range(1, J_ + 1):
        ok = t + 1 + j <= T - 1
        np.add.at(E[:, j - 1], t[ok], w[ok] * x[t[ok] + 1 + j, c[ok]])
    W = np.bincount(t, weights=w, minlength=T).astype(float)
    return E, W


def anchor(E, H, gross):
    """Σ_f Σ_{j ≤ H} E[f, j − 1] 对 Σ_t gross[t]·min(t − 1, H)（t ≥ 2）。返回 (左, 右, 相对差)。"""
    T = len(gross)
    lhs = float(E[:, :H].sum())
    den = np.minimum(np.arange(T) - 1, H).astype(float)
    g = np.where(np.isfinite(gross), gross, 0.0)
    rhs = float(np.sum(g[2:] * den[2:]))
    return lhs, rhs, abs(lhs - rhs) / max(abs(rhs), 1e-300)


def sig1_rows(obj, seg, years, Ec, Wc, Ep, Wp, T):
    from e6l_mde80 import hac_batch
    full = np.arange(T) <= T - 22
    rows = []
    for y in sorted(set(years)):
        sel_c = full & (years == y) & (Wc > 0)
        if not sel_c.any():
            rows.append(dict(object=obj, segment=seg, year=int(y), j='ALL', status='UNDEFINED', note='无完整窗口批次'))
            continue
        cc = np.cumsum(Ec[sel_c], axis=1) / Wc[sel_c][:, None]
        Cc = cc.mean(axis=0)
        Cp = None
        if Ep is not None:
            sel_p = full & (years == y) & (Wp > 0)
            Cp = (np.cumsum(Ep[sel_p], axis=1) / Wp[sel_p][:, None]).mean(axis=0) if sel_p.any() else np.full(J, np.nan)
        for j in range(J):
            rows.append(dict(object=obj, segment=seg, year=int(y), j=j + 1, cum_excess_child_decimal=float(Cc[j]),
                             cum_excess_parent_decimal=float(Cp[j]) if Cp is not None else np.nan,
                             cum_excess_diff_decimal=float(Cc[j] - Cp[j]) if Cp is not None else np.nan, n_batches=int(sel_c.sum()), status='COMPUTED'))
        se, _ = hac_batch(cc[:, J - 1][None, :], J)
        ok = bool(np.isfinite(se[0]) and Cc[J - 1] > 2.0 * se[0])
        rows.append(dict(object=obj, segment=seg, year=int(y), j='FIRST_DAY_SHARE', cum_excess_child_decimal=float(Cc[0] / Cc[J - 1]) if ok else np.nan,
                         n_batches=int(sel_c.sum()), se_cum20_decimal=float(se[0]) if np.isfinite(se[0]) else np.nan,
                         status='COMPUTED' if ok else 'UNDEFINED', note='' if ok else '年均 CumEx(20) ≤ 2·se（含为负）：第一天份额不算'))
    return rows


# ====================================================================== sig3
def group_day_means(t, T, sel, vals):
    """sel：格布尔；vals：格值（NaN 不计）→ (T,) 日均与 (T,) 有效数。"""
    ok = sel & np.isfinite(vals)
    n = np.bincount(t[ok], minlength=T).astype(float)
    s = np.bincount(t[ok], weights=vals[ok], minlength=T)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(n > 0, s / np.maximum(n, 1), np.nan), n


def sig3_rows(obj, seg, years, t, T, Fc, Fp, feats, ret):
    """years：(T,) 每日年份；t：格日序；Fc / Fp：子 / 父名单（格布尔）；feats：{名: 格值}；ret：格的入场后 H 日累计超额（窗口不全 = NaN）。"""
    groups = dict(kept=Fp & Fc, removed=Fp & ~Fc, added=Fc & ~Fp)
    size = {g: np.bincount(t[m], minlength=T).astype(float) for g, m in groups.items()}
    vals = dict(feats, ret=ret)
    day = {}
    for nm, v in vals.items():
        for g, m in groups.items():
            day[(nm, g)] = group_day_means(t, T, m, v)[0]
    rows = []
    for y in sorted(set(years)):
        dsel = (years == y) & ((size['kept'] + size['removed']) > 0)
        if not dsel.any():
            continue
        r = dict(object=obj, segment=seg, year=int(y), n_days=int(dsel.sum()),
                 days_removed_empty=int((dsel & (size['removed'] == 0)).sum()), days_added_empty=int((dsel & (size['added'] == 0)).sum()),
                 mean_n_kept=float(size['kept'][dsel].mean()), mean_n_removed=float(size['removed'][dsel].mean()), mean_n_added=float(size['added'][dsel].mean()))
        for nm in vals:
            for a_, b_ in (('kept', 'removed'), ('added', 'removed')):
                sp = day[(nm, a_)] - day[(nm, b_)]
                m = dsel & np.isfinite(sp)
                r['%s_%s_minus_%s' % (nm, a_, b_)] = float(np.mean(sp[m])) if m.any() else np.nan
                r['days_%s_%s_minus_%s' % (nm, a_, b_)] = int(m.sum())
        r['status'] = 'COMPUTED'
        rows.append(r)
    return rows


# ====================================================================== sig2
def zscore_rows(Y):
    """(n, k) 完整样本 → 每行标准化（总体 sd）；sd = 0 的行标 False。"""
    mu = Y.mean(axis=1, keepdims=True)
    sd = Y.std(axis=1, keepdims=True)
    ok = sd[:, 0] > 0
    Z = np.zeros_like(Y)
    Z[ok] = (Y[ok] - mu[ok]) / sd[ok]
    return Z, ok


def mean_corr(Z):
    """完整样本标准化收益 (n, k) → 平均两两相关（和的方差恒等式）。"""
    n, k = Z.shape
    if n < 2:
        return np.nan
    S = Z.sum(axis=0)
    return float((np.dot(S, S) / k - n) / (n * (n - 1)))


def resid_window(y, m, p, ok_rows):
    """OLS y ~ 1 + m + p（只用 ok_rows 的行）→ β 与全部行残差。"""
    X = np.column_stack([np.ones(len(y)), m, p])
    b, *_ = np.linalg.lstsq(X[ok_rows], y[ok_rows], rcond=None)
    return b, y - X @ b


try:
    import numba as nb

    @nb.njit(cache=False)
    def _take(i, taken, S, Z):
        taken[i] = True
        for kk in range(Z.shape[1]):
            S[kk] += Z[i, kk]

    @nb.njit(cache=False)
    def _paths_corr(Z, lvl, up01, up12, need0, ORD, out, short):
        """Z (n, k) 标准化收益；lvl (n, 3) 三层格号（层 0 ⊂ 层 1 ⊂ 层 2 = 行业；之上 = 全池）；up01 (G0,) / up12 (G1,) 上层格号；
        need0 (G0,) 层 0 各格应抽数；ORD (P, n) 每条路径按优先序（e6j_random.uniform 升序）排好的候选下标。
        每条路径：沿 ORD 先满足层 0 各格；缺口归到所属层 1 格沿同一优先序补（跳过已取），再归到层 2、最后全池。out ← 平均两两相关，short ← 补的人数。"""
        P, n = ORD.shape
        k = Z.shape[1]
        G0 = need0.shape[0]
        G1 = up12.shape[0]
        G2 = 0
        for g1 in range(G1):
            if up12[g1] + 1 > G2:
                G2 = up12[g1] + 1
        for p in range(P):
            taken = np.zeros(n, np.bool_)
            S = np.zeros(k)
            m0 = need0.copy()
            left = 0
            for g in range(G0):
                left += m0[g]
            cnt = 0
            sh = 0
            for ii in range(n):                                       # 层 0
                if left == 0:
                    break
                i = ORD[p, ii]
                g = lvl[i, 0]
                if m0[g] > 0:
                    _take(i, taken, S, Z)
                    m0[g] -= 1
                    left -= 1
                    cnt += 1
            if left > 0:                                              # 层 1
                m1 = np.zeros(G1, np.int64)
                for g in range(G0):
                    m1[up01[g]] += m0[g]
                for ii in range(n):
                    if left == 0:
                        break
                    i = ORD[p, ii]
                    if taken[i]:
                        continue
                    g1 = lvl[i, 1]
                    if m1[g1] > 0:
                        _take(i, taken, S, Z)
                        m1[g1] -= 1
                        left -= 1
                        cnt += 1
                        sh += 1
                if left > 0:                                          # 层 2（行业）
                    m2 = np.zeros(G2, np.int64)
                    for g1 in range(G1):
                        m2[up12[g1]] += m1[g1]
                    for ii in range(n):
                        if left == 0:
                            break
                        i = ORD[p, ii]
                        if taken[i]:
                            continue
                        g2 = lvl[i, 2]
                        if m2[g2] > 0:
                            _take(i, taken, S, Z)
                            m2[g2] -= 1
                            left -= 1
                            cnt += 1
                            sh += 1
                    for ii in range(n):                               # 全池
                        if left == 0:
                            break
                        i = ORD[p, ii]
                        if not taken[i]:
                            _take(i, taken, S, Z)
                            left -= 1
                            cnt += 1
                            sh += 1
            short[p] = sh
            if cnt < 2:
                out[p] = np.nan
            else:
                ss = 0.0
                for kk in range(k):
                    ss += S[kk] * S[kk]
                out[p] = (ss / k - cnt) / (cnt * (cnt - 1))
    HAVE_NB = True
except Exception:                                                     # pragma: no cover
    HAVE_NB = False


def level_codes(ind, size3, liq3, version):
    """候选的三层格号：A = 行业×size3×流动性3 ⊂ 行业×size3 ⊂ 行业；B = 行业×size3（层 0 = 层 1）⊂ 行业（缺失是显式类别）。"""
    l2 = pd.factorize(pd.Series(list(map(int, ind))))[0]
    l1 = pd.factorize(pd.Series(list(zip(map(int, ind), map(int, size3)))))[0]
    l0 = pd.factorize(pd.Series(list(zip(map(int, ind), map(int, size3), map(int, liq3)))))[0] if version == 'A' else l1
    lvl = np.column_stack([l0, l1, l2]).astype(np.int64)
    up01 = np.zeros(int(l0.max()) + 1, np.int64)
    up12 = np.zeros(int(l1.max()) + 1, np.int64)
    up01[l0] = l1
    up12[l1] = l2
    return lvl, up01, up12


def random_corr(Z, lv, actual_idx, ORD):
    """真实名单（候选下标）的层 0 格计数 → 1,024 条匹配随机名单的平均相关（均值、sd、平均补人数）。"""
    lvl, up01, up12 = lv
    need0 = np.bincount(lvl[actual_idx, 0], minlength=len(up01)).astype(np.int64)
    out = np.empty(ORD.shape[0])
    short = np.empty(ORD.shape[0], np.int64)
    _paths_corr(Z, lvl, up01, up12, need0, ORD, out, short)
    return float(np.nanmean(out)), float(np.nanstd(out, ddof=1)), float(short.mean())


def priority_order(keys, day_abs, tids):
    """每条路径的优先序（e6j_random.uniform 升序；块 = 绝对交易日）→ (P, n) 下标。"""
    import e6j_random as R
    U = np.vstack([R.uniform(k, np.full(len(tids), day_abs, np.int64), tids) for k in keys])
    return np.argsort(U, axis=1, kind='stable').astype(np.int64)


# ====================================================================== 真实段
def run(seg_name, out, which=('sig1', 'sig3', 'sig2')):
    import e6k_acct as AC
    import e6m_s_real as RL
    import e6m_s_stats as SS
    import e6m_s_meas as ME
    import e6j_random as R
    seg = RL.seg_of(seg_name, 'real')
    S, SE, ci = seg.S, seg.SE, seg.ci
    T, Nc, n = SE.T, SE.Nc, seg.n
    acct = AC.Acct(seg, impact=False)
    x = SE.r0 - SE.bench[:, None]
    years = np.array([pd.Timestamp(dd).year for dd in seg.dates])
    acc = M.P('accounts')
    d, _, d2t, dH, _ = SS.load(acc, seg_name)
    bits = {}
    for ad in SS.acc_dirs(acc):
        tag = '' if ad == acc else os.path.basename(os.path.normpath(ad)) + ':'
        sd_ = os.path.join(ad, seg_name)
        for f in sorted(os.listdir(sd_)) if os.path.isdir(sd_) else []:
            if f.endswith('.npz') and not f.startswith('weights_'):
                z = np.load(os.path.join(sd_, f), allow_pickle=False)
                zb = z['bits']
                for j, tid in enumerate(z['targets']):
                    bits['%s%s#%s' % (tag, f[:-4], tid)] = zb[j]
    Q = M.read_csv_keep(M.P('registry', 'b4_queries_E6m.csv'), dtype=str)
    objs = sorted(set(Q[Q.query_kind == 'SIGNATURE'].object))
    kept = lambda did: np.unpackbits(bits[d2t[did]])[:n].astype(bool)
    tg_cache = {}

    def target(did):
        k = d2t[did]
        if k not in tg_cache:
            tg_cache[k] = acct.target(kept(did))
        return tg_cache[k]
    outs, counts = [], {}
    if 'sig1' in which:
        rows, Ecache = [], {}
        for o in objs:
            if o not in d:
                rows.append(dict(object=o, segment=seg_name, year='ALL', j='ALL', status='SOURCE_WAIT'))
                continue
            H = dH[o]
            par = None if o.split('|')[2] == 'PARENT' else SS.parent_of(o)
            for did in [o] + ([par] if par else []):
                if did not in Ecache:
                    tg = target(did)
                    Ecache[did] = batch_excess(T, tg['t'], tg['c'], tg['w'], x)
            Ec, Wc = Ecache[o]
            Ep, Wp = Ecache[par] if par else (None, None)
            rows += sig1_rows(o, seg_name, years, Ec, Wc, Ep, Wp, T)
            for did in [o] + ([par] if par else []):
                l_, r_, rel = anchor(Ecache[did][0], H, np.asarray(d[did]['gross'], float))
                rows.append(dict(object=o, segment=seg_name, year='ALL', j='ANCHOR_%s' % ('CHILD' if did == o else 'PARENT'), anchor_lhs=l_, anchor_rhs=r_,
                                 anchor_rel=rel, status='COMPUTED' if rel <= TOL_REL else 'CLOSURE_FAIL'))
        p = os.path.join(out, 'b4_sig1_%s.csv' % seg_name)
        df = pd.DataFrame(rows)
        M.atomic_write_csv(p, df)
        outs.append(p)
        counts['sig1'] = df.status.value_counts().to_dict()
    if 'sig3' in which:
        kfs = RL.kfs_of(seg, 'real', ME.load(seg_name))
        rows = []
        for o in objs:
            if o not in d:
                rows.append(dict(object=o, segment=seg_name, year='ALL', status='SOURCE_WAIT'))
                continue
            if o.split('|')[2] == 'PARENT':
                rows.append(dict(object=o, segment=seg_name, year='ALL', status='NOT_APPLICABLE', note='原父对自身没有保留 / 剔除之分'))
                continue
            H = dH[o]
            meas, form = o.split('|')[0], o.split('|')[1]
            st = seg.struct(form)
            fx = dict(Q=np.asarray(kfs[meas], float), K=np.asarray(st.q0, float), size=np.asarray(seg.zT, float))
            okc = ci.t + 1 + H <= T - 1
            ret = np.full(n, np.nan)
            cs = np.zeros(int(okc.sum()))
            for j in range(1, H + 1):
                cs += x[ci.t[okc] + 1 + j, ci.c[okc]]
            ret[okc] = cs
            rows += sig3_rows(o, seg_name, years, ci.t, T, kept(o), kept(SS.parent_of(o)), fx, ret)
        p = os.path.join(out, 'b4_sig3_%s.csv' % seg_name)
        df = pd.DataFrame(rows)
        M.atomic_write_csv(p, df)
        outs.append(p)
        counts['sig3'] = df.status.value_counts().to_dict()
    if 'sig2' in which:
        ctx = seg.ctx
        idx, colsA = S.dr.index, S.dr.columns
        dr = S.dr.to_numpy(float)                                       # (T, 全部列)，无效 = NaN
        clean = ctx['clean'].reindex(index=idx, columns=colsA).fillna(0).to_numpy() == 1
        ind_all = pd.factorize(pd.Series(ctx['industry'].reindex(index=idx, columns=colsA).to_numpy().ravel()))[0].reshape(dr.shape)
        G0 = int(ind_all.max()) + 1
        ind_all = np.where(ind_all < 0, G0, ind_all)                     # 行业缺失 = 显式类别 G0；无效 / 非 clean 的格记到 G0 + 1（不计入同业）
        okv = np.isfinite(dr) & clean
        isum = np.zeros((T, G0 + 2))
        icnt = np.zeros((T, G0 + 2))
        for tt in range(T):
            g_ = np.where(okv[tt], ind_all[tt], G0 + 1)
            isum[tt] = np.bincount(g_, weights=np.where(okv[tt], dr[tt], 0.0), minlength=G0 + 2)
            icnt[tt] = np.bincount(g_, minlength=G0 + 2)
        bench = np.asarray(S.bench, float)
        ccols = np.asarray(seg.ccols)
        tr = ctx['data']['turnover_rate'].reindex(index=idx, columns=colsA).to_numpy(float)[:, ccols]
        liq = pd.DataFrame(tr).rolling(20, min_periods=10).mean().to_numpy()
        tid = R.ticker_ids(np.asarray(S.ccolnames))
        cal = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)['dates']
        day_abs = R.day_index([str(dd)[:10] for dd in seg.dates], [str(dd)[:10] for dd in cal])
        keys = [R.path_key('E6m.SIG2', 'POOL0_MATCHED', 'ALL', 'POOL0', 'PRIORITY', p) for p in range(NPATH)]
        lists = {}
        for o in objs:
            if o in d:
                tg = target(o)
                lists[o] = (np.asarray(tg['c']), np.searchsorted(tg['t'], np.arange(T + 1)))
        rows = []
        for tt in range(W_BETA - 1, T):
            a0, a1 = seg.off[tt], seg.off[tt + 1]
            cand_c = ci.c[a0:a1]                                         # 当日 pool0 列（ccols 下标）
            if len(cand_c) < 3:
                continue
            full_c = ccols[cand_c]
            Yr = dr[tt - W_RAW + 1:tt + 1, full_c].T                     # (n_cand, 60)
            raw_ok = np.isfinite(Yr).all(axis=1)
            Zr, zok = zscore_rows(np.where(np.isfinite(Yr), Yr, 0.0))
            raw_ok &= zok
            rows_b = slice(tt - W_BETA + 1, tt + 1)
            Yb = dr[rows_b][:, full_c]                                   # (120, n_cand)
            gi = ind_all[rows_b][:, full_c]
            own = okv[rows_b][:, full_c]
            rs = np.take_along_axis(isum[rows_b], gi, axis=1) - np.where(own, Yb, 0.0)
            rc = np.take_along_axis(icnt[rows_b], gi, axis=1) - own
            with np.errstate(invalid='ignore', divide='ignore'):
                peer = np.where(rc > 0, rs / np.maximum(rc, 1), np.nan)
            mk = bench[rows_b]
            Zs = np.zeros((len(full_c), W_RAW))
            res_ok = np.zeros(len(full_c), bool)
            for i in range(len(full_c)):
                okr = np.isfinite(Yb[:, i]) & np.isfinite(peer[:, i]) & np.isfinite(mk)
                if okr.sum() < MIN_BETA or not okr[-W_RAW:].all():
                    continue
                _, e = resid_window(Yb[:, i], mk, peer[:, i], okr)
                ew = e[-W_RAW:]
                if ew.std() > 0:
                    Zs[i] = (ew - ew.mean()) / ew.std()
                    res_ok[i] = True
            s3 = R.terciles_rowwise(seg.zc[tt][None, cand_c], np.ones((1, len(cand_c)), bool))[0]
            l3 = R.terciles_rowwise(liq[tt][None, cand_c], np.isfinite(liq[tt][None, cand_c]))[0]
            indc = np.asarray(S.icodes[tt, cand_c], np.int64)
            prep = {}
            for tag, Zx, okx in (('raw', Zr, raw_ok), ('resid', Zs, res_ok)):
                cand = np.flatnonzero(okx)
                if len(cand) < 2 or not HAVE_NB:
                    prep[tag] = None
                    continue
                remap = -np.ones(len(cand_c), np.int64)
                remap[cand] = np.arange(len(cand))
                ORD = priority_order(keys, int(day_abs[tt]), tid[cand_c[cand]])
                prep[tag] = (remap, ORD, {v: level_codes(indc[cand], s3[cand], l3[cand], v) for v in ('A', 'B')}, np.ascontiguousarray(Zx[cand]))
            posarr = -np.ones(Nc, np.int64)
            posarr[cand_c] = np.arange(len(cand_c))
            for o, (oc, off) in lists.items():
                if off[tt + 1] == off[tt]:
                    continue
                act = posarr[oc[off[tt]:off[tt + 1]]]
                act = act[act >= 0]
                r = dict(object=o, segment=seg_name, day=tt, year=int(years[tt]), n_list=int(off[tt + 1] - off[tt]))
                for tag, Zx, okx in (('raw', Zr, raw_ok), ('resid', Zs, res_ok)):
                    ai = act[okx[act]]
                    r['n_valid_%s' % tag] = int(len(ai))
                    r['corr_%s' % tag] = mean_corr(Zx[ai]) if len(ai) >= 2 else np.nan
                    if len(ai) >= 2 and prep[tag] is not None:
                        remap, ORD, lvs, Zc = prep[tag]
                        for v in ('A', 'B'):
                            r['rand%s_mean_%s' % (v, tag)], r['rand%s_sd_%s' % (v, tag)], r['rand%s_fill_%s' % (v, tag)] = random_corr(Zc, lvs[v], remap[ai], ORD)
                rows.append(r)
        D = pd.DataFrame(rows)
        agg = []
        fdays = {o: {int(y): int(((np.diff(off) > 0) & (years == y)).sum()) for y in sorted(set(years))} for o, (_, off) in lists.items()}
        done = set()
        for (o, y), g in (D.groupby(['object', 'year']) if len(D) else []):
            done.add((o, int(y)))
            a_ = dict(object=o, segment=seg_name, year=int(y), days=int(len(g)), formation_days_in_year=fdays[o].get(int(y), 0))   # 覆盖：算了的日 / 该年形成日
            for c_ in [c for c in g.columns if c.startswith(('corr_', 'rand', 'n_valid_', 'n_list'))]:
                a_[c_] = float(g[c_].mean())
            for tag in ('raw', 'resid'):
                for v in ('A', 'B'):
                    if 'corr_%s' % tag in g and 'rand%s_mean_%s' % (v, tag) in g:
                        a_['real_minus_rand%s_%s' % (v, tag)] = float((g['corr_%s' % tag] - g['rand%s_mean_%s' % (v, tag)]).mean())
            a_['status'] = 'COMPUTED'
            agg.append(a_)
        for o, fy in fdays.items():                                       # 有形成日但一天都没算的年（段首不够 60 / 120 日历史）→ 显式 UNDEFINED 行
            for y, nf in fy.items():
                if nf and (o, y) not in done:
                    agg.append(dict(object=o, segment=seg_name, year=y, days=0, formation_days_in_year=nf, status='UNDEFINED',
                                    note='段首历史不足（raw 60 日 / β 120 日窗口）'))
        for o in objs:
            if o not in lists:
                agg.append(dict(object=o, segment=seg_name, year='ALL', status='SOURCE_WAIT'))
        p = os.path.join(out, 'b4_sig2_%s.csv' % seg_name)
        df = pd.DataFrame(agg)
        M.atomic_write_csv(p, df)
        outs.append(p)
        counts['sig2'] = df.status.value_counts().to_dict() if len(df) else {}
    return outs, counts


# ====================================================================== selftest（合成）
def selftest():
    import e6m_s_decomp as DC
    rng = np.random.default_rng(81)
    res = []
    T, Nc, H = 120, 30, 5
    t = np.repeat(np.arange(T), 6)
    c = np.concatenate([rng.choice(Nc, 6, replace=False) for _ in range(T)])
    w = rng.uniform(0.05, 0.2, len(t))
    x = rng.normal(0, 0.02, (T, Nc))
    E, W = batch_excess(T, t, c, w, x)
    a = DC.act_dense(T, Nc, t, c, w, H)
    g = np.zeros(T)
    g[2:] = np.einsum('ij,ij->i', a[:-2], x[2:])
    l_, r_, rel = anchor(E, H, g)
    res.append(('签名 1 账户锚：Σ_f Σ_{j≤H} E = Σ_t gross·den(t−2)（合成 120 日，段尾批次截断）相对差 %.1e' % rel, rel <= TOL_REL))
    f0 = 10
    e1 = float(np.sum(w[t == f0] * x[f0 + 2, c[t == f0]]) / W[f0])
    res.append(('签名 1：e_f(1) = 入场后第一段（x[f + 2]）按投入资本归一', abs(E[f0, 0] / W[f0] - e1) <= 1e-15))
    T3 = 40
    t3 = np.repeat(np.arange(T3), 10)
    Fp = rng.random(len(t3)) < 0.6
    Fc = (Fp & (rng.random(len(t3)) < 0.8)) | (~Fp & (rng.random(len(t3)) < 0.1))
    fe = dict(Q=rng.normal(size=len(t3)), K=rng.normal(size=len(t3)), size=rng.random(len(t3)))
    ret = rng.normal(0, 0.01, len(t3))
    yrs = np.where(np.arange(T3) < 20, 2015, 2016)
    R3 = sig3_rows('o', 's', yrs, t3, T3, Fc, Fp, fe, ret)
    kp = np.bincount(t3[Fp & Fc], minlength=T3) + np.bincount(t3[Fp & ~Fc], minlength=T3)
    kc = np.bincount(t3[Fp & Fc], minlength=T3) + np.bincount(t3[Fc & ~Fp], minlength=T3)
    res.append(('签名 3：保留 + 剔除 = 父人数、保留 + 新增 = 子人数（逐日）', np.array_equal(kp, np.bincount(t3[Fp], minlength=T3)) and
                np.array_equal(kc, np.bincount(t3[Fc], minlength=T3))))
    dd = [d_ for d_ in range(20) if (Fp & ~Fc & (t3 == d_)).any() and (Fp & Fc & (t3 == d_)).any()]
    direct = np.mean([fe['Q'][(t3 == d_) & Fp & Fc].mean() - fe['Q'][(t3 == d_) & Fp & ~Fc].mean() for d_ in dd])
    res.append(('签名 3：Q 价差 = 逐日组均差的年均（直接算）', abs(R3[0]['Q_kept_minus_removed'] - direct) <= 1e-12))
    Y = rng.normal(size=(25, 60)) + 0.3 * rng.normal(size=(1, 60))
    Z, ok = zscore_rows(Y)
    C = np.corrcoef(Y)
    pw = float((C.sum() - 25) / (25 * 24))
    res.append(('签名 2：和的方差恒等式 = np.corrcoef 两两相关平均（完整样本）差 %.1e' % abs(mean_corr(Z) - pw), abs(mean_corr(Z) - pw) <= 1e-12))
    mk, pe = rng.normal(size=120), rng.normal(size=120)
    y = 0.001 + 0.5 * mk + 1.5 * pe
    b, e = resid_window(y, mk, pe, np.ones(120, bool))
    res.append(('签名 2：残差回归在无噪数据上取回 β（.5 / 1.5）', abs(b[1] - 0.5) <= 1e-10 and abs(b[2] - 1.5) <= 1e-10 and float(np.max(np.abs(e))) <= 1e-12))
    if not HAVE_NB:
        res.append(('签名 2：numba 不可用', False))
        return res
    nC = 60
    ind = rng.integers(0, 4, nC)
    s3 = rng.integers(0, 3, nC)
    l3 = rng.integers(0, 3, nC)
    lv = level_codes(ind, s3, l3, 'A')
    lvl = lv[0]
    actual = rng.choice(nC, 12, replace=False)
    Zc, _ = zscore_rows(rng.normal(size=(nC, 60)))
    import e6j_random as R
    keys = [R.path_key('E6m.SIG2.selftest', 'G', 'P', 'S', 'K', p) for p in range(8)]
    ORD = priority_order(keys, 1234, np.arange(nC, dtype=np.int64) + 1)
    need = np.bincount(lvl[actual, 0], minlength=len(lv[1])).astype(np.int64)
    out = np.empty(8)
    sh = np.empty(8, np.int64)
    _paths_corr(Zc, lvl, lv[1], lv[2], need, ORD, out, sh)
    rank = np.empty(nC, np.int64)
    rank[ORD[0]] = np.arange(nC)
    pick = np.concatenate([np.flatnonzero(lvl[:, 0] == g_)[np.argsort(rank[lvl[:, 0] == g_], kind='stable')[:need[g_]]] for g_ in range(len(need)) if need[g_]])
    res.append(('签名 2：分层抽样逐格复现真实名单的层 0 计数（无补人），路径相关 = 恒等式', int(sh[0]) == 0 and len(pick) == 12 and abs(out[0] - mean_corr(Zc[pick])) <= 1e-12))
    mu_, sd_, _ = random_corr(Zc, lv, actual, ORD)
    res.append(('签名 2：1,024 条接口（此处 8 条）返回均值与 sd', np.isfinite(mu_) and np.isfinite(sd_)))
    need2 = need.copy()
    g_big = int(np.argmax(need2))
    need2[g_big] += int((lvl[:, 0] == g_big).sum())                      # 该格人不够 → 必须向上层补
    _paths_corr(Zc, lvl, lv[1], lv[2], need2, ORD, out, sh)
    res.append(('签名 2：格内不够时向上层补人并计数（补人 = 缺口 %d、名单人数守恒）' % int(need[g_big]), int(sh[0]) == int(need[g_big]) and np.isfinite(out[0])))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['run', 'selftest'])
    ap.add_argument('--seg', default='')
    ap.add_argument('--out', default='')
    ap.add_argument('--only', default='sig1,sig3,sig2')
    a = ap.parse_args()
    t0 = time.time()
    if a.task == 'selftest':
        res = selftest()
        for nm, ok in res:
            print('%s  %s' % ('PASS' if ok else 'FAIL', nm))
        return 0 if all(ok for _, ok in res) else 1
    import e6m_s_seal as SEAL
    import e6m_s_gate as GT
    SEAL.require('deriv' if a.seg in M.DERIV_SEGS else 'post')
    GT.post_gate(a.seg, 'b4 signatures %s' % a.seg)                    # 直接读收益（SE / S.dr）
    os.makedirs(a.out, exist_ok=True)
    outs, counts = run(a.seg, a.out, tuple(x for x in a.only.split(',') if x))
    M.write_receipt(os.environ.get('E6M_TASK', 'S_b4_sig_%s' % a.seg), outs, status='SUCCEEDED', code=[__file__, M.__file__], counts=counts,
                    wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(seg=a.seg, counts=counts, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
