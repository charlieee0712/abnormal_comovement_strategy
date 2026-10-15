# -*- coding: utf-8 -*-
"""E6n 补齐 plan §12.4 / brief §5 S8 必交产物里尚无生成器的表（只新增文件，不改冻结件、不改任何已有结果）。
  penalty --seg S  results/full/penalty/penalty_change_<段>.csv（plan §5.5 末段：每个 RAW 构造 × 母体 × 记忆 / α 的四项变化
                   raw_changed / normalized_score_changed / zero_penalty_score_changed / final_membership_changed + 资格边界评分间距）；
                   名单层事实（masks 与测量），不读收益（与 Stage A 掩码层事实同约定）
  penalty_merge    → results/full/penalty_change_ledger.csv（四段合表）
  rawledger        results/full/measurement_raw_ledger.csv（meas/full、meas/<段>、meas/<段>/kf 与 minute_panel 下每个保存数组：形状、sha256、
                   有限 / 零份额、分位数 = raw 保存与数据指纹；minute_panel 只记 sha / 形状）
  cardmap          registration/card_query_map_E6n.csv（卡 / 断言 → query_id → 固定表 / 单位 / 占位）
  auth             registration/authorization_receipt_E6n.json（方式 B 授权 + 生效条件回执 + 冻结 / 封存 / 后段首写时间线，各件 sha，post_gate 现核）
  park             registration/park_reentry_E6n.csv（plan §11.2 携带项 + 本轮主 72 新对象的执行端草稿；字段 as_of / source_measurement / scope /
                   effect_interval / limitation / reentry_trigger / planned_retest / parent_unchanged；状态由决策端 REVIEW 定，恢复 ≠ 采纳）
  extern           registration/externality_register_E6n.csv（plan §11.3 九项 + 本轮机器实测事实 + 卡片 externality 字段）
  ledgers          results/full/{idea_ledger_G_final, execution_ledger_E_final, exposure_ledger_final}.csv（冻结账本原样 + 结果指针；冻结件不动）
  all_post         penalty_merge + cardmap + auth + park + extern + ledgers（读后段结果的项先过 post_gate）"""
import os
import re
import sys
import glob
import json
import time
import argparse
import subprocess

import numpy as np
import pandas as pd

import e6n_core as N

PARENTS6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
QS = (1, 5, 25, 50, 75, 95, 99)


def rd(*p):
    return pd.read_csv(N.P(*p), keep_default_na=False, low_memory=False)


def num(x):
    return pd.to_numeric(x, errors='coerce')


# ====================================================================== penalty（名单层）
def day_gaps(s, U, tid):
    """每日资格边界评分间距：低分保留时 = min(被拒) − max(保留)；高分保留时 = min(保留) − max(被拒)。返回 (间距数组, 方向)。"""
    if len(tid) and (np.diff(tid) < 0).any():
        o = np.argsort(tid, kind='stable')
        s, U, tid = s[o], U[o], tid[o]
    fin = np.isfinite(s)
    st = np.flatnonzero(np.r_[True, tid[1:] != tid[:-1]])
    kmax = np.maximum.reduceat(np.where(U & fin, s, -np.inf), st)
    kmin = np.minimum.reduceat(np.where(U & fin, s, np.inf), st)
    rmax = np.maximum.reduceat(np.where(~U & fin, s, -np.inf), st)
    rmin = np.minimum.reduceat(np.where(~U & fin, s, np.inf), st)
    lo = rmin - kmax
    hi = kmin - rmax
    ok = np.isfinite(lo) & np.isfinite(hi)
    if not ok.any():
        return np.array([]), 'NOT_COMPUTABLE'
    if (lo[ok] >= 0).mean() >= (hi[ok] >= 0).mean():
        return lo[ok], 'LOW_KEPT'
    return hi[ok], 'HIGH_KEPT'


def qsum(x, pre):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if not len(x):
        return {pre + k: np.nan for k in ('median', 'p10', 'p90')}
    return {pre + 'median': float(np.median(x)), pre + 'p10': float(np.percentile(x, 10)), pre + 'p90': float(np.percentile(x, 90))}


