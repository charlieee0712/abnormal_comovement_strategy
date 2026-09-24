#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i M2_SHAPE (plan §7.2 / §7.3; brief §5; 规格补全 registry/M2_program_spec.md)。推导段专用 (part1b)。

程序 = A0 的 M2 描述符 (§7.1 代表 x 母体 x H); 每程序:
  域      该代表 home 角色的排序域: SLOT = pool0 (DEP-T 为 S1); ADD = pool0; SWAP = 经济拒绝候选 E; VETO = pool0
  basis   u = 代表在域内 rank 中心化 (pct − 0.5); z = S_peerR20 同样处理 (S 轴: u = R_peer20, z = S 代表); 缺 z 取 0;
          [u, u², u·z] 在训练样本上日期等权中心化 / 标准化, 参数冻结
  目标    H 日 entry-fixed 毛超额 (bp); 日期等权 (每日权重和 = 1) 加权平方误差 + λ‖β‖² (平均损失口径, 截距不罚)
  成熟    训练只用 t + 1 + H < 决策日 的形成日; 2015-18 训练含 2010-14 全部成熟样本 (先跑 2010-14)
  回放    2012 起按年度; 成熟训练日 < 252 -> 该年回退母体 (零修改)
  内层    外层年 Y 的 fold = Y−2、Y−1 (各只用更早成熟日训练); 每个 λ 在 fold 年的形成日上改名单、其余日 = 母体,
          目标 = 完整账户 net8 相对母体之差 (另出 net12 版); 两个 fold 都可用才选, 否则 λ = 1;
          λ 并列取大; 最好的修改 <= 零修改 (容差 1e−9) -> 该年零修改
  接入    预测越高 bad-score 越低 (当日域内对 −ŷ 取 pct) -> home 角色的固定预算 (SLOT α=.25 FALLBACK / ADD γ=.125 /
          SWAP q=.10 / VETO k=10); 每年新模型只改该年形成日 (旧批次按 H 自然退出)
  变体    primary (net8 目标) / cost_target (net12 目标) / winsor (训练段 1%/99% winsor 的 y, net8 目标) —— 评估一律用原收益
输出 accounts/<seg>/M2_<NN>.csv/.npz (与 Stage 2 同列), m2/<seg>/ledger_<NN>.csv (逐年 λ / 回退 / 系数 / 内层分数),
m2/<seg>/folds_<NN>.csv (fold 分数, 供 2015-18 复用), m2/2010-2014/samples/<程序>.npz (训练样本)。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import io
import sys
import time
import argparse
import collections
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_s1base as SB
import e6i_ops as OP
import e6i_engine as E
import e6i_stage2 as S2

HOME_BUDGET = {'SLOT': 0.25, 'ADD_SCORE': 0.125, 'SWAP': 0.10, 'VETO_NEW': 10}
LEG = {'RT': 'T', 'RK': 'K', 'RC': 'C'}
LAMS = (0.1, 1.0, 10.0)
Z_STATE = 'S_peerR20'
MIN_DATES = 252
FIRST_YEAR = 2012
TOL = 1e-9
VARIANTS = ('primary', 'cost_target', 'winsor')


def rank_c(x, dom):
    X = np.where(dom & np.isfinite(x), x, np.nan)
    return pd.DataFrame(X).rank(axis=1, pct=True).values - 0.5


def is_fourarm(r):
    v = r.get('m2_variant')
    return v is not None and str(v) not in ('', 'nan')


def prog_key(r):
    if is_fourarm(r):                                   # A0 v1.3 四臂 K x A 的 M2 (单变量 / 双变量)
        return 'FA|%s|%s|a%s|H%d' % (r['m2_variant'], r['mother_id'], r['strength'], int(r['H']))
    return '%s|%s|%s|H%d' % (r['m2_home_route'], r['mother_id'], r['member_id'], int(r['H']))


