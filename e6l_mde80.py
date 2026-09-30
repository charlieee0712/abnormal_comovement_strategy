# -*- coding: utf-8 -*-
"""E6l 推导段配对 MDE80 表（brief §1.4 Stage A 末项 / ⑬；plan §11.1）：推导段确定性账户算完后、后段之前。
只算日差的 HAC(H) 标准误（不输出也不读取任何均值）：每条比较的日差 = Σ 系数 × net8（全部端点同日有限的日子），
se_H = √V（Bartlett lag = H；u_t = m_t(D_t − μ)，缺日 u = 0；e6j_stats.hac_se 同式的批量版），MDE80 = 2.80 × se_H（年化百分点）。
范围：comparison_manifest 的 SOURCE_RAW 两端 / 四端比较 + 附属视图（KERNEL_DOSE / 支持桥 / STRICT250）；MATCH_CAP 与真实 − 随机视图不在此表。
输出 results/deriv/paired_mde80_deriv.csv；results/deriv/cards_t13_deriv_E6l.csv（16 卡 ⑬ 可判定性：绑定比较 MDE80 的分位与机械标签；
标签只描述"配对差需多大才 80% 可辨"，不改任何预测、不作门）。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import time

import numpy as np
import pandas as pd

import e6l_core as L

VIEWS = ('SOURCE_RAW', 'DOSE_MATCHED_MEAN_RMS', 'COMMON_SUPPORT', 'Q0_MASKED_TO_CHILD_SUPPORT', 'STRICT250')


def load_net8(pname):
    d = {}
    for f in sorted(glob.glob(L.P('accounts', pname, '*.npz'))):
        if os.path.basename(f).startswith('weights_'):
            continue
        z = L.npz(f, keys=['desc', 'd_net8'])
        for did, x in zip([str(v) for v in z['desc']], z['d_net8']):
            d[did] = x
    return d


def hac_batch(Dm, L_):
    """Dm (m, T) 含 NaN → (se 日单位, n)；与 e6j_stats.hac_se 同式。"""
    I = np.isfinite(Dm)
    n = I.sum(1)
    with np.errstate(all='ignore'):
        mu = np.where(n > 0, np.nansum(Dm, 1) / np.maximum(n, 1), np.nan)
        u = np.where(I, Dm - mu[:, None], 0.0)
    s = np.einsum('ij,ij->i', u, u)
    T = Dm.shape[1]
    for l in range(1, int(L_) + 1):
        if l >= T:
            break
        s = s + 2.0 * (1.0 - l / (L_ + 1.0)) * np.einsum('ij,ij->i', u[:, l:], u[:, :-l])
    with np.errstate(all='ignore'):
        v = s / (n.astype(float) ** 2)
        se = np.where((n >= 3) & (v > 0), np.sqrt(v), np.nan)
    return se, n


ACC = ('KD', 'CSC', 'CSP', 'MQ0', 'S250', 'ICL', 'ICLPAR', 'BCP', 'BCPPAR')


def split_terms(terms):
    """'id1|id2|…'（登记 ID 5 段；附属 ID 6 段，首段为附属标记）→ [id, …]。"""
    tok = terms.split('|')
    out, i = [], 0
    while i < len(tok):
        k = 6 if tok[i] in ACC else 5
        out.append('|'.join(tok[i:i + k]))
        i += k
    return out


def main():
    t0 = time.time()
    CM = L.read_csv_keep(L.P('registry', 'comparison_manifest_E6l.csv'))
    CM = CM[CM.view.isin(VIEWS)].copy()
    CM['tl'] = CM.terms.map(split_terms)
    CM['H'] = [int(t[0].split('|')[4 if t[0].split('|')[0] in ACC else 3][1:]) for t in CM.tl]
    out = []
    for pname in L.DERIV_SEGS:
        L.deriv_only(pname, 'MDE80')
        d = load_net8(pname)
        for H, g in CM.groupby('H'):
            rows, keep = [], []
            for r in g.itertuples():
                tl = r.tl
                coefs = [int(c) for c in r.coef.split('|')]
                if len(tl) != len(coefs) or any(t not in d for t in tl):
                    continue
                x = np.zeros(len(d[tl[0]]))
                for c, t in zip(coefs, tl):
                    x = x + c * d[t]
                rows.append(x)
                keep.append(r)
            if not rows:
                continue
            Dm = np.vstack(rows)
            se, n = hac_batch(Dm, H)
            for r, s_, n_ in zip(keep, se, n):
                out.append(dict(cmp_id=r.cmp_id, kind=r.kind, view=r.view, left_id=r.left_id, right_id=r.right_id, H=int(H), segment=pname,
                                se_H_ann_pp=float(s_) * L.ANN, mde80_ann_pp=2.80 * float(s_) * L.ANN, n_days=int(n_), query_id=r.query_id))
        print('%s：%d 条（累计）%.0fs' % (pname, len(out), time.time() - t0), flush=True)
    M = pd.DataFrame(out)
    od = L.P('results', 'deriv')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'paired_mde80_deriv.csv')
    L.atomic_write_csv(p1, M)
    Cb = L.read_csv_keep(L.P('registry', 'cards_stageB_E6l.csv'))
    rows = []
    for r in Cb.itertuples():
        qs = r.queries.split('|')
        for s in L.DERIV_SEGS:
            v = M[(M.segment == s) & M.query_id.isin(qs)].mde80_ann_pp.values
            v = v[np.isfinite(v)]
            if len(v):
                med = float(np.median(v))
                lab = ('MDE80 中位 ≤ .10：.10 级配对差可 80% 分辨' if med <= 0.10 else
                       ('.10 < MDE80 中位 ≤ .30：只可分辨 .30 级；.05–.10 级机制差只可判符号' if med <= 0.30 else
                        'MDE80 中位 > .30：首看，只记录'))
            else:
                med, lab = np.nan, 'UNDEFINED（无绑定配对比较 / 方法卡）'
            rows.append(dict(card=r.card, segment=s, n_comparisons=int(len(v)), mde80_p10_ann_pp=float(np.percentile(v, 10)) if len(v) else np.nan,
                             mde80_median_ann_pp=med, mde80_p90_ann_pp=float(np.percentile(v, 90)) if len(v) else np.nan, t13_label=lab))
    T13 = pd.DataFrame(rows)
    p2 = os.path.join(od, 'cards_t13_deriv_E6l.csv')
    L.atomic_write_csv(p2, T13)
    L.write_receipt(L.next_rerun('mde80_deriv'), [p1, p2], 'SUCCEEDED', n_rows=len(M), wall_s=round(time.time() - t0, 1))
    print(T13.to_string(max_colwidth=60), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