def task_penalty(seg_name):
    import e6l_env as V
    import e6n_vars as VR
    import e6n_masks as MK
    t0 = time.time()
    seg = V.SegL(seg_name, state=False)
    B = VR.Base(seg_name)
    if not (np.array_equal(seg.ci.t, B.t) and np.array_equal(seg.ci.c, B.c)):
        raise RuntimeError('段单元坐标与测量单元不一致')
    R = MK.registry_rows()
    R = R[R.variant.str.startswith('RAW|') & R.parent.isin(PARENTS6)]
    K = R.drop_duplicates(['parent', 'memory', 'alpha_eff', 'variant'])
    q0raw, kQ = B.q0raw, B.kQ
    rows = []
    for form, g in K.groupby('parent'):
        st = seg.struct(form)
        z = np.load(N.P('masks', seg_name, '%s.npz' % form), allow_pickle=False)
        pos = {str(k): i for i, k in enumerate(z['mask_keys'])}
        n = int(z['n_cells'][0])
        ids = np.asarray(st.ids, np.int64)
        tid = seg.ci.t[ids]
        q0 = np.asarray(st.q0, float)
        unpack = lambda b, m: np.unpackbits(b)[:m].astype(bool)
        for (mem, al), gg in g.groupby(['memory', 'alpha_eff']):
            sc0 = np.asarray(st.gate_scores(VR.native_q(q0, kQ, al)[None, :]), float)
            U0 = np.asarray(st.gate_keep(sc0), bool)[0]
            gap0, ori0 = day_gaps(sc0[0], U0, tid)
            k0 = MK.mask_key(mem, al, 'Q0')
            F0 = unpack(z['final_bits'][pos[k0]], n) if k0 in pos else None
            for r in gg.itertuples():
                v = r.variant
                act, h, p = VR.raw_active(B, v)
                lam = float(p['lam'])
                idb = lam == 0.0 or not act.any()
                if idb:
                    raw_chg = 0
                else:
                    raw = q0raw.copy()
                    raw[act] = 1.0 / (B.dd[act] + lam * h[act] + VR.EPS)
                    raw_chg = int((act & (raw != q0raw)).sum())
                kf = np.asarray(VR.variant_kf(B, v)[0], float)
                diff = (np.isfinite(kf) != np.isfinite(kQ)) | (np.isfinite(kf) & np.isfinite(kQ) & (kf != kQ))
                zp = act & (np.nan_to_num(h, nan=-1.0) == 0)
                pp = act & (np.nan_to_num(h, nan=-1.0) > 0)
                sc = np.asarray(st.gate_scores(VR.native_q(q0, kf, al)[None, :]), float)
                U = np.asarray(st.gate_keep(sc), bool)[0]
                gap, ori = day_gaps(sc[0], U, tid)
                mk = MK.mask_key(mem, al, v)
                row = dict(segment=seg_name, form=form, memory=mem, alpha_K=al, variant=v, family=p['feature'], lam=lam, app=p['app'], fr=p['fr'], support=p['sup'],
                           n_cells=int(n), active_cells=int(act.sum()), active_days=int(len(np.unique(B.t[act]))) if act.any() else 0,
                           positive_penalty_cells=int(pp.sum()), zero_penalty_active_cells=int(zp.sum()), identity_branch=bool(idb),
                           raw_changed=raw_chg, normalized_score_changed=int(diff.sum()), normalized_score_changed_active=int((diff & act).sum()),
                           zero_penalty_score_changed=int((diff & zp).sum()), score_changed_outside_active=int((diff & ~act).sum()),
                           gate_membership_changed=int((U != U0).sum()), gate_changed_days=int(len(np.unique(tid[U != U0]))),
                           boundary_orientation=ori, boundary_days=int(len(gap)))
                row.update(qsum(gap0, 'boundary_gap_q0_'))
                row.update(qsum(gap, 'boundary_gap_'))
                if mk in pos and F0 is not None:
                    F = unpack(z['final_bits'][pos[mk]], n)
                    d = F != F0
                    row.update(final_membership_changed=int(d.sum()), final_changed_days=int(len(np.unique(B.t[d]))) if d.any() else 0,
                               final_members_q0=int(F0.sum()), final_members=int(F.sum()), final_status='COMPUTED')
                else:
                    row.update(final_membership_changed=np.nan, final_changed_days=np.nan, final_members_q0=np.nan, final_members=np.nan,
                               final_status='NOT_COMPUTABLE（masks 无此键或无同记忆 Q0 键）')
                rows.append(row)
        N.log('penalty %s %s：%d 键（%.0f s）' % (seg_name, form, len(g), time.time() - t0))
    df = pd.DataFrame(rows)
    od = N.P('results', 'full', 'penalty')
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, 'penalty_change_%s.csv' % seg_name)
    N.atomic_write_csv(p, N.to_status(df))
    N.write_receipt('E6n_fixed_penalty_%s' % seg_name, [p], code=[__file__], rows=len(df), wall_s=round(time.time() - t0, 1))
    return [p]


def task_penalty_merge():
    parts = [pd.read_csv(f, keep_default_na=False, low_memory=False) for f in sorted(glob.glob(N.P('results', 'full', 'penalty', 'penalty_change_*.csv')))]
    if not parts:
        raise RuntimeError('penalty 逐段表缺')
    df = pd.concat(parts, ignore_index=True)
    if set(df.segment) != set(N.SEGMENTS):
        raise RuntimeError('penalty 段不全：%s' % sorted(set(df.segment)))
    p = N.P('results', 'full', 'penalty_change_ledger.csv')
    N.atomic_write_csv(p, df)
    return [p]


