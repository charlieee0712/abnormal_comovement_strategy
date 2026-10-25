# -*- coding: utf-8 -*-
"""E6o 源层抽取（brief §1.3 C1 / C4 / C9、§2 S0-0 / S0-2；plan §4.1、§5.1）。只读源（只 import 不改）：
E6n masks/<段>/<母体>.npz（最终名单 final_bits、门名单 gate_bits）→ e6l_env.SegL + e6k_acct.Acct(impact=False).target（源 DEV）
→ e6i 稀疏引擎 SE.pnl（P_SOURCE 逐日 gross / pos / turn / net8，H 5 / 10 / 20）并与 E6n 账户 d_* 逐日比对（SOURCE_REPLICATION）。
同进程另出：
  T1a 状态面板（生产否决合同：CVR_20d 原值 → pool0 当日 log 市值 OLS（源 neutralize_by_mcap 函数体）→ precompute / qcut(rank first, 5) 第 5 组；
    池内有值 = 源分组；池外持仓 = 同一 (α_T, β_T) 残差对 cut_T（第 5 组最小残差）；无值 / 当日无切点 = UNKNOWN）+ 池内有值格与源 drop_mask 逐格比对；
  自然门 U（'NONE|a0.25|Q0' 的 gate_bits；RECONFIRM 用）；主母体 NEXT_RANK 候选序（Struct.order_keys：A4b 末级 T 优先序，排除最终名单与非法域）；
  段内 r0 / bench（全程面板的段内恒等核对用）。
输出 <cache>/source/<段>.npz + source_facts_<段>.json。用法：python3 e6o_source.py --seg 2010-2014 [--forms ...]"""
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6o_core as O

NEXT_TOP = 60


def _unpack(bits, n):
    return np.unpackbits(bits)[:n].astype(bool)


def t1a_panel(seg):
    """生产否决合同在全段列上的 T1a 状态（int8：1 坏 / 0 非坏 / −1 UNKNOWN）与逐日事实。"""
    import comprehensive_factor_diagnosis as C
    import e6j_prod as PR
    ctx = seg.ctx
    data, feats, industry = ctx['data'], ctx['feats'], ctx['industry']
    pool0 = ctx['pool0']
    raw = ctx['specs'][PR.F_CVR]['func'](data, feats, industry).reindex(index=pool0.index, columns=pool0.columns)
    logm = ctx['log_mcap'].reindex(index=pool0.index, columns=pool0.columns)
    drop = PR.drop_mask(ctx['neu_cvr'], pool0, 5)                         # 源否决（剔除集，含无值票）
    R = raw.to_numpy(float)
    X = logm.to_numpy(float)
    P0 = pool0.to_numpy() == 1
    T, Nf = R.shape
    out = np.full((T, Nf), -1, np.int8)
    facts = []
    cache = ctx['neu_cvr']
    dates = list(pool0.index)
    mism = 0
    for u in range(T):
        m = np.flatnonzero(P0[u])
        f = dict(u=u, date=str(dates[u])[:10], n_pool0=int(len(m)), mode='SKIP', n_valued=0, n_g5=0, cut=np.nan, alpha=np.nan, beta=np.nan)
        s = cache.get(dates[u])
        if len(m) < 6 or s is None:
            facts.append(f)
            continue
        df = pd.DataFrame({'f': s}).dropna()
        if len(df) < 15:                                                   # holds：< n_groups×3 → 源当日无保留（全剔）→ 切点不可得
            f['mode'] = 'TOO_FEW'
            facts.append(f)
            continue
        grp = pd.qcut(df['f'].rank(method='first'), 5, labels=range(1, 6))
        g5 = df.index[grp == 5]
        col = {c: j for j, c in enumerate(pool0.columns)}
        g5j = np.array([col[c] for c in g5], np.int64)
        valj = np.array([col[c] for c in df.index], np.int64)
        # 源 neutralize_by_mcap 函数体：成员上 (f, m) 都有限者 ≥ 10 → OLS；否则原值直返
        y, x = R[u, m], X[u, m]
        ok = np.isfinite(y) & np.isfinite(x)
        if ok.sum() >= 10 and np.var(x[ok]) > 0:
            beta = np.cov(x[ok], y[ok], bias=True)[0, 1] / np.var(x[ok])
            alpha = y[ok].mean() - beta * x[ok].mean()
            f['mode'] = 'OLS'
            res_all = R[u] - (alpha + beta * X[u])
        else:
            alpha, beta = 0.0, 0.0
            f['mode'] = 'RAW'
            res_all = R[u].copy()
        # 源残差（缓存值）与本函数重算的一致性
        rs = res_all[valj]
        dmax = float(np.nanmax(np.abs(rs - df['f'].to_numpy()))) if len(valj) else 0.0
        f['resid_recalc_maxabs'] = dmax
        cut = float(np.min(df['f'].to_numpy()[np.isin(valj, g5j)]))
        f.update(n_valued=int(len(valj)), n_g5=int(len(g5j)), cut=cut, alpha=float(alpha), beta=float(beta))
        st = np.full(Nf, -1, np.int8)
        offp = ~P0[u] & np.isfinite(res_all)
        st[offp] = (res_all[offp] >= cut).astype(np.int8)
        st[valj] = 0
        st[g5j] = 1
        out[u] = st
        # 池内有值格 vs 源 drop_mask
        mism += int(((out[u, valj] == 1) != drop[u, valj]).sum())
        f['n_off_pool_defined'] = int(offp.sum())
        facts.append(f)
    return out, pd.DataFrame(facts), mism, [str(c) for c in pool0.columns], [str(d)[:10] for d in dates]