class Program(object):
    def __init__(self, S, RN, r):
        self.S, self.RN, self.r = S, RN, r
        self.route, self.role = r['m2_home_route'], r['m2_role']
        self.mn, self.mid, self.H = r['mother_id'], r['member_id'], int(r['H'])
        self.axis = r['axis_id']
        M = self.M = RN.mother(self.mn)
        S_ = S
        self.basis_kind, self.budget = 'uz', None
        if is_fourarm(r):                               # K x A 四臂: uni = [u, u²]; bi = [u1, u2, u1·u2]
            self.basis_kind = 'uni' if r['m2_variant'] == 'uni' else 'bi'
            self.budget = float(r['strength'])
            u_mid, z_mid = 'K_res_log', ('T_evlevel' if self.basis_kind == 'bi' else Z_STATE)
        elif self.axis == 'S':
            u_mid, z_mid = 'R_peer20', self.mid
        else:
            u_mid, z_mid = self.mid, Z_STATE
        self.u_mid, self.z_mid = u_mid, z_mid
        if self.role == 'SLOT' and M.kind == 'dep' and LEG[self.route] == 'T':
            upct = OP._ns_pct_within(S_, SB.raw_member(S_, u_mid), M.s1, 'hi')
            dom = M.s1.copy()
        else:
            upct = SB.pct_member(S_, u_mid, direction='hi')
            if self.role == 'SWAP':
                dom = M.E_set()
            else:
                dom = S_.p0c.copy()
        dom = dom & np.isfinite(upct)
        self.dom = dom
        self.u = rank_c(upct, dom)
        zp = SB.pct_member(S_, z_mid, direction='hi')
        z = rank_c(zp, dom)
        self.z = np.where(np.isfinite(z), z, 0.0)
        self.y = SB.labels(S_)['entry_%d' % self.H]
        self.years = pd.DatetimeIndex(S_.dates).year.values
        self.T = S_.T

    # ---------------- 样本
    def samples(self):
        t, c = np.nonzero(self.dom & np.isfinite(self.u) & np.isfinite(self.y))
        u = self.u[t, c]
        return dict(t=t, date=np.asarray(pd.DatetimeIndex(self.S.dates)[t].strftime('%Y%m%d').astype(int)),
                    u=u, z=self.z[t, c], y=self.y[t, c])

    # ---------------- 应用: 只改 days 的形成日
    def mask_with(self, zM2):
        S, M = self.S, self.M
        role = self.role
        b = HOME_BUDGET[role] if self.budget is None else self.budget
        if role == 'SLOT':
            leg = LEG[self.route]
            if M.kind == 'dep' and leg == 'T':
                st2 = OP._blend(M.P.score, zM2, b, 'FALLBACK')
                keep, _, _ = M._keep_dep(stage2=st2, s1=M.s1)
                return keep & ~M.veto_drop()
            return M.slot(leg, lambda: zM2, b, 'FALLBACK')[0]
        if role == 'ADD_SCORE':
            return M.add_score(zM2, b)[0]
        if role == 'SWAP':
            return M.swap(zM2, b)[0]
        if role == 'VETO_NEW':
            days = np.isfinite(zM2).any(1)
            drop = OP.G.drop_SRC(np.where(days[:, None], zM2, np.nan), M.p0, int(b)).astype(bool)
            return M.B & ~(drop & days[:, None])
        raise ValueError(role)


def standardize_fit(X, y, w, lam):
    sw = w.sum()
    mu = (w[:, None] * X).sum(0) / sw
    Xc = X - mu
    sd = np.sqrt((w[:, None] * Xc * Xc).sum(0) / sw)
    sd = np.where(sd > 0, sd, 1.0)
    Z = Xc / sd
    ybar = (w * y).sum() / sw
    A = (Z.T * w) @ Z / sw + lam * np.eye(Z.shape[1])
    beta = np.linalg.solve(A, (Z.T * w) @ (y - ybar) / sw)
    return dict(mu=mu, sd=sd, b0=ybar, beta=beta)


def basis(u, z, kind='uz'):
    """uz (代表 M2): [u, u², u·z]; uni (四臂单变量): [u, u²]; bi (四臂双变量): [u1, u2, u1·u2] (z 位放 u2)。"""
    if kind == 'uni':
        return np.column_stack([u, u * u])
    if kind == 'bi':
        return np.column_stack([u, z, u * z])
    return np.column_stack([u, u * u, u * z])


