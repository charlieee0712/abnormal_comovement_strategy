# -*- coding: utf-8 -*-
"""E6n 四账户与分解（plan §6.4 / §6.4a / §6.5；brief §1.3-7；附录 A3-5、D）。读账户（推导段 deriv_ready；后段 post_gate）。
  fourway --seg S：
    INFO_X_MEMORY   Y00 = Q0 NONE、Y10 = 新 NONE、Y01 = Q0 记忆、Y11 = 新 记忆（同形态 / α / H；HG10 与 LAG1_10 各自）：I = Y10 − Y00、R = Y01 − Y00、
                    X = Y11 − Y10 − Y01 + Y00；逐日先闭合（|Y11 − Y00 − (I + R + X)|），再年化；中位数不相加
    COMBINATION     Q0、Q_PATH .125 共同掩码、Q_CLOSE_THIN .125 共同掩码、Q_BOTH .25：I_P、I_T、X = Y_B − Y_P − Y_T + Y_Q0
    SUPPORT         C_N − P_N = (C_S − P_S) + (C_N − C_S) − (P_N − P_S)（S = 源合法域 ∩ owner 技术可算；accounts_support/）
  → results/<phase>/four_account_ledger_<段>.csv、support_four_accounts_<段>.csv、results/checks/closure_four_accounts.csv（追加段）
  cdose --seg S：component_dose_ledger_<段>.csv（COMPONENT_DOSE 对象：段 D、不可构造日、越界率；匹配目标 = 同支持简化控制）
  mchm --seg S：match_cap_holdings_min_<段>.csv（MATCH_CAP_HOLDINGS_MIN：同日父 / 子滚动暴露向量各缩到 B_t = min(Σp, Σc)，不加杠杆；
                重生净订单 / 费用 / 基准缩放；与源 FULL_sc 并报，不回写）"""
import os
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

ANN = N.ANN


def load_net(seg, sub='accounts'):
    out = {}
    for f in sorted(glob.glob(N.P(sub, seg, '*.npz'))):
        z = np.load(f, allow_pickle=False)
        for did, x in zip([str(v) for v in z['desc']], z['d_net8']):
            out[did] = x
    return out


def ann(x):
    m = np.isfinite(x)
    return float(np.mean(x[m])) * ANN if m.any() else np.nan, int(m.sum())


def q0_id(parent, mem, H, alpha):
    return 'ANCHOR|Q0|%s|%s|H%d|s0|ALL|a%g|f5|d+1' % (parent, mem, H, float(alpha))


