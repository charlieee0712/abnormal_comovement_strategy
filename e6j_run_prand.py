# -*- coding: utf-8 -*-
"""E6j P 块随机对照（plan §8.1–§8.2；brief W08 / W14）：每 (形态, 非恒等臂) × 机制 × 1,024 路径起，每路径独立过算子 / DEV / 持仓 / 成本；
α .125 / .25 / .5 × H 3 / 5 / 10 / 20 共用同一套优先序（每 α / H 各自真实账户）。
机制（namespace 各自独立；种子 = e6j_random 稳定哈希；parent = 'P_production_v2' → 六形态共用同一置换 = 共同随机数）：
  IID      = R-MATCH-SRC（Z-MAP basic 匹配条件：当日新分量有效格内均匀置换；R-SCORE-IID 同定义，登记为别名）——政策 e 主参照
  P5       = R-SCORE-P5（稳定五日优先序）
  COND     = R-COND（行业 × size 三档 × 旧 K 三档不重叠分区，五日优先序）；COND_IID 为其 IID 版
  EDIT     = EDIT-ENTRY（固定真实换出与共同成员，只随机换入，行业 × 旧 K 粗层配额，五日优先序）；EDIT_IID 为其 IID 敏感性
  EDITB    = EDIT-BOTH（换出 / 换入都随机，分别配额）
SM：共享 donor（同一 donor 的 (S, M) 整行向量，缺失模式分组）。每任务先跑恒等置换锚：必须逐格复现真实子掩码。
存储：randoms/P/<段>/<形态>__<臂>.npz —— 主配置（α .25 × H5）逐路径完整日账本；其余 α / H 逐路径分段年化 + 路径均值日序列。"""
import e6j_boot  # noqa: F401
import os
import sys
import time
import json

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import e6j_slot as SL
import e6j_engine as EN
import e6j_random as RND
import e6j_run_p as RP
import e6j_fast as FAST

EN.STAGE2 = FAST.stage2_fast       # 逐位同 IR.dep_stage2_keep（e6j_test_fast.py）
OUT = os.path.join(J.RES, 'randoms', 'P_test' if '--test' in sys.argv else 'P')
ALPHAS = (0.125, 0.25, 0.5)
HS = EN.HS_P
MECHS = ('IID', 'P5', 'COND', 'COND_IID', 'EDIT', 'EDIT_IID', 'EDITB')
BATCH = 64
ARMS = {'S': [(1.0, 'S')], 'M': [(1.0, 'M')], 'SM': [(0.5, 'S'), (0.5, 'M')], 'C1': [(1.0, 'C1')]}
COMP = {'S': ('K_rar20', 'lo'), 'M': ('K_slope20', 'lo'), 'C1': ('K_MA3_E6F', 'hi')}


