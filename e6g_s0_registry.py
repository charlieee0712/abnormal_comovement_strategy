#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 阶段 0-d: registry/ —— U34 / U35 / NEW40 / 剩余键索引 (brief §2)。

每键给: 源码定义位置与函数体行、窗口/min_periods、单位、PIT、全市场占位、信号重叠、
别名、raw 与处理后 nunique / tie 占比 / 最大 tie 块、稳健重尾量、复权敏感(实测)、
访问史标签、feature_date / label_end 上界、诊断标记。

复权敏感【实测】而不是读公式: 把 open/close/high/low/vwap/lclose 全部乘后复权因子,
量/额/换手率不动, 重算 calc_all_daily_features, 与原值逐格比 + 日内秩比。
地基文件只读, 只是换了输入。
"""
import os, sys, re, json, time, inspect
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G
import e6e_core as K
import e6f_core as F
import comprehensive_factor_diagnosis as C
import features_daily as FD
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import (define_i11_signal, build_observation_pool,
                               apply_hard_constraints)

OUT = os.path.join(G.RES, 'registry')
os.makedirs(OUT, exist_ok=True)
PRICE_KEYS = ('open', 'close', 'high', 'low', 'vwap', 'lclose')


# ---------------------------------------------------------------- 源码定义
def source_index():
    """每个 feats 键 -> (来源文件, 函数, 行号, 窗口/min_periods 文本)。"""
    src = inspect.getsource(FD)
    lines = src.split('\n')
    fns = {}
    for i, ln in enumerate(lines):
        mm = re.match(r'\s*def\s+(\w+)\s*\(', ln)
        if mm:
            fns[mm.group(1)] = i
    # 键名在 features_daily 里出现的位置 (赋值行 out['key'] = ... / 'key':)
    idx = {}
    for k in sorted(set(G.CONFIRMED30) | set(G.NEW40)):
        pat = re.compile(r"""['"]%s['"]\s*[:=\]]""" % re.escape(k))
        hits = [i for i, ln in enumerate(lines) if pat.search(ln)]
        if not hits:
            hits = [i for i, ln in enumerate(lines) if k in ln]
        if not hits:
            idx[k] = dict(file='features_daily.py', lineno=None, snippet=None, windows='')
            continue
        i0 = hits[0]
        fn = None
        for nm, ln0 in fns.items():
            if ln0 <= i0 and (fn is None or ln0 > fns[fn]):
                fn = nm
        body = '\n'.join(lines[max(0, i0 - 2):i0 + 3])
        wins = ','.join(sorted(set(re.findall(r'(?:rolling|window|min_periods)\s*[=(]\s*(\d+)',
                                              '\n'.join(lines[max(0, i0 - 6):i0 + 4])))))
        idx[k] = dict(file='features_daily.py', func=fn, lineno=i0 + 1,
                      snippet=body.strip()[:400], windows=wins)
    # 4 个自定义 spec 在 comprehensive_factor_diagnosis.py
    csrc = inspect.getsource(C).split('\n')
    for k in G.CUSTOM4:
        hits = [i for i, ln in enumerate(csrc) if "'%s'" % k in ln]
        i0 = hits[0] if hits else None
        idx[k] = dict(file='comprehensive_factor_diagnosis.py', func='get_default_factor_specs',
                      lineno=(i0 + 1) if i0 is not None else None,
                      snippet='\n'.join(csrc[i0:i0 + 4]).strip()[:400] if i0 is not None else None,
                      windows='')
    idx[K.FCVR1] = dict(file='e6e_core.py', func='(研究 spec)', lineno=178,
                        snippet="specs[FCVR1] = {'name': FCVR1, "
                                "'func': lambda d, f, i: d['close'] / d['vwap'] - 1}",
                        windows='1')
    return idx


