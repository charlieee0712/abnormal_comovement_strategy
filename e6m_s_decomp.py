# -*- coding: utf-8 -*-
"""E6m 账户分解（plan §9.1 / §9.2；brief §5 S4）。读账户（真实目录先过封存门），逐对象、逐日、同单位闭合，段均只在闭合之后取。
  fourway      四账户（plan §9.1 表）：路线 SOURCE / BAND / PRIORITY / HARD，各自 Y00 / Y10 / Y01 / Y11（不跨算子借通用 OLD_LAG）：
               SOURCE   Y00 父 / Y10 Q0 LINEAR α NONE / Y01 K0 OLD_RULE 同源 HG10 或 LAG1_10 / Y11 Q0 LINEAR α 同源 HG10 或 LAG1_10
               BAND     Y00 COPY_GATE_ORDER（owner = 同 w 无记忆 BAND）/ Y10 真实 BAND / Y01 该 COPY 的 PROTECTED_LAG / Y11 真实 BAND PROTECTED_LAG
               PRIORITY Y00 COPY_PASS（owner = 同 c 无记忆 PASS）/ Y10 真实 PASS / Y01 COPY_PASS 自身分区 LAG / Y11 真实 PASS 分区 LAG
               HARD     Y00 父 / Y10 真实 HARD / Y01 K0 OLD_RULE LAG1_10（旧核心源 LAG）/ Y11 源 LAG 门之后的真实 HARD（RULE_LAG10）
               逐日 I = Y10 − Y00、R = Y01 − Y00、X = Y11 − Y10 − Y01 + Y00，核 I + R + X = Y11 − Y00（四者共同有限日；1e−12），另报 Y00 − 实际父。
  capdec       MATCH_CAP 对称分解（plan §9.2）：两边有仓日 Δgross = (u_c − u_p)·(pos_c + pos_p)/2【单位资本效果】+ (pos_c − pos_p)·(u_c + u_p)/2【资本变化】，
               u = gross / pos；单边有仓日另列；真空仓（两边 0）/ 无编辑（父子同一组合，两边有仓日的子集）/ 数据缺失分开计数，不合并；
               状态 UNKNOWN 只对状态条件对象有意义，在 B5 账本里另列。段均（_segavg）与有效日加权（_validavg）两版。
  weightchange Δgross 三项（plan §9.1 末段；plan 参考函数 classify_weight_change）：引擎持仓 act = 近 H 个形成日目标权重均值，gross = Σ act ×（r0 − bench）；
               逐日 新增持有 Σ_{父 0, 子 > 0} act_c·x、消失持有 −Σ_{父 > 0, 子 0} act_p·x、共同重定权 Σ_{都 > 0}(act_c − act_p)·x，三项加回 Δgross（1e−12）。
               需要真实引擎（阶段 S）；主 72 + T 重估桥对象。
输出 <out>/four_account_<段>.csv、cap_decomp_<段>.csv、weight_change_<段>.csv。"""
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


def ann(x):
    x = np.asarray(x, float)
    m = np.isfinite(x)
    return float(np.mean(x[m])) * ANN if m.any() else np.nan


def did(meas, form, op, prm, a, mem, H, ad, cond='-'):
    return '|'.join([meas, form, op, prm, a, mem, 'H%d' % H, ad, cond])


