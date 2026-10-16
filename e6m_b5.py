# -*- coding: utf-8 -*-
"""E6m B5（plan §8.2 B5a / §8.3 B5b；registry/b5_queries_E6m.csv 冻结：B5A_CVR_CONDITIONAL 30、B5B_V_STATE 720）。
  budget   B5b 删除预算（b5_delete_budget）：每个 V 对象 × H —— delete_count（段内实际删除格数合计，名单 facts f_deleted）、
           same_n_core_deep_ann_pp = V 对象 − 附属 SAME_N_CORE_DEEP（同父同 H 同删除数、按父门分自深向浅删）、
           random_ann_pp = V 对象 − 同层同数随机删（DELETE_BUDGET_COND 路径均值；random_refs 的 real_minus_rand）。
           相对无条件删票的增量与相对真正父的增量分开（parent 增量另在比较表 Q13）。
  ledger   状态账本（b5_state_ledger；引擎层，阶段 S）：按"形成日"状态把 gross 拆开——每个 vintage 冻结其形成状态（plan §8.2）：
           act_s = 只取形成日状态为 s 的目标权重做 e6i_sparse 同式滚动持仓，gross_s[t] = Σ_c act_s[t − 2, c]·(r0[t, c] − bench[t])；Σ_s gross_s = gross（逐日 1e−12）。
           B5A：A4b_CVRv5 − A4b 等三对（有 CVR − 同构无 CVR，先核两者除 CVR 外流程相同 = 门相同）× TREND3_FORMATION（个股形成日 Trend：UP / MIXED / DOWN / UNKNOWN）
                与 VOL3（形成日市场 Vol3：0 / 1 / 2 / UNKNOWN）× H1 / 3 / 5 / 10 / 20；
           B5B：V 对象 − 实际父 × 个股形成日 Trend。费用按执行日净订单整体记（TOTAL 行 fee_ann_pp），不按状态摊（不把个股 Trend 强贴到组合日 net）。
  clock    state_clock_ledger（E6l 固定表沿用；e6l_state_clock 三时钟移植，对象 = B4 的 78 个、H5）：形成状态 gross / 日历 Vol3 净差 / 执行日 Vol3 费用差
           + STRICT250 日数（见 task_clock）。ledger / clock 直接读收益：封存门 + 后段守卫。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_s_stats as SS

ANN = M.ANN
TOL = 1e-12
TREND = {2: 'UP', 1: 'MIXED', 0: 'DOWN', -1: 'UNKNOWN'}
VOL = {0: 'VOL_LOW', 1: 'VOL_MID', 2: 'VOL_HIGH', -1: 'UNKNOWN'}


def act_dense(T, Nc, t, c, w, H):
    import e6m_s_decomp as DC
    return DC.act_dense(T, Nc, t, c, w, H)


def state_split(T, Nc, tg, H, x, code_tc):
    """目标 tg（t, c, w）× 形成日状态码（每个目标格一个码）→ {码: 逐日 gross 贡献 (T,)}；Σ = 全部 gross（引擎同式）。"""
    out = {}
    codes = np.unique(code_tc)
    for s in codes:
        m = code_tc == s
        a = act_dense(T, Nc, tg['t'][m], tg['c'][m], tg['w'][m], H)
        g = np.zeros(T)
        g[2:] = np.einsum('ij,ij->i', a[:-2], x[2:])
        out[int(s)] = g
    return out


def task_budget(acc, stats, seg, out):
    d, t, d2t, dH, dates = SS.load(acc, seg)
    Q = M.read_csv_keep(M.P('registry', 'b5_queries_E6m.csv'), dtype=str)
    Q = Q[Q.query_kind == 'B5B_V_STATE']
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str, usecols=['aux_id', 'owner_id', 'mechanism'])
    core = {r.owner_id.split('@')[0]: r.aux_id for r in A[A.mechanism == 'SAME_N_CORE_DEEP'].itertuples()}
    sched = set(o.split('@')[0] for o in A[A.mechanism == 'DELETE_BUDGET_COND'].owner_id)
    rr = os.path.join(stats, 'random_refs_%s.csv' % seg)
    R = pd.read_csv(rr, keep_default_na=False, na_values=['']) if os.path.exists(rr) else None
    rmr = {} if R is None else {(r.desc_id, int(r.H)): r.real_minus_rand for r in R[R.mechanism == 'DELETE_BUDGET_COND'].itertuples()}
    facts = {}
    mdir = M.P('stageS_dev', 'masks', seg) if 'stageS_dev' in os.path.realpath(acc) else M.P('masks', seg)      # 开发（合成账本）读 mock 名单 facts
    for f in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        if f.startswith('facts_') and f.endswith('.csv'):
            F = M.read_csv_keep(os.path.join(mdir, f))
            if 'f_deleted' in F.columns:
                facts.update(dict(zip(F.config_id, F.f_deleted)))
    rows = []
    for r in Q.itertuples():
        H = int(r.H)
        x = dict(query_id='E6M-Q13-d', object=r.object, H=H, segment=seg)
        cfg = '|'.join(r.object.split('|')[:6] + r.object.split('|')[7:])
        x['delete_count'] = facts.get(cfg, np.nan)
        if r.object in d and core.get(r.object) in d:
            a_, b_ = np.asarray(d[r.object]['net8'], float), np.asarray(d[core[r.object]]['net8'], float)
            m = np.isfinite(a_) & np.isfinite(b_)
            x['same_n_core_deep_ann_pp'] = float(np.mean((a_ - b_)[m])) * ANN if m.any() else np.nan
            x['n_days'] = int(m.sum())
        else:
            x['same_n_core_deep_ann_pp'] = np.nan
        x['random_ann_pp'] = rmr.get((r.object, H), np.nan)
        if not np.isfinite(x['same_n_core_deep_ann_pp']):
            x['status'] = 'UNDEFINED'
        elif not np.isfinite(x['random_ann_pp']):
            x['status'] = 'UNDEFINED' if r.object in sched else 'RANDOM_NOT_SCHEDULED'      # 随机只登记在部分 H（附属清单 item 2–4）
        else:
            x['status'] = 'COMPUTED'
        rows.append(x)
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'b5_delete_budget_%s.csv' % seg)
    M.atomic_write_csv(p, df)
    return p, df


def state_arrays(seg):
    """云机状态缓存（Stage 0 S A4-3 核过；E6l v1.1 因果实现）→ 本段坐标：(vol_day 主定义, vol_day STRICT250, trend_tc (T, Nc))；缓存外 = −1（UNKNOWN）。"""
    T, Nc = seg.T, seg.Nc
    zs = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)
    di = {str(dd)[:10]: i for i, dd in enumerate(zs['dates'])}
    ci = {str(c): j for j, c in enumerate(zs['columns'])}
    rows_ix = np.array([di.get(str(dd)[:10], -1) for dd in seg.dates])
    cols_ix = np.array([ci.get(str(c), -1) for c in seg.S.ccolnames])
    ok_r, ok_c = rows_ix >= 0, cols_ix >= 0
    vol_day = np.where(ok_r, zs['vol_state'][np.maximum(rows_ix, 0)], -1).astype(int)
    vol_strict = np.where(ok_r, zs['vol_state_strict'][np.maximum(rows_ix, 0)], -1).astype(int)
    trend_tc = np.full((T, Nc), -1, int)
    trend_tc[np.ix_(ok_r, ok_c)] = zs['trend'][np.ix_(rows_ix[ok_r], cols_ix[ok_c])]
    return vol_day, vol_strict, trend_tc


def task_ledger(seg_name, out):
    """阶段 S（真实引擎）：B5A 三对 × 两分区 × 5 个 H；B5B 每个 V 对象 × 个股形成日 Trend。"""
    import e6k_acct as AC
    import e6m_s_real as RL
    seg = RL.seg_of(seg_name, 'real')
    acct = AC.Acct(seg)
    SE = seg.SE
    T, Nc = SE.T, SE.Nc
    x = SE.r0 - SE.bench[:, None]
    vol_day, _, trend_tc = state_arrays(seg)

    def final(form, cfg=None):
        z = np.load(M.P('masks', seg_name, '%s.npz' % form), allow_pickle=False)
        n = int(z['n_cells'][0])
        if cfg is None:
            return np.unpackbits(z['parent_final_bits'])[:n].astype(bool)
        j = [str(c) for c in z['config_ids']].index(cfg)
        return np.unpackbits(z['final_bits'][j])[:n].astype(bool)

    def ledger_rows(qid, obj, kept_c, kept_p, H, partition):
        tc, tp = acct.target(kept_c), acct.target(kept_p)
        if partition == 'VOL3':
            cc, cp = vol_day[tc['t']], vol_day[tp['t']]
            lab = VOL
        else:
            cc, cp = trend_tc[tc['t'], tc['c']], trend_tc[tp['t'], tp['c']]
            lab = TREND
        sc, sp = state_split(T, Nc, tc, H, x, cc), state_split(T, Nc, tp, H, x, cp)
        lc = acct.ledgers(tc, (H,), impact=False, roll=False)[H]
        lp = acct.ledgers(tp, (H,), impact=False, roll=False)[H]
        tot_c, tot_p = sum(sc.values()), sum(sp.values())
        clo = max(float(np.nanmax(np.abs(tot_c - lc['gross']))), float(np.nanmax(np.abs(tot_p - lp['gross']))))
        out_rows = []
        for s in sorted(set(sc) | set(sp)):
            g = sc.get(s, np.zeros(T)) - sp.get(s, np.zeros(T))
            out_rows.append(dict(query_id=qid, object=obj, partition='%s:%s' % (partition, lab.get(s, s)), H=H, gross_contrib_ann_pp=float(np.mean(g)) * ANN,
                                 fee_ann_pp=np.nan, n_days=int(np.unique(np.r_[tc['t'][cc == s], tp['t'][cp == s]]).size),
                                 status='COMPUTED' if clo <= TOL else 'CLOSURE_FAIL'))
        fee = float(np.nanmean((lc['gross'] - lc['net8']) - (lp['gross'] - lp['net8']))) * ANN
        out_rows.append(dict(query_id=qid, object=obj, partition='%s:TOTAL' % partition, H=H, gross_contrib_ann_pp=float(np.mean(tot_c - tot_p)) * ANN,
                             fee_ann_pp=fee, n_days=T, status='COMPUTED' if clo <= TOL else 'CLOSURE_FAIL'))
        return out_rows
    Q = M.read_csv_keep(M.P('registry', 'b5_queries_E6m.csv'), dtype=str)
    rows = []
    for r in Q[Q.query_kind == 'B5A_CVR_CONDITIONAL'].itertuples():
        f_with, f_wo = r.object.split('_VS_')
        sw, so = seg.struct(f_with), seg.struct(f_wo)
        if not np.array_equal(sw.ids, so.ids):                                  # 先核两者除 CVR 外流程相同；不同则记是哪一项
            gchk = 'IDS_DIFFER（门域单元 %d vs %d）' % (len(sw.ids), len(so.ids))
        else:
            nd = int((sw.gate_keep(sw.gate_scores(sw.q0[None, :])) != so.gate_keep(so.gate_scores(so.q0[None, :]))).sum())
            gchk = 'SAME' if nd == 0 else 'KEEP_DIFFERS（源门 %d 格不同）' % nd
        part = 'TREND3' if r.partition == 'TREND3_FORMATION' else 'VOL3'
        rs = ledger_rows('E6M-B5A-a', r.object, final(f_with), final(f_wo), int(r.H), part)
        for x_ in rs:
            x_['gate_check'] = gchk
            x_['status'] = x_['status'] if gchk == 'SAME' else 'GATE_DIFFERS'
        rows += rs
    for r in Q[Q.query_kind == 'B5B_V_STATE'].itertuples():
        form = r.object.split('|')[1]
        cfg = '|'.join(r.object.split('|')[:6] + r.object.split('|')[7:])
        try:
            kc = final(form, cfg)
        except ValueError:
            rows.append(dict(query_id='E6M-Q13-d', object=r.object, partition='TREND3', H=int(r.H), status='UNDEFINED'))
            continue
        rows += ledger_rows('E6M-Q13-d', r.object, kc, final(form), int(r.H), 'TREND3')
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'b5_state_ledger_%s.csv' % seg_name)
    M.atomic_write_csv(p, df)
    return p, df


# ====================================================================== state_clock_ledger（E6l 三时钟移植；限制登记 L-S5）
def clock_objects():
    """对象集 = plan §8.1 / registry/b4_queries_E6m.csv 冻结的 B4 对象（主展示 72 + 六原父；H5）。"""
    B = M.read_csv_keep(M.P('registry', 'b4_queries_E6m.csv'), dtype=str)
    return sorted(set(B.object))


def by_state_rows(x, state, H, labels, base):
    """一条日序列 x（NaN = 缺日）按日状态分组：contribution = Σ_{该状态} x / N_全部有限日（各状态加回 FULL 日均）、条件均值、HAC se（H）；
    另一行 SUM_CHECK（contribution 之和与 FULL 日均）。缺日 HAC：只用该状态且有限的日，其余日不当 0 样本（e6l_state_clock 同式）。"""
    from e6l_mde80 import hac_batch
    fx = np.isfinite(x)
    N = int(fx.sum())
    rows, ssum = [], 0.0
    for code, nm in labels.items():
        m = fx & (state == code)
        contrib = float(np.sum(x[m]) / N) * ANN if N else np.nan
        ssum += contrib if np.isfinite(contrib) else 0.0
        se, _ = hac_batch(np.where(m, x, np.nan)[None, :], H)
        rows.append(dict(base, state=nm, days=int(m.sum()), share=float(m.sum() / N) if N else np.nan, contribution_ann_pp=contrib,
                         conditional_mean_ann_pp=float(np.mean(x[m])) * ANN if m.any() else np.nan,
                         conditional_se_H_ann_pp=float(se[0]) * ANN if np.isfinite(se[0]) else np.nan, status='COMPUTED' if m.any() else 'UNDEFINED'))
    full = float(np.mean(x[fx])) * ANN if N else np.nan
    clo = abs(ssum - full) / ANN if N else np.nan
    rows.append(dict(base, state='SUM_CHECK', days=N, share=1.0, contribution_ann_pp=ssum, conditional_mean_ann_pp=full, closure_max_abs_decimal=clo,
                     status='UNDEFINED' if not N else ('COMPUTED' if clo <= TOL else 'CLOSURE_FAIL')))      # 与 FORMATION 同一闭合容差
    return rows


def task_clock(seg_name, out):
    """state_clock_ledger（e6l_state_clock 三时钟，E6m 对象集 = B4 的 78 个、H5；阶段 S 真实引擎）：
      FORMATION     形成日状态冻结的 gross 拆分：VOL3 = 形成日市场 Vol3，TREND3 = 个股形成日 Trend；子 / 父各自 Σ_s = 账户 gross（逐日核，closure 列）；
      CALENDAR_NET  Δnet8 = 子 − 同 H 原父（父对象 = 自身 net8，B4 同约定）按 u 日 Vol3：贡献（加回 FULL 日均）/ 条件均值 / HAC se；
      TRADING_FEE   Δfee = −8e−4·(turn 子 − turn 父) 按执行日 u 的 Vol3（净订单整体；不按形成状态倒分）；
      STRICT250     段级：主定义 vs STRICT250 的 Vol3 各状态日数与标签不同日数（object = SEGMENT）。
    E6l 的 Q12 切片（本轮无该卡）、压力窗口与跨段对称分解由 B4 的 event / SYMDEC 承担，不重复。输出 b5_state_clock_<段>.csv（宽表；固定表转长表）。"""
    import e6k_acct as AC
    import e6m_s_real as RL
    import e6m_s_seal as SEAL
    import e6m_s_stats as SS
    SEAL.require_for(M.P('accounts'), seg_name)
    seg = RL.seg_of(seg_name, 'real')
    acct = AC.Acct(seg, impact=False)
    SE = seg.SE
    T, Nc, n = SE.T, SE.Nc, seg.n
    x = SE.r0 - SE.bench[:, None]
    vol_day, vol_strict, trend_tc = state_arrays(seg)
    acc = M.P('accounts')
    d, _, d2t, dH, _ = SS.load(acc, seg_name)
    bits = {}
    for ad in SS.acc_dirs(acc):                                          # 与 SS.load 的目标键同式（accounts_aux 前缀 "accounts_aux:"）
        tag = '' if ad == acc else os.path.basename(os.path.normpath(ad)) + ':'
        sd = os.path.join(ad, seg_name)
        for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
            if f.endswith('.npz') and not f.startswith('weights_'):
                z = np.load(os.path.join(sd, f), allow_pickle=False)
                zb = z['bits']
                for j, tid in enumerate(z['targets']):
                    bits['%s%s#%s' % (tag, f[:-4], tid)] = zb[j]
    tcache = {}

    def target(did):
        k = d2t[did]
        if k not in tcache:
            tcache[k] = acct.target(np.unpackbits(bits[k])[:n].astype(bool))
        return tcache[k]
    rows = []
    for did in clock_objects():
        if did not in d:
            rows.append(dict(segment=seg_name, object=did, clock='ALL', state_var='', state='', status='SOURCE_WAIT'))
            continue
        H = dH[did]
        is_par = did.split('|')[2] == 'PARENT'
        par = SS.parent_of(did)
        if not is_par and par not in d:
            rows.append(dict(segment=seg_name, object=did, clock='ALL', state_var='', state='', status='SOURCE_WAIT'))
            continue
        tc = target(did)
        tp = None if is_par else target(par)
        for var, codes_of, labels in (('VOL3_FORMATION', lambda tg: vol_day[tg['t']], VOL), ('TREND3_FORMATION', lambda tg: trend_tc[tg['t'], tg['c']], TREND)):
            sc = state_split(T, Nc, tc, H, x, codes_of(tc))
            sp = state_split(T, Nc, tp, H, x, codes_of(tp)) if tp is not None else {}
            clo = float(np.nanmax(np.abs(sum(sc.values()) - d[did]['gross'])))
            if tp is not None:
                clo = max(clo, float(np.nanmax(np.abs(sum(sp.values()) - d[par]['gross']))))
            for code in sorted(set(sc) | set(sp)):
                gc, gp = sc.get(code, np.zeros(T)), sp.get(code, np.zeros(T))
                rows.append(dict(segment=seg_name, object=did, clock='FORMATION', state_var=var, state=labels.get(code, str(code)), H=H,
                                 gross_contrib_child_ann_pp=float(np.mean(gc)) * ANN, gross_contrib_parent_ann_pp=float(np.mean(gp)) * ANN if tp is not None else np.nan,
                                 gross_contrib_diff_ann_pp=float(np.mean(gc - gp)) * ANN, closure_max_abs_decimal=clo,
                                 status='COMPUTED' if clo <= TOL else 'CLOSURE_FAIL'))
        net_c, turn_c = np.asarray(d[did]['net8'], float), np.asarray(d[did]['turn'], float)
        dn = net_c if is_par else net_c - np.asarray(d[par]['net8'], float)
        dfee = -8e-4 * (turn_c if is_par else turn_c - np.asarray(d[par]['turn'], float))
        for clock, series in (('CALENDAR_NET', dn), ('TRADING_FEE', dfee)):
            rows += by_state_rows(series, vol_day, H, VOL, dict(segment=seg_name, object=did, clock=clock, state_var='VOL3_CALENDAR', H=H))
    for code, nm in VOL.items():
        rows.append(dict(segment=seg_name, object='SEGMENT', clock='STRICT250', state_var='VOL3_CALENDAR', state=nm, days=int((vol_day == code).sum()),
                         strict250_days=int((vol_strict == code).sum()), status='COMPUTED'))
    rows.append(dict(segment=seg_name, object='SEGMENT', clock='STRICT250', state_var='VOL3_CALENDAR', state='LABEL_DIFFERS_DAYS',
                     days=int((vol_day != vol_strict).sum()), strict250_days=int(((vol_day >= 0) & (vol_strict >= 0) & (vol_day != vol_strict)).sum()),
                     status='COMPUTED'))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'b5_state_clock_%s.csv' % seg_name)
    M.atomic_write_csv(p, df)
    return p, df


def selftest():
    rng = np.random.default_rng(55)
    T, Nc, H = 50, 40, 5
    t = np.repeat(np.arange(T), 8)
    c = np.concatenate([rng.choice(Nc, 8, replace=False) for _ in range(T)])
    tg = dict(t=t, c=c, w=rng.uniform(0.01, 0.05, len(t)))
    x = rng.normal(0, 0.02, (T, Nc))
    code = rng.integers(-1, 3, len(t))
    sp = state_split(T, Nc, tg, H, x, code)
    a = act_dense(T, Nc, t, c, tg['w'], H)
    g = np.zeros(T)
    g[2:] = np.einsum('ij,ij->i', a[:-2], x[2:])
    clo = float(np.max(np.abs(sum(sp.values()) - g)))
    res = [('状态拆分逐日加回总 gross（4 个状态码含 UNKNOWN）max|Δ| %.1e' % clo, clo <= 1e-15)]
    xs = rng.normal(0, 0.01, 300)
    xs[rng.choice(300, 20, replace=False)] = np.nan
    stt = rng.integers(-1, 3, 300)
    R = by_state_rows(xs, stt, 5, VOL, dict(object='synthetic'))
    chk = [r for r in R if r['state'] == 'SUM_CHECK'][0]
    res.append(('时钟 2 / 3：各状态贡献加回 FULL 日均（含 UNKNOWN 与 20 个缺日）|Δ| %.1e，SUM_CHECK 状态 %s' % (chk['closure_max_abs_decimal'], chk['status']),
                chk['closure_max_abs_decimal'] <= 1e-15 and chk['status'] == 'COMPUTED'))
    sh = sum(r['share'] for r in R if r['state'] != 'SUM_CHECK')
    res.append(('时钟 2 / 3：状态份额和 = 1（%.15f）' % sh, abs(sh - 1.0) <= 1e-12))
    cm = [r for r in R if r['state'] == 'VOL_HIGH'][0]
    m = np.isfinite(xs) & (stt == 2)
    res.append(('时钟 2 / 3：条件均值 = 该状态有限日均值', abs(cm['conditional_mean_ann_pp'] - float(np.mean(xs[m])) * ANN) <= 1e-12))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['budget', 'ledger', 'clock', 'selftest'])
    ap.add_argument('--acc', default='')
    ap.add_argument('--stats', default='')
    ap.add_argument('--seg', default='')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    if a.task == 'selftest':
        res = selftest()
        for nm, ok in res:
            print('%s  %s' % ('PASS' if ok else 'FAIL', nm))
        return 0 if all(ok for _, ok in res) else 1
    import e6m_s_seal as SEAL
    if a.acc:
        SEAL.require_for(a.acc, a.seg)
    if a.task in ('ledger', 'clock'):                                     # 直接读收益（SE）：封存门 + 后段守卫（授权绑定的冻结清单与生效条件）
        import e6m_s_gate as GT
        SEAL.require('deriv' if a.seg in M.DERIV_SEGS else 'post')
        GT.post_gate(a.seg, 'b5 %s %s' % (a.task, a.seg))
    os.makedirs(a.out, exist_ok=True)
    p, df = {'budget': lambda: task_budget(a.acc, a.stats, a.seg, a.out), 'ledger': lambda: task_ledger(a.seg, a.out),
             'clock': lambda: task_clock(a.seg, a.out)}[a.task]()
    st = df.status.value_counts().to_dict() if len(df) else {}
    M.write_receipt(os.environ.get('E6M_TASK', 'S_b5_%s_%s' % (a.task, a.seg)), [p], status='SUCCEEDED', code=[__file__, M.__file__], rows=len(df),
                    status_counts=st, wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(task=a.task, seg=a.seg, rows=len(df), status=st, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