# ====================================================================== rawledger
def task_rawledger():
    t0 = time.time()
    rows = []
    srcs = [('FULL_CALENDAR', 'ALL', N.P('meas', 'full'))] + [('SEG_CELLS', s, N.P('meas', s)) for s in N.SEGMENTS] + \
           [('SEG_KF_CACHE', s, N.P('meas', s, 'kf')) for s in N.SEGMENTS]
    for scope, seg, d in srcs:
        for f in sorted(glob.glob(os.path.join(d, '*.npy'))):
            x = np.load(f, mmap_mode='r', allow_pickle=False)
            row = dict(scope=scope, segment=seg, name=os.path.basename(f)[:-4], file=N.rel(f), sha256=N.sha_file(f), bytes=os.path.getsize(f), dtype=str(x.dtype),
                       shape='x'.join(str(s) for s in x.shape), generator='e6n_meas.py full' if scope == 'FULL_CALENDAR' else 'e6n_meas.py seg')
            if x.dtype.kind == 'f':
                v = np.asarray(x, float).ravel()
                fin = np.isfinite(v)
                nf = int(fin.sum())
                row.update(n=int(v.size), finite=nf, finite_share=nf / max(1, v.size))
                if nf:
                    w = v[fin]
                    row.update(zero_share=float((w == 0).mean()), min=float(w.min()), max=float(w.max()), mean=float(w.mean()),
                               **{'p%02d' % q: float(val) for q, val in zip(QS, np.percentile(w, QS))})
            rows.append(row)
    for f in sorted(glob.glob(N.P('minute_panel', '**', '*.npy'), recursive=True)):
        x = np.load(f, mmap_mode='r', allow_pickle=False)
        rows.append(dict(scope='MINUTE_PANEL', segment='ALL', name=os.path.basename(f)[:-4], file=N.rel(f), sha256=N.sha_file(f), bytes=os.path.getsize(f),
                         dtype=str(x.dtype), shape='x'.join(str(s) for s in x.shape), generator='e6n_etl.py'))
    df = pd.DataFrame(rows)
    p = N.P('results', 'full', 'measurement_raw_ledger.csv')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    N.atomic_write_csv(p, N.to_status(df))
    N.write_receipt('E6n_fixed_rawledger', [p], code=[__file__], rows=len(df), gb=round(float(df.bytes.sum()) / 1e9, 2), wall_s=round(time.time() - t0, 1))
    return [p]


# ====================================================================== cardmap
def task_cardmap():
    Q = rd('registry', 'query_registry_E6n.csv')
    K = rd('registration', 'cards_stageB_E6n.csv')
    A = rd('registration', 'claims_E6n.csv')
    rows = []
    kcols = [c for c in ('card', 'claim_id', 'new_prediction', 'estimand', 'control', 'domain', 'exposure', 'implementation') if c in K.columns]
    kc = K[kcols].drop_duplicates('card').set_index('card') if 'card' in K.columns else pd.DataFrame()
    for r in Q.itertuples():
        d = dict(link='CARD', card=r.card, query_id=r.query_id, schema=r.schema, object_rule=r.object_rule, table=r.table, unit=r.unit,
                 placeholder=r.placeholder, bound_fixed_table=r.bound_fixed_table)
        if r.card in kc.index:
            for c in kc.columns:
                d['card_' + c] = kc.loc[r.card, c]
        rows.append(d)
    qmap = Q.groupby('card').query_id.apply(lambda s: '|'.join(s)).to_dict()
    for r in A.itertuples():
        rows.append(dict(link='ASSERTION', card=getattr(r, 'card', ''), query_id=qmap.get(getattr(r, 'card', ''), 'NOT_APPLICABLE'),
                         assertion_id='E6N-' + str(r.assertion_id), schema='ASSERTION', object_rule='%s：%s' % (getattr(r, 'first_object', ''), getattr(r, 'frozen_direction', '')),
                         table='registration/claims_E6n.csv', unit='NOT_APPLICABLE', placeholder=False, bound_fixed_table='registration/claims_E6n.csv'))
    df = pd.DataFrame(rows)
    p = N.P('registration', 'card_query_map_E6n.csv')
    N.atomic_write_csv(p, N.to_status(df))
    return [p]


