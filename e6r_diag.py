# -*- coding: utf-8 -*-
"""E6r 诊断（plan §10；附录 B.23 / B.19；brief §0.1 #22）：D1–D12 长格式、landmark、T0 → age1 转移（四分母）、359 个局部快照、两层投影表、门反事实。
只读账户结果（accounts_run）、成交日志（trades_parts）、形成层缓存（overlay）与统计表；不改任何经济对象。
  python3 e6r_diag.py --phase B                        正式（全史；D3 只推导段，plan R04）
  python3 e6r_diag.py --phase A2 --root tmp/dryrun     空跑（推导段数据，后段行按状态标出）
口径：前向超额 = VWAP(d0) → VWAP(d0 + q)（后复权）减同窗口 clean 等权基准，终点超出授权末日 → RIGHT_CENSORED；landmark 只用截至 T 已知记录定状态；
日聚类 se（同 landmark / 形成日配对聚类）；资本贡献 = 批次名义 × 年龄段超额 / 账户平均 NAV / 年数（ann_pp）。"""
import os
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6r_core as O
import e6r_engine as E
import e6r_acct as A

LCOLS = ['block', 'item', 'key1', 'key2', 'segment', 'stat', 'value', 'unit', 'n', 'status', 'query_id']
LMCOLS = ['exec_id', 'landmark_age', 'state', 'q', 'weighting', 'n', 'mean_fwd_excess_bp', 'lo', 'hi', 'status']
SEG4 = list(O.SEGS)
SEG6 = SEG4 + ['FULL', 'G4']
LANDMARK_AGES = (1, 2, 3, 5, 10, 15, 20, 30)
QS = (1, 5, 10, 20)
GATE_SCHEMES = ('GATE_STATE', 'GATE_TILT', 'DROP_T3')
TILT_FAMILY = ('TILT_CVR_L050', 'TILT_CVR_L025', 'TILT_SIZE_L050', 'GATE_TILT', 'TILT_CVR5_L050', 'TILT_CVR_CELL_L050')
DIAG_NAMES = ['entry_age', 'transition', 'cvr_size', 'tilt_exit', 'concentration', 'risk', 'state_coverage', 'second_block', 'h40', 'tail30',
              'adaptation_bridge', 'closure']
ST_NM = {1: 'BAD', 0: 'GOOD', -1: 'UNKNOWN'}
G = {}
ROWS = {i: [] for i in range(1, 13)}


def L(i, block, item, key1, key2, segment, stat, value, unit, n='', status='COMPUTED', q=''):
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        value, status = '', ('UNKNOWN' if status == 'COMPUTED' else status)
    ROWS[i].append(dict(block=block, item=item, key1=key1, key2=key2, segment=segment, stat=stat, value=value, unit=unit, n=n, status=status,
                        query_id=q or 'QRY-%s' % block))


# ------------------------------------------------------------------ 载入
def setup(phase, root):
    cd = O.cache_dir()
    P = lambda k: np.load(os.path.join(cd, 'panels', k + '.npy'), mmap_mode='r')
    G['cd'] = cd
    G['phase'] = phase
    G['root'] = root
    G['dates'] = np.load(os.path.join(cd, 'panels', 'dates.npy'))
    G['codes'] = np.load(os.path.join(cd, 'panels', 'codes.npy'))
    G['T'] = len(G['dates'])
    G['d19'] = int(np.searchsorted(G['dates'], '2019-01-01'))
    G['d_end'] = G['T'] if phase == 'B' else G['d19']
    G['last'] = G['d_end'] - 1
    G['sub'] = 'full' if phase == 'B' else 'deriv'
    G['segi'] = O.segs_of_dates(G['dates'])
    G['years'] = np.array([int(d[:4]) for d in G['dates']])
    for k in ('pv_ff', 'pc_ff', 'zsize', 'iskid', 'ind', 'adv20', 'sig20', 'tail_cvr', 'tail_share'):
        G[k] = P(k)
    G['cumbench'] = np.cumprod(1.0 + np.nan_to_num(np.load(os.path.join(cd, 'panels', 'bench.npy')).astype(float)))
    mk = A.Market()
    G['mk'] = mk
    G['lvl'] = np.asarray(mk.lvl)
    G['cvr20'] = np.asarray(mk.cvr20)
    G['R'] = O.read_csv(O.P('registration', 'registry_E6r.csv'))
    G['reg'] = G['R'].set_index('exec_id', drop=False)
    G['lid2e'] = dict(zip(G['R'].logical_id, G['R'].exec_id))
    G['prim'] = json.load(open(O.P('registration', 'spec', 'primary.json'), encoding='utf-8'))
    G['claims'] = json.load(open(O.P('registration', 'spec', 'claims.json'), encoding='utf-8'))
    G['f'] = {}
    G['ov'] = {}


def formation(form, mem):
    if (form, mem) not in G['f']:
        G['f'][(form, mem)] = G['mk'].formation(form, mem)
    return G['f'][(form, mem)]


def overlay(form, mem):
    if (form, mem) not in G['ov']:
        G['ov'][(form, mem)] = np.load(os.path.join(G['cd'], 'overlay', '%s|%s.npz' % (form, mem)), allow_pickle=False)
    return G['ov'][(form, mem)]


def acct(h):
    return np.load(O.P('accounts_run', G['sub'], h[:2], '%s.npz' % h), allow_pickle=False)


def trades(h):
    a = np.load(O.P('trades_parts', 'deriv', h[:2], '%s.npz' % h), allow_pickle=False)
    if G['phase'] != 'B':
        return a['TL_i'], a['TL_f']
    b = np.load(O.P('trades_parts', 'full', h[:2], '%s.npz' % h), allow_pickle=False)
    return np.concatenate([a['TL_i'], b['TL_i']]), np.concatenate([a['TL_f'], b['TL_f']])


def fwd(sec, d0, q, last=None):
    last = G['last'] if last is None else last
    pv, cb = G['pv_ff'], G['cumbench']
    d0 = np.asarray(d0, np.int64)
    sec = np.asarray(sec, np.int64)
    d1 = d0 + np.asarray(q, np.int64)
    cens = d1 > last
    a = np.clip(np.minimum(d0, last), 0, None)
    b = np.clip(np.minimum(d1, last), 0, None)
    with np.errstate(all='ignore'):
        x = (np.asarray(pv[b, sec], float) / np.asarray(pv[a, sec], float) - 1.0) - (cb[b] / cb[a] - 1.0)
    return np.where(cens, np.nan, x), cens