class Perm(object):
    """单分量（或 SM 双分量）的随机置换器：只动新分量，有效掩码固定。"""

    def __init__(self, env, comps, q0c):
        self.env, self.comps = env, comps                    # comps: {名: 单元值 (n,)}
        ci, S = env.ci, env.S
        self.valid = {k: np.isfinite(v) for k, v in comps.items()}
        ind = np.asarray(S.icodes)                           # (T, Nc)
        lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
        oldk = np.full((ci.T, ci.Nc), np.nan); oldk[ci.t, ci.c] = q0c
        self.cond = {}
        for k in comps:
            V = np.zeros((ci.T, ci.Nc), bool); V[ci.t[self.valid[k]], ci.c[self.valid[k]]] = True
            r, c, cell, layer = RND.cond_cells(V, ind, lm, oldk)
            cid = np.full((ci.T, ci.Nc), -1, np.int64); cid[r, c] = cell
            self.cond[k] = (cid[ci.t, ci.c], layer)
        self.day = {k: ci.t.astype(np.int64) for k in comps}
        self.asg = {}                                        # 单分量：值序与路径无关，缓存（e6j_fast.Assigner，逐位同 assign_by_priority）
        if len(comps) == 1:
            k = list(comps)[0]; v = self.valid[k]
            self.asg[(k, 'day')] = FAST.Assigner(comps[k][v], self.day[k][v])
            self.asg[(k, 'cond')] = FAST.Assigner(comps[k][v], self.cond[k][0][v])

    def draw(self, mech, path, ident=False):
        """返回 {名: (n,) 置换后的值}；ident=True 返回恒等置换（锚）。"""
        env, ci = self.env, self.env.ci
        bd = 1 if mech in ('IID', 'COND_IID') else 5
        out = {}
        names = list(self.comps)
        if len(names) == 2:                                   # SM 共享 donor
            if ident:
                return dict(self.comps)
            T, Nc = ci.T, ci.Nc
            full = []
            for k in names:
                A = np.full((T, Nc), np.nan); A[ci.t, ci.c] = self.comps[k]; full.append(A)
            vfull = [np.isfinite(A) for A in full]
            kr = RND.path_key('E6j.P', 'K_rar20+K_slope20', 'P_production_v2', 'native', mech + ':rec', path)
            kd = RND.path_key('E6j.P', 'K_rar20+K_slope20', 'P_production_v2', 'native', mech + ':don', path)
            if mech.startswith('COND'):
                # 格 = COND 分区（用 S 分量的分区）× 缺失模式
                cid = np.full((T, Nc), -1, np.int64); cid[ci.t, ci.c] = self.cond[names[0]][0]
                outs = shared_donor_cells(full, vfull, env.grid, kr, kd, bd, cid)
            else:
                outs = RND.shared_donor_matrix(full, vfull, env.grid, kr, kd, bd)
            return {k: outs[j][ci.t, ci.c] for j, k in enumerate(names)}
        k = names[0]
        v = self.valid[k]; vals = self.comps[k][v]
        o = np.full(ci.n, np.nan)
        if ident:                                            # 恒等锚：原实现（u = 值本身，不是 2^-53 格点）
            cell = (self.cond[k][0] if mech.startswith('COND') else self.day[k])[v]
            o[v] = RND.assign_by_priority(vals, cell, vals.copy())
        else:
            key = RND.path_key('E6j.P', COMP_ID.get(k, k), 'P_production_v2', 'native', mech, path)
            u = env.grid.u_cells(key, ci.t[v], ci.c[v], bd)
            o[v] = self.asg[(k, 'cond' if mech.startswith('COND') else 'day')](u)
        out[k] = o
        return out


COMP_ID = {'S': 'K_rar20', 'M': 'K_slope20', 'C1': 'K_MA3_E6F'}


def shared_donor_cells(cols_vals, valid_each, grid, key_rec, key_don, block_days, cellid):
    """SM 共享 donor 的 COND 版：格 = COND 分区 × 缺失模式。"""
    pat = np.zeros(cols_vals[0].shape, dtype=np.int64)
    for j, v in enumerate(valid_each):
        pat |= (v.astype(np.int64) << j)
    rows, cols = np.nonzero(pat > 0)
    cell = cellid[rows, cols] * 8 + pat[rows, cols]
    cell = np.where(cellid[rows, cols] < 0, -1 - rows.astype(np.int64) * 8 - pat[rows, cols], cell)
    ur = grid.u_cells(key_rec, rows, cols, block_days); ud = grid.u_cells(key_don, rows, cols, block_days)
    o_r = np.lexsort((-ur, cell)); o_d = np.lexsort((-ud, cell))
    outs = []
    for j, v in enumerate(cols_vals):
        o = np.full(v.shape, np.nan)
        o[rows[o_r], cols[o_r]] = v[rows[o_d], cols[o_d]]
        o[~valid_each[j]] = np.nan
        outs.append(o)
    return outs


_K3 = {}


def edit_plans(env, parent_c, real, legal_c, q0c, form):
    """每 α 一个 e6j_fast.EditPlan（候选 / 需求 / 各层组号与路径无关）；旧 K 三档同 edit_masks。"""
    ci, S = env.ci, env.S
    oldk = np.full((ci.T, ci.Nc), np.nan); oldk[ci.t, ci.c] = q0c
    Ld = np.zeros((ci.T, ci.Nc), bool); Ld[ci.t[legal_c], ci.c[legal_c]] = True
    if form not in _K3:
        _K3[form] = RND.terciles_rowwise(oldk, Ld)
    ind = np.asarray(S.icodes)
    return {a: FAST.EditPlan(ci, ind, _K3[form], parent_c, real[a], legal_c, both=True) for a in real}