# ====================================================================== auth
def task_auth():
    import e6n_gate as GT
    rdir = N.P('registration')
    files = [GT.AUTH_STATUS, GT.AUTH_PRE, 'record_B_mode_B_E6n.json', GT.AUTH_COND, GT.FREEZE, GT.SEAL_B10, GT.SEAL_DERIV, 'seal_post.json']
    items = {}
    for f in files:
        p = os.path.join(rdir, f)
        if os.path.exists(p):
            j = json.load(open(p, encoding='utf-8'))
            items[f] = dict(sha256=N.sha_file(p), written_at=j.get('written_at', ''))
        else:
            items[f] = dict(sha256='', written_at='MISSING')
    pre = json.load(open(os.path.join(rdir, GT.AUTH_PRE), encoding='utf-8')) if os.path.exists(os.path.join(rdir, GT.AUTH_PRE)) else {}
    cond = json.load(open(os.path.join(rdir, GT.AUTH_COND), encoding='utf-8')) if os.path.exists(os.path.join(rdir, GT.AUTH_COND)) else {}
    gate = {}
    for s in N.POST_SEGS:
        try:
            GT.post_gate(s, 'authorization_receipt')
            gate[s] = 'PASS'
        except RuntimeError as e:
            gate[s] = 'RAISE ' + str(e)[:120]
    rec = []
    ret = ('E6n_accounts_', 'E6n_support_', 'E6n_b2_run_', 'E6n_b3_', 'E6n_b4_', 'E6n_decomp_', 'E6n_stats_', 'E6n_policy', 'E6n_bootstrap')
    for f in glob.glob(N.P('task_status', '*.receipt.json')):
        j = json.load(open(f, encoding='utf-8'))
        t = j.get('task_id', '')
        reads_returns = t.startswith(ret) or (t.startswith('E6n_rand_') and not t.startswith(('E6n_rand_selftest', 'E6n_rand_manifest')))
        if reads_returns and any(('_%s_' % s) in t or t.endswith('_' + s) for s in N.POST_SEGS) and j.get('status') == 'SUCCEEDED':
            rec.append((j.get('written_at', ''), t))
    rec.sort()
    acc = sorted(os.path.getmtime(f) for s in N.POST_SEGS for f in glob.glob(N.P('accounts', s, '*.npz')))
    first_post = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(acc[0])) if acc else ''
    cw = items[GT.AUTH_COND]['written_at']
    out = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), mode=pre.get('mode', ''), user_quote=pre.get('user_quote', ''), user_quote_date=pre.get('user_quote_date', ''),
               scope=pre.get('scope', ''), effective_conditions=pre.get('effective_conditions', []), freeze_sha256=pre.get('freeze_sha256', ''),
               conditions_all_pass=bool(cond.get('all_pass')), conditions=dict((k, cond.get(k)) for k in ('stage0_all_pass', 'a1_auto_all_pass', 'seal_B1_0', 'seal_deriv',
                                                                                                         'authorization_bound_to_freeze', 'frozen_files_checked',
                                                                                                         'frozen_files_changed')),
               post_gate_now=gate, files=items, first_post_segment_account_write=first_post, first_post_segment_receipt=rec[0] if rec else ('', ''),
               ordering_ok=bool(cw and cw != 'MISSING' and first_post and cw < first_post and (not rec or cw < rec[0][0])),
               note='方式 B：用户转交消息原话照录；执行端不代拟授权。ordering_ok = 生效条件回执写于任何后段账户 / 回执之前。')
    p = os.path.join(rdir, 'authorization_receipt_E6n.json')
    N.atomic_write_json(p, out)
    return [p]


# ====================================================================== park（读后段结果）
PLAN_PARK = [
    ('P57', 'BAND / BLEND（E6m 接入形式）', '原 Q、原 w / 父 / H 下不胜当前 Q memory', '新测量具有局部条件作用的来源 / 新母体绑定门变化；先固定比较', '已经知道新账户会赢'),
    ('P58', 'HARD（E6m 接入形式）', '只删不补及源重定权', '新信息明确是资格型、已定义现金 / 回填或固定预算的不同问题', '所有时期都为正'),
    ('P59/P51', '时间核（E6l / E6m）', '原日 Q 平均 / 两日表达', '不同经济时钟（事件、日内）或不同测量误差，明确共同支持', '原时间核先翻正'),
    ('P61', '位置 × 活动（第一道 P1–P4）', '特定 A20 / PRE_R20 / 原门两早段的读法与排序不稳', '新域、准确制度划分、替代活动测量或足够新观察，事前写差之差', '份额 ≥ 10%、上界 ≥ MDE、两段已同号'),
    ('P41', '日内 ID（OHLC / K 角色）', '既有 OHLC / K 角色', '同角色桥或新增分钟序列明确测不同对象', 'OHLC 桥必须为零')]
NEW_TRIGGER = '更好观测（真实成交 / 报价 / L2）、新对象或新解释，固定原对照重测（plan §11.2 "新分钟失败项"）'
NEW_RETEST = '固定原对照（同父 / 同记忆 Q0 / 同 α_K / H / 域 / 频率）重测；不把方向翻成赢家后追认'


