# -*- coding: utf-8 -*-
"""E6k 记录 B（brief §5 / W11；E6j e6j_a1_auto 草稿 / 条件回执同式）。
  --draft               part1 之后：reports/E6k_record_B_draft.md + registration/record_B_draft_objects_E6k.csv（逐描述符：exposure / 机制重要性 /
                        有效支持 / 推导读数 / 未解决限制；不设"推导中位 ≤ 0 不进"的门）；A1-auto 第 7 项（草稿字段齐）写 a1_auto_draft_E6k.json
  --approve "<原话>" --date YYYY-MM-DD [--note "<背景>"]
                        方式 A 下用户一句话后执行：registration/record_B_approved_E6k.json（引原话、日期、冻结清单 sha、闭包）；不自动执行
  --conditions          生效条件：Stage 0 六类全 PASS + A1-auto（pre / masks / draft）全 PASS + 冻结清单 B_package_manifest_E6k.json sha 未变
                        → registration/record_B_conditions_receipt_E6k.json（all_pass 才解锁 e6k_core.post_gate）"""
import e6k_boot  # noqa: F401
import os
import sys
import json

import numpy as np
import pandas as pd

import e6k_core as K

FAMILY_LIMITS = {
    'NATIVE': '原生对象：推导段读数与 E6i / E6j 已见账户同一（same_account_exposed 不增加独立证据次数）',
    'SZL': '条件排名：旧 K 不重处理；组内人群 = kf ∧ k0 ∧ z_T；与 SZL_OWN 并读；不保证组合层 size 中性',
    'OWN': '旧 K 复制控制：同分组同掩码；作 SZL 的处理成本基线，不是候选',
    'INC': '只投影新增评分（C 外 d = 0）；γ0 = INC_SUPPORT0 支持桥；INC_DOSE 同均值同 RMS 对照',
    'RP': '固定规范配对集内的最小修复（非全局最优编辑）；父 N 与行业人数保持；未配对的结构性编辑不执行',
    'LX': '配额 / 优先序移植（E6j matched_n 同 N 合同键）；非 DGTW AS 公式；A4b 的 T 重估不是固定共同门',
    'BAND': 'SA / PM / HG：b 以 K 腿单位（mean 门 b/3）；HG 状态段首空、按列递推；剂量控制只在四 owner',
    'HG_ONLY': '旧 K 上的续选规则（α0 不读新测量）；信息 × 规则四账户的 V01',
    'TREFIT': 'A4b 第二关 T 系数插值；g ∈ (0,1) 无合法同一模型的日子沿新原生模型（COEF_INTERP_UNAVAILABLE）',
    'POST2': 'A4b 第二关前加入局部新增坏度（共同支持）；α0 ≡ 父',
    'PARENT': '源母体',
}


def draft():
    M = pd.read_csv(K.P('results', 'deriv', 'descriptor_stats_deriv_merged.csv'))
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    X = pd.read_csv(K.P('registry', 'selection_exposure_ledger_E6k.csv'))
    q2o = pd.read_csv(K.P('registry', 'question_to_objects_E6k.csv'))
    MF = pd.read_csv(K.P('registry', 'mask_facts_deriv_E6k.csv'))
    cards = q2o.assign(card=q2o.query_id.str[4:7]).groupby('desc_id').card.apply(lambda s: '|'.join(sorted(set(s))))
    flags = MF.dropna(subset=['flags']).groupby('target_id').flags.apply(lambda s: '|'.join(sorted(set('|'.join(s).split('|')) - {''})))
    rows = []
    Dm = D.merge(X[['desc_id', 'exposure_type']], on='desc_id', how='left')
    Mi = M.set_index('desc_id')
    for r in Dm.itertuples():
        m = Mi.loc[r.desc_id] if r.desc_id in Mi.index else None
        imp = 'main_display' if (r.primary144 or r.c1_hi or r.sm_anchor) else ('source_parent' if r.op == 'PARENT' else
                                                                             ('control' if r.family in ('OWN', 'HG_ONLY') else 'research_grid'))
        rows.append(dict(desc_id=r.desc_id, exposure=r.exposure_type, mechanism_importance=imp, cards=cards.get(r.desc_id, ''),
                         effective_support_days=float(m['n']) if m is not None else np.nan,
                         D_2010_2014=float(m['D_2010-2014']) if m is not None else np.nan, D_2015_2018=float(m['D_2015-2018']) if m is not None else np.nan,
                         D_deriv=float(m['D']) if m is not None else np.nan, se_H=float(m['se_H']) if m is not None else np.nan,
                         D_vs_native=float(m['D_vs_native']) if (m is not None and 'D_vs_native' in m.index) else np.nan,
                         mask_flags=flags.get(r.target_id, ''), unresolved_limits=FAMILY_LIMITS.get(r.family, ''),
                         post_segments='待授权（方式 A）', gate_note='不设推导中位 ≤ 0 不进的门'))
    Dr = pd.DataFrame(rows)
    p = K.P('registration', 'record_B_draft_objects_E6k.csv')
    K.atomic_write_csv(p, Dr)
    need = ['exposure', 'mechanism_importance', 'effective_support_days', 'D_deriv', 'unresolved_limits']
    nonpar = Dr.mechanism_importance != 'source_parent'                  # PARENT 行没有"子 − 父"推导读数（源锚本身）
    miss = {c: int(Dr.loc[nonpar, c].isna().sum()) for c in need}
    ok = all(v == 0 for v in miss.values())
    a1 = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), stage='draft', item=7, all_pass=bool(ok), missing=miss)
    K.atomic_write_json(K.P('registration', 'a1_auto_draft_E6k.json'), a1)
    md = ['# E6k 记录 B 草稿（方式 A：推导两段算完、封存；后段等用户一句话）', '',
          '用途：brief §5 / W11。授权对象 = 冻结清单（`registration/B_package_manifest_E6k.json` + `P_package_manifest_E6k.json`）全部描述符 × 两后段 + '
          '其 COMMON_SUPPORT / 同资本 / 随机 / 附属对照闭包；逐对象字段见 `registration/record_B_draft_objects_E6k.csv`（%d 行）。' % len(Dr), '',
          '- 生效条件：Stage 0 六类全 PASS（source_manifest）+ A1-auto（pre / masks / draft）全 PASS + 进入后段时冻结清单 sha 不变（`--conditions` 回执）',
          '- 用户动作：一句话批准（或"B"事前整表授权）→ 执行端写 `record_B_approved_E6k.json`（引原话与日期）→ 条件回执 → 两后段同版本一次算完 → seal_post',
          '- 草稿不含门：不设"推导中位 ≤ 0 不进"；新算子不 chosen；deployment_authorized = false', '',
          '| 机制重要性 | 描述符数 | 暴露分布 |', '|---|---|---|']
    for imp, g in Dr.groupby('mechanism_importance'):
        md.append('| %s | %d | %s |' % (imp, len(g), json.dumps(g.exposure.value_counts().to_dict(), ensure_ascii=False)))
    md += ['', 'A1-auto 第 7 项（草稿字段齐，PARENT 源锚行除外）：%s（缺失计数 %s）' % ('PASS' if ok else 'FAIL', json.dumps(miss))]
    K.atomic_write_text(K.P('reports', 'E6k_record_B_draft.md'), '\n'.join(md) + '\n')
    K.write_receipt('record_b_draft', [p, K.P('reports', 'E6k_record_B_draft.md'), K.P('registration', 'a1_auto_draft_E6k.json')],
                    'SUCCEEDED' if ok else 'FAILED', rows=len(Dr))
    print('草稿 %d 行；A1-auto 第 7 项 %s' % (len(Dr), 'PASS' if ok else 'FAIL'), flush=True)
    return 0 if ok else 2