# ---------------------------------------------------------------- 访问史
def access_history():
    """历史是否算过收益相关量: 扫已有 results 的小体积注册/汇总表, 记录命中证据。"""
    roots = '/mnt/sda2/lichenchen/results'
    cand = []
    for d in sorted(os.listdir(roots)):
        p = os.path.join(roots, d)
        if not os.path.isdir(p):
            continue
        for dp, _, fns in os.walk(p):
            if dp.count(os.sep) - p.count(os.sep) > 2:
                continue
            for fn in fns:
                if not (fn.endswith('.csv') or fn.endswith('.json')):
                    continue
                fp = os.path.join(dp, fn)
                try:
                    if os.path.getsize(fp) > 8 * 1024 * 1024:
                        continue
                except OSError:
                    continue
                cand.append(fp)
    keys = sorted(set(G.U35) | set(G.NEW40))
    hits = {k: [] for k in keys}
    for fp in cand:
        try:
            with open(fp, 'r', errors='ignore') as fh:
                txt = fh.read()
        except Exception:
            continue
        short = fp.replace(roots + '/', '')
        for k in keys:
            if k in txt and len(hits[k]) < 8:
                hits[k].append(short)
    return hits, len(cand)


def label_of(k, hits):
    """七种访问史标签 (plan §2K1)。first_read != 独立 OOS。"""
    if k in G.SIGNAL_TRUNCATED:
        base = 'signal_component_truncated'
    else:
        base = None
    if k in K.FACTORS:
        lab = 'previous_outcome_seen'
    elif G.CANON_FORMULA.get(k) and any(G.CANON_FORMULA.get(n) == G.CANON_FORMULA[k]
                                        and n in K.FACTORS for n in G.CANON_FORMULA):
        lab = 'same_formula_alias'
    elif hits:
        lab = 'related_information'
    elif k in G.DIAGNOSTIC_ONLY:
        lab = 'feature_only_seen'
    else:
        lab = 'new_outcome_first_read_in_this_project'
    return lab, base


# ---------------------------------------------------------------- 逐段统计
def tie_stats(v):
    """v = 1 维有值数组。返回 (nunique, tie 占比, 最大 tie 块)。"""
    n = len(v)
    if n == 0:
        return 0, np.nan, 0
    u, c = np.unique(v, return_counts=True)
    return int(len(u)), float((c[c > 1].sum()) / n), int(c.max())


def heavy_tail(v):
    if len(v) == 0:
        return dict(q99_over_mad=np.nan, med=np.nan, mad=np.nan, maxabs=np.nan)
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med)))
    q99 = float(np.quantile(np.abs(v - med), 0.99))
    return dict(q99_over_mad=(q99 / mad if mad > 0 else np.nan), med=med, mad=mad,
                maxabs=float(np.max(np.abs(v))))


