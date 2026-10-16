# -*- coding: utf-8 -*-
"""E6m Stage B 与登记冻结（brief §5 S2 / W11 / A12；plan §3 / §12 / §13；e6l_prereg 同构）。不读任何收益。
  --stage-b  → <out>/cards_stageB_E6m.csv：18 卡。
                 - 卡片原文字段取 A0 编译的 cards_E6m.csv；
                 - ⑬ = PENDING_DERIV_MDE80（推导段账户后由 e6m_s_mde 机械填）；
                 - ⑮ 账户 / ⑯ 时间尺度 / ⑰ 随机 / ⑱ 状态：由各卡绑定比较左端描述符的 A0 字段机械汇总；
                 - 另列各卡 query_id 与绑定比较按 kind 的条数。
             → <out>/hypothesis_lineage_E6m.csv（字段沿 E6l plan §3.1）：
                 - plan §12 的 18 卡记 adopted；
                 - brief A1 所列被 plan 取代的 proposal 条款记 superseded；
                 - brief W09 记 #110 候选（决策端定号，复盘编号不自改）。
             → <out>/P_objects_E6m.csv：P 包 = 主展示 72（全部 H）+ PARENT 160。
  --freeze   → <out>/stageB_freeze_E6m.json：P / B 两包清单 = registry 与登记文档 sha。
             → 记录 B 状态：方式 A（registration/authorization_status_E6m.json：w11_mode）→ record_B_mode_A_E6m.json。
               推导段后由用户一句话授权两后段；方式 B 时改写 record_B_preauthorized_E6m.json（需用户原话，执行端不代写）。
B2 开发期输出到 stageS_dev/registry_b/；阶段 S 输出到结果目录 registry/ 与 registration/。"""
import e6j_boot  # noqa: F401
import os
import sys
import re
import json
import time
import argparse

import pandas as pd

import e6m_core as M

A1_SUPERSEDED = [
    ('A1-1', '"字典序接入 LEX_BAND / LEX_VETO / LEX_CONJ"命名与"HG 是字典序"的表述', 'plan §5 的 BAND_Q / BAND_BLEND / PRIORITY_PASS / HARD_CONJ；VETO 与 CONJ 的回填版统一 PRIORITY_PASS'),
    ('A1-2', '"⑲ 发生率 × 均值作效应上界并降卡"', '只登记机会人数 / 编辑资本 / 后续传播，不作上界门（plan §1.3）'),
    ('A1-3', '"MDE80 以下降为事实卡 / 只看符号"', 'MDE 只是列（plan §9.5）'),
    ('A1-4', '"三关准入 IC ≠ 0 / 重叠 < .9"', '撤销'),
    ('A1-5', '"B4 掩码回升 ≥ 50% → 事件、签名 ≥ 2 → 拥挤"三选一', '撤销，只输出相容 / 不相容证据（plan §8.1）'),
    ('A1-6', '"六格"', '九格（3 活动 × 3 价格反应）'),
    ('A1-7', '"B3 主读 clean"', 'pool0 主读、clean 与门内 / 拒绝集作镜像（plan §7.1）'),
    ('A1-8', '"E7 读法 ≥ 推导 × .5"', '撤销，E7 只做准备页（plan §11.3）'),
    ('A1-9', '"LAG1_10 作记忆族代表、HG10 别名"', '撤回（W09）'),
    ('A1-10', '"边界对象可进候选带标签"', '全部邻域并印，候选只按政策判，无"边界"预排除也无额外标签'),
]


def out_dir(a):
    """卡 / lineage / P 包：B2 → stageS_dev/registry_b；阶段 S（--real）→ registry/。"""
    return a.out or (M.P('registry') if getattr(a, 'real', False) else M.P('stageS_dev', 'registry_b'))


def rec_dir(a):
    """冻结清单与记录 B：B2 → stageS_dev/registry_b；阶段 S（--real）→ registration/（e6m_s_gate.post_gate 读这里）。"""
    return a.out or (M.P('registration') if getattr(a, 'real', False) else M.P('stageS_dev', 'registry_b'))