def day_se(x, d):
    if len(x) < 2:
        return np.nan
    g = pd.DataFrame(dict(d=d, x=x)).groupby('d').x.mean().to_numpy()
    return float(np.std(g, ddof=1) / np.sqrt(len(g))) if len(g) > 1 else np.nan


def lots_frame(ti, tf):
    """买入批次（REGULAR / EXTRA；不含部署）：e0、sec、qty、名义、due、计划票据额、T0 标签（成交日志列）；卖出合计 ≥ qty 的批次记关闭日 cl。"""
    b = (ti[:, 5] == 0) & np.isin(ti[:, 4], (E.OK_REGULAR, E.OK_EXTRA))
    df = pd.DataFrame(dict(lot=ti[b, 2], sec=ti[b, 1], e0=ti[b, 0], qty=tf[b, 0], nt=tf[b, 1], due=ti[b, 6], plan=np.nan_to_num(tf[b, 4]),
                           lab=ti[b, 9] if ti.shape[1] > 9 else 0, lab20=ti[b, 10] if ti.shape[1] > 10 else 0, st=ti[b, 11] if ti.shape[1] > 11 else -9,
                           kind=ti[b, 4]))
    lots = df.groupby('lot', as_index=False).agg(sec=('sec', 'first'), e0=('e0', 'min'), qty=('qty', 'sum'), nt=('nt', 'sum'), due=('due', 'max'),
                                                  plan=('plan', 'sum'), lab=('lab', 'first'), lab20=('lab20', 'first'), st=('st', 'first'), kind=('kind', 'first'))
    s = ti[:, 5] == 1
    sells = pd.DataFrame(dict(lot=ti[s, 2], day=ti[s, 0], kind=ti[s, 4], qty=tf[s, 0], nt=tf[s, 1]))
    last = sells.groupby('lot').agg(close_day=('day', 'max'), sold=('qty', 'sum'))
    lots = lots.merge(last, left_on='lot', right_index=True, how='left')
    closed = lots.sold.fillna(0).to_numpy() >= lots.qty.to_numpy() * (1 - 1e-9)
    lots['cl'] = np.where(closed, lots.close_day.fillna(-1), -1).astype(np.int64)
    return lots, sells


def segname(d):
    return G['segi'][np.clip(np.asarray(d, np.int64), 0, G['T'] - 1)]


def accounts_focus():
    """主 9 + 各自政策参照 / 无退出父 + E owner / reference（去重，保序）。"""
    R = G['reg']
    out = []
    for lid in G['prim']['primary9']:
        e = G['lid2e'][lid]
        for x in (e, R.loc[e].policy_reference_exec_id, R.loc[e].noexit_same_overlay_exec_id):
            if x and x not in out:
                out.append(x)
    for c in G['claims']:
        for k in ('owner', 'reference'):
            x = G['lid2e'].get(c[k])
            if x and x not in out:
                out.append(x)
    return out


# ------------------------------------------------------------------ landmark（plan §10）
def state_vec(T, iv, known, hs, hd, fo):
    st = np.full(len(T), 'NOT_TRIGGERED', dtype=object)
    st[known & (iv == T)] = 'BAD_STATE'
    st[known & (iv < T)] = 'REQUEST_PENDING'
    st[known & (hs == 1) & ~hd] = 'HALF_PENDING'
    st[known & (hs == 1) & hd] = 'HALF_DONE_RESIDUAL'
    st[known & (hs == 2)] = 'REARMED'
    st[known & fo] = 'DEADLINE_OVERRIDDEN'
    return st


def landmark(e):
    r = G['reg'].loc[e]
    H = int(float(r.funding_H))
    z = acct(r.exec_hash)
    IN = z['IN_i']
    ti, tf = trades(r.exec_hash)
    lots, sells = lots_frame(ti, tf)
    if not len(lots):
        return []
    half_done = sells[sells.kind == E.OK_EXIT_HALF].groupby('lot').day.max()
    forced = sells[sells.kind == E.OK_DEADLINE].groupby('lot').day.min()
    first_int, rearm_day = {}, {}
    for lid, d, k in zip(IN[:, E.IN_LID].tolist(), IN[:, E.IN_DAY].tolist(), IN[:, E.IN_KIND].tolist()):
        if k in (E.KD_TRIG, E.KD_RAND) and lid not in first_int:
            first_int[lid] = d
        if k == E.KD_REARM and lid not in rearm_day:
            rearm_day[lid] = d
    lid = lots.lot.to_numpy()
    e0, sec, cl, nt, st0 = lots.e0.to_numpy(), lots.sec.to_numpy(), lots.cl.to_numpy(), lots.nt.to_numpy(), lots.st.to_numpy()
    idd = np.array([first_int.get(int(l), -1) for l in lid], np.int64)
    hdd = np.array([int(half_done.get(int(l), -1)) for l in lid], np.int64)
    fdd = np.array([int(forced.get(int(l), -1)) for l in lid], np.int64)
    rdd = np.array([rearm_day.get(int(l), -1) for l in lid], np.int64)
    half = r.exit_op in ('EXIT_HALF_REARM', 'GATE_REARM_1E8', 'GATE_REARM_5E8')
    acc = {}
    for a in LANDMARK_AGES:
        if a > max(H, 30):
            continue
        T = e0 + a - 1
        v = (T < G['last']) & ((cl < 0) | (cl > T))
        if not v.any():
            continue
        Tv, sv, iv = T[v], sec[v], idd[v]
        known = (iv >= 0) & (iv <= Tv)
        hs = np.where(half & known, np.where((rdd[v] >= 0) & (rdd[v] <= Tv), 2, 1), 0)
        hd = (hdd[v] >= 0) & (hdd[v] <= Tv)
        fo = (fdd[v] >= 0) & (fdd[v] <= Tv)
        st = state_vec(Tv, iv, known, hs, hd, fo)
        if a == 1:
            st_t0 = np.array(['T0_%s' % ST_NM.get(int(x), 'UNKNOWN') for x in st0[v]], dtype=object)
        val = nt[v]
        for q in QS:
            x, cens = fwd(sv, Tv + 1, q)
            ok = ~cens & np.isfinite(x)
            groups = [(s_, st == s_) for s_ in np.unique(st)]
            if a == 1:
                groups += [(s_, st_t0 == s_) for s_ in np.unique(st_t0)]
            for s_, m in groups:
                o = acc.setdefault((a, s_, q), dict(x=[], w=[], d=[], cens=0))
                o['cens'] += int((m & cens).sum())
                o['x'].append(x[m & ok])
                o['w'].append(val[m & ok])
                o['d'].append(Tv[m & ok])
    out = []
    for (a, st_, q), o in sorted(acc.items()):
        x = np.concatenate(o['x'])
        w = np.concatenate(o['w'])
        d = np.concatenate(o['d'])
        for wt in ('EQUAL', 'CAPITAL'):
            if not len(x):
                out.append(dict(exec_id=e, landmark_age=a, state=st_, q=q, weighting=wt, n=0, mean_fwd_excess_bp='', lo='', hi='',
                                status='RIGHT_CENSORED' if o['cens'] else 'NOT_APPLICABLE'))
                continue
            ww = np.ones_like(x) if wt == 'EQUAL' else np.where(np.isfinite(w) & (w > 0), w, 0.0)
            if ww.sum() <= 0:
                out.append(dict(exec_id=e, landmark_age=a, state=st_, q=q, weighting=wt, n=int(len(x)), mean_fwd_excess_bp='', lo='', hi='', status='NOT_APPLICABLE'))
                continue
            mean = float((x * ww).sum() / ww.sum())
            dfm = pd.DataFrame(dict(d=d, xw=x * ww, w=ww)).groupby('d').sum()
            dfm = dfm[dfm.w > 0]
            dm = (dfm.xw / dfm.w).to_numpy()
            se = float(np.std(dm, ddof=1) / np.sqrt(len(dm))) if len(dm) > 1 else np.nan
            out.append(dict(exec_id=e, landmark_age=a, state=st_, q=q, weighting=wt, n=int(len(x)), mean_fwd_excess_bp=mean * 1e4,
                            lo=(mean - 1.96 * se) * 1e4 if np.isfinite(se) else '', hi=(mean + 1.96 * se) * 1e4 if np.isfinite(se) else '',
                            status='COMPUTED' if np.isfinite(se) else 'UNKNOWN'))
    return out