def fourway(seg, out):
    d = load_net(seg)
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    rb = D[D.random_bound.astype(str) == 'True']
    idx = {(r.kind, r.feature, r.parent, r.memory, int(r.H), float(r.strength), r.applicability, float(r.outer_alpha), int(r.frequency), int(r.direction)): r.desc_id
           for r in D.itertuples()}
    rows, clos = [], []
    for r in rb[rb.memory != 'NONE'].itertuples():
        k10 = (r.kind, r.feature, r.parent, 'NONE', int(r.H), float(r.strength), r.applicability, float(r.outer_alpha), int(r.frequency), int(r.direction))
        y11, y10 = d.get(r.desc_id), d.get(idx.get(k10))
        y01, y00 = d.get(q0_id(r.parent, r.memory, int(r.H), r.outer_alpha)), d.get(q0_id(r.parent, 'NONE', int(r.H), r.outer_alpha))
        if any(v is None for v in (y11, y10, y01, y00)):
            rows.append(dict(kind='INFO_X_MEMORY', desc_id=r.desc_id, segment=seg, status='ENDPOINT_NOT_COMPUTED'))
            continue
        ok = np.isfinite(y11) & np.isfinite(y10) & np.isfinite(y01) & np.isfinite(y00)
        I, R, X = y10 - y00, y01 - y00, y11 - y10 - y01 + y00
        tot = y11 - y00
        cl = float(np.max(np.abs((tot - (I + R + X))[ok]))) if ok.any() else np.nan
        rows.append(dict(kind='INFO_X_MEMORY', desc_id=r.desc_id, feature=r.feature, parent=r.parent, memory=r.memory, H=int(r.H), strength=r.strength,
                         outer_alpha=r.outer_alpha, segment=seg, I_ann_pp=ann(np.where(ok, I, np.nan))[0], R_ann_pp=ann(np.where(ok, R, np.nan))[0],
                         X_ann_pp=ann(np.where(ok, X, np.nan))[0], total_ann_pp=ann(np.where(ok, tot, np.nan))[0], n=int(ok.sum()), closure_maxabs=cl, status='COMPUTED'))
        clos.append(dict(segment=seg, kind='INFO_X_MEMORY', id=r.desc_id, closure_maxabs=cl))
    for r in rb[rb.kind == 'COMBINATION'].itertuples():
        kp = ('COMBO_COMPONENT', 'Q_PATH', r.parent, r.memory, int(r.H), .125, 'QGOOD', float(r.outer_alpha), 5, 1)
        kt = ('COMBO_COMPONENT', 'Q_CLOSE_THIN', r.parent, r.memory, int(r.H), .125, 'QGOOD', float(r.outer_alpha), 5, 1)
        yb, yp, yt, yq = d.get(r.desc_id), d.get(idx.get(kp)), d.get(idx.get(kt)), d.get(q0_id(r.parent, r.memory, int(r.H), r.outer_alpha))
        if any(v is None for v in (yb, yp, yt, yq)):
            rows.append(dict(kind='COMBINATION', desc_id=r.desc_id, segment=seg, status='ENDPOINT_NOT_COMPUTED'))
            continue
        ok = np.isfinite(yb) & np.isfinite(yp) & np.isfinite(yt) & np.isfinite(yq)
        IP, IT, X = yp - yq, yt - yq, yb - yp - yt + yq
        tot = yb - yq
        cl = float(np.max(np.abs((tot - (IP + IT + X))[ok]))) if ok.any() else np.nan
        rows.append(dict(kind='COMBINATION', desc_id=r.desc_id, feature='Q_BOTH', parent=r.parent, memory=r.memory, H=int(r.H), segment=seg,
                         I_ann_pp=ann(np.where(ok, IP, np.nan))[0], R_ann_pp=ann(np.where(ok, IT, np.nan))[0], X_ann_pp=ann(np.where(ok, X, np.nan))[0],
                         total_ann_pp=ann(np.where(ok, tot, np.nan))[0], n=int(ok.sum()), closure_maxabs=cl, note='I = I_PATH(.125)、R 列 = I_THIN(.125)、X = 交互',
                         status='COMPUTED'))
        clos.append(dict(segment=seg, kind='COMBINATION', id=r.desc_id, closure_maxabs=cl))
    F = pd.DataFrame(rows)
    ds = load_net(seg, 'accounts_support')
    srows = []
    for r in rb.itertuples():
        hits = [k for k in ds if k.endswith('|' + r.desc_id) and k.startswith('SUP|')]
        if not hits:
            continue
        sk = hits[0][4:-(len(r.desc_id) + 1)]
        cS = ds[hits[0]]
        pS = ds.get('SUP|%s|Q0|%s|a%g|H%d' % (sk, r.memory, float(r.outer_alpha), int(r.H)))
        cN, pN = d.get(r.desc_id), d.get(q0_id(r.parent, r.memory, int(r.H), r.outer_alpha))
        if any(v is None for v in (cS, pS, cN, pN)):
            srows.append(dict(owner_desc_id=r.desc_id, segment=seg, support_key=sk, status='ENDPOINT_NOT_COMPUTED'))
            continue
        ok = np.isfinite(cS) & np.isfinite(pS) & np.isfinite(cN) & np.isfinite(pN)
        nat, sup, csh, psh = cN - pN, cS - pS, cN - cS, pN - pS
        cl = float(np.max(np.abs((nat - (sup + csh - psh))[ok]))) if ok.any() else np.nan
        srows.append(dict(owner_desc_id=r.desc_id, segment=seg, support_key=sk, native_diff_ann_pp=ann(np.where(ok, nat, np.nan))[0],
                          support_diff_ann_pp=ann(np.where(ok, sup, np.nan))[0], child_shrink_ann_pp=ann(np.where(ok, csh, np.nan))[0],
                          parent_shrink_ann_pp=ann(np.where(ok, psh, np.nan))[0], n=int(ok.sum()), closure_maxabs=cl, status='COMPUTED'))
        clos.append(dict(segment=seg, kind='SUPPORT', id=r.desc_id, closure_maxabs=cl))
    S = pd.DataFrame(srows)
    os.makedirs(out, exist_ok=True)
    p1 = os.path.join(out, 'four_account_ledger_%s.csv' % seg)
    p2 = os.path.join(out, 'support_four_accounts_%s.csv' % seg)
    N.atomic_write_csv(p1, N.to_status(F))
    N.atomic_write_csv(p2, N.to_status(S) if len(S) else pd.DataFrame([dict(segment=seg, status='SOURCE_WAIT')]))
    cp = N.P('results', 'checks', 'closure_four_accounts.csv')
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    import fcntl
    with open(cp + '.lock', 'w') as lk:                                       # 两段并行时读改写加锁（防丢段）
        fcntl.flock(lk, fcntl.LOCK_EX)
        old = pd.read_csv(cp, keep_default_na=False) if os.path.exists(cp) else pd.DataFrame()
        if len(old):
            old = old[old.segment != seg]
        C = pd.concat([old, pd.DataFrame(clos)], ignore_index=True)
        N.atomic_write_csv(cp, C)
    return [p1, p2, cp], dict(fourway=len(F), support=len(S), closure_max=float(pd.to_numeric(pd.DataFrame(clos).closure_maxabs, errors='coerce').max()) if clos else np.nan)