def quads(D, A):
    """四账户清单：[(route, key, Y00, Y10, Y01, Y11, H, parent_id)]；COPY 端用附属账户 ID（aux_id）。"""
    copy = {}
    for r in A[A.mechanism.isin(['COPY_GATE_ORDER', 'COPY_PASS'])].itertuples():
        copy[(r.mechanism, r.owner_id.split('@')[0])] = r.aux_id
    ids = set(D.desc_id)
    out = []
    for r in D.itertuples():
        H = int(r.H)
        par = did('K0', r.parent, 'PARENT', '-', '-', 'NONE', H, 'SOURCE')
        if r.block == 'SOURCE' and r.memory in ('HG10', 'LAG1_10') and r.measurement == 'Q0':
            p = r.desc_id.split('|')
            y10 = did('Q0', r.parent, 'LINEAR', '-', p[4], 'NONE', H, 'SOURCE')
            y01 = did('K0', r.parent, 'OLD_RULE', '-', 'a0', r.memory, H, 'SOURCE')
            out.append(('SOURCE', r.desc_id, par, y10, y01, r.desc_id, H, par))
        elif r.operator in ('BAND_Q', 'BAND_BLEND') and r.memory == 'PROTECTED_LAG10' and r.adapter == 'ACTUAL_GATE':
            y10 = r.desc_id.replace('|PROTECTED_LAG10|', '|NONE|')
            out.append(('BAND', r.desc_id, copy.get(('COPY_GATE_ORDER', y10)), y10, copy.get(('COPY_GATE_ORDER', r.desc_id)), r.desc_id, H, par))
        elif r.operator == 'PRIORITY_PASS' and r.memory == 'RULE_LAG10':
            y10 = r.desc_id.replace('|RULE_LAG10|', '|NONE|')
            out.append(('PRIORITY', r.desc_id, copy.get(('COPY_PASS', y10)), y10, copy.get(('COPY_PASS', r.desc_id)), r.desc_id, H, par))
        elif r.operator == 'HARD_CONJ' and r.memory == 'RULE_LAG10':
            y10 = r.desc_id.replace('|RULE_LAG10|', '|NONE|')
            y01 = did('K0', r.parent, 'OLD_RULE', '-', 'a0', 'LAG1_10', H, 'SOURCE')
            out.append(('HARD', r.desc_id, par, y10, y01, r.desc_id, H, par))
    return [q for q in out if q[3] in ids and q[5] in ids]


def task_fourway(acc, seg, out):
    d, t, d2t, dH, dates = SS.load(acc, seg)
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str, usecols=['aux_id', 'owner_id', 'mechanism'])
    rows = []
    for route, key, y00, y10, y01, y11, H, par in quads(D, A):
        base = dict(route=route, object=key, Y00=y00 or 'UNDEFINED', Y10=y10, Y01=y01 or 'UNDEFINED', Y11=y11, H=H, segment=seg)
        miss = [nm for nm, x in (('Y00', y00), ('Y10', y10), ('Y01', y01), ('Y11', y11)) if not x or x not in d]
        if miss:
            rows.append(dict(base, status='UNDEFINED', note='缺账户：%s' % '|'.join(miss)))
            continue
        for metric in ('net8', 'gross'):
            Y = [np.asarray(d[x][metric], float) for x in (y00, y10, y01, y11)]
            m = np.all([np.isfinite(y) for y in Y], axis=0)
            I = Y[1] - Y[0]
            R = Y[2] - Y[0]
            X = Y[3] - Y[1] - Y[2] + Y[0]
            tot = Y[3] - Y[0]
            clo = float(np.max(np.abs((I + R + X - tot)[m]))) if m.any() else 0.0
            pr = np.asarray(d[par][metric], float) if par in d else np.full(len(m), np.nan)
            mp = m & np.isfinite(pr)
            rows.append(dict(base, metric=metric, I_ann_pp=ann(np.where(m, I, np.nan)), R_ann_pp=ann(np.where(m, R, np.nan)),
                             X_ann_pp=ann(np.where(m, X, np.nan)), total_ann_pp=ann(np.where(m, tot, np.nan)), closure_maxabs=clo,
                             y00_minus_parent_ann_pp=ann(np.where(mp, Y[0] - pr, np.nan)), n_common_days=int(m.sum()),
                             status='COMPUTED' if clo <= TOL else 'CLOSURE_FAIL'))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'four_account_%s.csv' % seg)
    M.atomic_write_csv(p, df)
    return p, df