# ------------------------------------------------------------------ T0 → age1 转移（四分母）+ D2
def transitions(e):
    r = G['reg'].loc[e]
    ti, tf = trades(r.exec_hash)
    lots, _ = lots_frame(ti, tf)
    rows = []
    if not len(lots):
        return rows
    e0, sec = lots.e0.to_numpy(), lots.sec.to_numpy()
    t0 = np.array([ST_NM.get(int(x), 'UNKNOWN') for x in lots.st.to_numpy()], dtype=object)
    a1 = np.array([ST_NM.get(int(x), 'UNKNOWN') for x in np.asarray(G['lvl'][np.clip(e0, 0, G['T'] - 1), sec])], dtype=object)
    seg = segname(e0)
    df = pd.DataFrame(dict(seg=seg, t0=t0, a1=a1, e0=e0, sec=sec, plan=lots.plan.to_numpy(), nt=lots.nt.to_numpy()))
    for s in SEG4 + ['FULL']:
        x = df if s == 'FULL' else df[df.seg == s]
        if not len(x):
            continue
        names = x.drop_duplicates(['e0', 'sec'])
        dens = {'NAMES': names.groupby(['t0', 'a1']).size(), 'BATCHES': x.groupby(['t0', 'a1']).size(),
                'SOURCE_TICKET_CNY': x.groupby(['t0', 'a1']).plan.sum(), 'NET_BUY_CNY': x.groupby(['t0', 'a1']).nt.sum()}
        for dn, ser in dens.items():
            tot = float(ser.sum())
            if tot <= 0:
                continue
            for (a_, b_), v in ser.items():
                rows.append(dict(exec_id=e, segment=s, t0_state=a_, age1_state=b_, denominator=dn, value=float(v), share=float(v) / tot, status='COMPUTED'))
    return rows


# ------------------------------------------------------------------ 两层投影表 / 快照 / 门反事实
def allocation_projection():
    rows = []
    for r in G['R'].itertuples(index=False):
        if r.weight_scheme not in TILT_FAMILY:
            continue
        z = acct(r.exec_hash)
        DY = z['DY']
        nav = DY[:, E.DYI['nav_post']]
        nd = len(DY)
        for s in SEG6:
            if s == 'G4':
                rows.append(dict(exec_id=r.exec_id, segment=s, status='NOT_APPLICABLE'))
                continue
            m = np.ones(nd, bool) if s == 'FULL' else (G['segi'][:nd] == s)
            m &= np.arange(nd) < G['d_end']
            if not m.any():
                rows.append(dict(exec_id=r.exec_id, segment=s, n_cohort_days=0, status='NOT_RUN'))
                continue
            act = DY[m, E.DY_OVCN] > 0
            with np.errstate(all='ignore'):
                # 总额恒等：算子后票据（常规 + 额外）= 计划 FLAT 票据（常规 + 额外）− 门删额（GATE_TILT 先删门掉票据、不回填；纯倾斜门删额 = 0）
                bt = DY[m, E.DY_OVB] + DY[m, E.DY_OVXB]
                rel = np.abs((DY[m, E.DY_OVX] + DY[m, E.DY_OVXX]) - (bt - DY[m, E.DY_OVGV])) / np.maximum(bt, 1.0)
                capv = DY[m, E.DY_OVCAPV] / np.where(nav[m] > 0, nav[m], 1.0)
                indv = DY[m, E.DY_OVINDV] / np.where(nav[m] > 0, nav[m], 1.0)
            rows.append(dict(exec_id=r.exec_id, segment=s, n_cohort_days=int(act.sum()), n_projection_calls=int(act.sum()),
                             n_solver_fallback=int((DY[m, E.DY_OVST] != 0).sum()), max_rel_total_diff=float(np.nanmax(rel[act])) if act.any() else 0.0,
                             max_cap_violation=float(np.nanmax(capv)) if act.any() else 0.0, max_industry_violation=float(np.nanmax(indv)) if act.any() else 0.0,
                             n_na_pinned=int(DY[m, E.DY_OVNAN].sum()), n_zero_support_blocked=int((DY[m, E.DY_OVST] == 2).sum()), status='COMPUTED'))
    return pd.DataFrame(rows, columns=['exec_id', 'segment', 'n_cohort_days', 'n_projection_calls', 'n_solver_fallback', 'max_rel_total_diff', 'max_cap_violation',
                                       'max_industry_violation', 'n_na_pinned', 'n_zero_support_blocked', 'status'])