def stage_b(a):
    od = out_dir(a)
    os.makedirs(od, exist_ok=True)
    K = M.read_csv_keep(M.P('registry', 'cards_E6m.csv'), dtype=str).fillna('')
    CM = M.read_csv_keep(M.P('registry', 'comparison_manifest_E6m.csv'), dtype=str).fillna('')
    Q = M.read_csv_keep(M.P('registry', 'query_registry_E6m.csv'), dtype=str).fillna('')
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str).set_index('desc_id')
    plan_sha = M.sha_file(M.P('PLAN_COPY.md'))
    pc = M.P('registration', 'counter_explanations_decision_E6m.json')      # ⑬b：决策端补写的反解释（在时进冻结卡的 t09；执行端只照录）
    dec = {e.get('card'): e for e in json.load(open(pc, encoding='utf-8')).get('cards', [])} if os.path.exists(pc) else {}
    rows, lin = [], []
    for k in K.itertuples():
        e = dec.get(k.card) or {}
        if e.get('text'):
            t09, t09s = e['text'], '⑬b 补写（%s，%s；%s sha %s）' % (e.get('role', ''), e.get('date', ''), os.path.basename(pc), M.sha_file(pc)[:16])
        elif str(getattr(k, 'counter_explicit_in_plan', '')).lower() in ('true', '1', 'yes'):
            t09, t09s = k.counter_explanation, 'plan 原文'
        else:
            t09, t09s = k.counter_explanation, 'A0 占位（plan 未单列；⑬b 待决策端）'
        views = [v for v in k.contrast_views_in_manifest.split('|') if v]
        cm = CM[CM.view.isin(views)]
        left = cm.left_desc_id[cm.left_desc_id.isin(D.index)]
        dl = D.loc[left.unique()] if len(left) else D.iloc[:0]
        qs = sorted(Q[Q.card == k.card].query_id)
        kinds = cm.kind.value_counts().to_dict()
        rows.append(dict(card=k.card, card_id=k.card_id, title=k.title, plan_line=k.plan_line, claim_id=k.claim_id, source_version=k.source_version,
                         estimand=k.estimand, unit=k.unit, contrast_views=k.contrast_views_in_manifest, bound_comparisons=int(k.bound_comparisons or 0), manifest_bound=len(cm),
                         bound_by_kind=json.dumps(kinds, ensure_ascii=False), query_ids='|'.join(qs) if qs else 'NOT_APPLICABLE',
                         t01_motivation=k.motivation, t02_prediction=k.prediction, t04_discriminator=k.discriminator, t09_counter=t09, t09_source=t09s,
                         t10_update=k.update_rule, t13_mde80='PENDING_DERIV_MDE80',
                         t15_account='|'.join(sorted(set(dl.parent))) if len(dl) else 'NOT_APPLICABLE',
                         t16_timescale='H' + ','.join(sorted(set(dl.H), key=int)) if len(dl) else 'NOT_APPLICABLE',
                         t17_random='|'.join(sorted(set(dl.e_random_mechanism))) if len(dl) else 'NOT_APPLICABLE',
                         t18_state='|'.join(sorted(set(dl.condition))) if len(dl) else 'NOT_APPLICABLE',
                         card_kind=k.card_kind, frozen_at=time.strftime('%Y-%m-%d %H:%M:%S')))
        lin.append(dict(claim_id=k.claim_id, source_sha=plan_sha[:16], source_section='plan §12 %s（第 %s 行）' % (k.card_id, k.plan_line),
                        verbatim_claim=k.prediction, author_role='规划端（plan v1.1）', status='adopted', test_id='|'.join(views) or 'NOT_APPLICABLE',
                        query_id='|'.join(qs) or 'NOT_APPLICABLE', first_exposure='E6m 推导段（阶段 S）', result_status='PENDING', design_update=''))
    brief_sha = M.sha_file(M.P('handoff_copy', 'E6m_access_form_stage.md')) if os.path.exists(M.P('handoff_copy', 'E6m_access_form_stage.md')) else '1db1924677bd80ed'
    for cid, old, new in A1_SUPERSEDED:
        lin.append(dict(claim_id='E6M-PROPOSAL-' + cid, source_sha='e6a699f8（E6m_proposal.md）', source_section='brief A1', verbatim_claim=old,
                        author_role='proposal（执行前研究起点）', status='superseded', test_id='NOT_APPLICABLE', query_id='NOT_APPLICABLE',
                        first_exposure='NOT_APPLICABLE', result_status='SUPERSEDED_BY_PLAN', design_update=new))
    lin.append(dict(claim_id='E6M-W09', source_sha=brief_sha[:16], source_section='brief W09', verbatim_claim='LAG1_10 作记忆族代表、HG10 别名（E6l REVIEW 文本）',
                    author_role='决策端', status='superseded', test_id='Q01_HG_VS_LAG', query_id='E6M-Q01-a', first_exposure='E6l',
                    result_status='复盘 #110 候选（决策端定号）', design_update='HG10 与 LAG1_10 各自保留身份，主表并排'))
    Cb = pd.DataFrame(rows)
    Lg = pd.DataFrame(lin)
    P = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    Pm = P[(P.is_primary72 == 'True') | (P.block == 'PARENT')][['desc_id', 'block', 'parent', 'primary_recipe', 'H']]
    p1, p2, p3 = (os.path.join(od, f) for f in ('cards_stageB_E6m.csv', 'hypothesis_lineage_E6m.csv', 'P_objects_E6m.csv'))
    M.atomic_write_csv(p1, Cb)
    M.atomic_write_csv(p2, Lg)
    M.atomic_write_csv(p3, Pm)
    bad = Cb[(Cb.query_ids == 'NOT_APPLICABLE') | (Cb.t09_counter.str.len() == 0)]          # 绑定看 query（B3 / B4–B6 / 方法卡的对象在各自机器表，不在比较清单）
    M.write_receipt(os.environ.get('E6M_TASK', 'S_stage_b'), [p1, p2, p3], status='SUCCEEDED' if bad.empty else 'FAILED', code=[__file__, M.__file__],
                    cards=len(Cb), lineage=len(Lg), P_objects=len(Pm), cards_without_binding_or_counter=len(bad))
    print(json.dumps(dict(cards=len(Cb), lineage=len(Lg), P_objects=len(Pm), bad=len(bad)), ensure_ascii=False))
    return 0 if bad.empty else 1