def run(pname):
    t0 = time.time()
    ps, pe = PERIODS[pname]
    data = G.F.guarded_load(ps, pe)
    feats = C.calc_all_daily_features(data)
    close = data['close']
    base_pool = get_base_pool(data)
    signal = define_i11_signal(feats, base_pool)
    obs = build_observation_pool(signal, obs_window=5)
    pool0 = apply_hard_constraints(obs, data, feats, min_mcap=0)
    p0 = (pool0.values == 1)
    log_mcap = C.compute_log_mcap(data.get('mcap'))
    lm = log_mcap.reindex(index=close.index, columns=close.columns).values

    # 复权对照: 只动价格, 量/额/换手率不动
    adjf = C.adjust_factor(data)
    dadj = dict(data)
    for kk in PRICE_KEYS:
        if kk in dadj and dadj[kk] is not None:
            dadj[kk] = dadj[kk] * adjf
    feats_adj = C.calc_all_daily_features(dadj)

    rows = []
    allkeys = sorted(set(feats.keys()) | {K.FCVR1})
    for k in allkeys:
        if k == K.FCVR1:
            fr = (data['close'] / data['vwap']).replace([np.inf, -np.inf], np.nan) - 1
            fa = ((dadj['close'] / dadj['vwap']).replace([np.inf, -np.inf], np.nan) - 1)
        else:
            fr, fa = feats[k], feats_adj[k]
        A = fr.reindex(index=close.index, columns=close.columns).values.astype(float)
        B = fa.reindex(index=close.index, columns=close.columns).values.astype(float)
        m = p0 & np.isfinite(A)
        v = A[m]
        nu, tf_, mb = tie_stats(v)
        ht = heavy_tail(v)
        # OLS leverage vs log 市值 (池内, 逐日最大 h_ii 的中位)
        lev = []
        for t in range(0, A.shape[0], 7):
            sel = p0[t] & np.isfinite(A[t]) & np.isfinite(lm[t])
            n = int(sel.sum())
            if n < 10:
                continue
            x = lm[t, sel]
            xc = x - x.mean()
            ss = float((xc ** 2).sum())
            if ss <= 0:
                continue
            lev.append(float((1.0 / n + (xc ** 2) / ss).max()))
        # 复权敏感 (实测)
        both = p0 & np.isfinite(A) & np.isfinite(B)
        if both.sum() == 0:
            adj_cls, adj_max, adj_rank = 'no_overlap', np.nan, np.nan
        else:
            d = np.abs(A[both] - B[both])
            sc = np.maximum(1e-12, np.abs(A[both]))
            rel = float(np.max(d / sc))
            adj_max = float(np.max(d))
            # 日内秩是否变 (只看有效票 >= 10 的日子, 抽样)
            chg = tot = 0
            for t in range(0, A.shape[0], 11):
                sel = p0[t] & np.isfinite(A[t]) & np.isfinite(B[t])
                if sel.sum() < 10:
                    continue
                ra = pd.Series(A[t, sel]).rank().to_numpy()
                rb = pd.Series(B[t, sel]).rank().to_numpy()
                tot += 1
                chg += int(not np.array_equal(ra, rb))
            adj_rank = (chg / tot) if tot else np.nan
            adj_cls = ('identical_under_adjustment' if rel < 1e-9 else
                       ('rank_invariant' if (adj_rank == 0) else 'changes_under_adjustment'))
        rows.append(dict(
            segment=pname, key=k, key_class=G.key_class(k),
            new40_blood=G.has_new40_blood(k),
            n_pool_cells=int(p0.sum()), n_valid=int(m.sum()),
            missing_rate=float(1.0 - m.sum() / max(1, p0.sum())),
            inf_rate=float(np.mean(~np.isfinite(A[p0]) & ~np.isnan(A[p0]))),
            nunique_raw=nu, tie_frac_raw=tf_, max_tie_block_raw=mb,
            q99_over_mad=ht['q99_over_mad'], median=ht['med'], mad=ht['mad'],
            maxabs=ht['maxabs'],
            ols_leverage_max_median=(float(np.median(lev)) if lev else np.nan),
            adj_class=adj_cls, adj_max_abs_diff=adj_max, adj_rank_change_frac=adj_rank,
        ))
        del A, B
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, 'key_stats_%s.csv' % pname), index=False)
    print('[%s] %d 键 %.0fs' % (pname, len(df), time.time() - t0), flush=True)
    return df


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'meta':
        si = source_index()
        hits, ncand = access_history()
        meta = []
        for k in sorted(set(G.U35) | set(G.NEW40)):
            lab, extra = label_of(k, hits.get(k, []))
            s = si.get(k, {})
            meta.append(dict(
                key=k, key_class=G.key_class(k), new40_blood=G.has_new40_blood(k),
                source_file=s.get('file'), source_func=s.get('func'), source_line=s.get('lineno'),
                windows_in_source=s.get('windows'), source_snippet=s.get('snippet'),
                market_wide_placeholder=k in G.MARKET_WIDE_PLACEHOLDER,
                signal_overlap=k in G.SIGNAL_TRUNCATED,
                diagnostic_only=k in G.DIAGNOSTIC_ONLY,
                formula_alias=G.CANON_FORMULA.get(k, ''),
                access_history_label=lab, extra_label=extra or '',
                access_history_evidence='; '.join(hits.get(k, [])[:5]),
                feature_date_max=G.FROZEN_END,
                label_end_max=(G.NEW40_LABEL_END if G.has_new40_blood(k) else '2026-03-27'),
                allowed_segments=('|'.join(G.DERIV_SEGS) if G.has_new40_blood(k)
                                  else '|'.join(G.SEGMENTS)),
            ))
        M = pd.DataFrame(meta)
        M.to_csv(os.path.join(OUT, 'key_registry_meta.csv'), index=False)
        json.dump(dict(n_scanned_files=ncand, n_keys=len(M)),
                  open(os.path.join(OUT, 'key_registry_meta.json'), 'w'), indent=1)
        print(M.groupby(['key_class', 'access_history_label']).size().to_string())
        print('meta 写好: %d 键, 扫了 %d 个文件' % (len(M), ncand))
    else:
        run(what)