def edit_masks(env, parent_c, child_c, legal_c, q0c, mech, path, form):
    """（参照实现，只供 e6j_test_fast 逐格核对）EDIT-ENTRY / EDIT-BOTH（单元坐标 → 稠密 → e6j_random → 单元）。"""
    ci, S = env.ci, env.S
    T, Nc = ci.T, ci.Nc
    def dense(b):
        A = np.zeros((T, Nc), bool); A[ci.t[b], ci.c[b]] = True; return A
    oldk = np.full((T, Nc), np.nan); oldk[ci.t, ci.c] = q0c
    ind = np.asarray(S.icodes)
    bd = 1 if mech == 'EDIT_IID' else 5
    Ld = dense(legal_c)
    if form not in _K3:
        _K3[form] = RND.terciles_rowwise(oldk, Ld)
    k3 = _K3[form]
    if mech in ('EDIT', 'EDIT_IID'):
        key = RND.path_key('E6j.P', 'EDIT-ENTRY', form, 'native', mech, path)
        m, short = RND.edit_entry(dense(parent_c), dense(child_c), Ld, env.grid, key, ind, oldk, bd, k3=k3)
    else:
        ko = RND.path_key('E6j.P', 'EDIT-BOTH:out', form, 'native', mech, path)
        ki = RND.path_key('E6j.P', 'EDIT-BOTH:in', form, 'native', mech, path)
        m, short = RND.edit_both(dense(parent_c), dense(child_c), Ld, env.grid, ko, ki, ind, oldk, bd, k3=k3)
    return m[ci.t, ci.c]