def capdec_one(c, p):
    gc, gp, pc, pp = (np.asarray(x, float) for x in (c['gross'], p['gross'], c['pos'], p['pos']))
    fin = np.isfinite(gc) & np.isfinite(gp) & np.isfinite(pc) & np.isfinite(pp)
    two = fin & (pc > 0) & (pp > 0)
    onec = fin & (pc > 0) & (pp <= 0)
    onep = fin & (pp > 0) & (pc <= 0)
    vac = fin & (pc <= 0) & (pp <= 0)
    with np.errstate(divide='ignore', invalid='ignore'):
        uc, up = np.where(pc > 0, gc / pc, np.nan), np.where(pp > 0, gp / pp, np.nan)
    unit = np.where(two, (uc - up) * (pc + pp) / 2.0, 0.0)
    capc = np.where(two, (pc - pp) * (uc + up) / 2.0, 0.0)
    one_c = np.where(onec, gc - gp, 0.0)
    one_p = np.where(onep, gc - gp, 0.0)
    dg = np.where(fin, gc - gp, np.nan)
    clo = float(np.nanmax(np.abs(np.where(fin, unit + capc + one_c + one_p - dg, 0.0)))) if fin.any() else 0.0
    T = len(gc)
    nv = max(int(fin.sum()), 1)
    same = two & (gc == gp) & (pc == pp)                       # 无编辑日（父子同一组合：Δ 恰为 0，单列不并入其它类）
    r = dict(closure_maxabs=clo, days_two_sided=int(two.sum()), days_no_edit=int(same.sum()), days_child_only=int(onec.sum()), days_parent_only=int(onep.sum()),
             days_vacuum=int(vac.sum()), days_missing=int((~fin).sum()))
    for nm, x in (('unit_capital_effect', unit), ('capital_change_effect', capc), ('one_sided_child', one_c), ('one_sided_parent', one_p),
                  ('dgross', np.where(fin, gc - gp, 0.0))):
        r['%s_ann_pp_segavg' % nm] = float(np.sum(x)) / T * ANN
        r['%s_ann_pp_validavg' % nm] = float(np.sum(x)) / nv * ANN
    return r


def task_capdec(acc, seg, out):
    d, t, d2t, dH, dates = SS.load(acc, seg)
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str, usecols=['desc_id', 'block'])
    rows = []
    for x in D[D.block != 'PARENT'].desc_id:
        if x not in d:
            continue
        pid = SS.parent_of(x)
        if pid not in d:
            continue
        r = capdec_one(d[x], d[pid])
        rows.append(dict(desc_id=x, parent_id=pid, segment=seg, status='COMPUTED' if r['closure_maxabs'] <= TOL else 'CLOSURE_FAIL', **r))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'cap_decomp_%s.csv' % seg)
    M.atomic_write_csv(p, df)
    return p, df


def task_trefit(acc, seg, out):
    """T 重估桥（plan §9.1 第 3 段）：附属 FROZEN_SOURCE_T_COEFFICIENTS 账户（沿源父 T 系数、只在新 G 上排序）− owner（完整 T 重估），
    以及两者各自相对实际父；逐日共同有效日相减后段均。只分离第一关变化与第二关样本改变，冻结系数版不是生产。"""
    d, t, d2t, dH, dates = SS.load(acc, seg)
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str, usecols=['aux_id', 'owner_id', 'mechanism', 'H'])
    A = A[A.mechanism == 'FROZEN_SOURCE_T_COEFFICIENTS']
    rows = []
    for r in A.itertuples():
        own = r.owner_id.split('@')[0]
        par = SS.parent_of(own)
        if r.aux_id not in d or own not in d or par not in d:
            rows.append(dict(aux_id=r.aux_id, owner=own, segment=seg, status='UNDEFINED'))
            continue
        x = dict(aux_id=r.aux_id, owner=own, H=int(r.H), segment=seg, status='COMPUTED')
        for k in ('net8', 'gross'):
            fz, ow, pa = (np.asarray(d[i][k], float) for i in (r.aux_id, own, par))
            m = np.isfinite(fz) & np.isfinite(ow) & np.isfinite(pa)
            x['frozen_minus_refit_%s_ann_pp' % k] = ann(np.where(m, fz - ow, np.nan))
            x['refit_minus_parent_%s_ann_pp' % k] = ann(np.where(m, ow - pa, np.nan))
            x['frozen_minus_parent_%s_ann_pp' % k] = ann(np.where(m, fz - pa, np.nan))
            x['n_common_days'] = int(m.sum())
        rows.append(x)
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'trefit_%s.csv' % seg)
    M.atomic_write_csv(p, df)
    return p, df