def task_park():
    import e6n_gate as GT
    for s in N.POST_SEGS:
        GT.post_gate(s, 'park_reentry')
    asof = time.strftime('%Y-%m-%d')
    rows = []
    for pid, meas, scope, trig, notreq in PLAN_PARK:
        rows.append(dict(park_id=pid, as_of=asof, source_measurement=meas, scope=scope, effect_interval='沿 E6m / E6l 已报（本轮未重测该子杠杆）', limitation='本轮未安排',
                         reentry_trigger=trig, planned_retest='触发后另行事前登记；本轮无', not_required_before_reentry=notreq, parent_unchanged=True,
                         draft_state='维持 park 建议（plan §11.1；待 RULING）', draft_by='plan §11.2 转录', comparison_id='NOT_APPLICABLE'))
    D = rd('registry', 'descriptors_E6n.csv')
    D = D[D.is_primary72.astype(str) == 'True']
    CF = rd('results', 'full', 'comparison_full.csv')
    BS = rd('results', 'full', 'bootstrap', 'bootstrap_comparisons.csv')
    BS = BS[(BS.scope == 'FULL') & (num(BS.L) == 20)].set_index('comparison_id')
    POL = rd('results', 'full', 'policy_E6n.csv').drop_duplicates('desc_id').set_index('desc_id')
    COV = rd('results', 'coverage_by_feature_year_exchange.csv')
    seg_cov = {}
    if {'feature', 'segment'} <= set(COV.columns):
        vc = next((c for c in ('share', 'coverage', 'computable_share', 'share_pool0') if c in COV.columns), None)
        if vc:
            seg_cov = COV.assign(v=num(COV[vc])).groupby(['feature', 'segment']).v.mean().to_dict()
    for r in D.itertuples():
        c = CF[(CF.left_desc_id == r.desc_id) & (CF.view == 'VS_SAME_MEMORY_Q0')]
        cm = CF[(CF.left_desc_id == r.desc_id) & (CF.view == 'VS_MASK_CLONE')]
        if not len(c):
            continue
        cid = c.comparison_id.iloc[0]
        est, lo, hi = (float(BS.loc[cid, k]) if cid in BS.index else np.nan for k in ('est_ann_pp', 'q025_ann_pp', 'q975_ann_pp'))
        full = float(num(c.FULL_ann_pp).iloc[0])
        if not np.isfinite(lo) or not np.isfinite(hi):
            stt = '未定（区间不可估）'
        elif hi < 0:
            stt = 'park 草稿（本域区间上界 < 0）'
        elif lo > 0:
            stt = '不 park（区间下界 > 0；读法交决策端）'
        else:
            stt = 'carried 草稿（区间跨 0）'
        pr = str(POL.loc[r.desc_id, 'policy_result']) if r.desc_id in POL.index else 'NOT_APPLICABLE'
        lim = []
        if 'POLICY_UNDECIDABLE_HISTORY' in pr:
            lim.append('政策不可判（分钟覆盖不足）')
        feat = getattr(r, 'feature', '')
        cv = [(s, seg_cov.get((feat, s))) for s in N.SEGMENTS if seg_cov.get((feat, s)) is not None]
        if cv:
            lim.append('段覆盖 ' + ' / '.join('%s %.3f' % (s, v) for s, v in cv if np.isfinite(v)))
        rows.append(dict(park_id='E6n-draft-%s' % r.desc_id, as_of=asof, source_measurement='%s（%s）' % (feat, getattr(r, 'input_variant', '')),
                         scope='母体 %s · 记忆 %s · H%s · α_K %s · 强度 %s · 域 %s · 频率 %s' % (r.parent, r.memory, r.H, r.outer_alpha, r.strength, r.applicability,
                                                                                       r.frequency),
                         effect_interval='vs 同记忆 Q0：FULL %+.3f（bootstrap 估计 %+.3f，95%% [%+.3f, %+.3f]，L = 20，2,000 次）ann_pp；vs 掩码克隆 FULL %s' % (
                             full, est, lo, hi, ('%+.3f' % float(num(cm.FULL_ann_pp).iloc[0])) if len(cm) and np.isfinite(float(num(cm.FULL_ann_pp).iloc[0])) else 'UNDEFINED'),
                         limitation='；'.join(lim) or '无额外限制（见限制登记）', reentry_trigger=NEW_TRIGGER, planned_retest=NEW_RETEST,
                         not_required_before_reentry='把方向偷偷翻成赢家后追认', parent_unchanged=True, draft_state=stt,
                         draft_by='执行端草稿（决策端 REVIEW 定；恢复 ≠ 采纳）', comparison_id=cid, policy_result=pr))
    P = rd('registration', 'probe_ledger.csv')
    for r in P[P.label.astype(str).str.startswith('未检验')].itertuples():
        rows.append(dict(park_id='E6n-nocov-%s' % r.member, as_of=asof, source_measurement=r.member, scope=r.domain, effect_interval='NOT_COMPUTABLE',
                         limitation=r.label, reentry_trigger='数据补齐（另作新版本）', planned_retest='数据补齐后按冻结 B1-0 规则重测', not_required_before_reentry='NOT_APPLICABLE',
                         parent_unchanged=True, draft_state='未覆盖 / SOURCE_WAIT（不是 park）', draft_by='执行端草稿', comparison_id='NOT_APPLICABLE'))
    df = pd.DataFrame(rows)
    p = N.P('registration', 'park_reentry_E6n.csv')
    N.atomic_write_csv(p, N.to_status(df))
    return [p]