def snapshots():
    """local_snapshot_refs 359 条：两层预算 / 费用桥（225）= owner 逐段计划总预算（常规 ov_B + 额外 ov_xB）= 实付名义（paid_reg + paid_ext）+ 未花（余量）；
    实付费按成交名义份额分摊（费用含在 NAV 侧，桥不含费口径）；格预算 / NA 固定漂移 = 引擎逐日最大值 / NAV。另两类（原始倾斜同格票据 122、GATE_TILT 部分随机 12）
    本轮不另跑（brief：局部快照只读、不跑），写 NOT_APPLICABLE 与原因。"""
    S = O.read_csv(O.P('registration', 'local_snapshot_refs_E6r.csv'))
    rows = []
    for x in S.itertuples(index=False):
        if x.kind != 'TWO_LAYER_BUDGET_AND_FEE_BRIDGE':
            why = {'RAW_TILT_WITHIN_CELL_TICKETS': '原始 CVR 两剂量同格票据：本轮不另跑（局部快照只读）；同格票据的可行性与 Σw / Σw² 守恒由 CELL 账户与 TICKETS 随机路径覆盖',
                   'REAL_GATE_RANDOM_TILT': 'GATE_TILT 部分随机（真实门 × 随机倾斜）：本轮不另跑；联合随机 JOINT 已覆盖，部分随机只作局部诊断',
                   'RANDOM_GATE_REAL_TILT': 'GATE_TILT 部分随机（随机门 × 真实倾斜）：本轮不另跑；联合随机 JOINT 已覆盖，部分随机只作局部诊断'}.get(x.kind, '')
            rows.append(dict(snapshot_id=x.snapshot_id, owner_exec_id=x.owner_exec_id, kind=x.kind, segment='FULL', n_snapshots=0, unspent_reason_top=why,
                             status='NOT_APPLICABLE'))
            continue
        r = G['reg'].loc[x.owner_exec_id]
        DY = acct(r.exec_hash)['DY']
        nd = len(DY)
        nav = DY[:, E.DYI['nav_post']]
        for s in SEG4 + ['FULL']:
            m = np.ones(nd, bool) if s == 'FULL' else (G['segi'][:nd] == s)
            m &= np.arange(nd) < G['d_end']
            if not m.any():
                rows.append(dict(snapshot_id=x.snapshot_id, owner_exec_id=x.owner_exec_id, kind=x.kind, segment=s, n_snapshots=0, status='NOT_RUN'))
                continue
            planned = float(DY[m, E.DY_OVB].sum() + DY[m, E.DY_OVXB].sum())
            paid = float(DY[m, E.DY_PAIDR].sum() + DY[m, E.DY_PAIDX].sum())
            fee = float(DY[m, E.DYI['fee']].sum())
            buy = float(DY[m, E.DYI['buy_val']].sum())
            sell = float(DY[m, E.DYI['sell_val']].sum())
            fee_buy = fee * buy / (buy + sell) if (buy + sell) > 0 else 0.0
            with np.errstate(all='ignore'):
                cd = float(np.nanmax(DY[m, E.DY_OVCELLD] / np.where(nav[m] > 0, nav[m], 1.0))) if m.any() else 0.0
                na = float(np.nanmax(DY[m, E.DY_OVNAD] / np.where(nav[m] > 0, nav[m], 1.0))) if m.any() else 0.0
            un = planned - paid
            rows.append(dict(snapshot_id=x.snapshot_id, owner_exec_id=x.owner_exec_id, kind=x.kind, segment=s, n_snapshots=int((DY[m, E.DY_OVCN] > 0).sum()),
                             planned_gross_budget_cny=planned, reserved_fee_cny=planned * O.FEE_RATE, actual_fee_cny=fee_buy, paid_notional_cny=paid, unspent_cny=un,
                             unspent_reason_top='UNFILLED_OR_CAPPED_AT_EXECUTION' if un > 1e-6 else '', cell_budget_max_abs_diff=cd if np.isfinite(cd) else 0.0,
                             na_pinned_max_abs_diff=na if np.isfinite(na) else 0.0, status='COMPUTED'))
    return pd.DataFrame(rows, columns=['snapshot_id', 'owner_exec_id', 'kind', 'segment', 'n_snapshots', 'planned_gross_budget_cny', 'reserved_fee_cny', 'actual_fee_cny',
                                       'paid_notional_cny', 'unspent_cny', 'unspent_reason_top', 'cell_budget_max_abs_diff', 'na_pinned_max_abs_diff', 'status'])


def update_snapshot_refs(root, SN):
    """注册件回填（附录 B.6："已注册"不算闭包）：computed_rows = 快照表中该 snapshot_id 的 COMPUTED 行数；status = COMPUTED（≥ 1 行）或 NOT_APPLICABLE（写缺因的行）。"""
    p = os.path.join(root, 'registration', 'local_snapshot_refs_E6r.csv')
    if not os.path.exists(p):
        p = O.P('registration', 'local_snapshot_refs_E6r.csv')
    L_ = pd.read_csv(p, dtype=str, keep_default_na=False)
    n = SN[SN.status == 'COMPUTED'].groupby('snapshot_id').size()
    L_['computed_rows'] = [int(n.get(s, 0)) for s in L_.snapshot_id]
    L_['status'] = ['COMPUTED' if n.get(s, 0) > 0 else 'NOT_APPLICABLE' for s in L_.snapshot_id]
    L_['table'] = 'diagnostics/entry_target_snapshot_E6r.csv'
    O.atomic_write_csv(p, L_)


