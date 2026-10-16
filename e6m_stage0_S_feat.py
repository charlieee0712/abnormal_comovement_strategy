# -*- coding: utf-8 -*-
"""E6m Stage 0 · 阶段 S 的特征 / 掩码 / 映射类项（附录 A2-4 映射、A2-5、A2-7、A2-8、A2-9、A3-16、A4-3）。不读任何收益。
  features  A2-5 E6j cache J_B1_qCC raw（e6j_slot.j_member_raw：sha / 形状 / 特征截止校验）在 pool0 单元上逐位 = 本轮 Q0 raw（meas）；
            A2-8 E6i V_park20_LEGACY__LEGACY_PARK_NAN（47 实名：estimand intraday_range_vol / source_bridge / legacy_key __park__；plan 写作 parkinson*__OBS；e6i_member_raw policy=LEGACY_PARK_NAN）先印 raw 分布与符号，再判与本轮 vol（= −源值）逐位同号 / 反号（plan §8.3 / M35）；
            A4-3 E6l cache/state/state_full_E6l.npz 与云机重建 state_full_E6m_cloud.npz 逐键逐位
  maskfacts A2-7 E6l results/stage_a/mask_facts_{deriv,post}_E6l.csv 的同构目标（Q0 / C1 / S / M × α × NATIVE / HG10 / LAG1_10；
            K0 旧规则 × HG10 / LAG1_10）= 本轮 Stage A 同目标（1e−9；列名 / 口径映射见 FIELD_MAP）
  anchormap A2-4 同构映射：E6m 描述符 → E6k / E6l 描述符 ID，按 anchor_candidate 计数核；S1：映射 ID 在源注册表的存在性 → 暴露标签；
            值比对函数 compare_policy 供 engine / A1-auto 用（本文件不读任何账户或政策值）
  claims    A2-9 数值句清单（E6l REVIEW v0.9b / E6m proposal）+ 四条预置机器查询；机器表到达前 SOURCE_WAIT
  memgate   A3 转录 src_mem_gate = 源 e6l_ops.mem_gate（AST 抽取执行，不 import 源模块）在 mock 上逐位；阶段 S 另在真实结构上用 import 核
  p44       A3-16 E6k SA（sa_q_native 转录；S 时与源函数逐位）与 BAND_Q：两端恒等 + 内点是否存在使两者逐位相同的参数
  selftest  伪造缓存（由本轮 raw / vol / 状态缓存写出，再故意改坏）核 A2-5 / A2-8 / A4-3 / A2-7 比对器"该过的过、改坏的抓到"
状态词同 e6m_stage0_S（PASS / FAIL / SOURCE_WAIT / INFO / NOT_RUN）。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time
import shutil
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_stage0_S as S0

SEGS = S0.SEGS
RN = S0.RN
TOL = 1e-9
FIELD_MAP = [                      # (E6l mask_facts 列, 本轮 Stage A 列或函数)
    ('nnames_mean', 'nnames_mean'), ('lv5_mean', 'lv5_mean'), ('edit_weight_share', 'edit_w_in_mean'),
    ('size_edit_gap_T', 'edit_gap_mean_T'), ('size_unknown_weight', 'unkT_mean'), ('small30_share_delta', 'small30_delta'),
    ('size_port_lo_T_segavg', 'port_size_lo_T'), ('size_port_hi_T_segavg', 'port_size_hi_T'),
    ('size_port_delta_T', lambda r: 0.5 * (r['port_size_lo_T'] + r['port_size_hi_T'])),
    ('total_edit_cells', lambda r: r['n_in'] + r['n_out']),
    ('bonus_reliant_share', 'f_bonus_reliant_share'), ('gate_retention', 'f_gate_retention'),
    ('reliant_run_p50', 'f_reliant_run_p50'), ('reliant_run_p90', 'f_reliant_run_p90'), ('reliant_run_max', 'f_reliant_run_max'),
    ('confirm_age_p50', 'f_confirm_age_p50'), ('confirm_age_p90', 'f_confirm_age_p90'), ('confirm_age_max', 'f_confirm_age_max'),
]


def meas(seg):
    return np.load(M.P('stageS_dev', 'meas', 'meas_%s.npz' % seg), allow_pickle=False)


TOL_A28 = 1e-12   # A2-8 逐位容差（2026-10-10 用户定：跨机器 / 跨轮次的舍入级差异不算不一致；A2-5 仍完全相等）


def cmp_cells(x, y):
    """逐位（NaN 位置一致 + 有限值完全相等）→ (相等?, NaN 模式不一致数, 有限值不等数, 最大 |Δ|)。"""
    nx, ny = np.isnan(x), np.isnan(y)
    pat = int((nx != ny).sum())
    m = ~(nx | ny)
    neq = int((x[m] != y[m]).sum())
    md = float(np.max(np.abs(x[m] - y[m]))) if m.any() else 0.0
    return pat == 0 and neq == 0, pat, neq, md


# ====================================================================== features
def member(root, rr, seg, mid, kind, policy='OBS'):
    """源读取函数读伪造 / 真实根下的成员缓存（sha / 形状 / 特征截止校验在源函数里）。"""
    import e6j_slot as SL
    attr = 'J_CACHE' if kind == 'J' else 'E6I_CACHE'
    old = getattr(SL, attr)
    setattr(SL, attr, os.path.join(root, RN[rr], 'cache'))
    try:
        return SL.j_member_raw(seg, mid) if kind == 'J' else SL.e6i_member_raw(seg, mid, policy)
    finally:
        setattr(SL, attr, old)


def a2_5(B, root):
    for seg in SEGS:
        if not os.path.exists(os.path.join(root, RN['J'], 'cache', seg, 'J_B1_qCC.npy')):
            B.add('A2-5', seg, 'E6j J_B1_qCC raw 在 pool0 单元逐位 = 本轮 Q0 raw', '逐位', 'X04 未到', 'SOURCE_WAIT', '本轮 kQ 维持 ANCHOR_PENDING')
            continue
        try:
            arr, meta = member(root, 'J', seg, 'J_B1_qCC', 'J')
        except (RuntimeError, OSError, ValueError) as e:
            B.add('A2-5', seg, '源读取（sha / 形状 / 特征截止）', '通过', repr(e)[:120], 'FAIL')
            continue
        z = meas(seg)
        t, c, raw = z['t'], z['c'], z['raw_Q0']
        shape_ok = arr.shape[1] == len(z['ccols']) and arr.shape[0] > int(t.max())
        B.ok('A2-5', seg, '缓存网格 (T, Nc) 与本轮 pool0 列一致', 'Nc=%d' % len(z['ccols']), 'shape=%s' % (tuple(arr.shape),), shape_ok)
        if not shape_ok:
            continue
        eq, pat, neq, md = cmp_cells(arr[t, c], raw)
        B.ok('A2-5', seg, 'raw 逐位（%d 单元）' % len(t), '0 / 0', 'NaN 模式不一致 %d / 有限值不等 %d / max|Δ| %.3e' % (pat, neq, md), eq)
        out = np.ones(arr.shape, bool)
        out[t, c] = False
        B.add('A2-5', seg, '缓存在 pool0 单元之外的有限值数（INFO）', '', int(np.isfinite(arr[out]).sum()), 'INFO')


def a2_8(B, root):
    for seg in SEGS:
        hits = sorted(glob.glob(os.path.join(root, RN['I'], 'cache', seg, 'V_park20_LEGACY__LEGACY_PARK_NAN.npy')))
        if not hits:
            B.add('A2-8', seg, 'E6i V_park20_LEGACY__LEGACY_PARK_NAN：raw 分布 / 符号 / 与本轮 vol 逐位', '逐位', 'X27 未到', 'SOURCE_WAIT',
                  '本轮 V 方向按源函数（−vol）取负，维持 ANCHOR_PENDING')
            continue
        z = meas(seg)
        t, c, vol = z['t'], z['c'], z['vol']
        for h in hits:
            mid = os.path.basename(h)[:-len('__LEGACY_PARK_NAN.npy')]
            try:
                arr, meta = member(root, 'I', seg, mid, 'I', policy='LEGACY_PARK_NAN')
            except (RuntimeError, OSError, ValueError) as e:
                B.add('A2-8', '%s %s' % (seg, mid), '源读取（sha / 形状 / 特征截止）', '通过', repr(e)[:120], 'FAIL')
                continue
            if arr.shape[1] != len(z['ccols']) or arr.shape[0] <= int(t.max()):
                B.add('A2-8', '%s %s' % (seg, mid), '缓存网格与本轮 pool0 列一致', 'Nc=%d' % len(z['ccols']), 'shape=%s' % (tuple(arr.shape),), 'FAIL')
                continue
            x = arr[t, c]
            f = np.isfinite(x)
            q = np.percentile(x[f], [1, 50, 99]) if f.any() else [np.nan] * 3
            B.add('A2-8', '%s %s' % (seg, mid), 'raw 分布（pool0 单元）', '', 'n=%d 有限 %d 正 %.4f 负 %.4f 零 %.4f p01 %.4g p50 %.4g p99 %.4g' %
                  (len(x), f.sum(), (x[f] > 0).mean() if f.any() else np.nan, (x[f] < 0).mean() if f.any() else np.nan,
                   (x[f] == 0).mean() if f.any() else np.nan, q[0], q[1], q[2]), 'INFO')
            same = cmp_cells(x, vol)
            anti = cmp_cells(x, -vol)
            ok_s = same[1] == 0 and same[3] <= TOL_A28        # NaN 位置一致 + 有限值 max|Δ| ≤ 1e−12（2026-10-10 用户定）
            ok_a = anti[1] == 0 and anti[3] <= TOL_A28
            which = '缓存 = +vol（经济方向）' if ok_s else ('缓存 = 源值（−vol）' if ok_a else '都不逐位')
            B.ok('A2-8', '%s %s' % (seg, mid), '逐位（NaN 位置一致 + 有限值 max|Δ| ≤ 1e−12）：缓存 = +vol 或 = 源值（−vol）', '其一成立',
                 '%s；同号比 NaN %d / 不等 %d / max|Δ| %.3e' % (which, same[1], same[2], same[3]), ok_s or ok_a)


def a4_3(B, root):
    sp = os.path.join(root, RN['L'], 'cache', 'state', 'state_full_E6l.npz')
    mine = M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz')
    if not os.path.exists(sp):
        B.add('A4-3', 'state_full_E6l.npz', '云机重建状态缓存逐键逐位 = E6l', '逐位', 'X21 未到', 'SOURCE_WAIT', '云机缓存维持 ANCHOR_PENDING')
        return
    za, zb = np.load(sp, allow_pickle=False), np.load(mine, allow_pickle=False)
    ka, kb = set(za.files), set(zb.files) - {'status'}
    for k in sorted(ka & kb):
        a, b = za[k], zb[k]
        if a.dtype.kind in 'fc' or b.dtype.kind in 'fc':
            ok = a.shape == b.shape and np.array_equal(a.astype(float), b.astype(float), equal_nan=True)
        else:
            ok = a.shape == b.shape and bool((a.astype(str) == b.astype(str)).all())
        B.ok('A4-3', k, '逐位', '%s %s' % (a.dtype, a.shape), '%s %s' % (b.dtype, b.shape), ok)
    for k in sorted(ka - kb):
        B.add('A4-3', k, '只在 E6l 缓存（INFO）', '', '', 'INFO')
    for k in sorted(kb - ka):
        B.add('A4-3', k, '只在云机缓存（INFO）', '', '', 'INFO')


# ====================================================================== maskfacts（A2-7）
def e6l_target(cid):
    """E6m 配置 ID（描述符去 H）→ E6l target_id（e6l_registry.target_of：f|p|a<α>|op）；非同构 → None。"""
    p = cid.split('|')
    if len(p) != 8:
        return None
    f, par, op, prm, a, mem, ad, cond = p
    if ad != 'SOURCE' or prm != '-' or cond != '-':
        return None
    if f == 'K0' and op == 'OLD_RULE' and mem in ('HG10', 'LAG1_10'):
        return 'K0|%s|a0|%s' % (par, mem)
    if f in ('Q0', 'C1', 'S', 'M') and op == 'LINEAR' and mem in ('NONE', 'HG10', 'LAG1_10'):
        return '%s|%s|%s|%s' % (f, par, a, 'NATIVE' if mem == 'NONE' else mem)
    return None


def fval(r, spec):
    try:
        v = spec(r) if callable(spec) else r[spec]
        return float(v)
    except (KeyError, TypeError, ValueError):
        return np.nan


def a2_7(B, root, sa_dir):
    for tag, segs in (('deriv', M.DERIV_SEGS), ('post', M.POST_SEGS)):
        lp = os.path.join(root, RN['L'], 'results', 'stage_a', 'mask_facts_%s_E6l.csv' % tag)
        if not os.path.exists(lp):
            B.add('A2-7', 'mask_facts_%s_E6l.csv' % tag, '同构 HG / LAG 目标 = 本轮 Stage A（1e−9）', '逐列', 'X18 未到', 'SOURCE_WAIT')
            continue
        E = M.read_csv_keep(lp)
        E = E[E.variant == 'REGISTERED'] if 'variant' in E.columns else E
        for seg in segs:
            fs = sorted(glob.glob(os.path.join(sa_dir, seg, 'mask_facts_*.csv')))
            if not fs:
                B.add('A2-7', seg, '本轮 Stage A 事实', '存在', '缺', 'NOT_RUN', '先跑 Stage A')
                continue
            Mi = pd.concat([M.read_csv_keep(f) for f in fs], ignore_index=True)
            Mi = Mi[(Mi.kind == 'MAIN') & (Mi.status == 'COMPUTED')].copy()
            Mi['e6l_target'] = Mi.target.map(e6l_target)
            Mi = Mi[Mi.e6l_target.notna()]
            Es = E[E.segment == seg].drop_duplicates('target_id').set_index('target_id')
            n_t = n_bad = 0
            for mi in Mi.to_dict('records'):                    # 记录字典（不走 itertuples：列名改写会静默丢列）
                if mi['e6l_target'] not in Es.index:
                    B.add('A2-7', '%s %s' % (seg, mi['target']), 'E6l 有同构目标', mi['e6l_target'], '缺', 'INFO', '源注册表无此目标（S1 交集定标签）')
                    continue
                e = Es.loc[mi['e6l_target']]
                n_t += 1
                for ecol, spec in FIELD_MAP:
                    if ecol not in Es.columns:
                        continue
                    a_, b_ = fval(e, ecol), fval(mi, spec)
                    if np.isnan(a_) and np.isnan(b_):
                        continue
                    ok = np.isfinite(a_) and np.isfinite(b_) and abs(a_ - b_) <= TOL
                    if not ok:
                        n_bad += 1
                        B.add('A2-7', '%s %s' % (seg, mi['target']), ecol, '%.12g' % a_, '%.12g' % b_, 'FAIL')
            B.ok('A2-7', '%s（%s）' % (seg, tag), '同构目标数 / 不一致字段数', '不一致 0', '%d 目标 / %d 不一致' % (n_t, n_bad), n_t > 0 and n_bad == 0)


# ====================================================================== anchormap（A2-4）
def _p(did):
    p = did.split('|')
    if len(p) != 9:
        raise ValueError(did)
    return p


def e6k_equiv(did):
    """E6m 描述符 → E6k 描述符 ID（E6k：Q / C1 / S / M × NATIVE / NATIVE_HG10；K0 × PARENT / HG_ONLY10）。"""
    f, p, op, prm, a, mem, H, ad, cond = _p(did)
    if ad != 'SOURCE' or prm != '-' or cond != '-':
        return None
    h = int(H[1:])
    if f == 'K0':
        if op == 'PARENT':
            return 'K0|%s|a0|H%d|PARENT' % (p, h)
        if op == 'OLD_RULE' and mem == 'HG10':
            return 'K0|%s|a0|H%d|HG_ONLY10' % (p, h)
        return None
    if op != 'LINEAR' or f not in ('Q0', 'C1', 'S', 'M'):
        return None
    fk = 'Q' if f == 'Q0' else f
    if mem == 'NONE':
        return '%s|%s|%s|H%d|NATIVE' % (fk, p, a, h)
    if mem == 'HG10':
        return '%s|%s|%s|H%d|NATIVE_HG10' % (fk, p, a, h)
    return None


def e6l_equiv(did):
    """E6m 描述符 → E6l 描述符 ID（e6l_registry.desc_id：f|p|a<α>|H|op；K0 父 = NATIVE）。"""
    f, p, op, prm, a, mem, H, ad, cond = _p(did)
    if ad != 'SOURCE' or prm != '-' or cond != '-':
        return None
    h = int(H[1:])
    if f == 'K0':
        if op == 'PARENT':
            return 'K0|%s|a0|H%d|NATIVE' % (p, h)
        if op == 'OLD_RULE' and mem in ('HG10', 'LAG1_10'):
            return 'K0|%s|a0|H%d|%s' % (p, h, mem)
        return None
    if op != 'LINEAR' or f not in ('Q0', 'C1', 'S', 'M'):
        return None
    return '%s|%s|%s|H%d|%s' % (f, p, a, h, 'NATIVE' if mem == 'NONE' else mem)


EXPECT_MAP = {   # anchor_candidate → (须有 e6k 映射, 须有 e6l 映射)
    'E6K_POLICY': (True, None), 'E6K_POLICY(K0×HG_ONLY10)': (True, None), 'E6L_POLICY': (None, True),
    'E6L_POLICY_CANDIDATE(K0×LAG1_10)': (None, True), 'E5A_POOL2+E6J_LEADER+E6K/E6L_PARENT': (True, True), 'E6I_PARENT_ANCHOR': (True, True),
    'NONE_NEW_OPERATOR': (False, False),
}


def task_anchormap(B, root, od):
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    D['e6k_id'] = D.desc_id.map(e6k_equiv)
    D['e6l_id'] = D.desc_id.map(e6l_equiv)
    for ac, g in D.groupby('anchor_candidate'):
        nk, nl = int(g.e6k_id.notna().sum()), int(g.e6l_id.notna().sum())
        ek, el = EXPECT_MAP.get(ac, (None, None))
        okk = True if ek is None else (nk == len(g) if ek else nk == 0)
        okl = True if el is None else (nl == len(g) if el else nl == 0)
        ok = okk and okl
        if ac == 'REGISTRY_INTERSECTION_AT_S1':
            ok = int((g.e6k_id.notna() | g.e6l_id.notna()).sum()) == len(g)
        B.ok('A2-4', ac, '映射计数（%d 个）' % len(g), '按候选类', 'E6k %d / E6l %d' % (nk, nl), ok)
    kp = os.path.join(root, RN['K'], 'registry', 'descriptors_E6k.csv')
    lp = os.path.join(root, RN['L'], 'registry', 'descriptors_E6l.csv')
    ks = set(pd.read_csv(kp, usecols=['desc_id']).desc_id) if os.path.exists(kp) else None
    ls = set(pd.read_csv(lp, usecols=['desc_id']).desc_id) if os.path.exists(lp) else None
    D['in_e6k'] = D.e6k_id.map(lambda x: 'NOT_APPLICABLE' if x is None or (isinstance(x, float)) else ('SOURCE_WAIT' if ks is None else str(x in ks)))
    D['in_e6l'] = D.e6l_id.map(lambda x: 'NOT_APPLICABLE' if x is None or (isinstance(x, float)) else ('SOURCE_WAIT' if ls is None else str(x in ls)))
    cand = D.exposure == 'SOURCE_WAIT_REGISTRY_INTERSECTION'

    def lab(r):
        if r.exposure != 'SOURCE_WAIT_REGISTRY_INTERSECTION':
            return r.exposure
        if 'SOURCE_WAIT' in (r.in_e6k, r.in_e6l) and 'True' not in (r.in_e6k, r.in_e6l):
            return 'SOURCE_WAIT_REGISTRY_INTERSECTION'
        return M.LABEL_SECOND if 'True' in (r.in_e6k, r.in_e6l) else M.LABEL_FIRST_LOOK
    D['exposure_S1'] = [lab(r) for r in D.itertuples()]
    for nm, s in (('descriptors_E6k.csv（X12）', ks), ('descriptors_E6l.csv（X18）', ls)):
        if s is None:
            B.add('A2-4', nm, 'S1 注册交集', '源注册表', '未到', 'SOURCE_WAIT', '暴露标签维持 SOURCE_WAIT_REGISTRY_INTERSECTION')
    if ks is not None:
        miss = D[D.anchor_candidate.isin(['E6K_POLICY', 'E6K_POLICY(K0×HG_ONLY10)']) & (D.in_e6k != 'True')]
        rel = miss[miss.in_e6l == 'True']      # E6k 未覆盖、E6l 有 → 改由 E6l 锚（2026-10-10 用户定；登记不改；engine 抽样归 E6l 组）
        bad = miss[miss.in_e6l != 'True']
        B.add('A2-4', 'E6K_POLICY 锚对象（E6k 未覆盖 → E6l）', 'descriptors_E6k 无、descriptors_E6l 有', '', '%d：%s' % (len(rel), list(rel.e6k_id[:3])), 'INFO',
              '前提 = 下一行 E6k∩E6l 一致性检查')
        kpp = os.path.join(root, RN['K'], 'results', 'full', 'policy_E6k.csv')
        lpp = os.path.join(root, RN['L'], 'results', 'full', 'policy_E6l.csv')
        if len(rel) and os.path.exists(kpp) and os.path.exists(lpp):
            cols = ['%s_%s' % (p, s) for s in SEGS for p in ('D', 'n', 'D_sc')]
            pk = pd.read_csv(kpp, keep_default_na=False, na_values=[''], usecols=['desc_id'] + cols).set_index('desc_id')
            pl = pd.read_csv(lpp, keep_default_na=False, na_values=[''], usecols=['desc_id'] + cols).set_index('desc_id')
            X = D[D.e6k_id.isin(pk.index) & D.e6l_id.isin(pl.index)]
            kv, lv = pk.loc[X.e6k_id, cols].to_numpy(float), pl.loc[X.e6l_id, cols].to_numpy(float)
            fin = np.isfinite(kv) & np.isfinite(lv)
            pat = int((np.isfinite(kv) != np.isfinite(lv)).sum())
            md = float(np.abs(kv - lv)[fin].max()) if fin.any() else 0.0
            B.ok('A2-4', 'E6k∩E6l 同构 %d 个（NATIVE_HG10 %d）' % (len(X), int(X.e6k_id.str.endswith('NATIVE_HG10').sum())),
                 'policy_E6k = policy_E6l（四段 D / n / D_sc）——E6k 未覆盖者改由 E6l 锚的前提', 'max|Δ| ≤ 1e−9、NaN 位置一致',
                 'max|Δ| %.2e / NaN 位置不一致 %d' % (md, pat), md <= 1e-9 and pat == 0 and len(X) > 0)
        B.ok('A2-4', 'E6K_POLICY 锚对象', '映射 ID 在 descriptors_E6k；未覆盖者须在 descriptors_E6l', '缺 0', '缺 %d：%s' % (len(bad), list(bad.e6k_id[:5])), bad.empty)
    if ls is not None:
        miss = D[(D.anchor_candidate == 'E6L_POLICY') & (D.in_e6l != 'True')]
        B.ok('A2-4', 'E6L_POLICY 锚对象', '映射 ID 全在 descriptors_E6l', '缺 0', '缺 %d：%s' % (len(miss), list(miss.e6l_id[:5])), miss.empty)
        cnd = D[D.anchor_candidate == 'E6L_POLICY_CANDIDATE(K0×LAG1_10)']
        B.add('A2-4', 'E6L_POLICY_CANDIDATE(K0×LAG1_10)', '映射 ID 在 descriptors_E6l 的个数（INFO）', len(cnd), int((cnd.in_e6l == 'True').sum()), 'INFO')
    c2 = D[cand].exposure_S1.value_counts().to_dict()
    B.add('A2-4', '注册交集候选 %d 个' % int(cand.sum()), 'S1 暴露标签分布（INFO）', '', json.dumps(c2, ensure_ascii=False), 'INFO')
    p = os.path.join(od, 'anchor_map_E6m.csv')
    M.atomic_write_csv(p, D[['desc_id', 'anchor_candidate', 'exposure', 'e6k_id', 'e6l_id', 'in_e6k', 'in_e6l', 'exposure_S1']].fillna('NOT_APPLICABLE'))
    return p


POLICY_COLS = tuple(['D_%s' % s for s in SEGS] + ['n_%s' % s for s in SEGS] + ['D_sc_%s' % s for s in SEGS] + ['FULL', 'G4'])


def compare_policy(mine, ref, id_col, cols=POLICY_COLS, tol=TOL, label=''):
    """A2-4 值比对（engine / A1-auto 调用；本模块不调用）：mine = policy_E6m（desc_id），ref = policy_E6k / E6l（desc_id），
    id_col = mine 中给出源 ID 的列。返回逐 (对象, 列) 行：mine / ref / |Δ| / 状态。"""
    R = ref.drop_duplicates('desc_id').set_index('desc_id')
    Mi = mine[mine[id_col].isin(R.index)]                       # 列名含连字符（D_2010-2014），只按列数组取，不走 itertuples 属性
    rows = []
    for c in cols:
        if c not in R.columns or c not in Mi.columns:
            continue
        a = pd.to_numeric(Mi[c], errors='coerce').to_numpy(float)
        b = pd.to_numeric(R.loc[Mi[id_col].values, c], errors='coerce').to_numpy(float)
        for did, rid, x, y in zip(Mi.desc_id.values, Mi[id_col].values, a, b):
            both_nan = np.isnan(x) and np.isnan(y)
            d = abs(x - y) if not (np.isnan(x) or np.isnan(y)) else np.nan
            ok = both_nan or (np.isfinite(d) and d <= tol)
            rows.append(dict(desc_id=did, ref_id=rid, column=c, mine=x, ref=y, absdiff=d, status='PASS' if ok else 'FAIL', anchor_label=label))
    return pd.DataFrame(rows, columns=['desc_id', 'ref_id', 'column', 'mine', 'ref', 'absdiff', 'status', 'anchor_label'])


# ====================================================================== claims（A2-9）
NUM = re.compile(r'(?<![\w§#.])[+−\-]?(?:\d+\.\d+|\.\d+)(?![\w.])|(?<![\w§#.])\d+(?:\.\d+)?\s*%')


def numeric_sentences(path, doc):
    """逐行切句（。；），保留含数值的句子；跳过代码块、标题行、sha / 路径行。"""
    out, code = [], False
    for i, ln in enumerate(open(path, encoding='utf-8'), 1):
        s = ln.rstrip('\n')
        if s.strip().startswith('```'):
            code = not code
            continue
        if code or not s.strip() or s.lstrip().startswith('#'):
            continue
        for sent in re.split(r'(?<=[。；])', s):
            sent = sent.strip()
            if len(sent) < 6 or not NUM.search(sent) or re.search(r'[0-9a-f]{16,}', sent):
                continue
            out.append(dict(doc=doc, line=i, source_text=sent[:400]))
    return out


PRESET = [
    ('HG_MINUS_LAG_MAIN', 'HG − LAG 主对象差', 'E6l policy：Q0 × {HG10, LAG1_10} × 六形态 × α .25 × H5 的 FULL 差（逐形态）'),
    ('LE_002_SET', '"≤ .02" 的实际集合', 'E6l policy：上式 |FULL 差| ≤ .02 的对象清单'),
    ('COVER_746', '.746 覆盖', '人工定位原句后指定（机器表到达后 S1）'),
    ('ALPHA05_LO_T', 'α .5 四段 lo_T', 'E6l policy：Q0 × α .5 × 六形态 × H5 的 port_size_lo_T_<段>（四段）'),
]


def preset_values(pol):
    out = {}
    P = pol.copy()
    six = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
    pick = lambda op, a: P[(P.meas == 'Q0') & (P.op == op) & (P.alpha.astype(float) == a) & (P.H.astype(int) == 5) & P.mother.isin(six)].set_index('mother')
    hg, lag = pick('HG10', .25), pick('LAG1_10', .25)
    d = (hg.FULL - lag.FULL).dropna()
    out['HG_MINUS_LAG_MAIN'] = '; '.join('%s %.4f' % (k, v) for k, v in d.items())
    out['LE_002_SET'] = '|'.join(sorted(k for k, v in d.items() if abs(v) <= 0.02)) or '空'
    n5 = pick('NATIVE', .5)
    out['ALPHA05_LO_T'] = '; '.join('%s %s' % (k, '/'.join('%.3f' % n5.at[k, 'port_size_lo_T_%s' % s] for s in SEGS if 'port_size_lo_T_%s' % s in n5.columns))
                                    for k in n5.index)
    return out


def task_claims(B, root, od):
    ho = os.path.join(M.RUNS, 'handoff', 'E6m')
    rows = []
    for f, doc in (('E6l_REVIEW.md', 'E6l REVIEW v0.9b'), ('E6m_proposal.md', 'E6m proposal')):
        p = os.path.join(ho, f)
        if os.path.exists(p):
            rows += numeric_sentences(p, doc)
        else:
            B.add('A2-9', f, '数值句来源', '存在', '缺', 'FAIL')
    pol_p = os.path.join(root, RN['L'], 'results', 'full', 'policy_E6l.csv')
    pv = {}
    if os.path.exists(pol_p):
        try:
            pv = preset_values(pd.read_csv(pol_p, low_memory=False))
        except (KeyError, ValueError, TypeError) as e:                 # E6l 列名与预期不符：记 INFO，人工在 S1 指定查询
            B.add('A2-9', 'policy_E6l.csv', '预置查询（列名假设：meas / op / mother / alpha / H / FULL / port_size_lo_T_<段>）', '可算',
                  '列不符：%s' % repr(e)[:120], 'INFO')
    for i, r in enumerate(rows, 1):
        r.update(claim='C%04d' % i, scope='逐句（S1 人工指定机器查询）', machine_query='', machine_value='SOURCE_WAIT' if not pv else 'UNDEFINED',
                 status='SOURCE_WAIT')
    for cid, name, q in PRESET:
        rows.append(dict(claim=cid, doc='附录 A2-9 点名', line=0, source_text=name, scope='预置查询', machine_query=q,
                         machine_value=pv.get(cid, 'SOURCE_WAIT'), status='SOURCE_WAIT' if cid not in pv else 'INFO'))
    df = pd.DataFrame(rows, columns=['claim', 'doc', 'line', 'source_text', 'scope', 'machine_query', 'machine_value', 'status'])
    p = os.path.join(od, 'source_claim_reconciliation.csv')
    M.atomic_write_csv(p, df)
    B.add('A2-9', 'source_claim_reconciliation.csv', '数值句 / 预置查询', '每句一行', '%d 句 + %d 预置' % (len(df) - len(PRESET), len(PRESET)),
          'SOURCE_WAIT' if not pv else 'INFO', '机器表（X17 / X22）到达后逐句回查；预置查询自动算')
    return p


# ====================================================================== p44（A3-16）
def sa_q_native(k0, kf, a, b):
    """e6k_ops.sa_q_native 转录：k = k0 + a·d·1(|d| ≥ b/100)，指示为 1 处取 (1 − a)·k0 + a·kf；kf 缺失 → k0。"""
    ind = np.isfinite(kf) & (np.abs(kf - k0) >= b / 100.0 - 1e-15)
    return np.where(ind, (1 - a) * k0 + a * kf, k0)


P44_TEXT = """A3-16（P44）文字核：
- E6k SA（e6k_ops.sa_q_native / sa_q_inc；supp1_band 只是同一 bootstrap 路径上的带统计量读数，与 SA 算子无关）：逐股评分层的死区——
  个股 |kf − k0| ≥ b/100 时才把评分移向新测量（(1−a)·k0 + a·kf），否则保持旧 K 分；无记忆、不看名单、不看门边界位置。
  两端：b = 0 ≡ NATIVE(α = a)；b → ∞ ≡ 父（k = k0）。