AUTH_S = 'authorization_status_E6m_S.json'          # 阶段 S 的 W11 决定（执行端照录用户原话）；在时取代阶段 N 文件的 w11_mode，阶段 N 文件不改


def auth_status(rd=None):
    """W11 方式：阶段 S 决定文件（registration/ 或开发目录 rd 里）优先，否则阶段 N 的 authorization_status_E6m.json。返回 (dict, 路径)。"""
    for p in ([os.path.join(rd, AUTH_S)] if rd else []) + [M.P('registration', AUTH_S), M.P('registration', 'authorization_status_E6m.json')]:
        if os.path.exists(p):
            return json.load(open(p, encoding='utf-8')), p
    raise RuntimeError('W11 授权状态文件不存在')


def freeze(a):
    """冻结 P / B 两包；方式 B（阶段 S 决定文件 w11_mode = B）时同一步写 record_B_preauthorized_E6m.json
    （brief W11"两包冻结时写"：照录决定文件里的用户原话 + 日期 + 本次冻结清单 sha；已存在不覆盖）。"""
    import e6m_s_gate as GT
    od = out_dir(a)
    rd = rec_dir(a)
    os.makedirs(rd, exist_ok=True)
    auth, auth_p = auth_status(rd if not getattr(a, 'real', False) else None)
    mode = auth.get('w11_mode', 'A')
    reg = [os.path.join(M.P('registry'), f) for f in sorted(os.listdir(M.P('registry'))) if f.endswith(('.csv', '.json'))]
    docs = [os.path.join(od, f) for f in ('cards_stageB_E6m.csv', 'hypothesis_lineage_E6m.csv', 'P_objects_E6m.csv')]
    docs += [M.P('registration', f) for f in ('policy_profiles_E6m_stageN.json', 'a0_manifest_E6m.json', 'authorization_status_E6m.json')]
    docs += [auth_p] if os.path.basename(auth_p) == AUTH_S else []
    docs += [p for p in (M.P('registration', 'counter_explanations_decision_E6m.json'), M.P('registration', 'delegated_decisions_E6m_S.json'))
             if os.path.exists(p)]                                         # ⑬b 补写与 §5 / 签名 1–3 的决定：冻结前定、进清单
    if getattr(a, 'real', False):
        docs += [M.P('registration', f) for f in ('a1_auto_E6m_S.json',)] + [M.P('stage0_S', 'stage0_S_gate.json')]
        docs = [p for p in docs if os.path.exists(p)]
    man = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE, P_package=dict(objects='P_objects_E6m.csv'),
               registry_sha256={os.path.basename(p): M.sha_file(p) for p in reg}, documents_sha256={os.path.basename(p): M.sha_file(p) for p in docs},
               no_returns_read_before=True, w11_mode=mode, w11_status_file=os.path.basename(auth_p))
    p1 = os.path.join(rd, GT.FREEZE)
    pre = os.path.join(rd, GT.AUTH_PRE)
    if getattr(a, 'real', False) and os.path.exists(p1):
        raise RuntimeError('冻结清单已存在（只增不覆盖；语义 amendment 需新授权）')
    if mode == 'B' and getattr(a, 'real', False) and os.path.exists(pre):
        raise RuntimeError('%s 已存在（不覆盖）' % GT.AUTH_PRE)
    if mode == 'B' and not (auth.get('user_quote') and auth.get('user_quote_date')):
        raise RuntimeError('方式 B 决定文件缺用户原话或日期（执行端不代写）')
    M.atomic_write_json(p1, man)
    fsha = M.sha_file(p1)
    rec = dict(written_at=man['written_at'], w11_mode=mode, freeze_manifest=os.path.basename(p1), freeze_sha256=fsha,
               rule='方式 A：推导两段后停等用户对两后段的一句话授权；方式 B：两包冻结时照录用户原话 + 日期 + 清单 sha（执行端不代写）',
               effective_conditions=['Stage 0 全 PASS', 'A1-auto 全 PASS', '进入后段时冻结清单 sha 不变'])
    p2 = os.path.join(rd, 'record_B_mode_%s_E6m.json' % mode)
    M.atomic_write_json(p2, rec)
    outs = [p1, p2]
    if mode == 'B':
        M.atomic_write_json(pre, dict(mode='B', user_quote=auth['user_quote'], user_quote_date=auth['user_quote_date'],
                                      user_message_verbatim=auth.get('user_message_verbatim', auth['user_quote']), question_asked=auth.get('question_asked', ''),
                                      w11_basis=auth.get('w11_basis', ''), status_file=os.path.basename(auth_p), status_file_sha256=M.sha_file(auth_p),
                                      written_at=man['written_at'], written_by='执行端照录用户原话（两包冻结时）', freeze_manifest=GT.FREEZE, freeze_sha256=fsha,
                                      effective_conditions=rec['effective_conditions'], amendment_rule='任何语义 amendment（冻结清单变化）使本授权失效，须重新授权',
                                      scope=auth.get('scope', 'E6m 两后段（2019-2023 / 2024-2026）')))
        outs.append(pre)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_stage_b_freeze'), outs, status='SUCCEEDED', code=[__file__, M.__file__], w11_mode=mode,
                    registry_files=len(reg))
    print(json.dumps(dict(w11_mode=mode, registry_files=len(reg), docs=len(docs), preauthorized=mode == 'B'), ensure_ascii=False))
    return 0