def gate_counterfactual():
    """GATE / DROP / GATE_TILT 账户：被挡名字 = 同退出 FLAT 参照当日实际买入批次中、本账户形成层 ρ = 0 的名字（同 cohort）；
    两种反事实分列：按源退出（FLAT 参照该批次的实际关闭日；未关闭 → 截到授权末日）与持有到原 due；另报 q1 / q5 / q10 前向（不混成避免损失）。"""
    rows = []
    for r in G['R'].itertuples(index=False):
        if r.weight_scheme not in GATE_SCHEMES:
            continue
        ref = G['reg'].loc[r.exec_id].flat_same_exit_exec_id
        rf = G['reg'].loc[ref]
        ti, tf = trades(rf.exec_hash)
        lots, _ = lots_frame(ti, tf)
        lots = lots[lots.kind == E.OK_REGULAR]
        ptr, col, w = formation(r.form, r.memory)
        rho = overlay(r.form, r.memory)['rho|' + r.weight_scheme]
        e0 = lots.e0.to_numpy().astype(np.int64)
        sec = lots.sec.to_numpy().astype(np.int64)
        blocked = np.zeros(len(e0), bool)
        for i, (d, s) in enumerate(zip(e0 - 1, sec)):
            if d < 0:
                continue
            a, b = ptr[d], ptr[d + 1]
            k = a + np.searchsorted(col[a:b], s)
            if k < b and col[k] == s and not (rho[k] > 0):
                blocked[i] = True
        bl = lots[blocked]
        e0b, secb = e0[blocked], sec[blocked]
        cl = bl.cl.to_numpy()
        due = bl.due.to_numpy()
        hold_src = np.where(cl >= 0, cl - e0b, G['last'] - e0b)
        hold_due = np.maximum(due - e0b, 1)
        xs = {}
        for nm, qv in (('src', hold_src), ('due', hold_due)):
            x = np.full(len(e0b), np.nan)
            for qq in np.unique(qv):
                if qq <= 0:
                    continue
                mm = qv == qq
                x[mm], _ = fwd(secb[mm], e0b[mm], int(qq))
            xs[nm] = x
        for q in (1, 5, 10):
            xs['q%d' % q], _ = fwd(secb, e0b, q)
        seg = segname(e0b) if len(e0b) else np.array([])
        for s in SEG6:
            if s == 'G4':
                rows.append(dict(exec_id=r.exec_id, segment=s, status='NOT_APPLICABLE'))
                continue
            m = np.ones(len(e0b), bool) if s == 'FULL' else (seg == s)
            if not m.any():
                rows.append(dict(exec_id=r.exec_id, segment=s, n_blocked=0, blocked_capital_cny=0.0, status='NOT_RUN' if s in O.POST_SEGS and G['phase'] != 'B' else 'COMPUTED'))
                continue

            def mb(v):
                vv = v[m]
                vv = vv[np.isfinite(vv)]
                return float(vv.mean() * 1e4) if len(vv) else ''
            rows.append(dict(exec_id=r.exec_id, segment=s, n_blocked=int(m.sum()), blocked_capital_cny=float(bl.nt.to_numpy()[m].sum()), cf_source_exit_ret_bp=mb(xs['src']),
                             cf_due_ret_bp=mb(xs['due']), fwd_q1_bp=mb(xs['q1']), fwd_q5_bp=mb(xs['q5']), fwd_q10_bp=mb(xs['q10']), status='COMPUTED'))
    return pd.DataFrame(rows, columns=['exec_id', 'segment', 'n_blocked', 'blocked_capital_cny', 'cf_source_exit_ret_bp', 'cf_due_ret_bp', 'fwd_q1_bp', 'fwd_q5_bp',
                                       'fwd_q10_bp', 'status'])


# ------------------------------------------------------------------ D1–D12
def d1_entry_age(focus):
    """D1：实际 T0 CVR20 标签（成交日志 cvr_tertile_T0）× 批次日龄的 q1 / q5 / q10 前向超额（等权）与年龄段资本贡献（1–5 / 6–10 / 11–20 / 21–30；ann_pp）。"""
    for e in focus:
        r = G['reg'].loc[e]
        ti, tf = trades(r.exec_hash)
        lots, _ = lots_frame(ti, tf)
        if not len(lots):
            continue
        e0, sec, cl, nt, lab = lots.e0.to_numpy(), lots.sec.to_numpy(), lots.cl.to_numpy(), lots.nt.to_numpy(), lots.lab20.to_numpy()
        tg = '%s|%s|H%s|%s' % (r.weight_scheme, r.trigger, r.funding_H, r.exit_op)
        DY = acct(r.exec_hash)['DY']
        navm = float(np.nanmean(DY[:G['d_end'], E.DYI['nav_post']]))
        yrs = G['d_end'] / 252.0
        for a in (1, 5, 10):
            Ta = e0 + a - 1
            alive = (cl < 0) | (cl > Ta)
            for q in (1, 5, 10):
                x, cens = fwd(sec, Ta + 1, q)
                for code, t in ((1, 'T1'), (2, 'T2'), (3, 'T3'), (0, 'NA')):
                    m = alive & np.isfinite(x) & (lab == code)
                    L(1, 'D1', 'fwd_excess_q%d' % q, tg, 'age%d|%s' % (a, t), 'FULL', 'mean_bp', float(x[m].mean() * 1e4) if m.any() else np.nan, 'bp', int(m.sum()))
        for a0, a1 in ((1, 5), (6, 10), (11, 20), (21, 30)):
            T0_, T1_ = e0 + a0 - 1, e0 + a1
            alive = (cl < 0) | (cl > T0_)
            end = np.where(cl >= 0, np.minimum(cl, T1_), T1_)
            span = np.maximum(end - T0_, 0)
            for code, t in ((1, 'T1'), (2, 'T2'), (3, 'T3')):
                m = alive & (lab == code) & (span > 0)
                if not m.any():
                    continue
                x = np.full(m.sum(), np.nan)
                ss, dd, sp = sec[m], T0_[m], span[m]
                for qq in np.unique(sp):
                    mm = sp == qq
                    x[mm], _ = fwd(ss[mm], dd[mm], int(qq))
                c = np.nansum(nt[m] * x) / navm / yrs * 100.0 if navm > 0 else np.nan
                L(1, 'D1', 'capital_contribution', tg, 'age%d_%d|%s' % (a0, a1, t), 'FULL', 'ann_pp', float(c), 'ann_pp', int(m.sum()))


def d2_transition(TR, GC):
    for (e, s), x in TR.groupby(['exec_id', 'segment']):
        for (dn), y in x.groupby('denominator'):
            bg = y[(y.t0_state == 'BAD') & (y.age1_state == 'GOOD')].share.sum()
            gb = y[(y.t0_state == 'GOOD') & (y.age1_state == 'BAD')].share.sum()
            L(2, 'D2', 'T0_to_age1', e.split('|')[0], dn, s, 'share_BAD_to_GOOD', float(bg), 'share')
            L(2, 'D2', 'T0_to_age1', e.split('|')[0], dn, s, 'share_GOOD_to_BAD', float(gb), 'share')
    for r in GC.itertuples(index=False):
        if r.status != 'COMPUTED':
            continue
        for k in ('cf_source_exit_ret_bp', 'cf_due_ret_bp', 'fwd_q5_bp'):
            v = getattr(r, k)
            L(2, 'D2', 'gate_counterfactual', r.exec_id.split('|')[0], k, r.segment, 'mean_bp', float(v) if v != '' else np.nan, 'bp', r.n_blocked)


