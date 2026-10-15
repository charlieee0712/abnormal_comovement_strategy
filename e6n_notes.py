# -*- coding: utf-8 -*-
"""E6n 执行端交付说明（reports/E6n_REVIEW_input_notes.md）：数字一律从机器表现取（不手抄、不下判词）；§8 待决事项 = notes_pending_items_E6n.md 原文。
另把 scratchpad 写好的 lessons_delta 原样放进 reports/（由调用方拷到结果目录 notes_in/E6n_lessons_delta.md）。"""
import os
import re
import sys
import json

import numpy as np
import pandas as pd

import e6n_core as N

MAIN_RX = r'^CORE\|.*\|A4b_CVRv5\|HG10\|H5\|s0\.25\|QGOOD\|a0\.25\|f5\|d\+1$'
FRONT = 'ANCHOR|Q0|A4b_CVRv5|HG10|H5|s0|ALL|a0.25|f5|d+1'
VIEWS = ('VS_SAME_MEMORY_Q0', 'VS_MASK_CLONE', 'VS_DOSE', 'VS_ORIGINAL_PARENT', 'PATH_MINUS_Q_RV', 'PATH_MINUS_Q_RANGE', 'THIN_MINUS_LEVEL')


def csv(p):
    p = N.P(p)
    return pd.read_csv(p, keep_default_na=False, na_values=[''], low_memory=False) if os.path.exists(p) else None


def f(v, nd=2):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    return 'UNDEFINED' if not np.isfinite(v) else ('%+.' + str(nd) + 'f') % v


def ci(bs, cid):
    if bs is None or cid not in bs.index:
        return 'bootstrap UNDEFINED'
    b = bs.loc[cid]
    return '95%% [%s, %s]' % (f(b.q025_ann_pp, 3), f(b.q975_ann_pp, 3))


