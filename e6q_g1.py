# -*- coding: utf-8 -*-
"""E6q S0-B（推导段基准率）+ S0-M（第一道 G-P-01…12，推导段）+ seal_A2（brief §2 / §4；附录 A-B / A-M；只打标签不选支、不删账户）。
只读 A2 产物（accounts_run/deriv、trades_parts/deriv、shadow_deriv、randoms/random_paths_A2.csv、tmp/a2stats/statistics）与 S0-A 对账表；
两推导段 = 2010-2014、2015-2018。输出：diagnostics/G1_E6q.csv（B.23 长格式）、diagnostics/stage0_E6q_part2.csv（S0-B / S0-M 行）、
registration/ledger_G_E6q.csv（state / result_row 更新）、registration/seal_A2.json + seal_A2_manifest.txt。用法：python3 e6q_g1.py"""
import os
import json
import time

import numpy as np
import pandas as pd

import e6q_core as O
import e6q_engine as E
import e6q_landmark as LM

LCOLS = ['block', 'item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status', 'query_id']
DSEG = list(O.DERIV_SEGS)
ROWS, ST0 = [], []


def L(block, item, key1, key2, segment, stat, value, unit, n='', status='COMPUTED', q=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN' if status == 'COMPUTED' else status
    ROWS.append(dict(block=block, item=item, key1=key1, key2=key2, segment=segment, stat=stat, value=value, unit=unit, n=n, status=status, query_id=q or 'QRY-G1-%s' % block))


def put(probe, item, key, value, unit='count', status='INFO', source_file='', note=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN'
    ST0.append(dict(probe_id=probe, item=item, key=key, value=value, unit=unit, status=status, source_file=source_file, note=note))


class C(object):
    pass


def setup():
    c = C()
    cd = O.cache_dir()
    c.cd = cd
    c.dates = np.load(os.path.join(cd, 'panels', 'dates.npy'))
    c.T = len(c.dates)
    c.d19 = int(np.searchsorted(c.dates, '2019-01-01'))
    c.segi = np.array([O.seg_of_date(d) for d in c.dates])
    c.R = O.read_csv(O.P('registration', 'registry_E6q.csv'), dtype=str).fillna('')
    c.adv = np.load(os.path.join(cd, 'panels', 'adv20.npy'), mmap_mode='r')
    c.pv = np.load(os.path.join(cd, 'panels', 'pv_ff.npy'), mmap_mode='r')
    b = np.nan_to_num(np.load(os.path.join(cd, 'panels', 'bench.npy')).astype(float))
    c.cumb = np.cumprod(1.0 + b)
    c.t1a = np.load(os.path.join(cd, 'triggers', 'T1a.npy'), mmap_mode='r')
    c.t8 = np.load(os.path.join(cd, 'triggers', 'T8_LIMIT_CLOSE.npy'), mmap_mode='r')
    c.lvl = np.load(os.path.join(cd, 'triggers', 'T1b_LEVEL.npy'), mmap_mode='r')
    return c


def pick(c, arm, trig, H='20', form=O.MAIN_FORM, mem='HG10', scen='FEASIBLE_DAILY'):
    R = c.R
    x = R[(R.arm == arm) & (R.trigger == trig) & (R.H == H) & (R.form == form) & (R.memory == mem) & (R.scenario == scen)]
    return x.iloc[0] if len(x) else None


def trades(c, h):
    z = np.load(O.P('trades_parts', 'deriv', h[:2], '%s.npz' % h), allow_pickle=False)
    return z['TL_i'], z['TL_f']


def acct(c, h):
    return np.load(O.P('accounts_run', 'deriv', h[:2], '%s.npz' % h), allow_pickle=False)


def segmask(c, day):
    return np.array([c.segi[d] for d in day])


# ------------------------------------------------------------------ G-P-01 / 02（S0-A 表推导段行）
def gp01_02(c):
    rc = O.read_csv(O.P('verify', 'impact_reconciliation_E6q.csv'))
    for r in rc[(rc.segment.isin(DSEG)) & (rc.order_kind == 'ALL')].itertuples(index=False):
        L('G-P-01', 'legacy_over_curve_ratio', r.object_label, 'ALL', r.segment, 'ratio', float(r.ratio), 'ratio', int(r.n_orders), q='QRY-S0A-RECON')
    for r in rc[(rc.segment.isin(DSEG)) & (rc.order_kind != 'ALL')].itertuples(index=False):
        tot = rc[(rc.object_label == r.object_label) & (rc.segment == r.segment) & (rc.order_kind == 'ALL')].curve_impact_ann_pp.iloc[0]
        L('G-P-02', 'curve_impact_share_by_order_kind', r.object_label, r.order_kind, r.segment, 'share', float(r.curve_impact_ann_pp / tot) if tot else np.nan, 'share',
          int(r.n_orders), q='QRY-S0A-RECON')


# ------------------------------------------------------------------ S0-B 与 G-P-03 / 04 / 05 / 08
def inventory_flags(ti, tf):
    """逐成交行：该证券在成交日前一日收盘是否已持有（由成交日志重建物理库存）。"""
    df = pd.DataFrame(dict(d=ti[:, 0], s=ti[:, 1], q=np.where(ti[:, 5] == 0, tf[:, 0], -tf[:, 0])))
    g = df.groupby(['s', 'd']).q.sum().reset_index().sort_values(['s', 'd'])
    g['inv_after'] = g.groupby('s').q.cumsum()
    g['inv_before'] = g.inv_after - g.q
    key = dict(zip(zip(g.s, g.d), g.inv_before))
    return np.array([key[(s, d)] > 1e-9 for s, d in zip(ti[:, 1], ti[:, 0])])


def s0b(c):
    for trig in ('T1b_LEVEL', 'T1a'):
        r = pick(c, 'NATIVE', trig)
        ti, tf = trades(c, r.exec_hash)
        held = inventory_flags(ti, tf)
        ex = (ti[:, 4] == E.OK_EXTRA) & (ti[:, 5] == 0)
        n_ex = int(ex.sum())
        rep_cnt = float(held[ex].mean()) if n_ex else np.nan
        rep_not = float(tf[ex & held, 1].sum() / tf[ex, 1].sum()) if n_ex else np.nan
        sg = np.where(ti[:, 5] == 0, 1.0, -1.0)
        df = pd.DataFrame(dict(d=ti[:, 0], s=ti[:, 1], v=sg * tf[:, 1], ex=ex, held=held, nv=np.where(ex, tf[:, 1], 0.0)))
        net = df.groupby(['d', 's']).agg(v=('v', 'sum'), exv=('nv', 'sum'), held=('held', 'max')).reset_index()
        nb = net[(net.v > 0) & (net.exv > 0)]
        ext = np.minimum(nb.v, nb.exv)
        rep_net = float(ext[nb.held].sum() / ext.sum()) if ext.sum() > 0 else np.nan
        for k, v, u in (('COUNT', rep_cnt, 'share'), ('NOTIONAL', rep_not, 'share'), ('NET_EXTERNAL', rep_net, 'share')):
            put('S0-B', 'EXTRA 内重复买入份额（推导段；%s H20 NATIVE）' % trig, 'BASE_RATE_EXTRA_REPEAT_SHARE_%s' % k, v, u, 'INFO', 'trades_parts/deriv',
                '与全账户 85%% 重复批次数分开；n_extra = %d' % n_ex)
            L('G-P-03', 'extra_repeat_share', trig, k, '2010-2018', 'share', v, 'share', n_ex)
        # 参与率超限四种加权 × 买卖 × 两 A（证券日净单；T 前 ADV20）
        net2 = net[net.v.abs() > 0]
        DY = acct(c, r.exec_hash)['DY']
        navp = DY[:, E.DYI['nav_pre']]
        dd, ss, vv = net2.d.to_numpy(), net2.s.to_numpy(), net2.v.to_numpy()
        adv = np.asarray(c.adv[dd, ss])
        for A_ in (1e8, 5e8):
            with np.errstate(all='ignore'):
                p = np.abs(vv) * (A_ / O.V0) / adv
            okp = np.isfinite(p)
            for side, sm in (('BUY', vv > 0), ('SELL', vv < 0)):
                m = okp & sm
                if not m.any():
                    continue
                exc = p[m] > O.P_STAR
                w_not = np.abs(vv[m])
                w_cap = np.abs(vv[m]) / navp[dd[m]]
                for k, v in (('COUNT', float(exc.mean())), ('NOTIONAL', float(w_not[exc].sum() / w_not.sum())), ('FEE', float(w_not[exc].sum() / w_not.sum())),
                             ('CAPITAL', float(w_cap[exc].sum() / w_cap.sum()))):
                    put('S0-B', '参与率 p > 2%% ADV20 的超限率（推导段；%s H20 NATIVE；A = %.0e）' % (trig, A_), 'BASE_RATE_PARTICIPATION_EXCEED_%s_%s_%s' % ('1E8' if A_ == 1e8 else '5E8', k, side),
                        v, 'share', 'INFO', 'trades_parts/deriv', '证券日净单 %d 笔；均值 p = %.4f（均值 > 2%% 不推出一半以上超限）' % (int(m.sum()), float(np.mean(p[m]))))
                    L('G-P-04', 'participation_exceed_2pct', '%s|A%.0e' % (trig, A_), '%s|%s' % (k, side), '2010-2018', 'share', v, 'share', int(m.sum()))
                for qn, qv in (('p50', 50), ('p90', 90), ('p99', 99)):
                    L('G-P-04', 'participation_quantile', '%s|A%.0e' % (trig, A_), side, '2010-2018', qn, float(np.percentile(p[m], qv)), 'ratio', int(m.sum()))
    # 当日合法 new 集合容量（REINVEST_NEW 账户 new_n）
    for trig in ('T1b_LEVEL', 'T1a'):
        r = pick(c, 'REINVEST_NEW', trig)
        DY = acct(c, r.exec_hash)['DY']
        nn = DY[:, E.DY_NEWN]
        lst = DY[:, E.DY_LISTN]
        m = lst > 0
        for q in (10, 50, 90):
            v = float(np.percentile(nn[m], q)) if m.any() else np.nan
            put('S0-B', '当日合法 new 集合容量（推导段；REINVEST_NEW %s H20）' % trig, 'BASE_RATE_NEW_NAMES_PER_DAY_Q%d' % q, v, 'count', 'INFO', 'accounts_run/deriv（new_n）',
                '源名单非空日 %d；空 new 日 %d' % (int(m.sum()), int(((nn == 0) & m).sum())))
            L('G-P-03', 'new_names_per_day', trig, 'Q%d' % q, '2010-2018', 'quantile', v, 'count', int(m.sum()))
    # 半量后余半再触发
    for trig, panel in (('T1b_LEVEL', c.lvl), ('T1a', c.t1a)):
        r = pick(c, 'EXIT_HALF', trig)
        ti, tf = trades(c, r.exec_hash)
        h = (ti[:, 4] == E.OK_EXIT_HALF) & (ti[:, 5] == 1)
        df = pd.DataFrame(dict(lot=ti[h, 2], d=ti[h, 0], s=ti[h, 1], due=ti[h, 6])).groupby('lot').agg(d=('d', 'max'), s=('s', 'first'), due=('due', 'first'))
        n = len(df)
        hit = 0
        for row in df.itertuples():
            lo, hi = int(row.d) + 1, min(int(row.due) - 1, c.d19 - 1)
            if hi >= lo and np.any(np.asarray(panel[lo:hi + 1, int(row.s)]) == 1):
                hit += 1
        v = hit / n if n else np.nan
        put('S0-B', '半量后余半到期前再触发份额（推导段；EXIT_HALF %s H20）' % trig, 'BASE_RATE_HALF_RETRIGGER_SHARE' if trig == 'T1b_LEVEL' else 'BASE_RATE_HALF_RETRIGGER_SHARE_T1A',
            v, 'share', 'INFO', 'trades_parts/deriv + triggers', '半量批次 %d；LEVEL 为持续状态，再触发份额高不等于几何减半（主 M4 不再开 episode）' % n)
        L('G-P-05', 'half_retrigger_share', trig, 'EXIT_HALF', '2010-2018', 'share', v, 'share', n)
    # T1a ∩ T8（持仓域：H20 NATIVE NONE 账户的物理持仓证券日）
    r = pick(c, 'NATIVE', 'NONE')
    ti, tf = trades(c, r.exec_hash)
    df = pd.DataFrame(dict(d=ti[:, 0], s=ti[:, 1], q=np.where(ti[:, 5] == 0, tf[:, 0], -tf[:, 0])))
    held_days = set()
    for s, g in df.groupby('s'):
        g = g.groupby('d').q.sum().sort_index()
        inv = g.cumsum()
        days = inv.index.to_numpy()
        vals = inv.to_numpy()
        for k in range(len(days)):
            if vals[k] > 1e-9:
                end = days[k + 1] if k + 1 < len(days) else c.d19
                for d in range(days[k], min(end, c.d19)):
                    held_days.add((d, s))
    hd = np.array(sorted(held_days))
    a = np.asarray(c.t1a[hd[:, 0], hd[:, 1]])
    b = np.asarray(c.t8[hd[:, 0], hd[:, 1]])
    ov = int(((a == 1) & (b == 1)).sum())
    t8n = int((b == 1).sum())
    put('S0-B', 'T1a ∩ T8 持仓证券日（推导段；H20 NATIVE NONE 持仓域）', 'BASE_RATE_T1A_T8_OVERLAP_SECURITY_DAYS', ov, 'count', 'INFO', 'triggers + trades_parts/deriv',
        '持仓证券日 %d；T8 = 1 共 %d' % (len(hd), t8n))
    put('S0-B', 'T8 落在 T1a 坏状态的份额', 'BASE_RATE_T8_IN_T1A_BAD_STATE_SHARE', ov / t8n if t8n else np.nan, 'share', 'INFO', 'triggers', '')
    L('G-P-08', 't1a_t8_overlap', 'held_security_days', 'T1a&T8', '2010-2018', 'count', float(ov), 'count', len(hd))
    L('G-P-08', 't8_in_t1a_bad_state_share', 'held_security_days', 'T8', '2010-2018', 'share', ov / t8n if t8n else np.nan, 'share', t8n)
    # 退出名字次日重选（只读；M5 不建账户）
    import e6q_acct as A
    mk = A.Market()
    ptr, col, w = mk.formation(O.MAIN_FORM, 'HG10')
    r = pick(c, 'NATIVE', 'T1b_LEVEL')
    IN = acct(c, r.exec_hash)['IN_i']
    m = IN[:, E.IN_KIND] == E.KD_TRIG
    d, s = IN[m, E.IN_DAY], IN[m, E.IN_SEC]
    re = np.array([E.in_csr(ptr, col, int(dd) + 1, int(sv)) if dd + 1 < c.d19 else False for dd, sv in zip(d, s)])
    put('S0-B', '退出名字次日重选份额（只读；NATIVE LEVEL H20 意向 → 次日源名单）', 'BASE_RATE_EXIT_NAME_RESELECTED_NEXT_DAY', float(re.mean()) if len(re) else np.nan, 'share', 'INFO',
        'accounts_run/deriv + source', 'M5"次日会重入所以今天不卖"只作前视反例，不建账户')


# ------------------------------------------------------------------ G-P-06 / 07 / 09–12
def gp06(c):
    for trig in ('T1a', 'T1b_LEVEL'):
        r = pick(c, 'NATIVE', trig)
        import e6q_run as RN
        key = RN.shadow_key(r.to_dict())
        p = O.P('accounts_run', 'shadow_deriv', key[:2], '%s.npz' % key)
        if not os.path.exists(p):
            L('G-P-06', 'firsthit_hazard', trig, 'H20', '2010-2018', 'ratio', np.nan, 'ratio', status='NOT_COMPUTABLE')
            continue
        z = np.load(p, allow_pickle=False)
        hits, risk = float(z['HITS'][:c.d19].sum()), float(z['RISK'][:c.d19].sum())
        panel = np.asarray(c.t1a if trig == 'T1a' else c.lvl)
        L('G-P-06', 'firsthit_hazard', trig, 'H20', '2010-2018', 'first_events_over_risk_lot_days', hits / risk if risk else np.nan, 'ratio', int(risk))
        L('G-P-06', 'firsthit_events', trig, 'H20', '2010-2018', 'count', hits, 'count', int(risk))


def gp07(c):
    p = O.P('randoms', 'random_paths_A2.csv')
    if not os.path.exists(p):
        return
    P = pd.read_csv(p, keep_default_na=False, na_values=[''])
    P = P[P.status == 'OK']
    for mech in ('RANDOM_TARGET_WITHIN_ARM', 'RANDOM_TARGET_SOURCE_DOMAIN'):
        X = P[P.mechanism == mech]
        for e, g in X.groupby('owner_exec_id'):
            r = c.R.set_index('exec_id').loc[e]
            if not (r.form == O.MAIN_FORM and r.memory == 'HG10' and r.H == '20'):
                continue
            for s in DSEG:
                tot = g['rtfeas_%s' % s].sum() + g['rtid_%s' % s].sum() + g['rtlim_%s' % s].sum() + g['rtnom_%s' % s].sum()
                if tot <= 0:
                    continue
                L('G-P-07', 'match_status_share', '%s|%s|%s' % (r.arm, r.trigger, mech), 'IDENTITY', s, 'share', float(g['rtid_%s' % s].sum() / tot), 'share', int(tot))
                L('G-P-07', 'match_status_share', '%s|%s|%s' % (r.arm, r.trigger, mech), 'ALGORITHM_LIMIT', s, 'share', float(g['rtlim_%s' % s].sum() / tot), 'share', int(tot))
                L('G-P-07', 'rand_mean_D', '%s|%s|%s' % (r.arm, r.trigger, mech), 'vs_same_arm_parent', s, 'mean', float(g['D_%s' % s].mean()), 'ann_pp', len(g))


def gp_stats(c):
    """G-P-10（两个密度）、G-P-11（卖半 × 再投半差中差）：A2 统计（tmp/a2stats）推导段行。"""
    root = O.P('tmp', 'a2stats', 'statistics')
    dn = O.read_csv(os.path.join(root, 'density_E6q.csv'))
    for r in dn[(dn.segment.isin(DSEG)) & (dn.A_cny.astype(float) == 1e8) & (dn.kappa.astype(float) == 0.5) & (dn.exponent.astype(float) == 0.5)].itertuples(index=False):
        rr = c.R.set_index('exec_id').loc[r.exec_id]
        L('G-P-10', 'value_density', '%s|%s|H%s' % (rr.arm, rr.trigger, rr.H), r.reference_kind, r.segment, 'ratio', float(r.value_density) if r.value_density != '' else np.nan,
          'ann_pp_per_turn', status='COMPUTED' if r.denominator_status == 'OK' else 'NOT_POSITIVE_DENOMINATOR')
        L('G-P-10', 'd_turn', '%s|%s|H%s' % (rr.arm, rr.trigger, rr.H), r.reference_kind, r.segment, 'diff', float(r.d_turn), 'turn')
    sm = O.read_csv(os.path.join(root, 'account_summary_E6q.csv')).set_index(['exec_id', 'segment'])
    for cpd in O.read_csv(O.P('registration', 'compound_contrasts_E6q.csv')).groupby('contrast_id'):
        cid, g = cpd
        for s in DSEG:
            v = sum(float(x.coefficient) * float(sm.loc[(x.term_exec_id, s), 'net_ann_pp']) for x in g.itertuples(index=False))
            L('G-P-11' if g.kind.iloc[0] == 'EXIT_X_RECYCLE_HALF' else 'G-P-08', 'compound_contrast', g.kind.iloc[0], cid, s, 'diff_in_diff', v, 'ann_pp', 4)


def gp09_12(c):
    """G-P-09（日龄剖面）/ G-P-12（入场信息 × 持久性）：H20 NATIVE NONE 账户批次（推导段）在 landmark 年龄的前向超额（T+1 VWAP 起 q 日，减 clean 基准）；
    G-P-12 按入场日源 DEV 权重（取向后好度）三分位分组。"""
    r = pick(c, 'NATIVE', 'NONE')
    ti, tf = trades(c, r.exec_hash)
    b = (ti[:, 5] == 0) & (ti[:, 4] == E.OK_REGULAR)
    lots = pd.DataFrame(dict(lot=ti[b, 2], s=ti[b, 1], e0=ti[b, 0], due=ti[b, 6]))
    import e6q_acct as A
    mk = A.Market()
    ptr, col, w = mk.formation(O.MAIN_FORM, 'HG10')
    wv = np.full(len(lots), np.nan)
    for i, (s, e0) in enumerate(zip(lots.s.to_numpy(), lots.e0.to_numpy())):
        f = int(e0) - 1
        if f < 0:
            continue
        a_, b_ = ptr[f], ptr[f + 1]
        k = np.searchsorted(col[a_:b_], s)
        if k < b_ - a_ and col[a_ + k] == s:
            wv[i] = w[a_ + k]
    lots['w'] = wv
    lots['tert'] = pd.qcut(lots.w.rank(method='first'), 3, labels=['LOW', 'MID', 'HIGH']) if lots.w.notna().sum() > 30 else 'NA'
    for a in (1, 2, 3, 5, 10, 15):
        Tv = lots.e0.to_numpy() + a - 1
        ok = Tv < c.d19 - 1
        for q in (1, 5, 10):
            s0, s1 = Tv + 1, Tv + 1 + q
            cens = s1 > c.d19 - 1
            m = ok & ~cens
            with np.errstate(all='ignore'):
                x = (np.asarray(c.pv[np.minimum(s1, c.T - 1), lots.s.to_numpy()]) / np.asarray(c.pv[np.minimum(s0, c.T - 1), lots.s.to_numpy()]) - 1.0) - \
                    (c.cumb[np.minimum(s1, c.T - 1)] / c.cumb[np.minimum(s0, c.T - 1)] - 1.0)
            m = m & np.isfinite(x)
            L('G-P-09', 'landmark_fwd_excess', 'age%d' % a, 'q%d' % q, '2010-2018', 'mean_bp', float(np.mean(x[m]) * 1e4) if m.any() else np.nan, 'bp', int(m.sum()))
            if a in (1, 10) and q == 5:
                for t in ('LOW', 'HIGH'):
                    mm = m & (lots.tert.astype(str).to_numpy() == t)
                    L('G-P-12', 'landmark_fwd_excess_by_entry_strength', 'age%d|%s' % (a, t), 'q5', '2010-2018', 'mean_bp', float(np.mean(x[mm]) * 1e4) if mm.any() else np.nan, 'bp',
                      int(mm.sum()))


def seal(c, t0):
    files = []
    for sub in ('registration', 'accounts_run/deriv', 'accounts_run/deriv_fb', 'accounts_run/shadow_deriv', 'trades_parts/deriv', 'checkpoints', 'randoms', 'diagnostics', 'verify'):
        base = O.P(*sub.split('/'))
        if not os.path.exists(base):
            continue
        for dp, _, fns in os.walk(base):
            for fn in fns:
                if '.tmp' in fn or fn == 'seal_A2.json' or fn == 'seal_A2_manifest.txt':
                    continue
                files.append(os.path.join(dp, fn))
    files.sort()
    lines = ['%s  %s' % (O.sha_file(p), O.rel(p)) for p in files]
    O.atomic_write_text(O.P('registration', 'seal_A2_manifest.txt'), '\n'.join(lines) + '\n')
    s = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=len(files), sha256_manifest=O.sha_file(O.P('registration', 'seal_A2_manifest.txt')),
             first_post_segment_write_at='', g1_rows=len(ROWS), note='推导段（2010-2014、2015-2018）全部预登记账户 / 反馈 / WARM / 影子 / 随机已跑；G1 已封存；之后才写后段')
    O.atomic_write_json(O.P('registration', 'seal_A2.json'), s)
    return s


def main():
    t0 = time.time()
    c = setup()
    gp01_02(c)
    s0b(c)
    gp06(c)
    gp07(c)
    gp_stats(c)
    gp09_12(c)
    G1 = pd.DataFrame(ROWS, columns=LCOLS)
    O.atomic_write_csv(O.P('diagnostics', 'G1_E6q.csv'), G1)
    # G 账本：状态只打标签（不选支）
    LG = O.read_csv(O.P('registration', 'ledger_G_E6q.csv'), dtype=str).fillna('')
    for i, r in LG.iterrows():
        g = G1[G1.block == r.g_id]
        LG.loc[i, 'result_row'] = 'diagnostics/G1_E6q.csv block=%s rows=%d' % (r.g_id, len(g))
        LG.loc[i, 'state'] = 'PRESPECIFIED_DISCRIMINATING_TEST' if len(g) else 'NOT_YET_SUPPORTED'
    O.atomic_write_csv(O.P('registration', 'ledger_G_E6q.csv'), LG)
    for gid in sorted(set(G1.block)):
        put('S0-M', '第一道 probe（推导段）%s' % gid, 'G1_%s' % gid.replace('-', '_'), int((G1.block == gid).sum()), 'count', 'INFO', 'diagnostics/G1_E6q.csv', '只打标签不选支、不删账户')
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6q_part2.csv'), pd.DataFrame(ST0))
    s = seal(c, t0)
    put('S0-M', 'seal_A2', 'SEAL_A2_WRITTEN_AT', s['written_at'], 'count', 'INFO', 'registration/seal_A2.json', 'n_files = %d' % s['n_files'])
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6q_part2.csv'), pd.DataFrame(ST0))
    O.write_receipt('E6q_g1', [O.P('diagnostics', 'G1_E6q.csv'), O.P('diagnostics', 'stage0_E6q_part2.csv'), O.P('registration', 'seal_A2.json')], code=[__file__, O.__file__],
                    g1_rows=len(G1), seal_files=s['n_files'], wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(g1_rows=len(G1), blocks=G1.block.value_counts().to_dict(), s0b=len(ST0), seal=s['written_at']), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