def act_dense(T, Nc, t, c, w, H):
    """引擎持仓：act[j] = Σ_{k < min(j+1, H)} W[j − k] / min(j + 1, H)（e6i_sparse 文档同式）。"""
    W = np.zeros((T, Nc))
    W[t, c] = w
    cs = np.cumsum(W, axis=0)
    act = cs.copy()
    if H < T:
        act[H:] -= cs[:-H]
    den = np.minimum(np.arange(1, T + 1), H).astype(float)
    return act / den[:, None]


def split_day(ac, ap, x):
    """一日：子 / 父持仓向量 ac / ap 与超额收益 x → (新增, 消失, 共同重定权, 总)（plan classify_weight_change 同式）。"""
    added = (ap == 0) & (ac > 0)
    removed = (ap > 0) & (ac == 0)
    common = (ap > 0) & (ac > 0)
    return float(ac[added] @ x[added]), float(-ap[removed] @ x[removed]), float((ac[common] - ap[common]) @ x[common]), float((ac - ap) @ x)


def task_weightchange(seg_name, out):
    """阶段 S（真实引擎）：主 72 + T 重估桥对象。"""
    import e6k_acct as AC
    import e6m_s_real as RL
    seg = RL.seg_of(seg_name, 'real')
    acct = AC.Acct(seg)
    SE = seg.SE
    T, Nc = SE.T, SE.Nc
    x_all = SE.r0 - SE.bench[:, None]
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    P72 = D[D.is_primary72 == 'True']
    rows = []
    for form, g in P72.groupby('parent'):
        z = np.load(M.P('masks', seg_name, '%s.npz' % form), allow_pickle=False)
        n = int(z['n_cells'][0])
        fin = {str(c): j for j, c in enumerate(z['config_ids'])}
        F0 = np.unpackbits(z['parent_final_bits'])[:n].astype(bool)
        tp = acct.target(F0)
        for r in g.itertuples():
            cfg = SS.config_id(r.desc_id) if hasattr(SS, 'config_id') else '|'.join(r.desc_id.split('|')[:6] + r.desc_id.split('|')[7:])
            if cfg not in fin:
                rows.append(dict(desc_id=r.desc_id, segment=seg_name, status='UNDEFINED'))
                continue
            H = int(r.H)
            kept = np.unpackbits(z['final_bits'][fin[cfg]])[:n].astype(bool)
            tc = acct.target(kept)
            ac = act_dense(T, Nc, tc['t'], tc['c'], tc['w'], H)
            ap = act_dense(T, Nc, tp['t'], tp['c'], tp['w'], H)
            parts = np.zeros((T, 4))
            for j in range(2, T):                                  # gross[t] 用 act[t − 2]（e6i_sparse：port[t] = r0[t]·act[t − 2]）
                parts[j] = split_day(ac[j - 2], ap[j - 2], x_all[j])
            led_c = acct.ledgers(tc, (H,), impact=False, roll=False)[H]['gross']
            led_p = acct.ledgers(tp, (H,), impact=False, roll=False)[H]['gross']
            clo_parts = float(np.max(np.abs(parts[:, :3].sum(1) - parts[:, 3])))
            clo_engine = float(np.nanmax(np.abs(parts[:, 3] - (led_c - led_p))))
            rows.append(dict(desc_id=r.desc_id, segment=seg_name, H=H, added_ann_pp=float(np.mean(parts[:, 0])) * ANN,
                             removed_ann_pp=float(np.mean(parts[:, 1])) * ANN, common_reweight_ann_pp=float(np.mean(parts[:, 2])) * ANN,
                             dgross_ann_pp=float(np.mean(parts[:, 3])) * ANN, closure_parts_maxabs=clo_parts, closure_vs_engine_maxabs=clo_engine,
                             status='COMPUTED' if max(clo_parts, clo_engine) <= TOL else 'CLOSURE_FAIL'))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'weight_change_%s.csv' % seg_name)
    M.atomic_write_csv(p, df)
    return p, df


