# -*- coding: utf-8 -*-
"""E6n 四账户支持桥（plan §6.4；brief §1.3-7；附录 A3-5）：父 P = 同 α / H / 记忆的 Q0，子 C = owner；
S_T = 源合法域（门域）∩ owner 本日技术可计算集（新测量有限 ∧ 源 Q 原值有限），**不与 QGOOD 相交**（QGOOD 只是 S 内是否激活新分量的固定标签）。
在 S_T 上父子都重跑：源 Q 中性化 / 排名（pct_src，池 = S_T）→ 生成语法（e6n_vars 同式）→ 门（门分数在 S 外 = +inf；当日保留数 = 源 k_of(|S ∩ 门域|, 源 keep%)）
→ 记忆（e6l_fast.rec_single，同 K_S）→ 下游（StructFast.down：A4b T 在幸存集重估、CVR 否决）→ DEV + 多 H 账本（e6l_fast.AcctFast）。S 外不保留源回退头寸（核：最终名单 ⊆ S）。
旧 K（k0 = 源 pcond 秩）不在 S 上重排（plan 只要求 Q 重中性化 / 排名）。一个进程 = (段, 形态)；输出 accounts_support/<段>/<形态>.npz：
desc（'SUP|<支持键>|<对象>' 与 'SUP|<支持键>|Q0|<记忆>|a<α>'）/ desc_H / dates / d_net8 / d_gross / d_turn / d_pos + 支持事实。读收益：推导段 deriv_ready、后段 post_gate。"""
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6n_core as N
import e6n_vars as VR
import e6n_masks as MK


def pct_pool(vals, pool, lm, off, direction):
    """pct_src 的池版：池 = pool 单元（源 precompute_neutralized_factor 的 filtered_pool）。池外 NaN。"""
    import e6n_rand as RN
    out = np.full(len(vals), np.nan)
    neg = direction == 'lo'
    for d in range(len(off) - 1):
        a, b = int(off[d]), int(off[d + 1])
        pm = pool[a:b]
        if int(pm.sum()) < 6:
            continue
        f = vals[a:b][pm]
        m = lm[a:b][pm]
        both = np.isfinite(f) & np.isfinite(m)
        res = None
        if int(both.sum()) >= 10:
            x, y = m[both], f[both]
            var_x = np.var(x)
            if not var_x < 1e-10:
                beta = np.cov(x, y, bias=True)[0, 1] / var_x
                alpha = y.mean() - beta * x.mean()
                res = np.full(len(f), np.nan)
                res[both] = y - (alpha + beta * x)
        if res is None:
            res = f
        fin = np.isfinite(res)
        if int(fin.sum()) < 6:
            continue
        v = res[fin]
        if neg:
            v = -v
        idx = a + np.flatnonzero(pm)[fin]
        out[idx] = RN.avg_rank_pct(np.ascontiguousarray(v))
    return out


def support_key(variant):
    p = variant.split('|')
    if p[0] == 'FACET':
        return 'FACET|%s|%s' % (p[1], p[4])
    if p[0] == 'RAW':
        return 'RAW|%s|%s' % (p[5][4:], p[4])
    raise ValueError(variant)


def support_cells(B, skey):
    p = skey.split('|')
    fr = int(p[2][1:])
    if p[0] == 'FACET':
        m = B.get(VR.km_name(p[1], fr, 1))
        tech = np.isfinite(m)
    else:
        tech = VR.support_mask(B, p[1], fr)
    return tech & np.isfinite(B.q0raw) & np.isfinite(B.dd)


