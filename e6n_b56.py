# -*- coding: utf-8 -*-
"""E6n B5 / B6（plan §9.3 / §9.4；brief §1.3-13；卡 H14 / H15 旁支、carried）。
  b5    身份去重：E6l 17 + E6m 21 个按各自政策表"通过"的对象 → 完整键 parent / measurement / operator / alpha / H / support / init / cost / source_hash，
        三级等价：CODE_EQUIVALENT（同定义）/ HISTORY_PATH_SAME（逐日 net8 序列逐位相同）/ SUMMARY_CLOSE（只 FULL 相近）；不相加成独立候选；
        每对象带"六条资格"与"相对当前 Q 前沿增量"（E6n 前沿表）。LEAK_BRIDGE w .02 / .05：E6m 已冻结的越界合同原样复现（E6m 账户 npz sha = 副本包清单后
        取其逐段 D 与配对 PROTECTED），本轮不新造同名算子。E7：只写未激活候选协议页（reports/E6n_E7_prep.md）。→ results/full/b5/*.csv
  b6    E6m 固定 W1 / W2 窗口（stage0/c4_data_windows.csv 原件）对当前固定锚 Q0|A4b_CVRv5|α.25|HG10|H5 与主 72 新行的贡献：固定总日数分母贡献、窗内条件均值、
        窗外条件均值、闭合；新分钟关系按年 / 制度（SH 改革前后 / SZ 由 B1-0 regimes）/ 市场状态（E6m 状态缓存市场级 vol_state / act_state 三态；个股 trend 不拆账户级日收益）展示 → results/full/b6/*.csv
后段数据：post_gate。"""
import os
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

RES = N.RES_ROOT
E6M_W = os.path.join(RES, '20261005_0556_E6m', 'E6m_stageN_20261005_0556')
E6L = os.path.join(RES, '20260930_1141_E6l_time_memory_stage')
FRONT = 'ANCHOR|Q0|A4b_CVRv5|HG10|H5|s0|ALL|a0.25|f5|d+1'


