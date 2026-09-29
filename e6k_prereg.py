# -*- coding: utf-8 -*-
"""E6k 事前登记（brief §1.4 / §3 / W15；plan §3.1 / §8 / §9 / §11 / §13.2）：两个登记包在任何新收益读取前同时落盘。
  registry/selection_exposure_ledger_E6k.csv  逐描述符暴露：same_account_exposed（与 E6j P / E6j B / E6i 已登记账户逐条匹配；R1 ≡ A4b_CVRv5）/
      related_exposed（同测量同方向在别的母体 / 参数上见过）/ new_combination / first_evaluation（新算子）/ source_parent
      （descriptors_E6k.csv 的 evidence_exposure 列是编译器按测量名的粗分类；逐账户暴露以本台账为准）
  registry/P_objects_E6k.csv                  P 包对象 = 144 主展示 + 4 C1_hi + 6 SM 锚 + 8 母体全部 H（PARENT）
  registry/hypothesis_lineage_E6k.csv         plan §3.1 字段：claim_id / author_role / exact_text / source_sha / source_section /
      status（adopted / superseded）/ brief_id / executed_test_id / outcome_query / exposure
  registration/preregistration_P_E6k.md / preregistration_B_E6k.md / P_package_manifest_E6k.json / B_package_manifest_E6k.json
不读任何收益。"""
import e6k_boot  # noqa: F401
import os
import sys
import json

import numpy as np
import pandas as pd

import e6k_core as K

E6J_MOTHER = {'A4b_CVRv5': 'R1', 'R2': 'R2', 'A06': 'A06'}
MID = {'S': ('K_rar20', 'low_bad'), 'M': ('K_slope20', 'low_bad'), 'C1': ('K_MA3_E6F', 'high_bad'), 'Q': ('J_B1_qCC', 'low_bad'),
       'RARPRE20_LT': ('J_B5_RARPRE_CC_W20_LT', 'low_bad'), 'RARPRE60_LT': ('J_B5_RARPRE_CC_W60_LT', 'low_bad'),
       'RARPRE20_SE': ('J_B5_RARPRE_CC_W20_SE', 'low_bad'), 'RARPRE60_SE': ('J_B5_RARPRE_CC_W60_SE', 'low_bad')}
PROPOSAL_CARDS = [  # E6k_proposal.md §5.5（L250–L260）→ plan 取代卡
    ('P-Q1', 250, 'E6k-Q1 size 中性接入', 'Q02|Q03|Q04'), ('P-Q2', 251, 'E6k-Q2 层 vs 层内', 'Q05|Q06'),
    ('P-Q3', 252, 'E6k-Q3 滞后带', 'Q09|Q10|Q11'), ('P-Q4', 253, 'E6k-Q4 测量 × 绑定环节地图', 'Q14'),
    ('P-Q5', 254, 'E6k-Q5 并集核 M 首看', 'Q15'), ('P-Q6', 255, 'E6k-Q6 均值核 C1 首看', 'Q15'),
    ('P-Q7', 256, 'E6k-Q7 q 是否比 S 干净', 'Q12'), ('P-Q8', 257, 'E6k-Q8 C1 高剂量长持有', 'Q01|Q17'),
    ('P-Q9', 258, 'E6k-Q9 衰减分解', 'Q16'), ('P-Q10', 259, 'E6k-Q10 六条的选择性', 'Q17'), ('P-Q11', 260, 'E6k-Q11 方法', 'Q18')]
PROPOSAL_PRED = [('P-B2', 229, 'Q02|Q03'), ('P-B4', 231, 'Q12'), ('P-B5', 232, 'Q09|Q10|Q11')]