def fit_on(train, lam, winsor, kind='uz'):
    X = basis(train['u'], train['z'], kind)
    y = train['y'].copy()
    if winsor:
        lo, hi = np.percentile(y, [1, 99])
        y = np.clip(y, lo, hi)
    dates = train['date']
    _, inv, cnt = np.unique(dates, return_inverse=True, return_counts=True)
    w = 1.0 / cnt[inv]
    return standardize_fit(X, y, w, lam)


def rank_pct_rows(V, m):
    """逐行 (日) 在 m 内的 average 并列 pct 排名 —— 与 pandas rank(axis=1, pct=True) 同值 (秩 = 并列位置均值,
       pct = 秩 / 当日有效数); 其余 NaN。只在 m 的单元上计算 (向量化)。"""
    t, c = np.nonzero(m)
    out = np.full(V.shape, np.nan)
    if len(t) == 0:
        return out
    v = V[t, c]
    o = np.lexsort((v, t))
    ts, vs, cs = t[o], v[o], c[o]
    newg = np.r_[True, ts[1:] != ts[:-1]]
    gstart = np.maximum.accumulate(np.where(newg, np.arange(len(ts)), 0))
    pos = np.arange(len(ts)) - gstart
    newr = newg | np.r_[True, vs[1:] != vs[:-1]]
    rid = np.cumsum(newr) - 1
    first = pos[newr]
    last = np.r_[pos[np.flatnonzero(newr)[1:] - 1], pos[-1]]
    rank = (first[rid] + last[rid]) / 2.0 + 1.0
    n = np.bincount(ts, minlength=V.shape[0])
    out[ts, cs] = rank / n[ts]
    return out


def predict_z(P, model, days_mask):
    """对 days_mask 的形成日, 在域内对 −ŷ 取 pct -> bad-score; 其余 NaN。"""
    u, z = P.u, P.z
    m = P.dom & np.isfinite(u) & days_mask[:, None]
    if model['beta'].std() == 0 and np.allclose(model['beta'], 0):
        return np.full(u.shape, np.nan)                  # 零预测方差 -> 零修改
    t, c = np.nonzero(m)
    X = basis(u[t, c], z[t, c], getattr(P, 'basis_kind', 'uz'))
    yh = np.full(u.shape, np.nan)
    yh[t, c] = model['b0'] + ((X - model['mu']) / model['sd']) @ model['beta']
    return rank_pct_rows(-yh, m)