def d3_cvr_size():
    """D3：CVR20 × size 3 × 3（FLAT NONE H20 主坐标常规批次；age1 q5；只推导段，plan R04）：E6q 域（当日形成名单 = 最终 cohort，E6q D3 同式）与源域（当日全部有值证券）两列。"""
    R = G['R']
    r = R[(R.trigger == 'NONE') & (R.weight_scheme == 'FLAT') & (R.funding_H == '20') & (R.exit_op == 'NATIVE') & (R.form == O.MAIN_FORM) & (R.memory == 'HG10') &
          (R.scenario == O.FEAS)].iloc[0]
    ti, tf = trades(r.exec_hash)
    lots, _ = lots_frame(ti, tf)
    lots = lots[(lots.kind == E.OK_REGULAR) & (lots.e0 >= 1) & (lots.e0 < G['d19'])]
    e0, sec = lots.e0.to_numpy().astype(np.int64), lots.sec.to_numpy().astype(np.int64)
    T0 = e0 - 1
    x, cens = fwd(sec, e0, 5, last=G['d19'] - 1)
    ptr, col, w = formation(r.form, r.memory)
    for dom in ('cohort', 'source'):
        lc = tert(G['cvr20'], T0, sec, dom, ptr, col)
        ls = tert(G['zsize'], T0, sec, dom, ptr, col)
        for a in (1, 2, 3):
            for b in (1, 2, 3):
                m = (lc == a) & (ls == b) & np.isfinite(x)
                L(3, 'D3', 'cvr20_x_size_q5_age1', 'CVR20_T%d' % a, 'SIZE_T%d' % b, 'DERIV_2010_2018', '%s_domain|mean_bp' % dom,
                  float(x[m].mean() * 1e4) if m.any() else np.nan, 'bp', int(m.sum()))
    L(3, 'D3', 'right_censored', 'q5', '', 'DERIV_2010_2018', 'n', int(cens.sum()), 'count', status='RIGHT_CENSORED' if cens.any() else 'COMPUTED')


def tert(Xp, T0, sec, domain, ptr, col):
    lab = np.zeros(len(T0), np.int64)
    o = np.argsort(T0, kind='stable')
    ds = T0[o]
    cut = np.flatnonzero(np.r_[True, ds[1:] != ds[:-1], True])
    for a, b in zip(cut[:-1], cut[1:]):
        d = int(ds[a])
        idx = o[a:b]
        if d < 0:
            continue
        dom = np.asarray(Xp[d, col[ptr[d]:ptr[d + 1]]], float) if domain == 'cohort' else np.asarray(Xp[d], float)
        v = np.sort(dom[np.isfinite(dom)])
        if len(v) < 3 or v[0] == v[-1]:
            continue
        xx = np.asarray(Xp[d, sec[idx]], float)
        lo = np.searchsorted(v, xx, 'left')
        hi = np.searchsorted(v, xx, 'right')
        p = (lo + 0.5 * (hi - lo)) / len(v)
        lab[idx] = np.where(np.isfinite(xx), np.where(p < 1 / 3.0, 1, np.where(p > 2 / 3.0, 3, 2)), 0)
    return lab


def d4_tilt_exit():
    """D4：倾斜后不同权重组（成交日志算子标签 = 形成层三分位：T1 增配 / T2 / T3 减配）的退出意向、实际卖量、卖单 p、再入场、早退与正常到期（count / amount / unique）。"""
    R = G['R']
    for trig in ('T1b_LEVEL', 'T1a'):
        for sc in ('TILT_CVR_L050', 'GATE_TILT'):
            x = R[(R.trigger == trig) & (R.weight_scheme == sc) & (R.funding_H == '20') & (R.exit_op == 'NATIVE') & (R.form == O.MAIN_FORM) & (R.memory == 'HG10') &
                  (R.scenario == O.FEAS)]
            if not len(x):
                continue
            r = x.iloc[0]
            ti, tf = trades(r.exec_hash)
            lots, sells = lots_frame(ti, tf)
            lab = dict(zip(lots.lot, lots.lab))
            sells = sells.assign(lab=sells.lot.map(lab).fillna(0).astype(int))
            tg = '%s|%s|H20' % (sc, trig)
            for code, t in ((1, 'T1'), (2, 'T2'), (3, 'T3'), (0, 'NA')):
                lm = lots.lab == code
                sm = sells.lab == code
                early = sm & sells.kind.isin([E.OK_EXIT, E.OK_EXIT_HALF, E.OK_EXIT_REARM, E.OK_DEADLINE])
                due = sm & (sells.kind == E.OK_DUE)
                for k, v, u in (('lots_count', int(lm.sum()), 'count'), ('lots_amount', float(lots.nt[lm].sum()), 'CNY'), ('unique_names', int(lots.sec[lm].nunique()), 'count'),
                                ('early_exit_count', int(early.sum()), 'count'), ('early_exit_amount', float(sells.nt[early].sum()), 'CNY'),
                                ('due_exit_count', int(due.sum()), 'count'), ('due_exit_amount', float(sells.nt[due].sum()), 'CNY')):
                    L(4, 'D4', 'tilt_group_exit', tg, t, 'FULL', k, v, u)


def d5_concentration():
    W = pd.read_csv(os.path.join(G['root'], 'statistics', 'weights_E6r.csv'), dtype=str, keep_default_na=False)
    p9 = {G['lid2e'][l] for l in G['prim']['primary9']}
    for r in W[W.exec_id.isin(p9) & (W.segment == 'FULL')].itertuples(index=False):
        for k in ('g_mean', 'n_eff_mean', 'shape_proxy_mean', 'cap_bound_stock_share', 'cap_bound_industry_share', 'cash_as_asset_concentration_mean'):
            v = getattr(r, k)
            L(5, 'D5', 'three_layer', r.exec_id.split('|')[0], r.layer, 'FULL', k, float(v) if v != '' else np.nan, 'mixed', r.n_obs)
    CC = None
    p = os.path.join(G['root'], 'statistics', 'cost_curve_E6r.csv.gz')
    if os.path.exists(p):
        CC = pd.read_csv(p, dtype=str, keep_default_na=False)
        x = CC[CC.exec_id.isin(p9) & (CC.comparator_kind == 'POLICY_REFERENCE') & (CC.segment == 'FULL') & (CC.A_cny == '100000000') & (CC.kappa == '0.5')]
        for r in x.itertuples(index=False):
            L(5, 'D5', 'delta_sensitivity', r.exec_id.split('|')[0], 'delta=%s' % r.exponent, 'FULL', 'net_after_impact_diff_ann_pp', float(r.net_after_impact_diff_ann_pp),
              'ann_pp')