def cdose(seg, out):
    d = load_net(seg)
    C = pd.read_csv(N.P('registry', 'component_controls_E6n.csv'), keep_default_na=False)
    rows = []
    facts = {}
    for f in glob.glob(N.P('masks', seg, 'facts_*.csv')):
        Fm = pd.read_csv(f, keep_default_na=False)
        for r in Fm.itertuples():
            if str(r.variant).startswith('CDOSE'):
                facts[(os.path.basename(f)[6:-4], r.mask_key)] = r
    import e6n_masks as MK
    R = MK.registry_rows()
    mk = dict(zip(R.obj, R.mask_key))
    for r in C[C.kind == 'COMPONENT_DOSE'].itertuples():
        x = d.get(r.comp_id)
        par = d.get('ANCHOR|ORIGINAL|%s|NONE|H%d|s0|ALL|a0|f5|d+1' % (r.parent, int(r.H)))
        own = d.get(r.owner_desc_id)
        fx = facts.get((r.parent, mk.get(r.comp_id)))
        info = {}
        if fx is not None:
            for c in ('cdose_days', 'cdose_unresolved_days', 'cdose_out_of_unit_share'):
                if hasattr(fx, c):
                    info[c] = getattr(fx, c)
        if x is None or par is None:
            rows.append(dict(comp_id=r.comp_id, owner_desc_id=r.owner_desc_id, segment=seg, status='ENDPOINT_NOT_COMPUTED'))
            continue
        dv, n = ann(x - par)
        do, _ = ann(own - x) if own is not None else (np.nan, 0)
        rows.append(dict(comp_id=r.comp_id, owner_desc_id=r.owner_desc_id, control_desc_id=r.input_control_desc_id, segment=seg, D_ann_pp=dv, n=n,
                         owner_minus_cdose_ann_pp=do, unresolved_days=info.get('cdose_unresolved_days', 'UNKNOWN'), cdose_days=info.get('cdose_days', 'UNKNOWN'),
                         oob_share_decimal=info.get('cdose_out_of_unit_share', 'UNKNOWN'), status='COMPUTED'))
    p = os.path.join(out, 'component_dose_ledger_%s.csv' % seg)
    os.makedirs(out, exist_ok=True)
    N.atomic_write_csv(p, N.to_status(pd.DataFrame(rows)))
    return [p], dict(rows=len(rows))