def approve(a):
    """把用户对两后段的授权原话照录成 e6m_s_gate 读的文件（方式 A：推导两段封存之后；方式 B：转交消息里的事前整表授权）。
    执行端只照录用户原话，不代写、不改写；原话或日期为空即拒绝。"""
    import e6m_s_gate as GT
    if not (a.quote.strip() and re.fullmatch(r'\d{4}-\d{2}-\d{2}', a.date or '')):
        raise RuntimeError('授权记录需要用户原话与日期（YYYY-MM-DD）')
    fz = M.P('registration', GT.FREEZE)
    if not os.path.exists(fz):
        raise RuntimeError('冻结清单不存在：先 freeze --real')
    if a.mode == 'A':
        sd = M.P('seal_deriv.json')
        if not (os.path.exists(sd) and json.load(open(sd, encoding='utf-8')).get('all_ok')):
            raise RuntimeError('方式 A：推导两段封存（seal_deriv all_ok）之后才登记用户对两后段的授权')
    name = GT.AUTH_APPROVED if a.mode == 'A' else GT.AUTH_PRE
    p = M.P('registration', name)
    if os.path.exists(p):
        raise RuntimeError('%s 已存在（不覆盖）' % name)
    M.atomic_write_json(p, dict(mode=a.mode, user_quote=a.quote, user_quote_date=a.date, written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
                                written_by='执行端照录用户原话', freeze_manifest=GT.FREEZE, freeze_sha256=M.sha_file(fz),
                                scope='E6m 两后段（2019-2023 / 2024-2026）：确定性 + 随机 + 增补 + 全段统计 / 政策 / bootstrap / 分解'))
    M.write_receipt(os.environ.get('E6M_TASK', 'S_record_B_%s' % a.mode), [p], status='SUCCEEDED', code=[__file__, M.__file__])
    print(json.dumps(dict(written=name, mode=a.mode), ensure_ascii=False))
    return 0


