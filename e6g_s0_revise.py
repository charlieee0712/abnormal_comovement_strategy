#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 阶段 0-b: 更正 E6f 遗留的"段内零仓位 0 天"判断 (brief §1.1, E6f_REVIEW §1.3)。

不覆盖 E6f 任何旧文件: 全部新产出写 E6g 的 revisions/E6f_interior_nopos/。
做四件事:
  1. 从 E6e 逐日 pos 账本【重算】每个配置每段的 nopos / warmup_lead / interior_nopos,
     与 all_candidates.csv 已存的全窗口 interior_nopos 对账;
  2. 复现 E6f_REVIEW §1.3 的四组计数 (20,282 / U0-broad / P54 / UA);
  3. 找回 (45,45) / (55,55) / (65,65) 的【确切 cfg_id】与 2010-2014 段的 246 / 67 / 4,
     逐年拆分与最长连跑 —— 不把"某族最大值"与"某条配置"混成一行;
  4. 落 interior_nopos 的逐段标准列, 供 E6g 全表 join。
"""
import os, sys, json, time
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G

E6E = G.E6E_DIR
E6F = G.E6F_DIR
OUT = os.path.join(G.RES, 'revisions', 'E6f_interior_nopos')
os.makedirs(OUT, exist_ok=True)
SEGS = G.SEGMENTS


def lead_run(z):
    """开头连续 True 的长度。"""
    if not z[0]:
        return 0
    nz = np.flatnonzero(~z)
    return int(nz[0]) if len(nz) else int(len(z))


def longest_run(z):
    best = cur = 0
    for v in z:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return int(best)


def main():
    t0 = time.time()
    ac = pd.read_csv(os.path.join(E6F, 'revisions', 'E6e_summary_fix', 'all_candidates.csv'))
    print('all_candidates: %d 行' % len(ac), flush=True)

    rows, per_seg_np = [], {}
    yearly, runs = {}, {}
    for sg in SEGS:
        P = pd.read_parquet(os.path.join(E6E, 'daily', 'daily_pos_%s.parquet' % sg))
        dates = pd.DatetimeIndex(P.index)
        V = P.to_numpy(dtype=float)                 # (T, n_cfg)
        # "无持仓" = pos 恰为 0 或缺失 (基准全 NaN 的段首 19 天也在其中)
        Z = (~np.isfinite(V)) | (V == 0.0)
        T = Z.shape[0]
        lead = np.array([lead_run(Z[:, j]) for j in range(Z.shape[1])], int)
        tot = Z.sum(axis=0).astype(int)
        inter = tot - lead
        per_seg_np[sg] = pd.DataFrame(dict(config_id=P.columns, seg=sg, T=T,
                                           nopos=tot, warmup_lead=lead,
                                           interior_nopos=inter))
        yrs = dates.year.to_numpy()
        yearly[sg] = (Z, yrs, list(P.columns))
        print('  %-10s T=%d  配置 %d  段内零仓位>0: %d  >=50: %d  (%.0fs)'
              % (sg, T, Z.shape[1], int((inter > 0).sum()), int((inter >= 50).sum()),
                 time.time() - t0), flush=True)
        del V, P

    NP = pd.concat(per_seg_np.values(), ignore_index=True)
    wide = NP.pivot(index='config_id', columns='seg', values='interior_nopos')
    wide.columns = ['interior_nopos_%s' % c.split('-')[0] for c in wide.columns]
    wide['interior_nopos_sum4seg'] = wide.sum(axis=1)
    lead_w = NP.pivot(index='config_id', columns='seg', values='warmup_lead')
    lead_w.columns = ['warmup_lead_%s' % c.split('-')[0] for c in lead_w.columns]
    std = wide.join(lead_w).reset_index()
    std.to_csv(os.path.join(OUT, 'interior_nopos_by_config_segment.csv'), index=False)

    # ---- 与 all_candidates 已存列对账 ----
    m = ac[['config_id', 'interior_nopos', 'days_nohold', 'warmup_lead_full',
            'kind', 'core', 'veto', 'family', 'cset']].merge(std, on='config_id', how='left')
    m['recalc_minus_stored'] = m['interior_nopos_sum4seg'] - m['interior_nopos']
    rec = dict(n_config=int(len(m)),
               n_matched=int(m['interior_nopos_sum4seg'].notna().sum()),
               max_abs_diff=float(np.nanmax(np.abs(m['recalc_minus_stored']))),
               n_diff_nonzero=int((m['recalc_minus_stored'].fillna(0) != 0).sum()))
    print('对账 重算 vs all_candidates.interior_nopos: 最大 |差| = %s, 不等条数 %d'
          % (rec['max_abs_diff'], rec['n_diff_nonzero']), flush=True)

    # ---- 复现 REVIEW §1.3 的四组计数 ----
    def cnt(df, col='interior_nopos_sum4seg'):
        return int((df[col] > 0).sum()), int((df[col] >= 50).sum())

    counts = {}
    counts['E6e_all_%d' % len(m)] = cnt(m)
    dom = pd.read_csv(os.path.join(E6F, 'domain_U0.csv'))
    dcol = 'config_id' if 'config_id' in dom.columns else dom.columns[0]
    u0 = m[m.config_id.isin(set(dom[dcol]))]
    counts['U0_broad_%d' % len(u0)] = cnt(u0)
    p54 = m[m.cset.astype(str).str.upper().eq('P54') & m.veto.isna()]
    counts['P54_core_%d' % len(p54)] = cnt(p54)
    # 同时按 stored 列复算一次, 确认两种口径给同一组数
    counts_stored = {'E6e_all': cnt(m, 'interior_nopos'),
                     'U0_broad': cnt(u0, 'interior_nopos'),
                     'P54_core': cnt(p54, 'interior_nopos')}
    print('计数(重算):', counts, flush=True)
    print('计数(已存):', counts_stored, flush=True)

    # ---- (a,b) 两段式核的确切 cfg_id 与逐年拆分 ----
    # 核名从 config_id 解析: 去掉否决段、参数花括号与 #/~ 后缀 (core 列带变体标签, 直接
    # startswith 会漏掉一部分 —— 会把每格 254 个配置误数成 163)
    import re as _re
    m['core_base'] = (m.config_id.astype(str).str.split('|').str[0]
                      .str.replace(r'[{#~].*$', '', regex=True))
    ab_rows = []
    dep_fams = ('KT_dep', 'CT_dep', 'K_gate_TC')
    for ab in ['(45,45)', '(55,55)', '(65,65)', '(30,80)', '(30,90)', '(35,70)',
               '(40,60)', '(50,50)']:
        for fam in dep_fams:
            s2 = m[m.core_base == fam + ab]
            if not len(s2):
                continue
            ab_rows.append(dict(ab=ab, family=fam, n_config=len(s2),
                                interior_2010_max=int(s2['interior_nopos_2010'].max()),
                                interior_2010_min=int(s2['interior_nopos_2010'].min()),
                                interior_2010_nuniq=int(s2['interior_nopos_2010'].nunique()),
                                interior_2015_max=int(s2['interior_nopos_2015'].max()),
                                interior_2019_max=int(s2['interior_nopos_2019'].max()),
                                interior_2024_max=int(s2['interior_nopos_2024'].max()),
                                n_gt0=int((s2['interior_nopos_sum4seg'] > 0).sum()),
                                n_ge50=int((s2['interior_nopos_sum4seg'] >= 50).sum()),
                                example_cfg=str(s2.sort_values('interior_nopos_2010',
                                                               ascending=False).config_id.iloc[0])))
    AB = pd.DataFrame(ab_rows)
    AB.to_csv(os.path.join(OUT, 'dep_core_ab_interior_nopos.csv'), index=False)
    print(AB.to_string(index=False), flush=True)

    # ---- 代表配置的逐年拆分与最长连跑 (2010-2014 段) ----
    Z, yrs, cols = yearly['2010-2014']
    cpos = {c: i for i, c in enumerate(cols)}
    detail = []
    for fam in ('KT_dep', 'CT_dep', 'K_gate_TC'):
        for ab in ['(45,45)', '(55,55)', '(65,65)']:
            s2 = m[m.core_base == fam + ab]
            if not len(s2):
                continue
            # 同一 (族, a, b) 下全部配置的 interior_nopos 完全相同 (由核的 3g 门槛决定,
            # 与否决无关) —— nuniq 列已核; 这里取 config_id 字典序第一条作代表并写明同值条数
            cid = str(sorted(s2.config_id)[0])
            j = cpos[cid]
            z = Z[:, j].copy()
            lead = lead_run(z)
            z[:lead] = False                              # 只看段内
            d = dict(family=fam, ab=ab, representative_config_id=cid,
                     n_config_same_value=int(len(s2)),
                     interior_nopos_nuniq=int(s2['interior_nopos_2010'].nunique()),
                     warmup_lead=lead, interior_nopos=int(z.sum()),
                     days_nohold_total=int(Z[:, j].sum()),
                     interior_if_subtract_19=int(Z[:, j].sum() - 19),
                     longest_interior_run=longest_run(z))
            for y in sorted(set(yrs)):
                d['y%d' % y] = int(z[yrs == y].sum())
            detail.append(d)
    DT = pd.DataFrame(detail)
    DT.to_csv(os.path.join(OUT, 'dep_core_yearly_2010_2014.csv'), index=False)
    print(DT.to_string(index=False), flush=True)

    # ---- 不受影响的核 (REVIEW 断言) ----
    unaffected = {}
    for nm, cid in [('R1', 'KT_dep(50,50)|C:k5'), ('R2', 'KT_mean@30|C:k5+cr5:k10'),
                    ('A06', 'KTC_mean@25|cvr_1d:k10+cr5:k10'), ('A08', 'T@30|C:k5+cr5:k10')]:
        r = m[m.config_id == cid]
        unaffected[nm] = (None if not len(r) else
                          {c: int(r.iloc[0][c]) for c in std.columns if c != 'config_id'})
    ktc = m[m.core.astype(str).str.startswith('KTC_mean')]
    tcore = m[m.core.astype(str).str.startswith('T@')]
    unaffected['KTC_mean_all'] = dict(n=len(ktc),
                                      n_interior_gt0=int((ktc['interior_nopos_sum4seg'] > 0).sum()))
    unaffected['T_core_all'] = dict(n=len(tcore),
                                    n_interior_gt0=int((tcore['interior_nopos_sum4seg'] > 0).sum()))
    print('不受影响核:', json.dumps(unaffected, ensure_ascii=False), flush=True)

    with open(os.path.join(OUT, 'reconcile.json'), 'w') as fh:
        json.dump(dict(reconcile=rec, counts_recalc=counts, counts_stored=counts_stored,
                       unaffected=unaffected, elapsed_s=round(time.time() - t0, 1)),
                  fh, indent=1, ensure_ascii=False)
    print('DONE %.0fs -> %s' % (time.time() - t0, OUT))


if __name__ == '__main__':
    main()