# ====================================================================== extern（读后段结果）
PLAN_EXT = [
    ('X1', '因子 / 生产污染', '原始分钟面、研究评分、候选清单分层，feature_version 独立命名；不改 features_daily 默认集合', '将来用户采纳需要实际迁移 / 回滚评估'),
    ('X2', '被新母体绑住', '同时保存原父和 Q0memory 父；下一轮允许从任一冻结父提问', '候选多会增加管理成本'),
    ('X3', '新数据源依赖', '每支字段 / 覆盖 / 基线 / 来源单列；无数据回原 Q；数据补齐另作为新版本', '供应商修订、成本与停供风险'),
    ('X4', '搜索和暴露积累', 'G / E / 总体 exposure 三表；首次 / 复现 / 探索分开；E7 隔离', '同历史适应性选择偏差不能完全消除'),
    ('X5', '方法论过度收口', '不把一轮失败升级为"必须分钟""不得某类因子""全部同轴无用"', '不能保证未来 hypothesis 不 miss'),
    ('X6', '参数锁定', 'α_K / η / λ / H / 频率为本实验坐标，不写成总研究库永久常数', '以后重定参数仍需暴露记录'),
    ('X7', '代码 / 登记债务', '单一 registry 编译比较与报告；raw 值 / 评分 / 名单 / 成本分层接口', '新管线有真实维护负担'),
    ('X8', '删信息换小增量', '保存 PL / RV / net / 量 8 格原值，不只保存综合 Q；原特征不覆盖', 'raw 资产存储与合规成本'),
    ('X9', '实施代价', '实算换手 / 净订单 / 缺价 / size，源 8bp 与中等冲击并列', '分钟特征不增加交易频率不等于不增加换手')]


def du_gb(d):
    tot, n = 0, 0
    for root, _, fs in os.walk(d):
        for f in fs:
            try:
                tot += os.path.getsize(os.path.join(root, f))
                n += 1
            except OSError:
                pass
    return tot / 1e9, n


def mean_turn(desc_ids):
    """各段账户 npz 的 d_turn 日均（有限日），n 加权四段。"""
    acc = {d: [0.0, 0] for d in desc_ids}
    for s in N.SEGMENTS:
        for f in glob.glob(N.P('accounts', s, '*.npz')):
            with np.load(f, allow_pickle=False) as z:
                ds = [str(x) for x in z['desc']]
                hit = [i for i, d in enumerate(ds) if d in acc]
                if not hit:
                    continue
                T = z['d_turn']
                for i in hit:
                    x = T[i]
                    ok = np.isfinite(x)
                    acc[ds[i]][0] += float(x[ok].sum())
                    acc[ds[i]][1] += int(ok.sum())
    return {d: (a / n if n else np.nan) for d, (a, n) in acc.items()}