def d6_risk():
    AS = pd.read_csv(os.path.join(G['root'], 'statistics', 'account_summary_E6r.csv'), dtype=str, keep_default_na=False)
    Y = pd.read_csv(os.path.join(G['root'], 'statistics', 'yearly_E6r.csv'), dtype=str, keep_default_na=False)
    p9 = [G['lid2e'][l] for l in G['prim']['primary9']]
    for e in p9:
        for r in AS[AS.exec_id == e].itertuples(index=False):
            for k in ('net_ann_pp', 'D_policy_ann_pp', 'fee_ann_pp', 'abs_net_ann_pp', 'max_drawdown_total', 'turnover_ann'):
                v = getattr(r, k)
                L(6, 'D6', 'segment_readings', e.split('|')[0], k, r.segment, 'value', float(v) if v != '' else np.nan, 'mixed')
        y = Y[(Y.exec_id == e) & (Y.status == 'COMPUTED')]
        dv = pd.to_numeric(y.D_policy_ann_pp.replace('', np.nan), errors='coerce')
        L(6, 'D6', 'years', e.split('|')[0], 'n_negative_D_policy_years', 'FULL', 'count', int((dv < 0).sum()), 'count', int(dv.notna().sum()))
        if dv.notna().any():
            top = dv.abs().sort_values(ascending=False)
            L(6, 'D6', 'years', e.split('|')[0], 'top2_abs_D_share', 'FULL', 'share', float(top.iloc[:2].sum() / top.sum()) if top.sum() > 0 else np.nan, 'share')


def d7_state_coverage():
    """D7：形成名单 T0 状态 BAD / UNKNOWN 份额按年（主坐标 HG10 名单；LEVEL 面板）；缺失原因 = 测量未知（UNKNOWN 不当 BAD）。"""
    ptr, col, w = formation(O.MAIN_FORM, 'HG10')
    st0 = overlay(O.MAIN_FORM, 'HG10')['st0']
    day = np.repeat(np.arange(G['T']), np.diff(ptr))
    yr = G['years'][day]
    ok = day < G['d_end']
    for y in sorted(set(yr[ok].tolist())):
        m = ok & (yr == y)
        L(7, 'D7', 'T0_state_share', 'LEVEL', str(y), 'FULL', 'share_BAD', float((st0[m] == 1).mean()), 'share', int(m.sum()))
        L(7, 'D7', 'T0_state_share', 'LEVEL', str(y), 'FULL', 'share_UNKNOWN', float((st0[m] == -1).mean()), 'share', int(m.sum()))


def d8_second_block():
    """D8：第二块（退出算子账户，LEVEL H30 主坐标）按订单类别的成交名义、笔数与 REARM / deadline 计数。"""
    R = G['R']
    for op in ('EXIT_GATE_LIQ_1E8', 'EXIT_GATE_LIQ_5E8', 'EXIT_HALF_REARM', 'GATE_REARM_1E8', 'GATE_REARM_5E8'):
        x = R[(R.trigger == 'T1b_LEVEL') & (R.weight_scheme == 'FLAT') & (R.funding_H == '30') & (R.exit_op == op) & (R.form == O.MAIN_FORM) & (R.memory == 'HG10') &
              (R.scenario == O.FEAS)]
        if not len(x):
            continue
        r = x.iloc[0]
        ti, tf = trades(r.exec_hash)
        z = acct(r.exec_hash)
        for k, nm in ((E.OK_EXIT, 'EXIT'), (E.OK_EXIT_HALF, 'EXIT_HALF'), (E.OK_EXIT_REARM, 'EXIT_REARM'), (E.OK_DEADLINE, 'DEADLINE_OVERRIDE'), (E.OK_DUE, 'DUE')):
            m = (ti[:, 4] == k) & (ti[:, 5] == 1)
            L(8, 'D8', 'order_kind', op, nm, 'FULL', 'notional_cny', float(tf[m, 1].sum()), 'CNY', int(m.sum()))
        Si = z['S_i']
        for k, v in (('rearm_episodes', Si[E.SI_REARMN]), ('half_requests', Si[E.SI_HALF]), ('deadline_overrides', Si[E.SI_OVERRIDE])):
            L(8, 'D8', 'state_machine', op, k, 'FULL', 'count', int(v), 'count')


def d9_h40():
    AS = pd.read_csv(os.path.join(G['root'], 'statistics', 'account_summary_E6r.csv'), dtype=str, keep_default_na=False).set_index(['exec_id', 'segment'])
    R = G['R']
    for r in R[R.h30_same_rule_exec_id != ''].itertuples(index=False):
        for e, tagn in ((r.exec_id, 'H40'), (r.h30_same_rule_exec_id, 'H30')):
            if (e, 'FULL') not in AS.index:
                continue
            a = AS.loc[(e, 'FULL')]
            for k in ('net_ann_pp', 'cagr_total', 'max_drawdown_total'):
                L(9, 'D9', 'h40_vs_h30', r.exec_id.split('|')[0], '%s|%s' % (tagn, k), 'FULL', 'value', float(a[k]) if a[k] != '' else np.nan, 'mixed')
        z = acct(r.exec_hash)['S_i']
        L(9, 'D9', 'original_lot_due_rate', r.exec_id.split('|')[0], 'H40', 'FULL', 'share', float(z[E.SI_LDUE] / z[E.SI_LCLOSED]) if z[E.SI_LCLOSED] > 0 else np.nan, 'share')


def d10_tail30():
    """D10：TAIL30（尾盘 30 分钟 CVR，分钟依赖，只读）：主坐标形成名单的分钟覆盖率按年、与 CVR20 的截面秩相关（中位）；不入本轮门或权重。"""
    ptr, col, w = formation(O.MAIN_FORM, 'HG10')
    tc = G['tail_cvr']
    for y in range(2010, 2027):
        ds = [d for d in range(G['d_end']) if G['years'][d] == y and ptr[d + 1] > ptr[d]]
        if not ds:
            continue
        cov, rc = [], []
        for d in ds[::5]:
            ss = col[ptr[d]:ptr[d + 1]]
            a = np.asarray(tc[d, ss], float)
            b = np.asarray(G['cvr20'][d, ss], float)
            cov.append(np.isfinite(a).mean())
            ok = np.isfinite(a) & np.isfinite(b)
            if ok.sum() >= 5:
                rc.append(pd.Series(a[ok]).rank().corr(pd.Series(b[ok]).rank()))
        L(10, 'D10', 'tail30_coverage', 'formation_list', str(y), 'FULL', 'mean_share', float(np.mean(cov)), 'share', len(cov), status='INFO')
        L(10, 'D10', 'tail30_vs_cvr20_rank_corr', 'formation_list', str(y), 'FULL', 'median', float(np.median(rc)) if rc else np.nan, 'ratio', len(rc), status='INFO')