def conditions(a):
    """授权生效条件回执（post_gate 读）：Stage 0 S 门 all_pass ∧ A1-auto（S）all_pass；冻结清单 sha 记下，进入后段时 post_gate 逐次比。"""
    import e6m_s_gate as GT
    g = M.P('stage0_S', 'stage0_S_gate.json')
    a1 = M.P('registration', 'a1_auto_E6m_S.json')
    fz = M.P('registration', GT.FREEZE)
    G = json.load(open(g, encoding='utf-8')) if os.path.exists(g) else {}
    A1 = json.load(open(a1, encoding='utf-8')) if os.path.exists(a1) else {}
    a1_ok, rc2 = bool(A1.get('all_pass')), M.P('registration', 'a1_auto_item2_reconciliation_E6m_S.json')
    if not a1_ok and os.path.exists(rc2):      # 只剩第 2 项 FAIL 且人工逐句核记录在案、绑定当前 a1_auto / 转录件 sha（用户 2026-10-11 原话放行；冻结件不改）
        R2 = json.load(open(rc2, encoding='utf-8'))
        np_ = A1.get('not_pass', [])
        a1_ok = (len(np_) == 1 and str(np_[0].get('item')) == '2' and R2.get('verdict') == 'PASS' and bool(R2.get('user_quote'))
                 and bool(R2.get('user_quote_date')) and R2.get('a1_auto_sha256') == M.sha_file(a1)
                 and R2.get('transcription_sha256') == M.sha_file(M.P('registration', 'policy_profiles_E6m_stageN.json')))
    ok = bool(G.get('all_pass')) and a1_ok and os.path.exists(fz)
    rec = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), all_pass=ok, stage0_S_all_pass=bool(G.get('all_pass')),
               stage0_S_not_pass=dict(fail=G.get('fail_items', []), wait=G.get('source_wait_items', []), not_run=G.get('not_run_items', [])),
               a1_auto_all_pass=bool(A1.get('all_pass')), a1_auto_not_pass=A1.get('not_pass', []),
               a1_auto_effective_pass=a1_ok, a1_auto_item2_reconciliation=M.rel(rc2) if os.path.exists(rc2) else '',
               frozen_manifest_sha256=M.sha_file(fz) if os.path.exists(fz) else '')
    p = M.P('registration', GT.AUTH_COND)
    M.atomic_write_json(p, rec)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_record_B_conditions'), [p], status='SUCCEEDED', code=[__file__, M.__file__], all_pass=ok)
    print(json.dumps(dict(all_pass=ok, stage0=rec['stage0_S_all_pass'], a1_auto=rec['a1_auto_all_pass'], a1_effective=a1_ok), ensure_ascii=False))
    return 0


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['stage-b', 'freeze', 'approve', 'conditions'])
    ap.add_argument('--out', default='')
    ap.add_argument('--real', action='store_true', help='阶段 S：卡等写 registry/，冻结与记录 B 写 registration/')
    ap.add_argument('--mode', default='A', choices=['A', 'B'])
    ap.add_argument('--quote', default='')
    ap.add_argument('--date', default='')
    a = ap.parse_args()
    sys.exit({'stage-b': stage_b, 'freeze': freeze, 'approve': approve, 'conditions': conditions}[a.task](a))
