#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 块 B1: 扩展结构域内的选择复验 (brief §8) —— 回答 Q9。

域: OLD = E6f 冻结的 U0-broad (6,038); EXPANDED = OLD ∪ E6g 的全部经济结构格。
    **按构造定义, 不按表现定义。** 排除对照 / 随机 / oracle / K / T0 学习产物 / L 的 H 变体与
    有状态缓冲。
规则: E6f 实际的 S1 / S3 / S4 + S1-cost (A = 1/5/10 亿, κ=0.5)。全部标 fixed_hindsight_library。
切点: E6f 的六个年末单次选择 + 之后评估; 以及 >=3 年初始历史后的逐年扩窗。
政策账户: **真的重走批次** —— 新规则只控制其后形成的目标, 旧批次延续到期, 整条路径一次过引擎。
"""
import os, sys, json, glob, time, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import e6g_desc as GD
import e6g_c as CC

BLOCK_DIR = {'H0': 'H0', 'H1': 'H1', 'H2': 'H2', 'H4a': 'H4', 'H4b': 'H4',
             'H5': 'H5', 'B2': 'B2'}
SPLITS = [2012, 2014, 2016, 2018, 2020, 2022]
WF_YEARS = list(range(2014, 2026))
KAPPA = 0.5
AS = [1.0, 5.0, 10.0]


def pareto_front(sc, tu):
    idx = np.argsort(-np.asarray(sc))
    best, out = np.inf, []
    for i in idx:
        if tu[i] < best:
            out.append(int(i)); best = tu[i]
    return out


def load_domain():
    """OLD (E6e 账本) + EXPANDED (E6g 账本), 全窗口拼接的逐日 gross / turn / 括号。"""
    gs, ts, bs, marks = [], [], [], []
    u0 = pd.read_csv(os.path.join(G.E6F_DIR, 'domain_U0.csv'))
    fam_old = u0.set_index('config_id')['family'].to_dict()
    for seg in G.SEGMENTS:
        g = pd.read_parquet(os.path.join(G.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % seg))
        t = pd.read_parquet(os.path.join(G.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % seg))
        keep = [c for c in u0.config_id if c in g.columns]
        g = g[keep]; t = t[keep]
        ng, nt, nb = {}, {}, {}
        for b, d in BLOCK_DIR.items():
            for fg in sorted(glob.glob(os.path.join(G.RES, d,
                                                    'daily_gross_%s_%s_s*.parquet' % (b, seg)))):
                ft = fg.replace('daily_gross_', 'daily_turn_')
                fs = fg.replace('daily_gross_', 'daily_brsqrt_')
                if not (os.path.exists(ft) and os.path.exists(fs)):
                    continue
                a1 = pd.read_parquet(fg); a2 = pd.read_parquet(ft); a3 = pd.read_parquet(fs)
                for i, c in enumerate(a1.columns):
                    ng[c] = a1.values[:, i]; nt[c] = a2.values[:, i]; nb[c] = a3.values[:, i]
        # H0 的固定展示组与 E6e 账本是同一批 config_id (按构造重叠), 去重保留 OLD 那份
        # —— 两份在自测里已验逐位相同 (max|d| = 0.000e+00)。
        dup = [c for c in ng if c in g.columns]
        for c in dup:
            ng.pop(c); nt.pop(c); nb.pop(c)
        NG = pd.DataFrame(ng, index=g.index)
        NT = pd.DataFrame(nt, index=g.index)
        NB = pd.DataFrame(nb, index=g.index)
        # OLD 列的括号从 E6f 已存的 C_impact 取 —— 不能留 NaN, 否则 S1-cost 会把
        # 「没算过冲击」当成「冲击为零」, 系统性偏向 OLD 域 (三个 A 会给出同一个选择)。
        ob = pd.DataFrame(np.nan, index=g.index, columns=g.columns)
        bp_ = os.path.join(G.E6F_DIR, 'C_impact', 'bracket_%s.npy' % seg)
        bc_ = os.path.join(G.E6F_DIR, 'C_impact', 'bracket_cols_%s.json' % seg)
        if os.path.exists(bp_) and os.path.exists(bc_):
            Bm = np.load(bp_)
            pos = {c: i for i, c in enumerate(json.load(open(bc_)))}
            hit = [c for c in g.columns if c in pos]
            if hit:
                ob.loc[:, hit] = Bm[:, [pos[c] for c in hit]]
            print('    %s OLD 括号覆盖 %d / %d' % (seg, len(hit), g.shape[1]), flush=True)
        gs.append(pd.concat([g, NG], axis=1))
        ts.append(pd.concat([t, NT], axis=1))
        bs.append(pd.concat([ob, NB], axis=1))
        marks.append(np.array([seg] * len(g.index)))
    cols = sorted(set.intersection(*[set(x.columns) for x in gs]))
    GG = pd.concat([x.reindex(columns=cols) for x in gs], axis=0)
    TT = pd.concat([x.reindex(columns=cols) for x in ts], axis=0)
    BB = pd.concat([x.reindex(columns=cols) for x in bs], axis=0)
    return GG, TT, BB, np.concatenate(marks), fam_old


def famcode(cols, fam_old, MS):
    """宏观族: OLD 沿 E6f 的 family; E6g 的新描述符按【母体的源家族】继承。
       映射在读收益之前冻结。"""
    pm = MS[MS.role == 'economic'].drop_duplicates('config_id').set_index(
        'config_id')['parent_cfg'].to_dict()
    out = {}
    for c in cols:
        if c in fam_old:
            out[c] = str(fam_old[c]); continue
        p = pm.get(c)
        base = str(p if isinstance(p, str) else c).split('|')[0]
        out[c] = base.split('{')[0].split('@')[0].split('(')[0]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--domain', default='EXPANDED', choices=['OLD', 'EXPANDED'])
    ap.add_argument('--accounts', action='store_true', help='重走批次建真实政策账户')
    A = ap.parse_args()
    t0 = time.time()
    out = os.path.join(G.RES, 'B')
    os.makedirs(out, exist_ok=True)
    MS = pd.read_csv(os.path.join(G.RES, 'D', 'master_summary.csv'), low_memory=False)
    econ = set(MS[MS.role == 'economic'].config_id)
    GG, TT, BB, segmark, fam_old = load_domain()
    if A.domain == 'OLD':
        keep = [c for c in GG.columns if c in fam_old]
    else:
        keep = [c for c in GG.columns if c in fam_old or c in econ]
    GG, TT, BB = GG[keep], TT[keep], BB[keep]
    N8 = GG.values - TT.values * F.COST / 1e4
    dts = pd.DatetimeIndex(GG.index)
    yrs = dts.year.to_numpy()
    FAM = famcode(keep, fam_old, MS)
    famcodes = pd.factorize(pd.Series([FAM[c] for c in keep]))[0]
    rank_name = np.argsort(np.argsort(np.array(keep)))
    print('域 %s: %d 配置 x %d 日, %d 个宏观族, %.0fs'
          % (A.domain, len(keep), len(dts), len(set(famcodes)), time.time() - t0), flush=True)

    def net_series(A_yi=None):
        """逐日 net8; A_yi 给出则按同模型同 (A, kappa) 扣冲击。a 与 b 必须同口径。"""
        if A_yi is None:
            return N8
        return N8 - np.nan_to_num(CC.impact_cost(BB.values, A_yi, KAPPA, 'sqrt'), nan=0.0)

    def score(mask, A_yi=None):
        """训练评分: 只用决策时已实现的收益与成本。A_yi 给出则按同模型扣冲击 (S1-cost)。"""
        x = net_series(A_yi)[mask]
        sc = np.nanmean(x, axis=0) * 252 * 100
        tu = np.nanmean(TT.values[mask], axis=0)
        return sc, tu

    def pick(sc, tu, rule):
        ok = np.isfinite(sc)
        sc2 = np.where(ok, sc, -np.inf)
        order = np.lexsort((rank_name, np.nan_to_num(tu, nan=9e9), -sc2))
        if rule.startswith('S1'):
            return [(keep[order[0]], 1.0)]
        if rule == 'S3':
            _, first = np.unique(famcodes[order], return_index=True)
            sel = order[np.sort(first)]
            return [(keep[i], 1.0 / len(sel)) for i in sel]
        if rule == 'S4':
            fr = pareto_front(sc2, np.nan_to_num(tu, nan=9e9))
            fr = sorted(fr, key=lambda i: tu[i])
            if len(fr) > 5:
                pos = np.linspace(0, len(fr) - 1, 5).round().astype(int)
                fr = [fr[i] for i in sorted(set(pos.tolist()))]
            return [(keep[i], 1.0 / len(fr)) for i in fr]
        raise ValueError(rule)

    RULES = ['S1', 'S3', 'S4'] + ['S1-cost@%g' % a for a in AS]
    rows, paths = [], []

    # ---------- (a) 六个年末单次选择 ----------
    for cut in SPLITS:
        tr = yrs <= cut
        ev = yrs > cut
        if tr.sum() < 250 or ev.sum() < 60:
            continue
        for rule in RULES:
            Ay = float(rule.split('@')[1]) if '@' in rule else None
            sc, tu = score(tr, Ay)
            sel = pick(sc, tu, rule)
            a_ = float(np.nansum([sc[keep.index(c)] * w for c, w in sel]))
            NS_ = net_series(Ay)
            ev_led = float(np.nanmean(
                np.nansum([NS_[:, keep.index(c)] * w for c, w in sel], axis=0)[ev])) * 252 * 100
            rows.append(dict(domain=A.domain, scheme='split', cut=cut, rule=rule,
                             n_selected=len(sel), a_train=a_, b_eval_ledger=ev_led,
                             b_minus_a=ev_led - a_,
                             selected='|'.join(c for c, _ in sel)[:400],
                             fixed_hindsight_library=True))
            paths.append(dict(scheme='split', cut=cut, rule=rule,
                              start=str(dts[ev].min().date()), sel=sel))
    print('单次选择完成 %.0fs' % (time.time() - t0), flush=True)

    # ---------- (b) 逐年扩窗 (>=3 年初始历史) ----------
    for rule in RULES:
        Ay = float(rule.split('@')[1]) if '@' in rule else None
        seq = []
        for y in WF_YEARS:
            tr = yrs < y
            if tr.sum() < 3 * 250:
                continue
            sc, tu = score(tr, Ay)
            sel = pick(sc, tu, rule)
            evm = yrs == y
            if evm.sum() < 60:
                continue
            a_ = float(np.nansum([sc[keep.index(c)] * w for c, w in sel]))
            NS_ = net_series(Ay)
            ev_led = float(np.nanmean(
                np.nansum([NS_[:, keep.index(c)] * w for c, w in sel], axis=0)[evm])) * 252 * 100
            rows.append(dict(domain=A.domain, scheme='walkforward', cut=y, rule=rule,
                             n_selected=len(sel), a_train=a_, b_eval_ledger=ev_led,
                             b_minus_a=ev_led - a_,
                             selected='|'.join(c for c, _ in sel)[:400],
                             fixed_hindsight_library=True))
            seq.append((y, sel))
        paths.append(dict(scheme='walkforward', cut='all', rule=rule, seq=seq))
    print('逐年扩窗完成 %.0fs' % (time.time() - t0), flush=True)

    pd.DataFrame(rows).to_csv(os.path.join(out, 'B1_selection_%s.csv' % A.domain), index=False)

    # ---------- (c) 可分辨度 ----------
    disc = []
    for cut in SPLITS:
        tr = yrs <= cut
        if tr.sum() < 250:
            continue
        sc, _ = score(tr)
        v = sc[np.isfinite(sc)]
        if len(v) < 10:
            continue
        top = np.sort(v)[::-1]
        n = tr.sum()
        pair_se = float(np.nanstd(N8[tr], axis=0).mean() * 252 * 100 / np.sqrt(n) * np.sqrt(2))
        disc.append(dict(domain=A.domain, cut=cut, n_config=len(v),
                         top1_minus_top2=float(top[0] - top[1]),
                         top1_minus_median=float(top[0] - np.median(v)),
                         pair_se=pair_se,
                         spread_to_pairSE=float((top[0] - top[1]) / pair_se) if pair_se else np.nan,
                         note='spread_to_pairSE 只作列, 不作门'))
    pd.DataFrame(disc).to_csv(os.path.join(out, 'B1_discernibility_%s.csv' % A.domain),
                              index=False)
    json.dump({'n_paths': len(paths),
               'rules': RULES, 'splits': SPLITS, 'wf_years': WF_YEARS,
               'domain_size': len(keep), 'n_old': int(sum(1 for c in keep if c in fam_old)),
               'n_new': int(sum(1 for c in keep if c not in fam_old)),
               'elapsed_s': round(time.time() - t0, 1)},
              open(os.path.join(out, 'B1_meta_%s.json' % A.domain), 'w'),
              indent=1, ensure_ascii=False)
    with open(os.path.join(out, 'B1_paths_%s.json' % A.domain), 'w') as fh:
        json.dump([{k: (v if k != 'seq' else [[y, s] for y, s in v]) for k, v in p.items()}
                   for p in paths], fh, ensure_ascii=False, indent=1, default=str)
    d = pd.DataFrame(rows)
    print()
    print('== b − a (评估 − 训练, 账本平均口径), 按规则 ==')
    print(d.groupby(['scheme', 'rule'])[['a_train', 'b_eval_ledger', 'b_minus_a']]
          .mean().round(3).to_string())

    # ---------- (d) 真实政策账户: 重走批次, 整条路径一次过引擎 ----------
    if A.accounts:
        acc_rows = []
        need = set()
        for p in paths:
            if p['scheme'] == 'walkforward':
                for _, sel in p['seq']:
                    need |= {c for c, _ in sel}
            else:
                need |= {c for c, _ in p['sel']}
        print('\n政策账户: 需重建 %d 个不同配置' % len(need), flush=True)
        for seg in G.SEGMENTS:
            S = G.seg(seg, verbose=False)
            ctx = GD.GCtx(S)
            M = CC.MarketCtx(S)
            sdts = pd.DatetimeIndex(S.dates)
            syr = sdts.year.to_numpy()
            masks, failed = {}, []
            for c in sorted(need):
                try:
                    masks[c] = ctx.full_mask_g(GD.parse_cfg(c))[0]
                except Exception as e:
                    failed.append((c, str(e)[:60]))
            print('  %s 重建 %d / %d (失败 %d)' % (seg, len(masks), len(need), len(failed)),
                  flush=True)
            refs = {}
            for lab in ('R1', 'R2'):
                pn, iv, _ = ctx.run(GD.parse_cfg(G.DISPLAY_ID[lab]))
                refs[lab] = pn[0] - pn[2] * F.COST / 1e4
            for p in paths:
                tgt = np.zeros((S.T, S.Nc), bool)
                wts = np.zeros((S.T, S.Nc))
                cover = np.zeros(S.T, bool)
                if p['scheme'] == 'walkforward':
                    for y, sel in p['seq']:
                        rowm = syr == y
                        if not rowm.any():
                            continue
                        for c, w in sel:
                            if c in masks:
                                wts[rowm] += masks[c][rowm] * w
                        cover |= rowm
                else:
                    rowm = sdts > pd.Timestamp('%d-12-31' % p['cut'])
                    if not rowm.any():
                        continue
                    for c, w in p['sel']:
                        if c in masks:
                            wts[rowm] += masks[c][rowm] * w
                    cover |= rowm
                if not cover.any() or wts.sum() == 0:
                    continue
                tgt = wts > 0
                idx, val = F.dev_from_dense(S, tgt)
                pn = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
                n8 = pn[0] - pn[2] * F.COST / 1e4
                br = CC.profile_and_impact(M, idx, val, K.HOLD, full_profile=False)[0]['sqrt']
                r = dict(domain=A.domain, scheme=p['scheme'], rule=p['rule'], cut=p['cut'],
                         segment=seg, n_days=int(cover.sum()),
                         policy_net8_ann=float(np.nanmean(n8[cover])) * 252 * 100,
                         d_vs_R1=float(np.nanmean((n8 - refs['R1'])[cover])) * 252 * 100,
                         d_vs_R2=float(np.nanmean((n8 - refs['R2'])[cover])) * 252 * 100,
                         bracket_sqrt_mean=float(np.nanmean(br[cover])),
                         n_rebuild_failed=len(failed),
                         note='真实批次: 新规则只控制其后形成的目标, 旧批次延续到期')
                acc_rows.append(r)
        AC = pd.DataFrame(acc_rows)
        AC.to_csv(os.path.join(out, 'B1_policy_accounts_%s.csv' % A.domain), index=False)
        print()
        print('== 真实政策账户 vs R1 / R2 (四段合并中位) ==')
        print(AC.groupby(['scheme', 'rule'])[['policy_net8_ann', 'd_vs_R1', 'd_vs_R2']]
              .median().round(3).to_string())
        print()
        print('政策账户里 vs R2 为正的条数: %d / %d'
              % (int((AC.d_vs_R2 > 0).sum()), len(AC)))
    print('DONE B1 %s %.0fs' % (A.domain, time.time() - t0))


if __name__ == '__main__':
    main()