def approve(quote, date, note=''):
    p = K.P('registration', 'record_B_approved_E6k.json')
    if os.path.exists(p):
        raise RuntimeError('已存在批准文件（只增不删）')
    man = K.P('registration', 'B_package_manifest_E6k.json')
    rec = dict(approval_id='E6K-RECORD-B-APPROVED-%s' % date.replace('-', ''), mode='A：推导段封存后用户一句话批准', user_quote=quote,
               user_quote_date=date, frozen_manifest='registration/B_package_manifest_E6k.json', frozen_manifest_sha256=K.sha_file(man),
               frozen_manifest_P_sha256=K.sha_file(K.P('registration', 'P_package_manifest_E6k.json')), post_segments=list(K.POST_SEGS),
               closure='全部 P / B 描述符 × 两后段；COMMON_SUPPORT 子 / 父、同资本、随机（全部登记机制）、附属对照与诊断',
               amendments_sha256={os.path.basename(f): K.sha_file(f) for f in sorted(__import__('glob').glob(K.P('registration', '*amend*')))},
               context_note=note, written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'))
    K.atomic_write_json(p, rec)
    print('写入', K.rel(p))
    return 0


def conditions():
    sm = json.load(open(K.P('source_manifest.json'), encoding='utf-8'))
    a1 = [bool(json.load(open(K.P('registration', f), encoding='utf-8')).get('all_pass', False)) for f in ('a1_auto_E6k.json', 'a1_auto_draft_E6k.json')]
    a1.append(os.path.exists(K.P('registration', 'a1_auto_masks_E6k.json')))
    pre_ok = os.path.exists(K.P('registration', 'record_B_approved_E6k.json')) or os.path.exists(K.P('registration', 'record_B_preauthorized_E6k.json'))
    auth = json.load(open(K.P('registration', 'record_B_approved_E6k.json' if os.path.exists(K.P('registration', 'record_B_approved_E6k.json'))
                              else 'record_B_preauthorized_E6k.json'), encoding='utf-8')) if pre_ok else {}
    man_sha = K.sha_file(K.P('registration', 'B_package_manifest_E6k.json'))
    same = auth.get('frozen_manifest_sha256') == man_sha
    ok = bool(sm['stage0_all_pass'] and all(a1) and pre_ok and same)
    rec = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), all_pass=ok, stage0_all_pass=sm['stage0_all_pass'], a1_auto=a1,
               authorization_present=pre_ok, frozen_manifest_sha256=man_sha, manifest_unchanged=same)
    K.atomic_write_json(K.P('registration', 'record_B_conditions_receipt_E6k.json'), rec)
    print(json.dumps(rec, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == '__main__':
    a = sys.argv
    if '--draft' in a:
        sys.exit(draft())
    if '--approve' in a:
        sys.exit(approve(a[a.index('--approve') + 1], a[a.index('--date') + 1], a[a.index('--note') + 1] if '--note' in a else ''))
    if '--conditions' in a:
        sys.exit(conditions())
    raise SystemExit('用法：--draft | --approve "<原话>" --date YYYY-MM-DD | --conditions')