def run(seg_name, form):
    import e6l_env as V
    import e6l_fast as FA
    import e6n_rand as RN
    import e6i_randoms as IR
    t0 = time.time()
    RN.load_ctx(seg_name, (form,))
    seg, B, lm, off = RN.CTX['seg'], RN.CTX['B'], RN.CTX['lm'], RN.CTX['off']
    st, SF = RN.CTX['structs'][form]
    AF = RN.CTX['AF']
    k0 = np.asarray(st.q0, float)
    inner = st.st
    pct = inner.a if st.kind == 'A4b' else (50 if st.kind == 'union' else inner.s)
    ids = np.asarray(st.ids, np.int64)
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    D = D[(D.random_bound.astype(str) == 'True') & (D.parent == form)]
    R = MK.registry_rows()
    R = R[(R.parent == form) & R.obj.isin(set(D.desc_id))]
    R['skey'] = R.variant.map(support_key)
    out = {k: [] for k in ('net8', 'gross', 'turn', 'pos')}
    desc, dH, facts = [], [], []
    be = np.full(seg.T, 10.0 * st.bunit)
    for skey, g in R.groupby('skey'):
        S = support_cells(B, skey)
        inS = S[ids]
        cnt = np.bincount(seg.ci.t[ids][inS], minlength=seg.T)
        KS = np.array([IR.k_of(int(n), pct) if n else 0 for n in cnt], np.int64)
        kQ_S = pct_pool(B.q0raw, S, lm, off, 'lo')
        cache = {}

        def finals(kf, memory, alpha):
            a = float(alpha)
            Q = np.where(np.isfinite(kf), (1 - a) * k0 + a * kf, k0)[None, :]
            SC = np.ascontiguousarray(np.where(inS[None, :], st.gate_scores(Q), np.inf))
            O, U = FA.order_U(SC, SF.off, KS)
            G = U if memory == 'NONE' else FA.rec_single(SC, O, U, SF.off, KS, SF.cols, be, SF.Nc, memory == 'LAG1_10')
            F = SF.down(G)[0]
            if (F & ~S).any():
                raise RuntimeError('S 外出现持仓：%s' % skey)
            return F

        def emit(name, F, Hs):
            o, nn = AF.run(F, np.asarray(sorted(set(Hs)), np.int64))
            for hi, H in enumerate(sorted(set(Hs))):
                desc.append(name % H if '%d' in name else name)
                dH.append(H)
                out['gross'].append(o[hi, 0])
                out['pos'].append(o[hi, 1])
                out['turn'].append(o[hi, 2])
                out['net8'].append(o[hi, 3])
        # 父：Q0（S 上重排）× 该支持下 owner 用到的 (记忆, α)
        for (mem, al), gg in g.groupby(['memory', 'alpha_eff']):
            Hs = sorted(set(int(h) for h in gg.H))
            F = finals(kQ_S, mem, al)
            emit('SUP|%s|Q0|%s|a%g|H%%d' % (skey, mem, al), F, Hs)
        # 子：owner 在 S 上重排
        for mk, gg in g.groupby('mask_key'):
            v = gg.variant.iloc[0]
            mem, al = gg.memory.iloc[0], float(gg.alpha_eff.iloc[0])
            if v not in cache:
                q = VR.parse(v)
                if q['family'] == 'FACET':
                    raw = B.get('raw_%s_f%d' % (q['feature'], q['fr']))
                    kmS = pct_pool(raw, S, lm, off, 'hi' if q['dir'] > 0 else 'lo')
                    act = B.active_dom(q['app']) & S & np.isfinite(kmS)
                    cache[v] = np.where(act, (1.0 - q['eta']) * kQ_S + q['eta'] * kmS, kQ_S)
                else:
                    act, h, _ = VR.raw_active(B, v)
                    act = act & S
                    raw = B.q0raw.copy()
                    raw[act] = 1.0 / (B.dd[act] + q['lam'] * h[act] + VR.EPS)
                    kn = pct_pool(raw, S, lm, off, 'lo')
                    cache[v] = np.where(act, kn, kQ_S)
            F = finals(cache[v], mem, al)
            Hs = sorted(set(int(h) for h in gg.H))
            o, nn = AF.run(F, np.asarray(Hs, np.int64))
            for obj, H in zip(gg.obj, gg.H):
                hi = Hs.index(int(H))
                desc.append('SUP|%s|%s' % (skey, obj))
                dH.append(int(H))
                out['gross'].append(o[hi, 0])
                out['pos'].append(o[hi, 1])
                out['turn'].append(o[hi, 2])
                out['net8'].append(o[hi, 3])
        facts.append(dict(segment=seg_name, form=form, support_key=skey, s_share_pool0=float(S.mean()), s_share_gate_domain=float(inS.mean()),
                          owners=int(g.obj.nunique()), keep_pct=float(pct)))
    od = N.P('accounts_support', seg_name)
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, '%s.npz' % form)
    N.atomic_write_npz(p, desc=np.array(desc, dtype='U'), desc_H=np.array(dH, np.int64), dates=np.array([str(d)[:10] for d in seg.dates], dtype='U'),
                       **{'d_' + k: np.vstack(v) for k, v in out.items()}, contract_version=np.array([N.CONTRACT_VERSION], dtype='U'))
    pf = os.path.join(od, 'facts_%s.csv' % form)
    N.atomic_write_csv(pf, pd.DataFrame(facts))
    return [p, pf], time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--form', required=True)
    a = ap.parse_args()
    import e6n_gate as GT
    GT.deriv_ready(a.seg, 'support %s %s' % (a.seg, a.form))
    outs, wall = run(a.seg, a.form)
    N.write_receipt('E6n_support_%s_%s' % (a.seg, a.form), outs, code=[__file__], wall_s=round(wall, 1),
                    rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    print(json.dumps(dict(seg=a.seg, form=a.form, wall_s=round(wall, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