def b5():
    out = N.P('results', 'full', 'b5')
    os.makedirs(out, exist_ok=True)
    pe = pd.read_csv(os.path.join(E6M_W, 'results', 'full', 'policy_E6m.csv'), keep_default_na=False, na_values=[''])
    pl = pd.read_csv(os.path.join(E6L, 'results', 'full', 'policy_E6l.csv'), keep_default_na=False, na_values=[''])
    # plan §9.3"E6l 17 和 E6m 21"= 两轮各自主展示集合里按 PROPOSED_PORT3_T × FULL 通过的对象（E6m is_primary72；E6l primary72），不是政策表全部通过行
    ce = pe[(pe.policy_result.astype(str) == '通过') & (pe.is_primary72.astype(str) == 'True')].copy()
    rl = [c for c in pl.columns if c.startswith('policy_') and 'PORT3_T' in c and c.endswith('FULL')]
    cl = pl[(pl[rl[0]].astype(str) == '通过') & (pl.primary72.astype(str) == 'True')].copy() if rl else pl.iloc[:0].copy()
    count_check = 'E6m %d（预期 21）/ E6l %d（预期 17）' % (len(ce), len(cl))
    if (len(ce), len(cl)) != (21, 17):
        N.log('B5 计数与 plan §9.3 不符：%s' % count_check)
    six = ('c_d10', 'd_ok', 'f_d10', 'e_cap_FULL', 'e_rand', 'positive_FULL', 'size_PROPOSED_PORT3_T')
    rows = []
    for r in ce.itertuples():
        g = r._asdict()
        rows.append(dict(source='E6m', desc_id=r.desc_id, parent=r.parent, measurement=r.measurement, operator=r.operator, alpha=r.alpha, memory=r.memory, H=int(r.H),
                         FULL_ann_pp=float(r.FULL), support=str(r.desc_id).split('|')[7],
                         init='SEGMENT_RESET_19D_WARMUP', cost='8BP', **{'elig_' + k: g.get(k, 'NOT_APPLICABLE') for k in six}))
    for r in cl.itertuples():
        g = r._asdict()
        # E6l 记忆族记法 → E6m 记法：NATIVE = LINEAR × 无记忆；HG10 / LAG1_10 / DECAY5_10 = LINEAR × 该记忆
        rows.append(dict(source='E6l', desc_id=r.desc_id, parent=r.mother, measurement=r.meas, operator='LINEAR', alpha=float(r.alpha),
                         memory='NONE' if r.op == 'NATIVE' else r.op, H=int(r.H), FULL_ann_pp=float(r.FULL), support='SOURCE', init='SEGMENT_RESET_19D_WARMUP', cost='8BP',
                         **{'elig_' + k: g.get(k, 'NOT_APPLICABLE') for k in six}))
    Dd = pd.DataFrame(rows)

    # 逐日 net8 序列指纹（两轮各取自己的账户 npz；四段逐段 sha 前 16 位）
    def fingerprints(root, ids):
        out = {}
        for s in N.SEGMENTS:
            for f in sorted(glob.glob(os.path.join(root, 'accounts', s, '*.npz'))):
                if os.path.basename(f).startswith('weights_'):
                    continue
                with np.load(f, allow_pickle=False) as z:
                    if 'desc' not in z.files or 'd_net8' not in z.files:
                        continue
                    ds = [str(v) for v in z['desc']]
                    hit = [i for i, d in enumerate(ds) if d in ids]
                    if hit:
                        X = z['d_net8']
                        for i in hit:
                            out.setdefault(ds[i], {})[s] = N.sha_bytes(np.ascontiguousarray(X[i]).tobytes())[:16]
        return out
    fp = fingerprints(E6M_W, set(Dd.desc_id[Dd.source == 'E6m']))
    fp.update(fingerprints(E6L, set(Dd.desc_id[Dd.source == 'E6l'])))
    Dd['source_hash'] = [('|'.join(fp[d][s] for s in N.SEGMENTS) if d in fp and len(fp[d]) == len(N.SEGMENTS) else 'SOURCE_WAIT（%s 账户缺段）' % src)
                         for d, src in zip(Dd.desc_id, Dd.source)]
    key = ['parent', 'measurement', 'operator', 'alpha', 'memory', 'H', 'support', 'init', 'cost']
    Dd['code_key'] = Dd[key].astype(str).agg('|'.join, axis=1)
    Dd['code_group'] = Dd.groupby('code_key').ngroup()
    hv = ~Dd.source_hash.str.startswith('SOURCE_WAIT')
    Dd['history_group'] = np.where(hv, Dd.groupby('source_hash').ngroup(), -1)
    cross = lambda col: Dd.groupby(col).source.transform('nunique') > 1
    Dd['equivalence'] = np.where(Dd.duplicated('code_key', keep=False), 'CODE_EQUIVALENT',
                                 np.where(hv & Dd.duplicated('source_hash', keep=False), 'HISTORY_PATH_SAME', 'DISTINCT'))
    Dd['equivalent_across_rounds'] = cross('code_key') | (hv & cross('source_hash'))
    # 仅汇总相近：同母体 / 测量 / 记忆 / H（HG 与 LAG 不并），他轮对象 |ΔFULL| ≤ .01 而代码键与历史指纹都不同
    sc = []
    for r in Dd.itertuples():
        o = Dd[(Dd.source != r.source) & (Dd.parent == r.parent) & (Dd.measurement == r.measurement) & (Dd.memory == r.memory) & (Dd.H == r.H)]
        sc.append(bool(r.equivalence == 'DISTINCT' and len(o) and (np.abs(o.FULL_ann_pp - r.FULL_ann_pp) <= .01).any()))
    Dd.loc[np.array(sc, bool), 'equivalence'] = 'SUMMARY_CLOSE'
    # 独立候选组：代码等价或历史路径相同连成一组
    par = list(range(len(Dd)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for col in ('code_key', 'source_hash'):
        for _, idx in Dd[hv | (col == 'code_key')].groupby(col).groups.items():
            idx = list(idx)
            for j in idx[1:]:
                par[find(j)] = find(idx[0])
    Dd['dedupe_group'] = [find(i) for i in range(len(Dd))]
    Dd['dedupe_group'] = Dd.dedupe_group.rank(method='dense').astype(int)
    Dd['n_independent_groups'] = int(Dd.dedupe_group.nunique())
    P = pd.read_csv(N.P('results', 'full', 'policy_E6n.csv'), keep_default_na=False, na_values=[''], low_memory=False).set_index('desc_id')
    ffull = float(P.at[FRONT, 'FULL_ann_pp']) if FRONT in P.index else np.nan
    Dd['frontier_desc_id'] = FRONT
    Dd['d_vs_frontier_FULL_ann_pp'] = np.where(Dd.H == 5, Dd.FULL_ann_pp - ffull, np.nan)
    Dd['count_check'] = count_check
    Dd['status'] = 'COMPUTED'
    p1 = os.path.join(out, 'b5_dedupe.csv')
    N.atomic_write_csv(p1, N.to_status(Dd))
    # LEAK_BRIDGE（E6m 冻结合同原样复现）
    De = pd.read_csv(os.path.join(E6M_W, 'registry', 'descriptors_E6m.csv'), keep_default_na=False)
    lk = De[De.block == 'LEAK_BRIDGE']
    pol = pe.set_index('desc_id')
    rep = {}
    for f in glob.glob(os.path.join(E6M_W, 'replica', 'replica_manifest_P1_LEDGER_final.json')):
        for r in json.load(open(f, encoding='utf-8')).get('files', []):
            rep[r['path']] = r['sha256']
    lrows = []
    for r in lk.itertuples():
        x = pol.loc[r.desc_id] if r.desc_id in pol.index else None
        prot = r.desc_id.replace('LEAK', 'PROTECTED') if 'LEAK' in r.desc_id else 'NOT_APPLICABLE'
        lrows.append(dict(desc_id=r.desc_id, parent=r.parent, operator=r.operator, param=r.param, alpha=r.alpha, memory=r.memory, H=r.H,
                          FULL_ann_pp=float(x.FULL) if x is not None else np.nan, **({('D_%s_ann_pp' % s): float(x['D_%s' % s]) for s in N.SEGMENTS} if x is not None else {}),
                          policy_result=str(x.policy_result) if x is not None else 'NOT_APPLICABLE', paired_protected=prot,
                          source='E6m 已冻结结果原样复现（账户 sha = E6m P1 副本清单；本轮不新造同名算子）', status='REPRODUCED_FROM_E6M_FROZEN' if x is not None else 'SOURCE_WAIT'))
    p2 = os.path.join(out, 'b5_leak_bridge.csv')
    N.atomic_write_csv(p2, N.to_status(pd.DataFrame(lrows)))
    ok = 0
    for s in N.SEGMENTS:
        for f in glob.glob(os.path.join(E6M_W, 'accounts', s, '*.npz')):
            rel = os.path.relpath(f, E6M_W)
            ok += (rep.get(rel) == N.sha_file(f))
    e7 = ['# E6n E7 准备页（未激活候选协议；plan §9.3；本轮不读 E7 / 2026-03-27 之后任何行情，含分钟）', '',
          '本页只登记"若用户将来授权一次性 E7"时的对象、读取范围、诊断与再设计暴露记法；**不构成授权、不读取样本、预热不跨 2026-03-27**。', '',
          '| 项 | 内容 |', '|---|---|',
          '| 对象 | 本轮政策表 `policy_E6n.csv` 中 policy_result = 通过 且实质改善表相对当前前沿 FULL > 0 的对象（以交付时机器表为准；本页不预选） |',
          '| 一次读取范围 | 2026-03-30 起由用户指定的连续窗口；分钟分区同样只在授权后由读取接口放开（当前接口硬截断） |',
          '| 诊断 | 段 D、FULL 不适用（单窗）、同资本、费用、随机（LEGACY 合同）、与前沿差；不改成员 / 方向 / 频率 |',
          '| 再设计暴露记法 | 任何依据 E7 结果的再设计 = 新 idea（G 账本）+ 已见量登记；E7 只读一次 |',
          '| 当前状态 | NOT_AUTHORIZED（E7 HOLD） |']
    p3 = N.P('reports', 'E6n_E7_prep.md')
    os.makedirs(os.path.dirname(p3), exist_ok=True)
    N.atomic_write_text(p3, '\n'.join(e7) + '\n')
    return [p1, p2, p3], dict(dedupe=len(Dd), independent_groups=int(Dd.dedupe_group.nunique()), equivalence=Dd.equivalence.value_counts().to_dict(),
                              count_check=count_check, leak=len(lrows), e6m_account_sha_ok=ok)


def b6():
    import e6n_stats as SS
    out = N.P('results', 'full', 'b6')
    os.makedirs(out, exist_ok=True)
    W = pd.read_csv(os.path.join(E6M_W, 'stage0', 'c4_data_windows.csv'), keep_default_na=False)
    win = {('W1_20240115_20240223' if r.window == 'W1' else 'W2_20240924_PM20'): (str(r.first)[:10], str(r.last)[:10]) for r in W.itertuples()}
    seg = '2024-2026'
    d, t, d2t, dH, dates = SS.load(seg)
    ds = np.array([str(x)[:10] for x in dates])
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    objs = list(dict.fromkeys([FRONT] + list(D.desc_id[(D.is_primary72.astype(str) == 'True')])))   # 前沿锚本身也在主 72 里：去重，不重复出行
    rows = []
    for o in objs:
        if o not in d:
            continue
        par = 'ANCHOR|ORIGINAL|%s|NONE|H%d|s0|ALL|a0|f5|d+1' % (o.split('|')[2], int(o.split('|')[4][1:]))
        if par not in d:
            continue
        x = d[o]['net8'] - d[par]['net8']
        fin = np.isfinite(x)
        n_all = int(fin.sum())
        Dfull = float(np.mean(x[fin])) * N.ANN
        for wn, (a, b) in win.items():
            inw = (ds >= a) & (ds <= b) & fin
            out_ = fin & ~inw
            cin = float(x[inw].sum() / n_all) * N.ANN
            cout = float(x[out_].sum() / n_all) * N.ANN
            rows.append(dict(object=o, parent=par, window=wn, D_full_ann_pp=Dfull, contrib_in_ann_pp=cin, contrib_out_ann_pp=cout,
                             cond_mean_in_ann_pp=float(np.mean(x[inw])) * N.ANN if inw.any() else np.nan,
                             cond_mean_excl_ann_pp=float(np.mean(x[out_])) * N.ANN if out_.any() else np.nan, closure=abs(Dfull - cin - cout), n_in=int(inw.sum()),
                             n_all=n_all, status='COMPUTED'))
    p1 = os.path.join(out, 'b6_event_contrib.csv')
    N.atomic_write_csv(p1, N.to_status(pd.DataFrame(rows)))
    # 年度 / 市场状态（四段；主 72 新行 vs 原父 与 vs 同记忆 Q0）
    zs = np.load(os.path.join(E6M_W, 'stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)
    sdate = {str(x)[:10]: i for i, x in enumerate(zs['dates'])}
    # E6m 状态缓存的市场级三态 = vol_state / act_state（日 × 1；-1 = 预热 / 无参照）；trend 是日 × 股票（个股状态），账户级日收益不能按它拆 → 不在此表
    keys = [k for k in ('vol_state', 'act_state') if k in zs.files and zs[k].ndim == 1]
    if not keys:
        raise RuntimeError('E6m 状态缓存缺市场级三态键（vol_state / act_state）')
    yrows = []
    for s in N.SEGMENTS:
        d, t, d2t, dH, dates = SS.load(s)
        ds = np.array([str(x)[:10] for x in dates])
        yr = np.array([int(x[:4]) for x in ds])
        for o in D.desc_id[(D.is_primary72.astype(str) == 'True')]:
            if o not in d:
                continue
            p = o.split('|')
            par = 'ANCHOR|ORIGINAL|%s|NONE|H%d|s0|ALL|a0|f5|d+1' % (p[2], int(p[4][1:]))
            q0 = 'ANCHOR|Q0|%s|%s|H%d|s0|ALL|a0.25|f5|d+1' % (p[2], p[3], int(p[4][1:]))
            for vs, ref in (('VS_PARENT', par), ('VS_SAME_MEMORY_Q0', q0)):
                if ref not in d or ref == o:
                    continue
                x = d[o]['net8'] - d[ref]['net8']
                for y in np.unique(yr):
                    m = (yr == y) & np.isfinite(x)
                    yrows.append(dict(object=o, versus=vs, segment=s, split='YEAR', cell=str(y), D_ann_pp=float(np.mean(x[m])) * N.ANN if m.any() else np.nan,
                                      n=int(m.sum()), status='COMPUTED' if m.any() else 'NOT_COMPUTABLE'))
                for k in keys:
                    sv = np.array([zs[k][sdate[x]] if (x in sdate and zs[k].ndim == 1) else -9 for x in ds])
                    for c in np.unique(sv):
                        m = (sv == c) & np.isfinite(x)
                        yrows.append(dict(object=o, versus=vs, segment=s, split='STATE_%s' % k, cell=str(c), D_ann_pp=float(np.mean(x[m])) * N.ANN if m.any() else np.nan,
                                          n=int(m.sum()), status='COMPUTED' if m.any() else 'NOT_COMPUTABLE'))
    p2 = os.path.join(out, 'b6_year_state.csv')
    N.atomic_write_csv(p2, N.to_status(pd.DataFrame(yrows)))
    return [p1, p2], dict(event_rows=len(rows), year_state_rows=len(yrows), state_keys=keys)


def main():
    import e6n_gate as GT
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['b5', 'b6'])
    a = ap.parse_args()
    for s in N.POST_SEGS:
        GT.post_gate(s, a.task)
    t0 = time.time()
    outs, info = {'b5': b5, 'b6': b6}[a.task]()
    N.write_receipt('E6n_%s' % a.task, outs, code=[__file__], wall_s=round(time.time() - t0, 1), **info)
    print(json.dumps(dict(task=a.task, wall_s=round(time.time() - t0, 1), **info), ensure_ascii=False, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