def selftest():
    """合成：随机持仓 / 收益下三项加回总差；act_dense 与 e6i_sparse 的 pos 定义一致（Σ act[t − 2] = pos[t]）。"""
    rng = np.random.default_rng(91)
    T, Nc, H = 40, 30, 5
    t = np.repeat(np.arange(T), 6)
    c = np.concatenate([rng.choice(Nc, 6, replace=False) for _ in range(T)])
    w = rng.uniform(0.01, 0.05, len(t))
    act = act_dense(T, Nc, t, c, w, H)
    sw = np.bincount(t, weights=w, minlength=T)
    rs = sw.copy()
    for k in range(1, H):
        rs[k:] += sw[:T - k]
    den = np.minimum(np.arange(1, T + 1), H)
    ok1 = np.allclose(act.sum(1), rs / den, atol=1e-15)
    t2 = np.repeat(np.arange(T), 5)
    c2 = np.concatenate([rng.choice(Nc, 5, replace=False) for _ in range(T)])
    act2 = act_dense(T, Nc, t2, c2, rng.uniform(0.01, 0.05, len(t2)), H)
    x = rng.normal(0, 0.02, (T, Nc))
    worst = max(abs(sum(split_day(act[j], act2[j], x[j])[:3]) - split_day(act[j], act2[j], x[j])[3]) for j in range(T))
    rd = dict(gross=np.r_[0.01, np.nan, 0.02, 0.0], pos=np.r_[0.9, 0.9, 0.0, 0.0])
    rp = dict(gross=np.r_[0.005, 0.01, 0.01, 0.0], pos=np.r_[0.8, 0.8, 0.5, 0.0])
    cd = capdec_one(rd, rp)
    ok3 = cd['closure_maxabs'] <= TOL and cd['days_missing'] == 1 and cd['days_parent_only'] == 1 and cd['days_vacuum'] == 1 and cd['days_two_sided'] == 1
    return [('act_dense 的 Σ act = 源仓位分母式', ok1), ('三项加回 Δgross（合成 40 日）max|Δ| %.1e' % worst, worst <= 1e-15),
            ('capdec 闭合且四类日数分开计（两边 / 单边父 / 真空 / 缺失各 1）', ok3)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['fourway', 'capdec', 'trefit', 'weightchange', 'selftest'])
    ap.add_argument('--acc', default='')
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
    if a.task == 'weightchange':
        import e6m_s_gate as GT
        SEAL.require('deriv' if a.seg in M.DERIV_SEGS else 'post')
        GT.post_gate(a.seg, 'decomp weightchange %s' % a.seg)            # 直接读后段收益（SE）
    os.makedirs(a.out, exist_ok=True)
    fn = {'fourway': lambda: task_fourway(a.acc, a.seg, a.out), 'capdec': lambda: task_capdec(a.acc, a.seg, a.out),
          'trefit': lambda: task_trefit(a.acc, a.seg, a.out),
          'weightchange': lambda: task_weightchange(a.seg, a.out)}[a.task]
    p, df = fn()
    st = df.status.value_counts().to_dict() if len(df) else {}
    M.write_receipt(os.environ.get('E6M_TASK', 'S_decomp_%s_%s' % (a.task, a.seg)), [p], status='SUCCEEDED', code=[__file__, M.__file__], rows=len(df),
                    status_counts=st, wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(task=a.task, seg=a.seg, rows=len(df), status=st, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