def task_extern():
    import e6n_gate as GT
    for s in N.POST_SEGS:
        GT.post_gate(s, 'externality_register')
    facts = {}
    fnd = ['data_loader.py', 'features_daily.py', 'event_study.py', 'pool_screening_v2.py']
    st = subprocess.run(['git', '-c', 'safe.directory=%s' % os.path.realpath(N.CODE), 'status', '--porcelain', '--'] + fnd, cwd=N.CODE, capture_output=True, text=True).stdout
    facts['X1'] = '四地基 git 改动 %d 个（%s）；分钟面与研究评分只写本轮结果目录' % (len([l for l in st.split('\n') if l.strip()]), ' / '.join(f[:-3] for f in fnd))
    D = rd('registry', 'descriptors_E6n.csv')
    nh = {}
    for s in N.SEGMENTS:
        k = set()
        for f in glob.glob(N.P('accounts', s, '*.npz')):
            with np.load(f, allow_pickle=False) as z:
                k |= set(str(x) for x in z['desc'])
        nh[s] = (sum(1 for x in k if x.startswith('ANCHOR|ORIGINAL')), sum(1 for x in k if '|Q0|' in x or x.startswith('ANCHOR|Q0')))
    facts['X2'] = '各段账户里原父 / Q0 族描述符数：' + '；'.join('%s %d / %d' % (s, a, b) for s, (a, b) in nh.items())
    C = rd('stage0', 'c7_minute', 'a7_12_field_dependency.csv') if os.path.exists(N.P('stage0', 'c7_minute', 'a7_12_field_dependency.csv')) else pd.DataFrame()
    dc = json.load(open(N.P('stage0', 'data_contract.json'), encoding='utf-8')) if os.path.exists(N.P('stage0', 'data_contract.json')) else {}
    facts['X3'] = '分钟字段依赖 %d 行（stage0/c7_minute/a7_12_field_dependency.csv）；数据合同版本 %s；读取截止 %s' % (
        len(C), dc.get('contract_version', dc.get('version', 'UNDEFINED')), N.MARKET_DATA_END_MAX)
    Gl, El, Xl = rd('registration', 'idea_ledger_G.csv'), rd('registration', 'execution_ledger_E.csv'), rd('registration', 'exposure_ledger.csv')
    facts['X4'] = 'G %d 行 / E %d 行 / exposure %d 行；描述符 exposure 计数 %s' % (len(Gl), len(El), len(Xl), json.dumps(D.exposure.value_counts().to_dict(), ensure_ascii=False))
    pr = json.load(open(N.P('registration', 'policy_profiles_E6n.json'), encoding='utf-8'))
    facts['X5'] = '本轮新增条款键：%s（无新否决门）' % ', '.join(sorted((pr.get('e6n_additions') or {}).keys()) if isinstance(pr.get('e6n_additions'), dict) else ['见 policy_profiles_E6n.json'])
    co = {}
    for c in ('outer_alpha', 'strength', 'H', 'frequency', 'memory', 'applicability'):
        if c in D.columns:
            co[c] = sorted(set(str(x) for x in D[c] if str(x) not in ('', 'NOT_APPLICABLE')))[:12]
    facts['X6'] = '本实验坐标取值：' + json.dumps(co, ensure_ascii=False)
    dl = pd.read_csv(N.P('code_register', 'deploy_log.csv'), keep_default_na=False)
    last = dl.sort_values('time').drop_duplicates('file', keep='last')
    facts['X7'] = 'e6n 模块 %d 个、共 %d 行（code_register/deploy_log.csv 末版）；registry 文件 %d 个' % (len(last), int(num(last.lines).sum()),
                                                                                                   len(glob.glob(N.P('registry', '*'))))
    g1, n1 = du_gb(N.P('meas'))
    g2, n2 = du_gb(N.P('minute_panel'))
    facts['X8'] = 'raw 保存：meas/ %.1f GB（%d 文件）、minute_panel/ %.1f GB（%d 文件）；清单 results/full/measurement_raw_ledger.csv' % (g1, n1, g2, n2)
    P72 = D[D.is_primary72.astype(str) == 'True']
    par = {r.desc_id: 'ANCHOR|ORIGINAL|%s|NONE|H%d|s0|ALL|a0|f5|d+1' % (r.parent, int(r.H)) for r in P72.itertuples()}
    mt = mean_turn(set(par) | set(par.values()))
    dd = np.array([mt[a] - mt[b] for a, b in par.items() if np.isfinite(mt.get(a, np.nan)) and np.isfinite(mt.get(b, np.nan))])
    facts['X9'] = ('主 72 相对原父日均换手差（小数）：中位 %+.4f、最小 %+.4f、最大 %+.4f（%d 对；accounts d_turn 四段 n 加权）' % (np.median(dd), dd.min(), dd.max(), len(dd))
                   if len(dd) else '主 72 换手差 UNDEFINED（账户缺）')
    rows = [dict(ext_id=i, risk=rk, mitigation_this_round=mt_, cannot_guarantee=cg, machine_fact=facts.get(i, 'NOT_APPLICABLE'), source='plan §11.3') for i, rk, mt_, cg in PLAN_EXT]
    K = rd('registration', 'cards_stageB_E6n.csv')
    if 'externality' in K.columns:
        for r in K.itertuples():
            rows.append(dict(ext_id='CARD-%s' % getattr(r, 'card', r.claim_id), risk='卡片 externality 字段', mitigation_this_round=r.externality, cannot_guarantee='NOT_APPLICABLE',
                             machine_fact='NOT_APPLICABLE', source='registration/cards_stageB_E6n.csv'))
    df = pd.DataFrame(rows)
    p = N.P('registration', 'externality_register_E6n.csv')
    N.atomic_write_csv(p, N.to_status(df))
    return [p]