def run(seg_name, forms):
    import e6l_env as V
    import e6k_acct as AC
    import e6n_vars as VR
    t0 = time.time()
    seg = V.SegL(seg_name, state=False)
    acct = AC.Acct(seg, impact=False)
    S, ci = seg.S, seg.ci
    n, T = seg.n, seg.T
    codes = [str(x) for x in S.ccolnames]
    dates = [str(d)[:10] for d in seg.dates]
    O.assert_end_ok(dates[-1], 'source dates %s' % seg_name)
    B = VR.Base(seg_name)
    if not (np.array_equal(B.t, ci.t) and np.array_equal(B.c, ci.c)):
        raise RuntimeError('测量单元与段单元不一致')
    arr = dict(dates=np.array(dates), codes=np.array(codes), cell_t=ci.t.astype(np.int32), cell_c=ci.c.astype(np.int32))
    facts = dict(segment=seg_name, T=T, n_cells=n, Nc=len(codes), forms={})
    rep_rows = []
    for form in forms:
        z = np.load(O.E6N('masks', seg_name, '%s.npz' % form), allow_pickle=False)
        keys = [str(k) for k in z['mask_keys']]
        if int(z['n_cells'][0]) != n:
            raise RuntimeError('名单单元数不一致 %s %s' % (seg_name, form))
        st = seg.struct(form)
        ids = np.asarray(st.ids, np.int64)
        acc = np.load(O.E6N('accounts', seg_name, '%s.npz' % form), allow_pickle=False)
        adesc = [str(x) for x in acc['desc']]
        finals = {}
        for mem in O.MEMS:
            j = keys.index(O.MEMKEY[mem])
            F = _unpack(z['final_bits'][j], n)
            finals[mem] = F
            tg = acct.target(F)
            o = np.lexsort((tg['c'], tg['t']))
            t_, c_, w_ = tg['t'][o].astype(np.int32), tg['c'][o].astype(np.int32), tg['w'][o].astype(np.float64)
            arr['fm_t|%s|%s' % (form, mem)] = t_
            arr['fm_c|%s|%s' % (form, mem)] = c_
            arr['fm_w|%s|%s' % (form, mem)] = w_
            led = seg.SE.pnl(t_.astype(np.int64), c_.astype(np.int64), w_, O.HS, 8.0)
            for H in O.HS:
                g, p, u, nt = led[H]
                for k, v in (('gross', g), ('pos', p), ('turn', u), ('net8', nt)):
                    arr['src_%s|%s|%s|H%d' % (k, form, mem, H)] = v
                did = 'ANCHOR|Q0|%s|%s|H%d|s0|ALL|a0.25|f5|d+1' % (form, mem, H)
                row = dict(segment=seg_name, form=form, memory=mem, H=H, e6n_desc=did, n_targets=int(len(t_)))
                if did in adesc:
                    i = adesc.index(did)
                    for k, v in (('gross', g), ('pos', p), ('turn', u), ('net8', nt)):
                        ref = acc['d_' + k][i]
                        fa, fb = np.isfinite(v), np.isfinite(ref)
                        row['nan_same_' + k] = bool(np.array_equal(fa, fb))
                        row['maxabs_' + k] = float(np.max(np.abs(v[fa & fb] - ref[fa & fb]))) if (fa & fb).any() else 0.0
                    row['status'] = 'COMPUTED'
                else:
                    row['status'] = 'NOT_APPLICABLE'
                rep_rows.append(row)
        # 自然门 U（无记忆 Q0 α .25 的门；gate_bits 在 Struct.ids 域上）
        jn = keys.index(O.MEMKEY['NONE'])
        G = _unpack(z['gate_bits'][jn], len(ids))
        arr['gateU|%s' % form] = np.sort(ids[G]).astype(np.int64)
        facts['forms'][form] = dict(gate_dom=int(len(ids)), gateU_cells=int(G.sum()), finals={m: int(finals[m].sum()) for m in O.MEMS})
        # NEXT_RANK 候选序（只主母体；plan §6.1）
        if form == O.MAIN_FORM:
            K = VR.native_q(np.asarray(st.q0, float), B.kQ, 0.25)
            legal = st.legal()
            col = ci.c.astype(np.int64)
            for mem in O.MEMS:
                k1, k2, k3 = st.order_keys(K, finals[mem])
                cand_t, cand_c, cand_r = [], [], []
                for d in range(T):
                    a, b = seg.off[d], seg.off[d + 1]
                    if a == b:
                        continue
                    sl = np.arange(a, b)
                    ok = legal[sl] & ~finals[mem][sl]
                    sl = sl[ok]
                    if not len(sl):
                        continue
                    o = np.lexsort((col[sl], k3[sl], k2[sl], k1[sl]))[:NEXT_TOP]
                    cand_t.append(np.full(len(o), d, np.int32))
                    cand_c.append(col[sl[o]].astype(np.int32))
                    cand_r.append(np.arange(len(o), dtype=np.int32))
                arr['next_t|%s' % mem] = np.concatenate(cand_t) if cand_t else np.zeros(0, np.int32)
                arr['next_c|%s' % mem] = np.concatenate(cand_c) if cand_c else np.zeros(0, np.int32)
                arr['next_r|%s' % mem] = np.concatenate(cand_r) if cand_r else np.zeros(0, np.int32)
        O.log('source %s %s 完成（%.0f s）' % (seg_name, form, time.time() - t0))
    # T1a（全段列）
    t1a, t1f, mism, fcols, fdates = t1a_panel(seg)
    if fdates != dates:
        raise RuntimeError('T1a 日期轴与段不一致')
    arr['t1a'] = t1a
    arr['t1a_cols'] = np.array(fcols)
    facts['t1a'] = dict(in_pool_valued_mismatch_vs_source_drop=int(mism), days=int(len(t1f)), days_cut=int((t1f['mode'].isin(['OLS', 'RAW'])).sum()),
                        days_skip=int((t1f['mode'] == 'SKIP').sum()), days_too_few=int((t1f['mode'] == 'TOO_FEW').sum()),
                        resid_recalc_maxabs=float(np.nanmax(t1f['resid_recalc_maxabs'].to_numpy(float))) if 'resid_recalc_maxabs' in t1f else float('nan'))
    # 段内市场数组（全程面板恒等核对用）
    arr['seg_r0'] = np.asarray(seg.SE.r0, np.float64)
    arr['seg_bench'] = np.asarray(seg.SE.bench, np.float64)
    od = os.path.join(O.cache_dir(), 'source')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, '%s.npz' % seg_name)
    O.atomic_write_npz(p, **arr)
    pf = os.path.join(od, 't1a_facts_%s.csv' % seg_name)
    O.atomic_write_csv(pf, t1f)
    pr = os.path.join(od, 'replication_%s.csv' % seg_name)
    O.atomic_write_csv(pr, pd.DataFrame(rep_rows))
    facts.update(wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_json(os.path.join(od, 'source_facts_%s.json' % seg_name), facts)
    O.write_receipt('E6o_source_%s' % seg_name, [p, pf, pr], code=[__file__, O.__file__], wall_s=facts['wall_s'], rss_peak_gb=facts['rss_peak_gb'])
    return p, facts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--forms', default=','.join(O.FORMS))
    a = ap.parse_args()
    p, facts = run(a.seg, [f for f in a.forms.split(',') if f])
    print(json.dumps(dict(out=O.rel(p), **{k: v for k, v in facts.items() if k != 'forms'}), ensure_ascii=False, default=str), flush=True)


if __name__ == '__main__':
    main()