def main():
    BS = csv('results/full/bootstrap/bootstrap_comparisons.csv')
    if BS is not None:
        BS = BS[(BS.scope == 'FULL') & (pd.to_numeric(BS.L, errors='coerce') == 20)].drop_duplicates('comparison_id').set_index('comparison_id')
    CF = csv('results/full/comparison_full.csv')
    P = csv('results/full/policy_E6n.csv')
    G = csv('registration/probe_ledger.csv')
    L = ['# E6n REVIEW_input_notes —— 执行端交付说明（读数全部取自机器表；页内数字可回链到所列文件）', '',
         '> 本轮无 E7 与部署授权；协议按 v1.5 候选执行（按流程建议、协议未正式裁定）。B1-0 只打标签、不改任何对象（plan §2.2）。本页只列机器数与出处，不下判词（读法归决策端 REVIEW）。', '']
    # ------------------------------------------------------------------ §0
    L += ['## §0 数字摘要（单位 ann_pp，除注明外；bootstrap = 段内分层平稳，L = 20，2,000 次，FULL 口径）', '']
    main_rows = CF[CF.left_desc_id.str.contains(MAIN_RX, regex=True)] if CF is not None else pd.DataFrame()
    if len(main_rows):
        x = main_rows[main_rows.view == 'VS_SAME_MEMORY_Q0'].sort_values('FULL_ann_pp')
        L.append('- 主母体 A4b_CVRv5 × HG10 × H5 × α_K .25 × QGOOD，七个分钟对象相对同记忆 Q0：' + '；'.join(
            '%s %s（%s）' % (r.left_desc_id.split('|')[1], f(r.FULL_ann_pp, 3), ci(BS, r.comparison_id)) for r in x.itertuples()) + '（`results/full/comparison_full.csv`）。')
        y = main_rows[main_rows.view.isin(['PATH_MINUS_Q_RV', 'PATH_MINUS_Q_RANGE', 'THIN_MINUS_LEVEL'])]
        L.append('- 两条构造相对日线 / 去量对照：' + '；'.join('%s %s（%s）' % (r.view, f(r.FULL_ann_pp, 3), ci(BS, r.comparison_id)) for r in y.itertuples()) + '。')
    if P is not None:
        P['head'] = P.policy_result.astype(str).str.split('（').str[0]
        p72 = P[P.is_primary72.astype(str) == 'True']
        t = p72.groupby(['feature', 'head']).size().unstack(fill_value=0)
        L.append('- 主 72 政策（PROPOSED_PORT3_T × FULL）：' + '；'.join('%s %s' % (k, ' / '.join('%s %d' % (c, int(v)) for c, v in row.items() if v)) for k, row in t.iterrows()) + '。')
        L.append('- 全表 %d 个政策对象：%s；新对象（首评）%d 个中通过 %d、POLICY_UNDECIDABLE_HISTORY %d。' % (
            len(P), json.dumps(P['head'].value_counts().to_dict(), ensure_ascii=False), int((P.exposure == N.LABEL_FIRST_LOOK).sum()),
            int(((P.exposure == N.LABEL_FIRST_LOOK) & (P.policy_result == '通过')).sum()),
            int(((P.exposure == N.LABEL_FIRST_LOOK) & P.policy_result.astype(str).str.contains('POLICY_UNDECIDABLE_HISTORY')).sum())))
    F = csv('results/full/frontier_E6n.csv')
    if F is not None and 'd_vs_frontier_FULL_ann_pp' in F.columns:
        F = F[F.desc_id != FRONT]
        v = pd.to_numeric(F.d_vs_frontier_FULL_ann_pp, errors='coerce')
        L.append('- 前沿表（A4b_CVRv5 × H5 共 %d 个对象相对 %s）：FULL 差 > 0 的 %d 个；其中政策通过的 %d 个（`results/full/frontier_E6n.csv`）。' % (
            len(F), FRONT, int((v > 0).sum()), int(((v > 0) & (F.policy_result == '通过')).sum())))
    I = csv('results/full/improvement_E6n.csv')
    if I is not None and 'dnet8_FULL_ann_pp' in I.columns:
        s = I.groupby('versus').dnet8_FULL_ann_pp.apply(lambda z: float((pd.to_numeric(z, errors='coerce') > 0).mean()))
        L.append('- 实质改善表 Δnet8 FULL > 0 的份额：' + '；'.join('%s %.3f' % (k, v_) for k, v_ in s.items()) + '（`results/full/improvement_E6n.csv`）。')
    if G is not None:
        lab = G.label.astype(str).str.split('；').str[0].str.split('（').str[0].value_counts().to_dict()
        L.append('- B1-0 主域标签计数：%s；带"池子层面读法"注记 %d 个（`registration/probe_ledger.csv`）。' % (
            json.dumps(lab, ensure_ascii=False), int(G.label.astype(str).str.contains('池子层面').sum())))
    B5 = csv('results/full/b5/b5_dedupe.csv')
    if B5 is not None and 'dedupe_group' in B5.columns:
        L.append('- B5：%s → 独立候选组 %d；等价分级 %s（`results/full/b5/b5_dedupe.csv`）。' % (B5.count_check.iloc[0], B5.dedupe_group.nunique(),
                                                                                  json.dumps(B5.equivalence.value_counts().to_dict(), ensure_ascii=False)))
    L.append('')
    # ------------------------------------------------------------------ §1
    L += ['## §1 跑了什么', '']
    a0 = json.load(open(N.P('registration', 'a0_counts_E6n.json'), encoding='utf-8'))
    L.append('- 登记：主 %s / 附属 %s / 主展示 %s / MATCHED %s / COMPONENT_DOSE %s / 比较 %s（`registration/a0_counts_E6n.json`；registry_sha256 前缀 %s）。' % (
        a0.get('main'), a0.get('auxiliary'), a0.get('primary72'), a0.get('matched'), a0.get('cdose'), a0.get('comparisons_total'), str(a0.get('registry_sha256'))[:8]))
    for ph in ('B1_0', 'deriv', 'post'):
        p = N.P('registration', 'seal_%s.json' % ph)
        if os.path.exists(p):
            j = json.load(open(p, encoding='utf-8'))
            L.append('- seal_%s：written_at %s，n_files %s，queued_missing %s，n_receipts %s。' % (ph, j.get('written_at'), j.get('n_files'), j.get('queued_missing'), j.get('n_receipts')))
    R = csv('results/full/random_refs.csv')
    if R is not None:
        g = R[(R.kind == 'OBJECT') & (R.segment != 'FULL')].groupby('mechanism').agg(lo=('paths_run', 'min'), hi=('paths_run', 'max'), segs=('segment', 'nunique'),
                                                                                   mcse=('mcse', 'max')).reset_index()
        L.append('- 随机路径（对象 × 段）：' + '；'.join('%s %d 段 %d–%d 路径（最大 MCSE %s）' % (r.mechanism, r.segs, r.lo, r.hi, f(r.mcse, 4)) for r in g.itertuples()) +
                 '；MC 增补计划四段均 0 组（`results/full/mc_plan_<段>.csv`）。')
    L.append('')
    # ------------------------------------------------------------------ §2
    L += ['## §2 第一道（B1-0）读法（主域 = QGOOD ∩ Q0|A4b_CVRv5|α.25|HG10 形成集；FWD_SOURCE h5 低 − 高；bp）', '']
    if G is not None:
        for r in G.itertuples():
            L.append('- %s：两推导段 %s / %s bp（n %s / %s）→ 总体 %s；%s' % (r.member, f(r.seg1_value), f(r.seg2_value), r.n_seg1, r.n_seg2, f(r.overall), r.label))
    L.append('')
    # ------------------------------------------------------------------ §3
    L += ['## §3 主问题的账户读数（主母体 A4b_CVRv5 × HG10 × H5 × .25 × QGOOD；FULL = n 加权四段，G4 = 段中位；单位 ann_pp）', '']
    if len(main_rows):
        sub = main_rows[main_rows.view.isin(VIEWS)].copy()
        sub['vo'] = sub.view.map({v_: i for i, v_ in enumerate(VIEWS)})
        for r in sub.sort_values(['left_desc_id', 'vo']).itertuples():
            L.append('- %s %s：FULL %s，G4 %s，%s（`results/full/comparison_full.csv` %s）' % (r.left_desc_id.split('|')[1], r.view, f(r.FULL_ann_pp, 3), f(r.G4_ann_pp, 3),
                                                                                     ci(BS, r.comparison_id), r.comparison_id))
    L.append('')
    # ------------------------------------------------------------------ §4
    L += ['## §4 资格与前沿', '']
    if P is not None:
        L.append('- PROPOSED_PORT3_T × FULL 结果计数：%s（`results/full/policy_E6n.csv`）。' % json.dumps(P['head'].value_counts().to_dict(), ensure_ascii=False))
        und = P[P.policy_result.astype(str).str.contains('POLICY_UNDECIDABLE_HISTORY')]
        tags = und.policy_result.astype(str).str.replace(r'\d+', 'k', regex=True).str[:70].value_counts().head(4).to_dict()
        L.append('- 不可判的主要标签（数字归一为 k）：%s；可用期研究表 `results/full/policy_available_period_E6n.csv`（只报数）。' % json.dumps(tags, ensure_ascii=False))
    if F is not None and 'd_vs_frontier_FULL_ann_pp' in F.columns:
        top = F.assign(v=pd.to_numeric(F.d_vs_frontier_FULL_ann_pp, errors='coerce')).sort_values('v', ascending=False).head(8)
        for r in top.itertuples():
            L.append('- 前沿差前列：%s FULL %s（G4 %s；政策 %s）' % (r.desc_id, f(r.d_vs_frontier_FULL_ann_pp, 3), f(r.d_vs_frontier_G4_ann_pp, 3), r.policy_result))
    L.append('')
    # ------------------------------------------------------------------ §5
    L += ['## §5 支持块（B2–B6）与补齐表', '']
    B2 = csv('results/full/b2/b2_controls.csv')
    if B2 is not None and len(B2):
        for nm, segs in (('推导两段', N.DERIV_SEGS), ('四段', N.SEGMENTS)):
            x = B2[(B2.form == 'A4b_CVRv5') & (B2.object_key == 'HG10|a0.25|Q0') & (pd.to_numeric(B2.H, errors='coerce') == 5) & (B2.control == 'SAME_RATE_RANDOM')
                   & B2.segment.isin(segs)]
            w = pd.to_numeric(x.n_events_real, errors='coerce')
            v = pd.to_numeric(x.real_minus_control_bp, errors='coerce')
            ok = np.isfinite(v) & (w > 0)
            L.append('- B2（H12）Q0 HG 主母体 H5，CVR 跳升触发 − 同率随机，%s事件加权：%s bp / 事件（%d 事件；`results/full/b2/b2_controls.csv`）。' % (
                nm, f(np.average(v[ok], weights=w[ok]) if ok.any() else np.nan, 3), int(w[ok].sum()) if ok.any() else 0))
    B3 = csv('results/full/b3/b3_same_count.csv')
    if B3 is not None and len(B3):
        x = B3[(B3.core == 'A4b') & (B3.object_key == 'HG10|a0.25|Q0') & (pd.to_numeric(B3.H, errors='coerce') == 5) & (B3.weights == 'REDO_DEV')]
        rr = x[x.control == 'CVR_REAL'].set_index('segment').D_vs_parent_ann_pp
        for ctl in ('RANDOM_LEGAL_CVR', 'WORST_OLD_K', 'SOURCE_PRIORITY'):
            cc = x[x.control == ctl].set_index('segment').D_vs_parent_ann_pp
            dd = (pd.to_numeric(rr, errors='coerce') - pd.to_numeric(cc, errors='coerce')).dropna()
            L.append('- B3（H13）Q0 HG 主裸 A4b，CVR_REAL − %s（REDO_DEV，H5）：逐段 %s（`results/full/b3/b3_same_count.csv`）。' % (
                ctl, '；'.join('%s %s' % (k, f(v_, 3)) for k, v_ in dd.items()) or 'UNDEFINED'))
    B6 = csv('results/full/b6/b6_event_contrib.csv')
    if B6 is not None and len(B6):
        for r in B6[B6.object == FRONT].itertuples():
            L.append('- B6 当前前沿 %s 相对原父：%s 窗内贡献 %s、窗外 %s、全期 %s（闭合 %s；`results/full/b6/b6_event_contrib.csv`）。' % (
                FRONT, r.window, f(r.contrib_in_ann_pp, 3), f(r.contrib_out_ann_pp, 3), f(r.D_full_ann_pp, 3), '%.1e' % float(r.closure)))
    if B5 is not None and len(B5):
        L.append('- B5：见 §0；LEAK_BRIDGE 复现 `results/full/b5/b5_leak_bridge.csv`；E7 只写未激活候选协议页 `reports/E6n_E7_prep.md`。')
    PC = csv('results/full/penalty_change_ledger.csv')
    if PC is not None and len(PC):
        a = pd.to_numeric(PC.active_cells, errors='coerce').sum()
        L.append('- penalty_change_ledger（%d 行 = 四段 × 六形态 × RAW 键）：激活单元中"零惩罚而评分变了"的份额 %.4f；最终名单相对同记忆 Q0 变化的单元份额 %.5f；边界间距中位（Q0 / RAW）%s / %s。' % (
            len(PC), pd.to_numeric(PC.zero_penalty_score_changed, errors='coerce').sum() / max(a, 1),
            pd.to_numeric(PC.final_membership_changed, errors='coerce').sum() / max(pd.to_numeric(PC.n_cells, errors='coerce').sum(), 1),
            f(pd.to_numeric(PC.boundary_gap_q0_median, errors='coerce').median(), 4), f(pd.to_numeric(PC.boundary_gap_median, errors='coerce').median(), 4)))
    RL = csv('results/full/measurement_raw_ledger.csv')
    if RL is not None and len(RL):
        L.append('- measurement_raw_ledger：%d 个保存数组（%s），共 %.1f GB；每个带 sha256 = 数据指纹。' % (
            len(RL), json.dumps(RL.scope.value_counts().to_dict(), ensure_ascii=False), pd.to_numeric(RL.bytes, errors='coerce').sum() / 1e9))
    for nm in ('registration/park_reentry_E6n.csv', 'registration/externality_register_E6n.csv', 'registration/card_query_map_E6n.csv'):
        D = csv(nm)
        L.append('- `%s`：%d 行%s。' % (nm, len(D) if D is not None else 0, '（执行端草稿；状态由决策端 REVIEW 定）' if 'park' in nm or 'extern' in nm else ''))
    L.append('')
    # ------------------------------------------------------------------ §6
    L += ['## §6 闭合与核验', '']
    C = csv('results/checks/closure_four_accounts.csv')
    if C is not None:
        L.append('- 四账户 / 合用 / 支持桥逐日闭合 max |残差|：%.2e（%d 组）。' % (float(pd.to_numeric(C.closure_maxabs, errors='coerce').max()), len(C)))
    g0 = json.load(open(N.P('stage0', 'stage0_gate.json'), encoding='utf-8'))
    L.append('- Stage 0 门：%s；A1-auto：%s；生效条件回执 all_pass = %s（逐文件核冻结清单）。' % (
        json.dumps(g0.get('counts'), ensure_ascii=False), json.dumps(json.load(open(N.P('registration', 'a1_auto_E6n.json'), encoding='utf-8')).get('counts'), ensure_ascii=False),
        json.load(open(N.P('registration', 'record_B_conditions_receipt_E6n.json'), encoding='utf-8')).get('all_pass')))
    L.append('- 闭包门结果：`closure_E6n.json` / `closure_E6n.csv`（本页生成后运行；首跑 S07 误报留档 superseded/，见 §8 P16）。')
    L.append('')
    L += ['## §7 限制与经验', '', '- 限制登记：`reports/E6n_limit_register.md`；经验增量：`reports/E6n_lessons_delta.md`；代码变更：`reports/E6n_code_change_register.md`；SCHEMA：`reports/SCHEMA.md`（含 plan §12.4 必交项 → 文件对照）。', '']
    L += ['## §8 待决策端追认 / 裁定事项（跑批途中代拟、未中途发消息；用户 10-11 定）', '']
    pn = N.P('notes_pending_items_E6n.md')
    if os.path.exists(pn):
        txt = open(pn, encoding='utf-8').read()
        L += [re.sub(r'^#', '###', ln) if ln.startswith('#') else ln for ln in txt.split('\n')]
    out = '\n'.join(L) + '\n'
    out = re.sub(r'(?<![A-Za-z_])(nan|NaN|None)(?![A-Za-z_])', 'UNDEFINED', out)
    p = N.P('reports', 'E6n_REVIEW_input_notes.md')
    N.atomic_write_text(p, out)
    src = N.P('notes_in', 'E6n_lessons_delta.md')
    if os.path.exists(src):
        N.atomic_write_text(N.P('reports', 'E6n_lessons_delta.md'), open(src, encoding='utf-8').read())
    N.write_receipt('E6n_notes', [p], code=[__file__])
    print(N.rel(p))
    return 0


if __name__ == '__main__':
    sys.exit(main())