def d11_bridge():
    C = O.read_csv(O.P('registration', 'comparisons_E6r.csv'))
    CR = pd.read_csv(os.path.join(G['root'], 'statistics', 'comparison_results_E6r.csv'), dtype=str, keep_default_na=False)
    want = C[C.kind.str.contains('CVR5|CELL|GATE_X_TILT|ENTRY_X_EXIT|BRIDGE', regex=True)]
    x = CR[CR.comparison_id.isin(set(want.comparison_id)) & (CR.segment.isin(['FULL', 'G4']))]
    for r in x.itertuples(index=False):
        L(11, 'D11', 'direct_pair', r.kind, r.comparison_id, r.segment, 'D_net_ann_pp', float(r.D_net_ann_pp) if r.D_net_ann_pp != '' else np.nan, 'ann_pp')
    K = pd.read_csv(os.path.join(G['root'], 'statistics', 'compound_results_E6r.csv'), dtype=str, keep_default_na=False)
    for r in K[K.segment == 'FULL'].itertuples(index=False):
        L(11, 'D11', 'compound', r.kind, r.contrast_id, 'FULL', 'I_net_ann_pp', float(r.I_net_ann_pp), 'ann_pp')
        L(11, 'D11', 'compound', r.kind, r.contrast_id, 'FULL', 'AB_minus_max_net_ann_pp', float(r.AB_minus_max_net_ann_pp), 'ann_pp')


def d12_closure(SN):
    root = G['root']

    def n(rel):
        p = os.path.join(root, rel)
        if not os.path.exists(p) and os.path.exists(p + '.gz'):
            p += '.gz'
        return len(pd.read_csv(p, dtype=str, keep_default_na=False)) if os.path.exists(p) else 0
    for k, rel, want in (('registry', 'registration/registry_E6r.csv', 350), ('comparisons', 'registration/comparisons_E6r.csv', 2988),
                         ('random_refs', 'registration/random_control_refs_E6r.csv', 1408), ('snapshot_refs', 'registration/local_snapshot_refs_E6r.csv', 359),
                         ('feedback_refs', 'registration/cost_feedback_refs_E6r.csv', 202)):
        got = len(O.read_csv(O.P(*rel.split('/'))))
        L(12, 'D12', 'registration_count', k, str(want), 'FULL', 'rows', got, 'count', status='PASS' if got == want else 'DIFFERS')
    for k, rel, want in (('account_summary', 'statistics/account_summary_E6r.csv', 350 * 6), ('comparison_results', 'statistics/comparison_results_E6r.csv', 2988 * 6),
                         ('compound_results', 'statistics/compound_results_E6r.csv', 20 * 6), ('cost_feedback', 'statistics/cost_feedback_E6r.csv', 202 * 6),
                         ('cost_feedback_pairs', 'statistics/cost_feedback_pairs_E6r.csv', 1822 * 6)):
        got = n(rel)
        L(12, 'D12', 'table_rows', k, str(want), 'FULL', 'rows', got, 'count', status='PASS' if got == want else 'DIFFERS')
    snap = set(SN.snapshot_id)
    refs = set(O.read_csv(O.P('registration', 'local_snapshot_refs_E6r.csv')).snapshot_id)
    L(12, 'D12', 'snapshot_closure', 'refs_with_rows', str(len(refs)), 'FULL', 'count', len(refs & snap), 'count', status='PASS' if refs <= snap else 'DIFFERS')
    L(12, 'D12', 'snapshot_closure', 'computed_rows', '', 'FULL', 'count', int((SN.status == 'COMPUTED').sum()), 'count', status='INFO')


# ------------------------------------------------------------------ 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', choices=['A2', 'B'], required=True)
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    t0 = time.time()
    root = O.P(*a.root.split('/')) if a.root else O.work()
    setup(a.phase, root)
    focus = accounts_focus()
    LM = []
    TR = []
    for e in focus:
        LM += landmark(e)
        TR += transitions(e)
    LMd = pd.DataFrame(LM, columns=LMCOLS)
    TRd = pd.DataFrame(TR, columns=['exec_id', 'segment', 't0_state', 'age1_state', 'denominator', 'value', 'share', 'status'])
    AP = allocation_projection()
    SN = snapshots()
    update_snapshot_refs(root, SN)
    GC = gate_counterfactual()
    out = {'diagnostics/landmark_E6r.csv': LMd, 'diagnostics/entry_transition_T0_age1_E6r.csv': TRd, 'diagnostics/allocation_projection_E6r.csv': AP,
           'diagnostics/entry_target_snapshot_E6r.csv': SN, 'events/entry_gate_counterfactual_E6r.csv': GC}
    d1_entry_age(focus)
    d2_transition(TRd, GC)
    d3_cvr_size()
    d4_tilt_exit()
    d5_concentration()
    d6_risk()
    d7_state_coverage()
    d8_second_block()
    d9_h40()
    d10_tail30()
    d11_bridge()
    d12_closure(SN)
    for i, nm in enumerate(DIAG_NAMES, start=1):
        rows = ROWS[i] or [dict(block='D%d' % i, item='empty', key1='', key2='', segment='FULL', stat='note', value='', unit='none', n='', status='NOT_APPLICABLE',
                                query_id='QRY-D%d' % i)]
        out['diagnostics/D%d_%s_E6r.csv' % (i, nm)] = pd.DataFrame(rows, columns=LCOLS)
    paths = []
    for rel, df in out.items():
        p = os.path.join(root, *rel.split('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        O.atomic_write_csv(p, df)
        paths.append(p)
    facts = dict(phase=a.phase, focus=len(focus), landmark_rows=len(LMd), transition_rows=len(TRd), projection_rows=len(AP), snapshot_rows=len(SN), gate_cf_rows=len(GC),
                 d_rows={i: len(ROWS[i]) for i in ROWS}, wall_s=round(time.time() - t0, 1))
    O.atomic_write_json(os.path.join(root, 'diagnostics', 'diag_facts_E6r.json'), facts)
    O.write_receipt('E6r_diag_%s' % a.phase, paths, code=[__file__, O.__file__], **{k: v for k, v in facts.items() if k != 'd_rows'})
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
