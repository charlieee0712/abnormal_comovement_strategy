# -*- coding: utf-8 -*-
"""E6m 固定输出表（registry/fixed_outputs_E6m.csv 中 carried = True 的表；骨架 reports_skeleton/fixed/<表>.csv 列序固定；附录 A6-5）。
长表列：query_id | object | segment | metric | value | unit | aggregation | support | status（B3–B6 各自骨架列）。
  --phase deriv  只取推导两段（统计 / 分解 / 随机读 results/deriv）；--phase full 四段（两后段授权 + seal_post 之后）
每张表至少一行；来源未到 → 一行 status（SOURCE_WAIT：输入未到；NOT_RUN：生成模块属后续阶段，reason 写在 support 列）；输出列 ≠ 骨架列即报错。
不读任何未封存的账户：读真实统计目录前过封存门。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M

LONG = ['query_id', 'object', 'segment', 'metric', 'value', 'unit', 'aggregation', 'support', 'status']
NOT_YET = {
    'b3_cells': 'B3 先行结果锚过后并入（S4）', 'b3_pairs': '同上', 'b3_random': '同上', 'b3_mirror_cvr': '同上', 'b3_mirror_gap': '同上',
    'replica_manifest_P0': '副本包（S4）', 'replica_manifest_P1': '副本包（S4）', 'replica_manifest_P2': '副本包（S4）', 'replica_manifest_P3': '副本包（S4）',
}
UNIT = (('_ann_pp', 'ann_pp'), ('ann_pp', 'ann_pp'), ('port_size', 'pct_pt'), ('edit_gap', 'pct_pt'), ('mcse', 'ann_pp'), ('rand_', 'ann_pp'),
        ('real_minus', 'ann_pp'), ('days', 'count'), ('n_', 'count'), ('_count', 'count'), ('paths', 'count'), ('have', 'count'), ('topup', 'count'),
        ('share', 'decimal'), ('rel', 'decimal'))


def unit_of(c):
    for k, u in UNIT:
        if k in c:
            return u
    return 'decimal'


def skel(name):
    return pd.read_csv(M.P('reports_skeleton', 'fixed', '%s.csv' % name), nrows=0).columns.tolist()


def status_row(cols, name, status, why=''):
    r = {c: '' for c in cols}
    r['query_id'], r['status'] = name, status
    if 'support' in r:
        r['support'] = why
    return pd.DataFrame([r], columns=cols)


def long(df, name, obj, metrics, seg='segment', agg='', sup='', status='COMPUTED'):
    rows = []
    for r in df.to_dict('records'):
        o = '|'.join(str(r[c]) for c in obj) if isinstance(obj, (list, tuple)) else str(r[obj])
        for m in metrics:
            if m not in r:
                continue
            v = r[m]
            undefined = (not isinstance(v, str)) and pd.isna(v)
            numeric = not isinstance(v, str) or v.replace('.', '', 1).replace('-', '', 1).replace('e', '', 1).isdigit()
            rows.append(dict(query_id=name, object=o, segment=r.get(seg, '') if seg else '', metric=m, value='' if undefined else v,
                             unit=unit_of(m) if numeric else 'text', aggregation=agg, support=sup, status='UNDEFINED' if undefined else status))
    return pd.DataFrame(rows, columns=LONG)


def segs_of(phase):
    return tuple(M.DERIV_SEGS) if phase == 'deriv' else tuple(M.SEGMENTS)


def cat(pattern, segs, **kw):
    parts = [pd.read_csv(pattern % s, keep_default_na=False, na_values=[''], low_memory=False, **kw).assign(segment=s)
             for s in segs if os.path.exists(pattern % s)]
    return pd.concat(parts, ignore_index=True) if parts else None


def stage_a(segs, sa_dir):
    parts = []
    for s in segs:
        for f in sorted(glob.glob(os.path.join(sa_dir, s, 'mask_facts_*.csv'))):
            parts.append(M.read_csv_keep(f, dtype={'param': str, 'alpha': str}))
    return pd.concat(parts, ignore_index=True) if parts else None


def build(name, a, segs):
    st = a.stats
    if name.startswith('b3_') and getattr(a, 'b3', '') and os.path.exists(os.path.join(a.b3, '%s.csv' % name)):
        return M.read_csv_keep(os.path.join(a.b3, '%s.csv' % name)), 'e6m_b3_merge（锚已通过后并入）'
    if name in NOT_YET:
        return None, NOT_YET[name]
    if name in ('source_lineage', 'external_inputs_E6m'):
        p = M.P('stage0_S', 'intake', 'external_inputs_E6m_S.csv')
        p = p if os.path.exists(p) else M.P('registry', 'external_inputs_E6m.csv')
        E = M.read_csv_keep(p, dtype=str)
        E['obj'] = E['id'] + '|' + E['path'].str.slice(0, 80)
        return long(E, name, 'obj', ['status', 'sha256', 'read_step', 'stage'], seg=None, agg='文件', sup=M.rel(p)), ''
    if name == 'import_closure_E6m':
        I = M.read_csv_keep(M.P('registry', 'import_closure_E6m.csv'), dtype=str)
        ocol = I.columns[0]
        return long(I, name, ocol, [c for c in I.columns if c != ocol], seg=None, agg='模块', sup='registry/import_closure_E6m.csv'), ''
    if name == 'hypothesis_lineage':
        p = M.P('registry', 'hypothesis_lineage_E6m.csv')
        if not os.path.exists(p):
            return None, 'SOURCE_WAIT：Stage B（--real）未跑'
        L = M.read_csv_keep(p, dtype=str)
        return long(L, name, 'claim_id', ['status', 'author_role', 'source_section', 'test_id', 'query_id', 'result_status', 'design_update'], seg=None,
                    agg='逐条', sup='registry/hypothesis_lineage_E6m.csv'), ''
    if name == 'comparison_manifest':
        C = M.read_csv_keep(M.P('registry', 'comparison_manifest_E6m.csv'), dtype=str, usecols=['view', 'kind'])
        g = C.groupby(['view', 'kind']).size().reset_index(name='comparisons')
        return long(g, name, ['view', 'kind'], ['comparisons'], seg=None, agg='计数', sup='registry/comparison_manifest_E6m.csv'), ''
    if name == 'policy_profiles':
        d = json.load(open(M.P('registration', 'policy_profiles_E6m_stageN.json'), encoding='utf-8'))
        rows = []

        def walk(x, pre):
            if isinstance(x, dict):
                for k, v in x.items():
                    if k == 'status_words_forbidden' and isinstance(v, list):      # 合同在列举禁用词：整份写成一个文本值（不让扫描器把清单当状态）
                        rows.append(dict(obj='%s/%s' % (pre, k) if pre else k, value='禁用状态词清单：' + '、'.join(map(str, v))))
                        continue
                    walk(v, '%s/%s' % (pre, k) if pre else k)
            elif isinstance(x, list):
                for i, v in enumerate(x):
                    walk(v, '%s[%d]' % (pre, i))
            else:
                rows.append(dict(obj=pre, value=str(x)))
        walk(d, '')
        return long(pd.DataFrame(rows), name, 'obj', ['value'], seg=None, agg='合同文本', sup='registration/policy_profiles_E6m_stageN.json'), ''
    if name == 'memory_contracts':
        R = [('HG10', '本路径昨日实际 G', 'b·bunit（mean = 1/300）', '空门日清空'), ('LAG1_10', '同算子昨日无 bonus 自然 U', 'b·bunit', '空门日清空'),
             ('PROTECTED_LAG10', '同算子昨日无 bonus 自然 U（带内）', '.10·K_loading_i', '空门日清空；不出带'),
             ('UNPROTECTED_LAG10', '同算子昨日无 bonus 自然 U', '.10·K_loading_i', '可越带边界（泄漏桥）'),
             ('RULE_LAG10', '旧核心源 LAG1_10 门（U_oldlag）之后施加 PASS / HARD', '源 b·bunit', 'Q 缺失保留 U_oldlag 身份'),
             ('NATIVE_METRIC_LAG', '同带 BAND_BLEND 无记忆自然 U（native 度量）', '.10·K_loading_i', '补充对象')]
        df = pd.DataFrame(R, columns=['memory', 'reference', 'bonus', 'reset'])
        return long(df, name, 'memory', ['reference', 'bonus', 'reset'], seg=None, agg='合同', sup='plan §5.3 / §5.3a / §5.4'), ''
    if name == 'state_unknown_days':
        S = M.read_csv_keep(M.P('stage0', 'c4_data_state_unknown.csv'))
        S = S[S.segment.isin(segs)]
        return long(S, name, 'table', [c for c in S.columns if c not in ('table', 'segment')], agg='段', sup='stage0/c4_data_state_unknown.csv（ANCHOR_PENDING 至 A4-3）'), ''
    if name in ('random_refs',):
        R = cat(os.path.join(st, 'random_refs_%s.csv'), segs) if st else None
        if R is None:
            return None, 'SOURCE_WAIT：随机统计未到'
        R['obj'] = R.desc_id + '|' + R.mechanism + '|H' + R.H.astype(str)
        return long(R, name, 'obj', ['rand_mean', 'rand_sd', 'mcse', 'n', 'paths_run', 'real_net8_ann', 'real_minus_rand'], agg='路径均值 / 段',
                    sup='每路径先按自身有效日求均值'), ''
    if name == 'mc_precision':
        rows = []
        for s in segs:
            fs = sorted(glob.glob(M.P('results', 'mc', 'mc_plan_%s_r*.csv' % s)), key=lambda f: int(f.rsplit('_r', 1)[1][:-4]))
            if fs:
                rows.append(pd.read_csv(fs[-1]).assign(segment=s, round=len(fs) - 1))
        if not rows:
            return None, 'SOURCE_WAIT：MC 增补未跑'
        P = pd.concat(rows, ignore_index=True)
        return long(P, name, 'rtask', ['have', 'need_max', 'target', 'topup', 'worst_mcse', 'worst_sd'], agg='共享路径组', sup='最后一轮规划'), ''
    if name == 'completion_coverage':
        S = cat(os.path.join(st, 'descriptor_stats_%s.csv'), segs, usecols=['desc_id', 'status']) if st else None
        if S is None:
            return None, 'SOURCE_WAIT：描述符统计未到'
        D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str, usecols=['desc_id', 'block'])
        S = S.merge(D, on='desc_id', how='left')
        g = S.groupby(['block', 'segment', 'status']).size().reset_index(name='n_objects')
        g['obj'] = g.block + '|' + g.status
        L1 = long(g, name, 'obj', ['n_objects'], agg='计数', sup='主描述符：registered == computed 核对')
        ap_ = os.path.join(a.aux or '', 'aux_status_summary_%s.csv' % a.phase)
        if a.aux and os.path.exists(ap_):                               # 附属 66,698 行逐行状态（e6m_s_aux_status）：LIMIT 等显式状态算闭合，缺行不算
            X = M.read_csv_keep(ap_, dtype=str)
            X['obj'] = 'AUX|item' + X['item'] + '|' + X.aux_kind + '|' + X.status
            X['n_objects'] = pd.to_numeric(X.rows)
            L1 = pd.concat([L1, long(X.assign(segment='/'.join(segs)), name, 'obj', ['n_objects'], agg='计数', sup='附属清单逐行状态')], ignore_index=True)
        return L1, ''
    if name in ('turn_cost_frontier', 'risk_tight_bounds'):
        S = cat(os.path.join(st, 'descriptor_stats_%s.csv'), segs) if st else None
        if S is None:
            return None, 'SOURCE_WAIT：描述符统计未到'
        S = S[S.status == 'COMPUTED']
        cols = ['D', 'D_6bp', 'D_12bp', 'D_gross', 'turn_rel', 'turn_mean_decimal'] if name == 'turn_cost_frontier' else \
            ['port_size_lo_T', 'port_size_hi_T', 'port_size_absmean_mid_T', 'port_size_p95abs_mid_T', 'port_size_maxabs_mid_T', 'port_size_lo_L', 'port_size_hi_L']
        return long(S, name, 'desc_id', cols, agg='段', sup='相对同 H 实际父'), ''
    if name in ('band_facts', 'filter_facts', 'edit_budget_ledger', 'two_day_support', 'copy_gate_ledger', 'memory_reference_ledger'):
        A = stage_a(segs, a.stage_a)
        if A is None:
            return None, 'SOURCE_WAIT：Stage A 未到'
        A = A[A.status == 'COMPUTED']
        pick = {'band_facts': (A.kind == 'MAIN') & A.block.isin(['BAND_Q', 'BAND_BLEND', 'LEAK_BRIDGE']),
                'filter_facts': (A.kind == 'MAIN') & (A.block == 'FILTER'),
                'edit_budget_ledger': (A.kind == 'MAIN') & (A.block == 'EDIT_MATCH'),
                'two_day_support': ((A.kind == 'MAIN') & (A.block == 'TWO_DAY')) | ((A.kind == 'AUX') & A.block.str.contains('TWO_DAY')),
                'copy_gate_ledger': (A.kind == 'AUX') & A.block.str.startswith('COPY'),
                'memory_reference_ledger': (A.kind == 'MAIN') & A.memory.fillna('NONE').ne('NONE')}[name]
        X = A[pick]
        meta = {'segment', 'form', 'target', 'kind', 'block', 'measurement', 'operator', 'param', 'alpha', 'memory', 'status'}
        cols = [c for c in X.columns if c not in meta and X[c].notna().any()]
        return long(X, name, 'target', cols, agg='段（掩码层，不读收益）', sup='Stage A'), ''
    if name in ('four_account_ledger', 'match_cap_ledger', 'weight_change_attribution'):
        fn = {'four_account_ledger': 'four_account_%s.csv', 'match_cap_ledger': 'cap_decomp_%s.csv', 'weight_change_attribution': 'weight_change_%s.csv'}[name]
        X = cat(os.path.join(a.decomp, fn), segs) if a.decomp else None
        if X is None:
            return None, 'SOURCE_WAIT：分解（e6m_s_decomp）未跑'
        if name == 'four_account_ledger':
            X['obj'] = X.route + '|' + X.object + '|' + X.metric.fillna('')
            cols = ['I_ann_pp', 'R_ann_pp', 'X_ann_pp', 'total_ann_pp', 'closure_maxabs', 'y00_minus_parent_ann_pp', 'n_common_days']
        else:
            X['obj'] = X.desc_id
            cols = [c for c in X.columns if c.endswith(('_ann_pp', '_segavg', '_validavg', '_maxabs')) or c.startswith('days_')]
        return long(X, name, 'obj', cols, agg='逐日闭合后段均', sup='e6m_s_decomp'), ''
    if name in ('b4_event_contrib', 'symdec', 'b4_signatures'):
        if a.phase != 'full':
            return None, 'NOT_AUTHORIZED：B4 读后段（W1 / W2 在 2024-2026；SYMDEC 含后段对）'
        cols = skel(name)
        if name == 'b4_signatures':
            Q = M.read_csv_keep(M.P('registry', 'b4_queries_E6m.csv'), dtype=str)
            Q = Q[Q.query_kind == 'SIGNATURE']
            okd = {'SIG4': bool(a.b4) and os.path.exists(os.path.join(a.b4, 'b4_sig4_detail.csv'))}
            for w_ in ('SIG1', 'SIG2', 'SIG3'):                          # 引擎层详表逐段（e6m_b4_sig；定义 = delegated_decisions 第 22 项）
                okd[w_] = bool(a.b4) and all(os.path.exists(os.path.join(a.b4, 'b4_sig%s_%s.csv' % (w_[-1], s))) for s in segs)
            rows = [dict({c: '' for c in cols}, query_id='E6M-Q14-b', object=r.object, window=r.window,
                         status=('INFO' if okd.get(r.window) else 'NOT_RUN')) for r in Q.itertuples()]
            return pd.DataFrame(rows, columns=cols), ('骨架列装不下签名输出（第 22 项决定：详表 + 状态行）：SIG1–3 见 b4_sig1 / 2 / 3_<段>.csv，'
                                                      'SIG4 见 b4_sig4_detail.csv')
        fn = os.path.join(a.b4 or '', 'b4_event_contrib_detail.csv' if name == 'b4_event_contrib' else 'symdec_detail.csv')
        if not os.path.exists(fn):
            return None, 'SOURCE_WAIT：e6m_b4 未跑'
        X = M.read_csv_keep(fn)
        return X[cols], ''
    if name == 'state_clock_ledger':
        # E6l 固定表沿用：e6m_b5 clock（三时钟 + STRICT250，逐段宽表）→ 长表；object = 对象|时钟|状态变量|状态，各行保留来源状态
        X = cat(os.path.join(a.b5, 'b5_state_clock_%s.csv'), segs) if getattr(a, 'b5', '') else None
        if X is None:
            return None, 'SOURCE_WAIT：e6m_b5 clock 未跑'
        net = ['days', 'share', 'contribution_ann_pp', 'conditional_mean_ann_pp', 'conditional_se_H_ann_pp']
        per_clock = {'FORMATION': ['gross_contrib_child_ann_pp', 'gross_contrib_parent_ann_pp', 'gross_contrib_diff_ann_pp', 'closure_max_abs_decimal'],
                     'CALENDAR_NET': net, 'TRADING_FEE': net, 'STRICT250': ['days', 'strict250_days']}      # 只印该时钟适用的量（不适用 ≠ UNDEFINED）
        agg, sup = '段内日均 × 252 × 100（ann_pp）；日数为段内计数', 'e6m_b5 clock（e6l_state_clock 移植；H5；状态 = 云机状态缓存）'
        rows = []
        for r in X.to_dict('records'):
            o = '|'.join(str(r.get(k, '') if pd.notna(r.get(k, '')) else '') for k in ('object', 'clock', 'state_var', 'state'))
            src_st = str(r.get('status', 'COMPUTED'))
            mets = list(per_clock.get(r.get('clock'), []))
            if r.get('state') == 'SUM_CHECK':
                mets = ['days', 'contribution_ann_pp', 'conditional_mean_ann_pp', 'closure_max_abs_decimal']
            if r.get('clock') == 'FORMATION' and str(r.get('object', '')).split('|')[2:3] == ['PARENT']:
                mets.remove('gross_contrib_parent_ann_pp')                # 父对象没有"父"一侧（差 = 自身，B4 同约定）
            if not mets:
                rows.append(dict(query_id=name, object=o, segment=r['segment'], metric='status', value='', unit='text', aggregation=agg, support=sup, status=src_st))
                continue
            for m in mets:
                v = r.get(m, np.nan)
                na = (not isinstance(v, str)) and pd.isna(v)
                rows.append(dict(query_id=name, object=o, segment=r['segment'], metric=m, value='' if na else v, unit=unit_of(m), aggregation=agg, support=sup,
                                 status=src_st if src_st not in ('COMPUTED', 'UNDEFINED') else ('UNDEFINED' if na else 'COMPUTED')))   # 状态无日：日数 0 有定义，条件均值才 UNDEFINED
        out = pd.DataFrame(rows, columns=LONG)
        return (out if len(out) else None), ('' if len(out) else 'SOURCE_WAIT：e6m_b5 clock 无可转行')
    if name in ('b5_delete_budget', 'b5_state_ledger', 'b6_trigger_ledger'):
        # 骨架无段列（STAGE_S_IMPL_PLAN §5 第 23 项）：汇总到本阶段各段——计数求和；比率按批次数加权；年化量按段日数加权；逐段明细见详表
        if name == 'b6_trigger_ledger':
            if a.phase != 'full':
                return None, 'NOT_AUTHORIZED：B6 只在四段汇总'
            pat, src, key = os.path.join(a.b6 or '', 'b6_trigger_ledger_%s.csv'), a.b6, ['query_id', 'object', 'trigger']
        else:
            pat = os.path.join(a.b5 or '', ('b5_delete_budget_%s.csv' if name == 'b5_delete_budget' else 'b5_state_ledger_%s.csv'))
            src, key = a.b5, ['query_id', 'object', 'H'] + (['partition'] if name == 'b5_state_ledger' else [])
        X = cat(pat, segs) if src else None
        if X is None:
            return None, 'SOURCE_WAIT：%s 未跑' % ('e6m_b6_accounts' if name == 'b6_trigger_ledger' else 'e6m_b5')
        cols = skel(name)
        wd = pd.to_numeric(X['n_days'], errors='coerce').fillna(0.0) if 'n_days' in X.columns else pd.Series(1.0, index=X.index)
        wv = pd.to_numeric(X['vintages'], errors='coerce').fillna(0.0) if 'vintages' in X.columns else wd
        rows = []
        for k, g in X.assign(_wd=wd, _wv=wv).groupby(key, sort=False):
            r = dict(zip(key, k))
            ok = g.status.eq('COMPUTED').all() and len(g) == len(segs)
            for c in cols:
                if c in key or c == 'status':
                    continue
                v = pd.to_numeric(g[c], errors='coerce')
                if c in ('delete_count', 'n_days', 'restricted_inventory_days'):
                    r[c] = float(v.sum())
                    continue
                w_ = g._wv if c == 'trigger_rate_decimal' else g._wd
                m = v.notna() & (w_ > 0)
                r[c] = float((v[m] * w_[m]).sum() / w_[m].sum()) if m.any() else np.nan
            r['status'] = 'COMPUTED' if ok else (g.status[g.status != 'COMPUTED'].iloc[0] if (g.status != 'COMPUTED').any() else 'UNDEFINED')
            rows.append(r)
        return pd.DataFrame(rows)[cols], '汇总到 %s（计数求和；比率按批次数、年化量按段日数加权）' % '/'.join(segs)
    if name == 'memory_age_daily':
        parts = []
        for s in segs:
            for f in sorted(glob.glob(os.path.join(a.masks or M.P('masks'), s, 'memory_age_*.csv'))):
                parts.append(M.read_csv_keep(f))
        if not parts:
            return None, 'SOURCE_WAIT：e6m_s_memage 未跑'
        X = pd.concat(parts, ignore_index=True)
        X['obj'] = X.target_id + '|' + X.date.astype(str)
        return long(X, name, 'obj', ['reliant_share', 'reliant_run_p50', 'confirm_age_p50'], agg='逐日（名单层）', sup='e6m_s_ops.gate_facts 逐日版'), ''
    if name == 'trefit_bridge':
        X = cat(os.path.join(a.decomp, 'trefit_%s.csv'), segs) if a.decomp else None
        if X is None:
            return None, 'SOURCE_WAIT：T 桥账户比较未跑（附属 FROZEN_SOURCE_T_COEFFICIENTS 账户 − owner）'
        return long(X, name, 'aux_id', [c for c in X.columns if c.endswith('_ann_pp')], agg='段', sup='附属账户'), ''
    if name in ('primary72', 'neighborhood_panels'):
        pol = a.policy if a.policy and os.path.exists(a.policy) else ''
        S = cat(os.path.join(st, 'descriptor_stats_%s.csv'), segs) if st else None
        if S is None and not pol:
            return None, 'SOURCE_WAIT：统计 / 政策未到'
        D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
        keep = D[D.is_primary72 == 'True'] if name == 'primary72' else D[(D.is_primary72 != 'True') & D.primary_recipe.ne('NOT_APPLICABLE')
                                                                                                & D.primary_recipe.ne('')]
        if pol and a.phase == 'full':
            P = pd.read_csv(pol, keep_default_na=False, na_values=[''], low_memory=False)
            P = P[P.desc_id.isin(keep.desc_id)]
            return long(P.assign(segment='FULL'), name, 'desc_id', ['FULL', 'G4', 'FULL_sc', 'FULL_imp', 'years_pos', 'policy_result', 'size_PROPOSED_PORT3_T']
                        if 'policy_result' in P.columns else ['FULL', 'G4'], agg='四段', sup='policy_E6m'), ''
        S = S[S.desc_id.isin(keep.desc_id)]
        return long(S, name, 'desc_id', ['D', 'n', 'se_H', 'MDE80', 'D_sc', 'D_imp', 'turn_rel'], agg='段', sup='推导段'), ''
    return None, 'UNDEFINED：未知表'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', required=True, choices=['deriv', 'full'])
    ap.add_argument('--stats', default='')
    ap.add_argument('--stage-a', default='')
    ap.add_argument('--decomp', default='')
    ap.add_argument('--b4', default='')
    ap.add_argument('--b5', default='')
    ap.add_argument('--b6', default='')
    ap.add_argument('--b3', default='')
    ap.add_argument('--aux', default='')
    ap.add_argument('--masks', default='')
    ap.add_argument('--policy', default='')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t0 = time.time()
    if a.phase == 'full':
        import e6m_s_gate as GT
        GT.post_gate(M.POST_SEGS[0], 'fixed tables full')
    if a.stats and os.path.realpath(a.stats).startswith(os.path.realpath(M.P('results')) + os.sep):
        import e6m_s_seal as SEAL
        SEAL.require('deriv')
        if a.phase == 'full':
            SEAL.require('post')
    segs = segs_of(a.phase)
    F = M.read_csv_keep(M.P('registry', 'fixed_outputs_E6m.csv'), dtype=str)
    F = F[F.carried == 'True']
    os.makedirs(a.out, exist_ok=True)
    summ, outs = [], []
    for name in F.e6m_name:
        cols = skel(name)
        df, why = build(name, a, segs)
        if df is None or not len(df):
            st = 'NOT_RUN' if name in NOT_YET else ('SOURCE_WAIT' if why.startswith('SOURCE_WAIT') else ('NOT_AUTHORIZED' if why.startswith('NOT_AUTHORIZED') else 'UNDEFINED'))
            df = status_row(cols, name, st, why)
        if list(df.columns) != cols:
            raise RuntimeError('%s 输出列与骨架不一致：%s' % (name, sorted(set(df.columns) ^ set(cols))))
        p = os.path.join(a.out, '%s.csv' % name)
        M.atomic_write_csv(p, df)
        outs.append(p)
        summ.append(dict(table=name, rows=len(df), status=json.dumps(df.status.value_counts().to_dict(), ensure_ascii=False),
                         forbidden_status_hits=len(M.scan_status_words(df)), note=why))
    S = pd.DataFrame(summ)
    ps = os.path.join(a.out, 'fixed_summary_%s.csv' % a.phase)
    M.atomic_write_csv(ps, S)
    ok = int(S.forbidden_status_hits.sum()) == 0 and (S.rows > 0).all()
    M.write_receipt(os.environ.get('E6M_TASK', 'S_fixed_%s' % a.phase), [ps] + outs, status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__],
                    tables=len(S), wall_s=round(time.time() - t0, 1))
    print(S[['table', 'rows', 'status']].to_string(max_colwidth=60), flush=True)
    print(json.dumps(dict(tables=len(S), forbidden=int(S.forbidden_status_hits.sum()), empty=int((S.rows == 0).sum())), ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