def run(pname, form, arm, n_paths=1024, path0=0, profile=False, mechs=None):
    """profile=True：新分量用"旧 K 的复制"代替真实成员（无新增信息，只测时），结果不入库。mechs：只在 profile 时可缩机制。"""
    global MECHS
    if mechs:
        if not profile and '--test' not in sys.argv and not (path0 >= 1024 and tuple(mechs) == ('IID',)):
            raise RuntimeError('正式运行只有 MC 增补分片（path0 ≥ 1024、只 IID = R-MATCH-SRC）可缩机制')
        MECHS = tuple(mechs)
    t0 = time.time()
    ok, why = RP.registration_ok()
    if not ok and not profile:
        raise RuntimeError('登记门：%s' % why)
    env = EN.Env(pname, with_prod=True)
    ctx, ci, SE = env.ctx, env.ci, env.SE
    T = ci.T
    names = [m for _, m in ARMS[arm]]
    if profile:
        comps = {k: env.pK.copy() for k in names}
    else:
        comps = {k: env._dense_cells(SL.member_pct(ctx, *COMP[k])[0]) for k in names}
    st = EN.prod_structure(env, form)
    q0c = env.pK
    perm = Perm(env, comps, q0c)
    legal = ~env.cvr if form.endswith('_CVRv5') else np.ones(ci.n, bool)
    parent = st.kept(st.q0[None, :])[0]
    real = {a: st.kept(EN.blend(st.q0, [(sh, comps[m][None, :]) for sh, m in ARMS[arm]], a))[0] for a in ALPHAS}
    # 恒等置换锚
    anchors = {}
    for mech in ('IID', 'COND'):
        idv = perm.draw(mech, 0, ident=True)
        k = st.kept(EN.blend(st.q0, [(sh, idv[m][None, :]) for sh, m in ARMS[arm]], 0.25))[0]
        anchors[mech] = int((k != real[0.25]).sum())
    if any(anchors.values()):
        raise RuntimeError('恒等置换未复现真实子掩码：%s' % anchors)
    Hi = {H: i for i, H in enumerate(HS)}
    nm = len(MECHS)
    main = np.zeros((nm, n_paths, 4, T))                    # α .25 × H5：net8 / gross / pos / turn
    ann = np.full((nm, n_paths, len(ALPHAS), len(HS), 4), np.nan)   # net8_ann / gross_ann / turn_mean / pos_mean
    mean_daily = np.zeros((nm, len(ALPHAS), len(HS), T))
    plans = edit_plans(env, parent, real, legal, q0c, form) if any(m.startswith('EDIT') for m in MECHS) else {}
    pl0 = plans[ALPHAS[0]] if plans else None                # 候选（合法 \ 父）与父单元对三个 α 相同
    for mi, mech in enumerate(MECHS):
        tm = time.time()
        for b0 in range(0, n_paths, BATCH):
            ps = list(range(path0 + b0, path0 + min(b0 + BATCH, n_paths)))
            # 与 α 无关的随机量每路径只算一次（原实现在每个 α 重算同一结果；e6j_test_fast 逐格核对）
            if mech in ('EDIT', 'EDIT_IID'):
                bd = 1 if mech == 'EDIT_IID' else 5
                UI = [env.grid.u_cells(RND.path_key('E6j.P', 'EDIT-ENTRY', form, 'native', mech, p), pl0.cand_rc[0], pl0.cand_rc[1], bd) for p in ps]
            elif mech == 'EDITB':
                UO = [env.grid.u_cells(RND.path_key('E6j.P', 'EDIT-BOTH:out', form, 'native', mech, p), pl0.par_rc[0], pl0.par_rc[1], 5) for p in ps]
                UI = [env.grid.u_cells(RND.path_key('E6j.P', 'EDIT-BOTH:in', form, 'native', mech, p), pl0.cand_rc[0], pl0.cand_rc[1], 5) for p in ps]
            else:
                DV = [perm.draw(mech, p) for p in ps]
            for ai, a in enumerate(ALPHAS):
                if mech in ('EDIT', 'EDIT_IID'):
                    K = np.vstack([plans[a].entry(u)[None, :] for u in UI])
                elif mech == 'EDITB':
                    K = np.vstack([plans[a].both(uo, ui)[None, :] for uo, ui in zip(UO, UI)])
                else:
                    K = st.kept(np.vstack([EN.blend(st.q0, [(sh, dv[m][None, :]) for sh, m in ARMS[arm]], a) for dv in DV]))
                for j, p in enumerate(ps):
                    kj = K[j]; t, c = ci.t[kj], ci.c[kj]; w = SE.dev(t, c)
                    led = SE.pnl(t, c, w, HS, 8.0)
                    pi = p - path0
                    for H in HS:
                        g, pos, tu, n = led[H]
                        ann[mi, pi, ai, Hi[H]] = (np.nanmean(n) * J.ANN, np.nanmean(g) * J.ANN, np.mean(tu), np.mean(pos))
                        mean_daily[mi, ai, Hi[H]] += np.nan_to_num(n) / n_paths
                        if a == 0.25 and H == 5:
                            main[mi, pi] = (n, g, pos, tu)
        J.log('  %s %s %s %s: %d 路径 %.0fs' % (pname, form, arm, mech, n_paths, time.time() - tm),
              os.path.join(J.RES, 'logs', 'run_prand_%s%s.log' % ('test_' if '--test' in sys.argv else '', pname)))
    if profile:
        J.log('PROFILE %s %s %s paths=%d wall %.0fs' % (pname, form, arm, n_paths, time.time() - t0),
              os.path.join(J.RES, 'logs', 'run_prand_profile.log'))
        return 0
    os.makedirs(os.path.join(OUT, pname), exist_ok=True)
    tag = '' if path0 == 0 else '_p%d' % path0
    path = os.path.join(OUT, pname, '%s__%s%s.npz' % (form, arm, tag))
    J.atomic_write_npz(path, mechs=np.array(MECHS), alphas=np.array(ALPHAS), Hs=np.array(HS), path0=np.array([path0]),
                       main=main, ann=ann, mean_daily=mean_daily, anchors=np.array([anchors['IID'], anchors['COND']]))
    J.write_receipt(('test_' if '--test' in sys.argv else '') + 'run_prand_%s_%s_%s%s' % (pname, form, arm, tag), [path], 'SUCCEEDED',
                    n_paths=n_paths, path0=path0, generator=RND.GEN_ID, wall_s=round(time.time() - t0, 1))
    return 0


if __name__ == '__main__':
    a = sys.argv
    sys.exit(run(a[a.index('--segment') + 1], a[a.index('--form') + 1], a[a.index('--arm') + 1],
                 int(a[a.index('--paths') + 1]) if '--paths' in a else 1024, int(a[a.index('--path0') + 1]) if '--path0' in a else 0,
                 profile='--profile' in a, mechs=a[a.index('--mechs') + 1].split(',') if '--mechs' in a else None))