def matured(train, t_dec_date, H, date_index):
    """训练行: 标签结束 (形成日 + 1 + H 个交易日) 严格早于决策日。date_index: 合并交易日历 (int yyyymmdd 升序)。"""
    pos = np.searchsorted(date_index, train['date'])
    end = pos + 1 + H
    dpos = np.searchsorted(date_index, t_dec_date)
    return end < dpos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--fourarm', action='store_true', help='只跑 A0 v1.3 的四臂 K x A M2 (单变量 / 双变量); 默认只跑代表 M2')
    ap.add_argument('--samples-only', action='store_true',
                    help='Stage 3 技术修复: 只保存本段训练样本 m2/<seg>/samples/ (不写账户 / 台账 / folds / 日历); '
                         '供后段按"当时已成熟的全部历史"训练')
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS or I.post_allowed(a.segment)   # Stage 3 技术修复: 后段需 E6i 记录 B
    seg = a.segment
    t0 = time.time()
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    dd = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    dd = dd[dd.route_id == 'M2']
    fa_rows = dd.m2_variant.astype(str).isin(['uni', 'bi']) if 'm2_variant' in dd.columns else pd.Series(False, index=dd.index)
    dd = dd[fa_rows if a.fourarm else ~fa_rows].reset_index(drop=True)
    progs = dd.to_dict('records')[a.shard::a.nshard]
    if a.limit:
        progs = progs[:a.limit]
    S = I.seg_i(seg, warm=False)
    RN = S2.Runner(S)
    md = os.path.join(I.RES, 'm2', seg)
    os.makedirs(os.path.join(md, 'samples'), exist_ok=True)
    # 合并交易日历 (成熟判断用): 2015-18 需要 2010-14 的日期
    cal = [int(x) for x in pd.DatetimeIndex(S.dates).strftime('%Y%m%d')]
    prev_folds = None
    prev_segs = list(I.SEGMENTS[:I.SEGMENTS.index(seg)])      # 本段之前的全部段 (训练历史)
    if not a.samples_only:
        np.save(os.path.join(md, 'calendar.npy'), np.asarray(cal))
    if seg in I.POST_SEGS and not a.samples_only:
        # Stage 3 技术修复 (后段): 合并日历与 fold 分数取此前全部段 (推导两段 + 已跑的后段); 训练样本同理 (见下)
        cals = [np.load(os.path.join(I.RES, 'm2', s_, 'calendar.npy')) for s_ in prev_segs]
        cal = sorted(set(int(x) for c_ in cals for x in c_) | set(cal))
        fs = [os.path.join(I.RES, 'm2', s_, f) for s_ in prev_segs for f in os.listdir(os.path.join(I.RES, 'm2', s_))
              if f.startswith('folds_') and f.endswith('.csv') and '_timing' not in f]
        prev_folds = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()
    elif seg == '2015-2018':
        cal1 = np.load(os.path.join(I.RES, 'm2', '2010-2014', 'calendar.npy'))
        cal = sorted(set(int(x) for x in cal1) | set(cal))
        fs = [os.path.join(I.RES, 'm2', '2010-2014', f) for f in os.listdir(os.path.join(I.RES, 'm2', '2010-2014'))
              if f.startswith('folds_') and f.endswith('.csv')]
        prev_folds = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame()
    cal = np.asarray(cal)
    seg_dates = np.asarray([int(x) for x in pd.DatetimeIndex(S.dates).strftime('%Y%m%d')])
    print('段就绪 %.0fs; M2 shard %d/%d: %d 程序' % (time.time() - t0, a.shard, a.nshard, len(progs)), flush=True)
    rows, ledger, folds_out = [], [], []
    series = collections.defaultdict(list)
    n_fail = 0
    for gi, r in enumerate(progs):
        ts = time.time()
        key = prog_key(r)
        try:
            members = [m for m in (r['member_id'], Z_STATE, 'R_peer20') if m in FE.CATALOG_IDS]
            I.guard_i(members, ['M2'], segment=seg, label_end=str(S.dates[-1].date()), use='trade',
                      where=r['descriptor_id'])
            P = Program(S, RN, r)
            M = P.M
            smp = P.samples()
            if a.samples_only:
                np.savez(os.path.join(md, 'samples', key.replace('|', '__') + '.npz'), **smp)
                print('  %d/%d %s 样本 %d %.0fs' % (gi + 1, len(progs), key, len(smp['y']), time.time() - t0), flush=True)
                continue
            if seg == '2010-2014':
                np.savez(os.path.join(md, 'samples', key.replace('|', '__') + '.npz'), **smp)
                train_all = smp
            elif seg in I.POST_SEGS:
                # Stage 3 技术修复: 训练 = 此前全部段的样本 + 本段样本 (成熟判断照旧由 matured() 按合并日历做);
                # 本段样本另存, 供下一后段使用
                np.savez(os.path.join(md, 'samples', key.replace('|', '__') + '.npz'), **smp)
                parts = []
                for s_ in prev_segs:
                    p1 = os.path.join(I.RES, 'm2', s_, 'samples', key.replace('|', '__') + '.npz')
                    with np.load(p1) as z1:
                        parts.append({k: z1[k] for k in z1.files})
                parts.append(smp)
                train_all = {k: np.concatenate([x_[k] for x_ in parts]) for k in ('date', 'u', 'z', 'y')}
            else:
                p1 = os.path.join(I.RES, 'm2', '2010-2014', 'samples', key.replace('|', '__') + '.npz')
                with np.load(p1) as z1:
                    s1 = {k: z1[k] for k in z1.files}
                train_all = {k: np.concatenate([s1[k], smp[k]]) for k in ('date', 'u', 'z', 'y')}
            Wp = RN.parent_W[P.mn]
            pn = RN.ppnl(P.mn, P.H)
            parent_net8 = I.ann(pn[3])
            parent_net12 = I.ann(pn[0] - pn[2] * I.COST_HI / 1e4)
            years = sorted(set(P.years))
            year_first = {y: seg_dates[P.years == y][0] for y in years}

            def train_before(dec_date):
                m = matured(train_all, dec_date, P.H, cal)
                sub = {k: v[m] for k, v in train_all.items() if k in ('date', 'u', 'z', 'y')}
                return sub, len(np.unique(sub['date'])) if len(sub['date']) else 0

            def account(zM2):
                mask = P.mask_with(zM2)
                W = E.dev_weights(S, mask)
                g, p, u, n = E.pnl_W(S, W, P.H, I.COST)
                return mask, (g, p, u, n)

            # ---- fold 分数 (本段年份) ----
            fold = {}
            for F in years:
                dec = year_first[F]
                tr, nd = train_before(dec)
                if nd < MIN_DATES:
                    continue
                days = P.years == F
                # 只有 F 年形成日被改: 全段均值之差 x (段长 / F 年形成日数) = 每个被改形成日的平均效应,
                # 两段 fold 平均时分母可比 (2010-14 与 2015-18 段长不同)
                scale = float(P.T) / max(int(days.sum()), 1)
                for lam in LAMS:
                    for wz in (False, True):
                        mdl = fit_on(tr, lam, wz, P.basis_kind)
                        zM2 = predict_z(P, mdl, days)
                        _, (g, p, u, n) = account(zM2)
                        d8 = I.ann(n) - parent_net8
                        d12 = I.ann(g - u * I.COST_HI / 1e4) - parent_net12
                        fold[(F, lam, wz)] = (d8 * scale, d12 * scale)
                        folds_out.append(dict(program=key, segment=seg, fold_year=F, lam=lam, winsor=wz,
                                              d_net8_vs_parent=d8 * scale, d_net12_vs_parent=d12 * scale,
                                              d_net8_segment_mean=d8, n_formation_days=int(days.sum()),
                                              n_train_dates=nd))
            if prev_folds is not None and len(prev_folds):
                pf = prev_folds[prev_folds.program == key]
                for rr in pf.itertuples():
                    fold[(int(rr.fold_year), float(rr.lam), bool(rr.winsor))] = (rr.d_net8_vs_parent,
                                                                                rr.d_net12_vs_parent)
            # ---- 外层逐年 ----
            outer_years = [y for y in years if y >= FIRST_YEAR]
            for variant in VARIANTS:
                wz = variant == 'winsor'
                zfull = np.full(P.u.shape, np.nan)
                for Y in outer_years:
                    dec = year_first[Y]
                    tr, nd = train_before(dec)
                    rec = dict(program=key, segment=seg, variant=variant, year=Y, n_train_dates=nd)
                    if nd < MIN_DATES:
                        rec.update(action='fallback_parent', reason='成熟训练日 < 252')
                        ledger.append(rec)
                        continue
                    fy = [Y - 2, Y - 1]
                    usable = all((F, 1.0, wz) in fold for F in fy)
                    if usable:
                        sc = {}
                        for lam in LAMS:
                            j = 1 if variant == 'cost_target' else 0
                            sc[lam] = float(np.mean([fold[(F, lam, wz)][j] for F in fy]))
                        best = max(LAMS, key=lambda l_: (round(sc[l_], 12), l_))
                        rec.update({'inner_%s' % l_: sc[l_] for l_ in LAMS})
                        if sc[best] <= TOL:
                            rec.update(action='zero_modification', lam=best, inner_best=sc[best])
                            ledger.append(rec)
                            continue
                        lam = best
                        rec.update(inner_best=sc[best])
                    else:
                        lam = 1.0
                        rec.update(reason='内层可用年度不足两个 -> λ=1')
                    mdl = fit_on(tr, lam, wz, P.basis_kind)
                    days = P.years == Y
                    zY = predict_z(P, mdl, days)
                    zfull = np.where(days[:, None], zY, zfull)
                    bb = mdl['beta']
                    rec.update(action='modified', lam=lam, b_u=bb[0], b_u2=bb[1],
                               b_uz=(bb[2] if len(bb) > 2 else np.nan), b0=mdl['b0'], basis_kind=P.basis_kind)
                    ledger.append(rec)
                mask, (g, p, u, n) = account(zfull)
                gp_, pp_, up_, np_ = pn
                both = np.isfinite(n) & np.isfinite(np_)
                dn = np.where(both, n - np_, np.nan)
                did = r['descriptor_id'] + ('' if variant == 'primary' else '|' + variant)
                rows.append(dict(descriptor_id=did, status='SUCCEEDED', route_id='M2', mother_id=P.mn,
                                 member_id=P.mid, role='M2', strength=HOME_BUDGET[P.role], policy=variant,
                                 direction='learned', direction_role='shape', H=P.H, representative=True,
                                 companion=(variant != 'primary'), m2_home_route=P.route, m2_role=P.role,
                                 u_member=P.u_mid, z_member=P.z_mid, axis_id=P.axis,
                                 net8_ann=I.ann(n), gross_ann=I.ann(g), net12_ann=I.ann(g - u * I.COST_HI / 1e4),
                                 turn_mean=float(np.nanmean(u)), pos_mean=float(np.nanmean(p)),
                                 parent_net8_ann=parent_net8, d_net8_ann=I.ann(dn),
                                 d_gross_ann=I.ann(np.where(both, g - gp_, np.nan)),
                                 d_turn=float(np.nanmean(u - up_)), d_pos=float(np.nanmean(p - pp_)),
                                 n_changed_cells=int((mask != M.B).sum()),
                                 n_modified_years=int(sum(1 for x in ledger if x['program'] == key and
                                                          x['variant'] == variant and x.get('action') == 'modified'))))
                series['descriptor_id'].append(did)
                for nm, arr in (('net8', n), ('gross', g), ('pos', p), ('turn', u), ('dnet8', dn)):
                    series[nm].append(np.asarray(arr, np.float64))
        except Exception as e:
            n_fail += 1
            traceback.print_exc()
            rows.append(dict(descriptor_id=r['descriptor_id'], status='FAILED_TECH',
                             note='%s: %s' % (type(e).__name__, str(e)[:150])))
        print('  %d/%d %s %.0fs (末个 %.1fs)' % (gi + 1, len(progs), key, time.time() - t0, time.time() - ts),
              flush=True)
    if a.samples_only:
        I.write_receipt(os.path.join(I.RES, 'task_status', 'm2_samples_%s_%02d%s.receipt.json'
                                     % (seg, a.shard, '_fa' if a.fourarm else '')),
                        'm2_samples:%s:%02d' % (seg, a.shard), [], status='SUCCEEDED' if n_fail == 0 else 'FAILED',
                        n_fail=n_fail, n_programs=len(progs), elapsed_s=round(time.time() - t0, 1))
        print('[%s M2 样本] 程序 %d / 失败 %d; %.0fs' % (seg, len(progs), n_fail, time.time() - t0))
        sys.exit(0 if n_fail == 0 else 1)
    od = os.path.join(I.RES, 'accounts', seg)
    fa_sfx = '_fa' if a.fourarm else ''
    tag = 'M2_%02d' % a.shard + fa_sfx + ('_timing' if a.limit else '')
    I.atomic_write_csv(os.path.join(od, tag + '.csv'), pd.DataFrame(rows))
    I.atomic_write_csv(os.path.join(md, 'ledger_%02d%s%s.csv' % (a.shard, fa_sfx, '_timing' if a.limit else '')),
                       pd.DataFrame(ledger))
    I.atomic_write_csv(os.path.join(md, 'folds_%02d%s%s.csv' % (a.shard, fa_sfx, '_timing' if a.limit else '')),
                       pd.DataFrame(folds_out))
    outs = [os.path.join(od, tag + '.csv')]
    if series['descriptor_id']:
        buf = io.BytesIO()
        np.savez(buf, descriptor_id=np.asarray(series['descriptor_id']),
                 **{k: np.vstack(v) for k, v in series.items() if k != 'descriptor_id'})
        I.atomic_write_bytes(os.path.join(od, tag + '.npz'), buf.getvalue())
        outs.append(os.path.join(od, tag + '.npz'))
    I.write_receipt(os.path.join(I.RES, 'task_status', 'm2_%s_%s.receipt.json' % (seg, tag)),
                    'm2:%s:%s' % (seg, tag), outs, status='SUCCEEDED' if n_fail == 0 else 'FAILED',
                    n_fail=n_fail, n_programs=len(progs), elapsed_s=round(time.time() - t0, 1))
    print('[%s %s] 程序 %d / 失败 %d; %.0fs' % (seg, tag, len(progs), n_fail, time.time() - t0))
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == '__main__':
    main()
