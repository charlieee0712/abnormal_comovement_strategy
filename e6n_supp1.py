# -*- coding: utf-8 -*-
"""E6n supplement 1（执行端更正，只给数；不改任何已冻结交付表）：四账户支持桥的父账户取错母体。
缺陷：e6n_support 的父账户描述符名 'SUP|<支持键>|Q0|<记忆>|a<α>|H<H>' 不含母体；e6n_decomp.fourway 把六个母体的 accounts_support npz 合进一个字典，
同名父账户被最后读入的母体（M_union3_v2_CVRv5）覆盖 → 其余五个母体 owner 的 P_S（及 support_diff / child_shrink / parent_shrink）取自错的母体。
闭合（native = support + child_shrink − parent_shrink）是代数恒等式，不受影响，所以 A3-5 / N03 没拦住。
更正：按 owner 自己母体的 npz 取 P_S（文件本身是对的），其余口径与 e6n_decomp.fourway 支持段逐字相同。
输出 results/full/supplement_1/support_four_accounts_corrected.csv（四段长表 + 与已交付表的逐行对照列）与 support_main_summary.csv（主母体七对象 n 加权四段）。"""
import os
import sys
import json
import time

import numpy as np
import pandas as pd

import e6n_core as N

ANN = N.ANN
PARENTS6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
MAIN_RX = r'^CORE\|.*\|A4b_CVRv5\|HG10\|H5\|s0\.25\|QGOOD\|a0\.25\|f5\|d\+1$'


def ann(x):
    m = np.isfinite(x)
    return float(np.mean(x[m])) * ANN if m.any() else np.nan


def q0_id(parent, mem, H, alpha):
    return 'ANCHOR|Q0|%s|%s|H%d|s0|ALL|a%g|f5|d+1' % (parent, mem, H, float(alpha))


def main():
    import e6n_gate as GT
    for s in N.POST_SEGS:
        GT.post_gate(s, 'supplement_1')
    t0 = time.time()
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False).set_index('desc_id')
    old = pd.read_csv(N.P('results', 'full', 'support_four_accounts.csv'), keep_default_na=False, na_values=[''], low_memory=False)
    old = old.set_index(['owner_desc_id', 'segment'])
    rows = []
    for seg in N.SEGMENTS:
        nat = {}
        for f in sorted(os.listdir(N.P('accounts', seg))):
            if f.endswith('.npz'):
                with np.load(N.P('accounts', seg, f), allow_pickle=False) as z:
                    for did, x in zip([str(v) for v in z['desc']], z['d_net8']):
                        nat[did] = x
        for form in PARENTS6:
            p = N.P('accounts_support', seg, '%s.npz' % form)
            with np.load(p, allow_pickle=False) as z:
                ds = {str(d): x for d, x in zip(z['desc'], z['d_net8'])}
            for key, cS in ds.items():
                # 键 = 'SUP|<族>|<特征>|<频率>|' + owner（子）或 + 'Q0|<记忆>|a<α>|H<H>'（父）；支持键恒为三段
                parts = key.split('|')
                if parts[0] != 'SUP' or len(parts) < 6 or parts[4] == 'Q0':
                    continue                                                     # 父账户行
                owner = '|'.join(parts[4:])
                if owner not in D.index:
                    continue
                r = D.loc[owner]
                sk = '|'.join(parts[1:4])
                pS = ds.get('SUP|%s|Q0|%s|a%g|H%d' % (sk, r.memory, float(r.outer_alpha), int(r.H)))
                cN, pN = nat.get(owner), nat.get(q0_id(r.parent, r.memory, int(r.H), r.outer_alpha))
                if r.parent != form:
                    raise RuntimeError('owner 母体与文件不符：%s / %s' % (owner, form))
                if any(v is None for v in (cS, pS, cN, pN)):
                    rows.append(dict(owner_desc_id=owner, segment=seg, form=form, support_key=sk, status='ENDPOINT_NOT_COMPUTED'))
                    continue
                ok = np.isfinite(cS) & np.isfinite(pS) & np.isfinite(cN) & np.isfinite(pN)
                nat_, sup, csh, psh = cN - pN, cS - pS, cN - cS, pN - pS
                cl = float(np.max(np.abs((nat_ - (sup + csh - psh))[ok]))) if ok.any() else np.nan
                row = dict(owner_desc_id=owner, segment=seg, form=form, support_key=sk, native_diff_ann_pp=ann(np.where(ok, nat_, np.nan)),
                           support_diff_ann_pp=ann(np.where(ok, sup, np.nan)), child_shrink_ann_pp=ann(np.where(ok, csh, np.nan)),
                           parent_shrink_ann_pp=ann(np.where(ok, psh, np.nan)), n=int(ok.sum()), closure_maxabs=cl, status='COMPUTED')
                if (owner, seg) in old.index:
                    o = old.loc[(owner, seg)]
                    o = o.iloc[0] if isinstance(o, pd.DataFrame) else o
                    for c in ('support_diff_ann_pp', 'child_shrink_ann_pp', 'parent_shrink_ann_pp', 'native_diff_ann_pp'):
                        row['delivered_' + c] = float(pd.to_numeric(o[c], errors='coerce'))
                rows.append(row)
    C = pd.DataFrame(rows)
    od = N.P('results', 'full', 'supplement_1')
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'support_four_accounts_corrected.csv')
    N.atomic_write_csv(p1, N.to_status(C))
    m = C[C.owner_desc_id.str.contains(MAIN_RX, regex=True) & (C.status == 'COMPUTED')].copy()
    m['feature'] = m.owner_desc_id.str.split('|').str[1]
    cols = ['native_diff_ann_pp', 'support_diff_ann_pp', 'child_shrink_ann_pp', 'parent_shrink_ann_pp']
    S = m.groupby('feature').apply(lambda g: pd.Series({**{c: float(np.average(g[c], weights=g['n'])) for c in cols},
                                                        **{'%s_%s' % (c.replace('_ann_pp', ''), s_): float(g[g.segment == s_][c].iloc[0]) if (g.segment == s_).any() else np.nan
                                                           for c in ('support_diff_ann_pp',) for s_ in N.SEGMENTS}}), include_groups=False).reset_index()
    S['status'] = 'COMPUTED'
    p2 = os.path.join(od, 'support_main_summary.csv')
    N.atomic_write_csv(p2, S)
    chg = C[(C.status == 'COMPUTED') & C.get('delivered_support_diff_ann_pp', pd.Series(dtype=float)).notna()]
    nchg = int((np.abs(chg.support_diff_ann_pp - chg.delivered_support_diff_ann_pp) > 1e-9).sum()) if len(chg) else 0
    info = dict(rows=len(C), computed=int((C.status == 'COMPUTED').sum()), rows_changed_vs_delivered=nchg,
                rows_unchanged_vs_delivered=int(len(chg) - nchg), closure_max=float(pd.to_numeric(C.closure_maxabs, errors='coerce').max()),
                wall_s=round(time.time() - t0, 1))
    N.write_receipt('E6n_supp1_support', [p1, p2], code=[__file__], **info)
    print(json.dumps(info, ensure_ascii=False))
    print(S.round(3).to_string())
    return 0


if __name__ == '__main__':
    sys.exit(main())