# ====================================================================== ledgers（冻结件不动；结果版另写）
def task_ledgers():
    import e6n_gate as GT
    for s in N.POST_SEGS:
        GT.post_gate(s, 'ledgers_final')
    G = rd('registration', 'idea_ledger_G.csv')
    E = rd('registration', 'execution_ledger_E.csv')
    X = rd('registration', 'exposure_ledger.csv')
    P = rd('registration', 'probe_ledger.csv')
    f = lambda v: 'UNDEFINED' if not np.isfinite(num(pd.Series([v])).iloc[0]) else '%+.2f' % float(v)
    pr, mr = {}, {}
    for r in P.itertuples():
        pr.setdefault(r.idea_id, []).append('%s：主域两段 %s / %s bp（n %s / %s）→ 总体 %s；%s' % (r.member, f(r.seg1_value), f(r.seg2_value), r.n_seg1, r.n_seg2, f(r.overall), r.label))
        if str(r.miss_root_hypotheses) not in ('NOT_APPLICABLE', ''):
            mr.setdefault(r.idea_id, set()).add(str(r.miss_root_hypotheses))
    ptr = {'G-H12': '见 results/full/b2/b2_controls.csv / b2_order_overlay.csv（B2 只账本诊断）', 'G-H13': '见 results/full/b3/b3_same_count.csv（B3 同数对照）'}
    G2 = G.copy()
    G2['probe_result'] = [' || '.join(pr[i]) if i in pr else ptr.get(i, G.probe_result.iloc[k] if G.probe_result.iloc[k] != 'NOT_RUN' else 'NOT_MEASURED（本轮未安排探针）')
                          for k, i in enumerate(G.idea_id)]
    G2['miss_root_hypotheses'] = [' || '.join(sorted(mr[i])) if i in mr else ('NOT_APPLICABLE' if i in pr else G.miss_root_hypotheses.iloc[k]) for k, i in enumerate(G.idea_id)]
    G2['miss_root_hypotheses'] = G2.miss_root_hypotheses.replace('NOT_RUN', 'NOT_APPLICABLE')
    G2['result_source'] = ['registration/probe_ledger.csv' if i in pr else ('results/full' if i in ptr else 'NOT_APPLICABLE') for i in G.idea_id]
    Qd = {}
    for f_ in glob.glob(N.P('reports', 'queries_full', '*.csv')):
        x = pd.read_csv(f_, dtype=str, keep_default_na=False)
        Qd[os.path.basename(f_)[:-4]] = (len(x), x.status.value_counts().to_dict() if 'status' in x.columns else {})
    E2 = E.copy()
    res = []
    for r in E.itertuples():
        qs = [q for q in str(r.query_id).split('|') if q in Qd]
        res.append('；'.join('%s：%d 行 %s' % (q, Qd[q][0], json.dumps(Qd[q][1], ensure_ascii=False)) for q in qs) if qs else 'NOT_APPLICABLE（无绑定 query）')
    E2['result'] = res
    E2['result_source'] = 'reports/queries_full/<query_id>.csv'
    E2['interpretation'] = 'DECISION_SIDE（REVIEW 写；执行端只给数）'
    E2['next_design_change'] = 'DECISION_SIDE（REVIEW / RULING）'
    X2 = X.copy()
    have = {}
    for s in N.SEGMENTS:
        k = set()
        for f_ in glob.glob(N.P('accounts', s, '*.npz')):
            with np.load(f_, allow_pickle=False) as z:
                k |= set(str(x) for x in z['desc'])
        have[s] = k
    D = rd('registry', 'descriptors_E6n.csv')
    comp = []
    for r in X.itertuples():
        g = D[(D.kind == r.family) & (D.feature == r.feature)] if r.family in set(D.kind) else None
        comp.append('NOT_APPLICABLE' if g is None or not len(g) else '；'.join('%s %d / %d' % (s, len(set(g.desc_id) & have[s]), len(g)) for s in N.SEGMENTS))
    X2['computed_per_segment'] = comp
    outs = []
    for nm, df in (('idea_ledger_G_final.csv', G2), ('execution_ledger_E_final.csv', E2), ('exposure_ledger_final.csv', X2)):
        p = N.P('results', 'full', nm)
        N.atomic_write_csv(p, N.to_status(df))
        outs.append(p)
    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['penalty', 'penalty_merge', 'rawledger', 'cardmap', 'auth', 'park', 'extern', 'ledgers', 'all_post'])
    ap.add_argument('--seg', default='')
    a = ap.parse_args()
    t0 = time.time()
    if a.task == 'penalty':
        if a.seg not in N.SEGMENTS:
            raise SystemExit('penalty 需要 --seg')
        outs = task_penalty(a.seg)
    elif a.task == 'rawledger':
        outs = task_rawledger()
    elif a.task == 'all_post':
        outs = []
        for fn in (task_penalty_merge, task_cardmap, task_auth, task_park, task_extern, task_ledgers):
            outs += fn()
        N.write_receipt('E6n_fixed_all_post', outs, code=[__file__], wall_s=round(time.time() - t0, 1))
    else:
        outs = dict(penalty_merge=task_penalty_merge, cardmap=task_cardmap, auth=task_auth, park=task_park, extern=task_extern, ledgers=task_ledgers)[a.task]()
        N.write_receipt('E6n_fixed_%s' % a.task, outs, code=[__file__], wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(task=a.task, outputs=[N.rel(p) for p in outs], wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