def exposure(D):
    """逐描述符与 E6j P / E6j B / E6i SLOT FALLBACK 已登记账户匹配。"""
    ej = K.E6J_RES
    P = pd.read_csv(os.path.join(ej, 'registry', 'descriptors_P.csv'))
    B = pd.read_csv(os.path.join(ej, 'registry', 'descriptors_B.csv'))
    I = pd.read_csv(os.path.join(K.E6I_RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    I = I[(I.role == 'SLOT') & (I.policy == 'FALLBACK') & I.route_id.isin(['RK', 'RA'])]
    keyP = {}
    for r in P.itertuples():
        keyP[(r.form, r.arm, str(r.member), round(float(r.alpha), 6), int(r.H))] = r.descriptor_id
    keyB = {}
    for r in B.itertuples():
        keyB[(r.mother, r.slot, r.measurement_id, r.direction, round(float(r.alpha), 6), int(r.H))] = r.descriptor_id
    keyI = {}
    for r in I.itertuples():
        try:
            keyI[(r.mother_id, r.member_id, r.direction, round(float(r.strength), 6), int(r.H))] = r.descriptor_id
        except (TypeError, ValueError):
            continue
    seenB = set((m, d) for (_, _, m, d, _, _) in keyB)
    seenI = set((m, d) for (_, m, d, _, _) in keyI)
    seenP = set((arm, mem) for (_, arm, mem, _, _) in keyP)
    rows = []
    for r in D.itertuples():
        f, p, a, h, op = r.meas, r.mother, round(float(r.alpha), 6), int(r.H), r.op
        hits = []
        if op == 'PARENT':
            rows.append(dict(desc_id=r.desc_id, exposure_type='source_parent', same_account_ids='', segments_seen='2010-2014|2015-2018|2019-2023|2024-2026',
                             note='源母体（E5a / E6i / E6j 锚）'))
            continue
        if op != 'NATIVE':
            rows.append(dict(desc_id=r.desc_id, exposure_type='first_evaluation', same_account_ids='', segments_seen='',
                             note=K.LABEL_FIRST_LOOK))
            continue
        if f == 'SM':
            k = keyP.get((p, 'SM', 'K_rar20+K_slope20', a, h))
            hits += ['E6j_P:' + k] if k else []
        elif f in MID:
            mid, d = MID[f]
            if f in ('S', 'M', 'C1'):
                k = keyP.get((p, f, mid, a, h))
                if k:
                    hits.append('E6j_P:' + k)
            if p in E6J_MOTHER:
                k = keyB.get((E6J_MOTHER[p], 'K', mid, d, a, h))
                if k:
                    hits.append('E6j_B:' + k)
                k = keyI.get((E6J_MOTHER[p], mid, d, a, h))
                if k:
                    hits.append('E6i:' + k)
        if hits:
            et = 'same_account_exposed'
            note = '同一账户已算已读（R1 ≡ A4b_CVRv5）'
        else:
            mid, d = MID.get(f, (f, ''))
            rel = ((mid, d) in seenB) or ((mid, d) in seenI) or ((f, mid) in seenP) or (f == 'SM')
            et = 'related_exposed' if rel else 'new_combination'
            note = '同测量同方向在别的母体 / 参数上已见；本账户未算' if rel else '本测量在此母体上从未计算'
        rows.append(dict(desc_id=r.desc_id, exposure_type=et, same_account_ids='|'.join(hits),
                         segments_seen='2010-2014|2015-2018|2019-2023|2024-2026' if hits else '', note=note))
    return pd.DataFrame(rows)


def main():
    reg = K.P('registry')
    rgn = K.P('registration')
    D = pd.read_csv(os.path.join(reg, 'descriptors_E6k.csv'))
    A = pd.read_csv(os.path.join(reg, 'accessory_E6k.csv'))
    RR = pd.read_csv(os.path.join(reg, 'randoms_E6k.csv'))
    C = pd.read_csv(os.path.join(reg, 'cards_E6k.csv'))
    Qy = pd.read_csv(os.path.join(reg, 'query_registry_E6k.csv'))
    plan_sha = K.sha_file(K.P('PLAN_COPY.md'))
    prop = open(os.path.join(K.CODE, 'exec_briefs', 'E6k_proposal.md'), encoding='utf-8').read().split('\n')
    prop_sha = K.sha_file(os.path.join(K.CODE, 'exec_briefs', 'E6k_proposal.md'))
    # ---- 暴露台账
    X = exposure(D)
    px = os.path.join(reg, 'selection_exposure_ledger_E6k.csv')
    K.atomic_write_csv(px, X)
    # ---- P 对象
    Pm = D[D.primary144 | D.c1_hi | D.sm_anchor | (D.op == 'PARENT')][['desc_id', 'meas', 'mother', 'alpha', 'H', 'op', 'primary144', 'c1_hi', 'sm_anchor']]
    pp = os.path.join(reg, 'P_objects_E6k.csv')
    K.atomic_write_csv(pp, Pm)
    # ---- 假设血缘
    lin = []
    q2o = pd.read_csv(os.path.join(reg, 'question_to_objects_E6k.csv'))
    for r in C.itertuples():
        body = r.text
        hyp = body.split('**工作假设：**')[1].split('**')[0].strip() if '**工作假设：**' in body else body[:200]
        objs = set(q2o.desc_id[q2o.query_id.str.startswith('E6K-%s-' % r.card)])
        ex = X[X.desc_id.isin(objs)].exposure_type.value_counts().to_dict()
        lin.append(dict(claim_id='E6K-%s' % r.card, author_role='web_plan_v1.1', exact_text=hyp, source_sha=plan_sha,
                        source_section='PLAN_COPY.md §11 L%d–L%d' % (r.plan_line, r.plan_line + 1), status='adopted', brief_id='W01',
                        executed_test_id=r.queries, outcome_query=r.queries, exposure=json.dumps(ex, ensure_ascii=False)))
    for cid, ln, title, repl in PROPOSAL_CARDS:
        lin.append(dict(claim_id=cid, author_role='decision_side_proposal', exact_text=prop[ln - 1][:600], source_sha=prop_sha,
                        source_section='E6k_proposal.md §5.5 L%d（%s）' % (ln, title), status='superseded',
                        brief_id='W01（plan §3.1 / §3.3 / §14 取代；proposal 为参考输入）', executed_test_id='',
                        outcome_query='|'.join('E6K-%s-a' % q for q in repl.split('|')), exposure='见取代卡'))
    for cid, ln, repl in PROPOSAL_PRED:
        lin.append(dict(claim_id=cid, author_role='decision_side_proposal', exact_text=prop[ln - 1][:600], source_sha=prop_sha,
                        source_section='E6k_proposal.md §4 L%d' % ln, status='superseded',
                        brief_id='W01（plan §3.3：不要求没有数据依据的留存 / 重叠 / 降换手数字）', executed_test_id='',
                        outcome_query='|'.join('E6K-%s-a' % q for q in repl.split('|')), exposure='见取代卡'))
    L = pd.DataFrame(lin)
    pl = os.path.join(reg, 'hypothesis_lineage_E6k.csv')
    K.atomic_write_csv(pl, L)
    # ---- 登记文档
    man_a0 = json.load(open(os.path.join(rgn, 'a0_manifest_E6k.json'), encoding='utf-8'))
    cnt = man_a0['counts']
    exc = X.exposure_type.value_counts().to_dict()
    pr = json.load(open(os.path.join(rgn, 'policy_profiles_E6k.json'), encoding='utf-8'))
    P_md = ['# E6k preregistration_P（P 包：固定展示与源锚；任何新收益读取前落盘）', '',
            '用途：冻结 plan §8.2 的 144 行主展示、四条 C1_hi、六条 SM 交互锚、八母体（PARENT 全 H），以及 §9 政策 profile 全文与暴露台账；'
            '本包与 B 包同时冻结（brief §1.4），后段按 E6k 自身授权（方式 A：registration/record_B_mode_A.json）。', '',
            '## 1. 身份', '- PLAN_COPY.md sha256 `%s`；brief `8be4df3d`；附录 `2258b2c6`；A0 清单 `registration/a0_manifest_E6k.json`（与 plan §16.3 compile_design 逐元组相等）' % plan_sha,
            '- 执行端补充（读数前）：`registration/executor_supplements_E6k.json` + `executor_supplements_E6k_amend_1.json`', '',
            '## 2. 对象（`registry/P_objects_E6k.csv`，%d 个描述符 / 段）' % len(Pm),
            '- 144 主展示 = 六生产形态 × 四测量（S / M / Q / C1）× 六接入（NATIVE、SZL5、INC1、RP3、NATIVE_HG10、INC1_HG10），统一 α .25 × H5',
            '- 四条 C1_hi = C1 × {A4b, A4b_CVRv5} × α .5 × H{10, 20}（NATIVE；另印同 H 父与生产 H5 双参照）',
            '- 六条 SM 锚 = SM（S / M 各半，FALLBACK 双分量）× 六形态 × α .25 × H5', '- 八母体 PARENT × H1…20（源锚）', '',
            '## 3. 政策（`registration/policy_profiles_E6k.json` 全文；policy_provisional = true）', '```json', json.dumps(pr, ensure_ascii=False, indent=1), '```', '',
            '## 4. 暴露（`registry/selection_exposure_ledger_E6k.csv`；逐账户匹配 E6j P / B 与 E6i SLOT FALLBACK）',
            '- P 包内：%s' % json.dumps(X[X.desc_id.isin(Pm.desc_id)].exposure_type.value_counts().to_dict(), ensure_ascii=False),
            '- 新算子标签 `%s`；原生对象按台账（same_account_exposed = 同一账户已算已读，不增加独立证据次数）。' % K.LABEL_FIRST_LOOK,
            '- 注：`descriptors_E6k.csv` 的 evidence_exposure 列是编译器按测量名粗分类，逐账户暴露以本台账为准。', '',
            '## 5. 相关卡片', ] + ['- **E6K-%s** %s（PLAN_COPY L%d；queries %s）' % (r.card, r.title.split('｜', 1)[-1], r.plan_line, r.queries)
                                 for r in C.itertuples() if r.card in ('Q01', 'Q12', 'Q14', 'Q15', 'Q17')]
    B_md = ['# E6k preregistration_B（B 包：全部其他接入 / 机制 / 对照；任何新收益读取前落盘）', '',
            '用途：冻结 plan §5–§8、§10 的全部研究描述符（编译器现算）、附属清单、随机与 bootstrap 登记、18 张卡原文与假设血缘；设计全文 = PLAN_COPY.md（sha `%s`）。' % plan_sha, '',
            '## 1. 计数（`registration/a0_manifest_E6k.json`）',
            '- 每段原始账户描述符 **%d**（块计数 %s）；目标（与 H 无关）%d；144 主展示唯一存在；与 plan §16.3 compile_design 逐元组 / 块集合相等' % (
                cnt['raw_id_count'], json.dumps(cnt['block_counts'], ensure_ascii=False), cnt['target_count']),
            '- 附属：INC 同支持 / 同剂量 %d；BAND 剂量控制 %d；COMMON_SUPPORT 子 %d / 父 %d；影子账户对象 %d；bootstrap 比较 %d' % (
                cnt['accessory_INC'], cnt['band_dose_controls'], cnt['cs_children'], cnt['cs_parents'], cnt['shadow_accounts'], cnt['bootstrap_comparisons']),
            '- 随机：%s（`registry/randoms_E6k.csv`；首 1,024 路径，MCSE ≤ .03 按 512 增补至 8,192）' % json.dumps(RR.mechanism.value_counts().to_dict(), ensure_ascii=False),
            '- 暴露：%s' % json.dumps(exc, ensure_ascii=False), '',
            '## 2. 设计全文引用（PLAN_COPY.md 行号，逐字以原文为准）',
            '- §5 接入算子 L218–L284；§6 层配置 L285–L337；§7 SA / PM / HG L338–L382；§8 范围与参数 L383–L444；§9 政策 L445–L490；§10 随机 / 风险 / 时间 L491–L560；§12 资本 / 成本 / 库存 L620–L657；§13 执行与冻结 L658–L721', '',
            '## 3. 18 张卡（原文逐字；`registry/cards_E6k.csv`）'] + sum([['### E6K-%s（PLAN_COPY L%d）' % (r.card, r.plan_line), r.title, '', r.text, '',
                                                                    '- queries：%s' % r.queries, ''] for r in C.itertuples()], []) + [
            '## 4. 假设血缘（`registry/hypothesis_lineage_E6k.csv`）',
            '- plan 18 卡 adopted（W01）；proposal §5.5 的 11 卡与 §4 三条预测 superseded（plan §3.1 / §3.3 / §14；proposal 是参考输入）', '',
            '## 5. 读数与授权边界',
            '- 推导两段（2010-2014 / 2015-2018）全部 P / B 算完 → `seal_deriv.json` → part1 + 记录 B 草稿 → 方式 A 停等用户（后段任何新对象计算前 `e6k_core.post_gate`）',
            '- 不按推导段收益预筛或改网格；不在出数后选 profile / 随机机制 / bootstrap 块长；新算子不自动 chosen；任何语义 amendment 使后段授权失效（W11）']
    pP = os.path.join(rgn, 'preregistration_P_E6k.md')
    pB = os.path.join(rgn, 'preregistration_B_E6k.md')
    K.atomic_write_text(pP, '\n'.join(P_md) + '\n')
    K.atomic_write_text(pB, '\n'.join(B_md) + '\n')
    reg_files = sorted(f for f in os.listdir(reg) if f.endswith('.csv'))
    regsha = {f: K.sha_file(os.path.join(reg, f)) for f in reg_files}
    docs = {f: K.sha_file(os.path.join(rgn, f)) for f in ('executor_supplements_E6k.json', 'executor_supplements_E6k_amend_1.json',
                                                         'policy_profiles_E6k.json', 'record_B_mode_A.json', 'a0_manifest_E6k.json')}
    docs.update({f: K.sha_file(K.P(f)) for f in ('PLAN_COPY.md', 'engine_contract.md', 'source_resolution.md', 'source_manifest.json')})
    now = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    for nm, md, objs in (('P', pP, int(len(Pm))), ('B', pB, int(len(D) - len(Pm)))):
        K.atomic_write_json(os.path.join(rgn, '%s_package_manifest_E6k.json' % nm),
                            dict(package=nm, written_at=now, version=K.VERSION, preregistration=os.path.basename(md), preregistration_sha256=K.sha_file(md),
                                 registry_sha256=regsha, registration_docs_sha256=docs, objects_per_segment=objs,
                                 authorization='方式 A（record_B_mode_A.json）：后段须用户一句话后 record_B_approved_E6k.json + 条件回执',
                                 no_returns_read_before=True))
    K.write_receipt('prereg_packages', [pP, pB, px, pp, pl, os.path.join(rgn, 'P_package_manifest_E6k.json'), os.path.join(rgn, 'B_package_manifest_E6k.json')],
                    'SUCCEEDED', P_objects=int(len(Pm)), exposure=exc)
    print('P %d / B %d；暴露 %s；血缘 %d 行' % (len(Pm), len(D) - len(Pm), exc, len(L)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