- E6m BAND_Q（plan §5.1）：门边界附近的名单带——逐日按源总序，带外（A 稳进 / C 稳出）身份固定，只在宽 w 的边界带内按 kQ 重排 m 个可动名额；
  作用在名单层而非评分层，可动者由"离门边界多远"决定而不是由"|Δ分| 多大"决定。两端：w = 0 ≡ 源对象；FULL_MUTABLE（A = C 空）≡ 全域按 kQ 取名额。
- 读法：两者只在端点可能重合（b → ∞ 与 w = 0 都回父；单腿形态 SA(a = 1, b = 0) 与 FULL_MUTABLE 至多差在 Q 缺失回退与 tie 键），
  内点作用对象不同；下表在真实 / mock 结构上逐位核端点，并对每个 w 在 (a, b) 网格上找最小名单差——最小差 > 0 即"实现不等价"，
  BAND 成员保留（不按 P44 作废），R0 写明。"""


def task_p44(B, struct_kind, od, segs=('2010-2014', '2015-2018')):
    import e6m_s_ops as SO
    rows = []
    with open(os.path.join(od, 'p44_text.md'), 'w', encoding='utf-8') as fh:
        fh.write(P44_TEXT + '\n')
    try:
        import e6k_ops as KO                                   # 账户侧（import 期经 e6e_core 读 roles.csv）
        rng = np.random.default_rng(44)
        k0, kf = rng.uniform(size=5000), np.where(rng.uniform(size=5000) < .1, np.nan, rng.uniform(size=5000))
        same = all(np.array_equal(KO.sa_q_native(k0, kf, a, b), sa_q_native(k0, kf, a, b), equal_nan=True)
                   for a in (.125, .25, .5, 1.0) for b in (0, 2, 5, 10, 30))
        B.ok('A3-16', 'sa_q_native', '转录 = 源函数逐位（合成 5,000 × 20 组）', '逐位', same, same)
    except Exception as e:                                       # noqa: BLE001
        B.add('A3-16', 'sa_q_native', '转录 = 源函数逐位', '逐位', 'e6k_ops 不可 import：%s' % type(e).__name__, 'SOURCE_WAIT', 'X01 到达后在阶段 S 重跑')
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    ws = sorted(set(D[(D.operator == 'BAND_Q') & (D.measurement == 'Q0') & (D.memory == 'NONE')].param.astype(float)))
    A_ = (0.125, 0.25, 0.5, 1.0)
    B_ = (0.0, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 50.0, 1e6)
    for seg in segs:
        if struct_kind == 'mock':
            import e6m_s_mock as MK
            sg = MK.MockSeg(seg)
        else:
            import e6m_stage0_S_engine as EN
            sg = EN.real_seg(seg)
        kq = meas(seg)['kQ0'] if struct_kind == 'mock' else sg.meas_kf('Q0')
        for form in ('A4b', 'M_mean3_v2', 'M_union3_v2'):
            st = sg.struct(form)
            ctx = SO.Ctx(st, kq)
            U0 = ctx.U0
            sa = {}
            for a in A_:
                for b in B_:
                    q = sa_q_native(st.q0, kq, a, b)
                    sa[(a, b)] = st.gate_keep(st.gate_scores(q[None, :]))[0]
            for a in A_:
                nat, _ = SO.source_gate(ctx, a)
                B.ok('A3-16', '%s %s' % (seg, form), 'SA(a=%g, b=0) ≡ NATIVE(α=%g)' % (a, a), '0 格差', int((sa[(a, 0.0)] != nat).sum()),
                     not (sa[(a, 0.0)] != nat).any())
            B.ok('A3-16', '%s %s' % (seg, form), 'SA(b → ∞) ≡ 父 U0', '0 格差', int((sa[(0.5, 1e6)] != U0).sum()), not (sa[(0.5, 1e6)] != U0).any())
            g0 = SO.band_gates(ctx, 0.0)[0]
            B.ok('A3-16', '%s %s' % (seg, form), 'BAND_Q(w=0) ≡ 源 U0', '0 格差', int((g0 != U0).sum()), not (g0 != U0).any())
            gf = SO.band_gates(ctx, 0.5)[0]
            dfm = int((gf != sa[(1.0, 0.0)]).sum())
            B.add('A3-16', '%s %s' % (seg, form), 'BAND_Q FULL_MUTABLE（w = .5）vs SA(a=1, b=0)（INFO：单腿至多差在缺失回退 / tie）', '', '%d 格差' % dfm, 'INFO')
            for w in ws:
                gw = SO.band_gates(ctx, w)[0]
                diffs = {k: int((gw != v).sum()) for k, v in sa.items()}
                kbest = min(diffs, key=diffs.get)
                rows.append(dict(segment=seg, form=form, w=w, best_a=kbest[0], best_b=kbest[1], min_cells_diff=diffs[kbest], band_vs_U0=int((gw != U0).sum())))
                B.add('A3-16', '%s %s w=%g' % (seg, form, w), 'SA 网格内与 BAND_Q 最小名单差（> 0 = 无参数使两者相同）', '> 0',
                      '%d 格（a=%g, b=%g）；BAND 对 U0 %d 格' % (diffs[kbest], kbest[0], kbest[1], rows[-1]['band_vs_U0']), 'INFO')
    R = pd.DataFrame(rows)
    M.atomic_write_csv(os.path.join(od, 'p44_grid.csv'), R)
    eq = bool(len(R)) and bool((R.min_cells_diff == 0).all())
    B.add('A3-16', 'P44 判读（%s 结构）' % struct_kind, '实现等价？', '内点任一 w 有最小差 0 → 等价', 'EQUIVALENT' if eq else 'NOT_EQUIVALENT',
          'INFO', 'NOT_EQUIVALENT → BAND 成员保留（不按 P44 作废），R0 写明；mock 结果在阶段 S 用真实结构重跑定稿')
    return R


# ====================================================================== memgate（A3：转录 = 源函数文本）
def extract_source_funcs(path, names, consts=()):
    """从源文件按 AST 抽出指定顶层函数 / 常量，在只含 numpy / hashlib 的命名空间里编译执行（不 import 源模块，不触发其 import 期读文件）。"""
    import ast
    import hashlib
    src = open(path, encoding='utf-8').read()
    tree = ast.parse(src)
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name in names)
            or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in consts for t in n.targets))]
    got = set(n.name for n in keep if isinstance(n, ast.FunctionDef))
    if got != set(names):
        raise RuntimeError('源函数缺：%s' % sorted(set(names) - got))
    mod = ast.Module(body=keep, type_ignores=[])
    ns = {'np': np, 'hashlib': hashlib, '__name__': 'e6l_ops_extract'}
    exec(compile(mod, path, 'exec'), ns)                         # noqa: S102（只执行源文件中的纯函数定义）
    return ns, M.sha_bytes(src.encode('utf-8'))


def task_memgate(B, segs=SEGS):
    """转录 e6m_s_ops.src_mem_gate 与源 e6l_ops.mem_gate（AST 抽取执行）在 mock 结构上逐位：HG10 / LAG1_10 × α {0（父分）, .125, .25, .5} × 六形态。"""
    from types import SimpleNamespace
    import e6m_s_ops as SO
    import e6m_s_mock as MK
    path = os.path.join(M.CODE, 'e6l_ops.py')
    ns, sh = extract_source_funcs(path, ('parse_op', 'ids_hash', 'cold_state', '_date_at', '_check_resume', 'select_rows', 'mem_gate',
                                         'permute_marks_day'), consts=('STATE_OPS', 'RMARK_MECHS'))
    B.add('A3', 'e6l_ops.py', '源文件 sha（抽取执行的函数来自此版本）', '', sh, 'INFO')
    for seg in segs:
        sg = MK.MockSeg(seg)
        sg.S = SimpleNamespace(ccolnames=sg.ccolnames)               # 源 mem_gate 只读 seg.S.ccolnames（续跑 tick 哈希）
        kq = meas(seg)['kQ0']
        for form in MK.FORMS:
            st = sg.struct(form)
            ctx = SO.Ctx(st, kq)
            nd = 0
            nr = 0
            dk = SO.mid_gate_day(st)
            for a in (0.0, 0.125, 0.25, 0.5):
                sc = (ctx.sc0 if a == 0.0 else ctx.native_s(a))[None, :]
                U = st.gate_keep(sc)
                for kind, op in (('HG', 'HG10'), ('LAG1', 'LAG1_10')):
                    g1 = SO.src_mem_gate(st, sc, U, kind, 10.0)
                    g2 = ns['mem_gate'](st, sc, U, ns['parse_op'](op), b_day=np.full(sg.T, 10.0))[0]
                    nd += int((g1 != g2).sum())
                    if a == 0.25:                                            # 断点续跑（plan §13.3）：中段门日切分，转录与源各自续跑
                        bd = np.full(sg.T, 10.0)
                        ga, sa = SO.src_mem_gate_s(st, sc, U, kind, 10.0, d1=dk)
                        gb, sb = SO.src_mem_gate_s(st, sc, U, kind, 10.0, state=sa, d0=dk)
                        ha, ta, _ = ns['mem_gate'](st, sc, U, ns['parse_op'](op), b_day=bd, d1=dk)
                        hb, tb, _ = ns['mem_gate'](st, sc, U, ns['parse_op'](op), b_day=bd, state=ta, d0=dk)
                        good = (np.array_equal(ga | gb, g1) and np.array_equal(ga, ha) and np.array_equal(gb, hb) and SO.states_equal(sa, ta)
                                and SO.states_equal(sb, tb))
                        nr += int(not good)
            B.ok('A3', '%s %s' % (seg, form), '转录 src_mem_gate = 源 mem_gate（抽取执行；HG10 / LAG1_10 × 4 个 α）', '0 格差', nd, nd == 0)
            B.ok('A3', '%s %s' % (seg, form), '断点续跑：转录 = 源 mem_gate（抽取执行；α .25，d%d 切分；分片 G = 全程、两段末状态逐键）' % dk, '0 处不符', nr, nr == 0)


# ====================================================================== selftest
def task_selftest(B):
    """伪造 results 根：J_B1_qCC / parkinson OBS / 状态缓存由本轮数组写出（应 PASS），再各改坏一处（应 FAIL）；A2-7 用 E6l 列名伪造。"""
    import e6j_core as J
    fx = M.P('tmp', 'stage0_S_feat_fixture')
    shutil.rmtree(fx, ignore_errors=True)
    root = os.path.join(fx, 'results')
    seg = '2010-2014'
    z = meas(seg)
    t, c = z['t'], z['c']
    T, Nc = int(t.max()) + 1, len(z['ccols'])

    def put_member(rr, mid, cells_vals):
        d = os.path.join(root, RN[rr], 'cache', seg)
        os.makedirs(d, exist_ok=True)
        A = np.full((T, Nc), np.nan)
        A[t, c] = cells_vals
        p = os.path.join(d, mid + '.npy')
        np.save(p, A)
        json.dump(dict(shape=[T, Nc], sha256=J.sha_file(p), max_feature_date='2014-12-31', segment=seg, synthetic=True), open(p[:-4] + '.json', 'w'))
    put_member('J', 'J_B1_qCC', z['raw_Q0'])
    put_member('I', 'V_park20_LEGACY__LEGACY_PARK_NAN', -z['vol'])
    sd = os.path.join(root, RN['L'], 'cache', 'state')
    os.makedirs(sd)
    shutil.copyfile(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), os.path.join(sd, 'state_full_E6l.npz'))
    exp = []
    B1 = S0.Book()
    a2_5(B1, root)
    a2_8(B1, root)
    a4_3(B1, root)
    d1 = B1.df()
    exp.append(('A2-5 本轮 raw 写出的缓存 → 逐位 PASS', ((d1.item == 'A2-5') & (d1.object == seg) & d1.metric.str.startswith('raw 逐位') & (d1.status == 'PASS')).sum() == 1))
    exp.append(('A2-5 其余三段 → SOURCE_WAIT', ((d1.item == 'A2-5') & (d1.status == 'SOURCE_WAIT')).sum() == 3))
    exp.append(('A2-8 缓存 = −vol → PASS 且判"源值"', ((d1.item == 'A2-8') & d1.got.str.contains('源值') & (d1.status == 'PASS')).sum() == 1))
    exp.append(('A4-3 同文件 → 全键 PASS', ((d1.item == 'A4-3') & (d1.status == 'FAIL')).sum() == 0 and ((d1.item == 'A4-3') & (d1.status == 'PASS')).sum() > 10))
    raw = z['raw_Q0'].copy()
    j = int(np.flatnonzero(np.isfinite(raw))[7])
    raw[j] = np.nextafter(raw[j], np.inf)
    put_member('J', 'J_B1_qCC', raw)
    v = -z['vol']
    v[int(np.flatnonzero(np.isfinite(v))[3])] *= -1.0
    put_member('I', 'V_park20_LEGACY__LEGACY_PARK_NAN', v)
    zz = dict(np.load(os.path.join(sd, 'state_full_E6l.npz'), allow_pickle=False))
    zz['vol_pct'] = zz['vol_pct'].copy()
    k = int(np.flatnonzero(np.isfinite(zz['vol_pct']))[5])
    zz['vol_pct'][k] += 1e-12
    np.savez(os.path.join(sd, 'state_full_E6l.npz'), **zz)
    B2 = S0.Book()
    a2_5(B2, root)
    a2_8(B2, root)
    a4_3(B2, root)
    d2 = B2.df()
    exp.append(('A2-5 改 1 个 ulp → FAIL', ((d2.item == 'A2-5') & d2.metric.str.startswith('raw 逐位') & (d2.status == 'FAIL')).sum() == 1))
    exp.append(('A2-8 翻 1 个符号 → FAIL', ((d2.item == 'A2-8') & d2.metric.str.startswith('逐位') & (d2.status == 'FAIL')).sum() == 1))
    exp.append(('A4-3 vol_pct 改 1e−12 → 只该键 FAIL', set(d2[(d2.item == 'A4-3') & (d2.status == 'FAIL')].object) == {'vol_pct'}))
    # A2-7：用本轮 Stage A 行写出 E6l 列名的伪造表（应 PASS），再改一个字段（应 FAIL）
    sa_dir = M.P('stageS_dev', 'stage_a')
    fs = sorted(glob.glob(os.path.join(sa_dir, seg, 'mask_facts_*.csv')))
    Mi = pd.concat([M.read_csv_keep(f) for f in fs], ignore_index=True)
    Mi = Mi[(Mi.kind == 'MAIN') & (Mi.status == 'COMPUTED')].copy()
    Mi['tid'] = Mi.target.map(e6l_target)
    Mi = Mi[Mi.tid.notna()]
    rows = []
    for d in Mi.to_dict('records'):
        rows.append(dict(segment=seg, target_id=d['tid'], variant='REGISTERED', **{ecol: fval(d, spec) for ecol, spec in FIELD_MAP}))
    nf = sum(int(np.isfinite(r_['bonus_reliant_share'])) for r_ in rows)
    exp.append(('A2-7 夹具含门层记忆事实（f_ 列非空 %d 行）' % nf, nf > 0))
    E = pd.DataFrame(rows)
    lp = os.path.join(root, RN['L'], 'results', 'stage_a')
    os.makedirs(lp)
    E.to_csv(os.path.join(lp, 'mask_facts_deriv_E6l.csv'), index=False)
    B3 = S0.Book()
    a2_7(B3, root, sa_dir)
    d3 = B3.df()
    s3 = d3[(d3.item == 'A2-7') & (d3.object == '%s（deriv）' % seg)]
    exp.append(('A2-7 本轮 Stage A 写出的伪造 E6l 表 → PASS（%d 同构目标）' % len(E), len(s3) == 1 and s3.status.iloc[0] == 'PASS'))
    E.loc[E.index[0], 'nnames_mean'] = E.loc[E.index[0], 'nnames_mean'] + 1e-6
    E.to_csv(os.path.join(lp, 'mask_facts_deriv_E6l.csv'), index=False)
    B4 = S0.Book()
    a2_7(B4, root, sa_dir)
    d4 = B4.df()
    exp.append(('A2-7 改 1 个字段 1e−6 → 该字段 FAIL', ((d4.item == 'A2-7') & (d4.metric == 'nnames_mean') & (d4.status == 'FAIL')).sum() == 1))
    # 映射函数：E6l desc 与 target 互相一致
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    smp = D[D.anchor_candidate == 'E6L_POLICY'].desc_id.head(50)
    okm = all(e6l_equiv(x).rsplit('|', 2)[0] + '|' + e6l_equiv(x).rsplit('|', 1)[1] == e6l_target('|'.join(x.split('|')[:6] + x.split('|')[7:]))
              for x in smp)
    exp.append(('E6l desc 映射与 target 映射一致（50 例）', okm))
    mine = pd.DataFrame({'desc_id': ['x1', 'x2'], 'ref': ['r1', 'r2'], 'D_2010-2014': [0.1, 0.2], 'FULL': [1.0, np.nan]})
    ref = pd.DataFrame({'desc_id': ['r1', 'r2'], 'D_2010-2014': [0.1, 0.2 + 1e-6], 'FULL': [1.0, np.nan]})
    cp = compare_policy(mine, ref, 'ref', cols=('D_2010-2014', 'FULL'))
    exp.append(('compare_policy：连字符列被比较、1e−6 被抓到、双 NaN 视为一致', len(cp) == 4 and int((cp.status == 'FAIL').sum()) == 1
                and cp[cp.status == 'FAIL'].column.iloc[0] == 'D_2010-2014'))
    shutil.rmtree(fx, ignore_errors=True)
    for name, ok in exp:
        B.ok('SELFTEST', 'fixture', name, True, bool(ok), bool(ok))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['features', 'maskfacts', 'anchormap', 'claims', 'p44', 'memgate', 'selftest'])
    ap.add_argument('--out', default='')
    ap.add_argument('--struct', default='mock', choices=['mock', 'real'])
    ap.add_argument('--stage-a-dir', default='')
    a = ap.parse_args()
    t0 = time.time()
    out = a.out or M.P('stage0_S')
    root = S0.default_root()
    B = S0.Book()
    # mock 结构上的结果写 mock/（close 不计入 Stage 0 门，只作 B2 证据）；真实结构结果写 c3/
    sub = {'features': 'c2_c4', 'maskfacts': 'c2_c4', 'anchormap': 'c2_c4', 'claims': 'c2_c4', 'memgate': 'mock', 'selftest': 'selftest',
           'p44': 'mock' if a.struct == 'mock' else 'c3'}[a.task]
    od = os.path.join(out, sub)
    os.makedirs(od, exist_ok=True)
    outs = []
    if a.task == 'features':
        a2_5(B, root)
        a2_8(B, root)
        a4_3(B, root)
    elif a.task == 'maskfacts':
        a2_7(B, root, a.stage_a_dir or M.P('stageS_dev', 'stage_a'))
    elif a.task == 'anchormap':
        outs.append(task_anchormap(B, root, od))
    elif a.task == 'claims':
        outs.append(task_claims(B, root, od))
    elif a.task == 'memgate':
        task_memgate(B)
    elif a.task == 'p44':
        task_p44(B, a.struct, od)
        outs += [os.path.join(od, 'p44_grid.csv'), os.path.join(od, 'p44_text.md')]
    else:
        task_selftest(B)
    tag = a.task if a.task != 'p44' else 'p44_%s' % a.struct
    p = B.write(os.path.join(od, 'checks_%s.csv' % tag))
    df = B.df()
    cnt = df.status.value_counts().to_dict()
    M.write_receipt(os.environ.get('E6M_TASK', 'S0_feat_' + tag), [os.path.join(od, 'checks_%s.csv' % tag)] + outs, status='SUCCEEDED',
                    code=[__file__, S0.__file__, M.__file__], counts=cnt, wall_s=round(time.time() - t0, 1),
                    note='FAIL 行是检查结果（Stage 0 门在 close 汇总），不是任务失败')
    print(json.dumps(dict(task=tag, counts=cnt, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    show = df[df.status.isin(['FAIL', 'NOT_RUN'])]
    if len(show):
        print(show[['item', 'object', 'metric', 'expected', 'got', 'status']].head(40).to_string(max_colwidth=70))
    return 0 if (a.task != 'selftest' or not (df.status == 'FAIL').any()) else 1


if __name__ == '__main__':
    sys.exit(main())