def mchm(seg, out):
    """MATCH_CAP_HOLDINGS_MIN（plan §6.5）：子 / 父形成目标 → 引擎 act（有效批次权重 / den）→ 同日 B_t = min(Σact_c, Σact_p) → 各自缩放 → 收益 / 基准 / 换手 / 费用重生。"""
    import e6l_env as V
    import e6k_acct as AC
    seg_ = V.SegL(seg, state=False)
    acct = AC.Acct(seg_, impact=False)
    SE = seg_.SE
    r0 = np.asarray(SE.r0, float)
    bench = np.asarray(SE.bench, float)
    T, Nc = r0.shape
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    pol = D[(D.in_policy_table.astype(str) == 'True') & (D.H.astype(int) == 5)]
    rows = []
    cache = {}

    def act_of(form, key, H):
        if (form, key, H) in cache:
            return cache[(form, key, H)]
        z = np.load(N.P('masks', seg, '%s.npz' % form), allow_pickle=False)
        keys = [str(k) for k in z['mask_keys']]
        n = int(z['n_cells'][0])
        F = np.unpackbits(z['final_bits'][keys.index(key)])[:n].astype(bool)
        tg = acct.target(F)
        W = np.zeros((T, Nc))
        np.add.at(W, (tg['t'], tg['c']), tg['w'])
        A = np.cumsum(W, axis=0)
        A[H:] -= A[:-H]
        den = np.minimum(np.arange(1, T + 1), H).astype(float)
        A = A / den[:, None]
        if len(cache) > 40:
            cache.clear()
        cache[(form, key, H)] = A
        return A

    def ledger(A):
        gross = np.zeros(T)
        pos = np.zeros(T)
        gross[2:] = (A[:-2] * r0[2:]).sum(1)
        pos[2:] = A[:-2].sum(1)
        gross = gross - bench * pos
        turn = np.zeros(T)
        dA = np.abs(np.diff(A, axis=0)).sum(1)
        tt = np.zeros(T)
        tt[1:] = dA
        turn[3:] = 0.5 * tt[1:T - 2]
        return gross - turn * 8e-4
    import e6n_masks as MK
    R = MK.registry_rows()
    mkey = dict(zip(R.obj, R.mask_key))
    for r in pol.itertuples():
        H = int(r.H)
        k = mkey.get(r.desc_id)
        if k is None:
            continue
        Ac = act_of(r.parent, k, H)
        Ap = act_of(r.parent, 'NONE|a0|NATIVE', H)
        Sc, Sp = Ac.sum(1), Ap.sum(1)
        Bt = np.minimum(Sc, Sp)
        kc = np.where(Sc > 0, Bt / np.where(Sc > 0, Sc, 1), 0.0)
        kp = np.where(Sp > 0, Bt / np.where(Sp > 0, Sp, 1), 0.0)
        nc, npar = ledger(Ac * kc[:, None]), ledger(Ap * kp[:, None])
        dv, n = ann(nc[2:] - npar[2:])
        rows.append(dict(desc_id=r.desc_id, segment=seg, H=H, D_holdings_min_ann_pp=dv, n=n, status='COMPUTED'))
    p = os.path.join(out, 'match_cap_holdings_min_%s.csv' % seg)
    os.makedirs(out, exist_ok=True)
    N.atomic_write_csv(p, N.to_status(pd.DataFrame(rows)))
    return [p], dict(rows=len(rows), note='H5 政策对象（附表）')


def main():
    import e6n_gate as GT
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['fourway', 'cdose', 'mchm'])
    ap.add_argument('--seg', required=True)
    a = ap.parse_args()
    GT.deriv_ready(a.seg, 'decomp %s %s' % (a.task, a.seg))
    out = N.P('results', 'deriv' if a.seg in N.DERIV_SEGS else 'full', 'decomp')
    t0 = time.time()
    outs, info = {'fourway': fourway, 'cdose': cdose, 'mchm': mchm}[a.task](a.seg, out)
    N.write_receipt('E6n_decomp_%s_%s' % (a.task, a.seg), outs, code=[__file__], wall_s=round(time.time() - t0, 1), **{k: v for k, v in info.items()})
    print(json.dumps(dict(task=a.task, seg=a.seg, wall_s=round(time.time() - t0, 1), **info), ensure_ascii=False, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
