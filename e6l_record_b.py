# -*- coding: utf-8 -*-
"""E6l 记录 B（brief §5 / W11；方式 B）。
  --draft        part1 之后：reports/E6l_record_B_draft.md + registration/record_B_draft_objects_E6l.csv（逐描述符：exposure / 机制重要性 /
                 卡 / 推导段有效支持 / 推导读数 / Stage A flags / 未解决限制；不设"推导中位 ≤ 0 不进"的门）；A1-auto 草稿项 → a1_auto_draft_E6l.json
  --entry-post   进入后段前的条件核验（方式 B 生效条件）：Stage 0 全 PASS + A1-auto（pre / 草稿）全 PASS + 冻结 B 包清单 sha 未变 + seal_deriv 核对通过
                 → registration/record_B_entry_post_E6l.json（后段链启动前必须 all_pass；原条件回执不改）"""
import e6l_boot  # noqa: F401
import os
import sys
import json

import numpy as np
import pandas as pd

import e6l_core as L

FAMILY_LIMITS = {
    'PARENT': '源母体（锚）',
    'NATIVE': '原生测量（Q0 / C1 / S / M）：与 E6k 同构者为 SECOND_EVALUATION_SAME_HISTORY，只作锚与基线',
    'SMOOTH': 'Q 平滑 / 秩族：raw 只在形成日 T 做一次源中性化 + 方向 + 秩；有效数 ≥ ceil(.6k) 且当前 d 有效；缺失回旧 K（FALLBACK）',
    'HG': '递归选择记忆（b 以 K 坏度百分位点；Mmean b/3）；状态段首空、按列递推；HG20 / 30 为搜索边界端点',
    'MEMORY': 'LAG1（非递归）/ DECAY（L 2 / 5 重确认衰减）/ INV（按 H 独立递推的库存身份）；INV 同资本另有 INV_LOOP 诊断（不进正式 FULL_sc）',
    'STATE': 'Vol3 PIT 状态调度（UNKNOWN → b10；段 1 前 186 日 UNKNOWN）；STRICT250 对照 96 项',
    'OLD_RULE': '旧 K 上的规则（α0 不读新测量；NO_NEW_CONTENT_TO_PERMUTE）',
}


def draft():
    M = pd.read_csv(L.P('results', 'deriv', 'descriptor_stats_deriv_merged.csv'), keep_default_na=False, na_values=[''])
    D = L.read_csv_keep(L.P('registry', 'descriptors_E6l.csv'))
    q2o = L.read_csv_keep(L.P('registry', 'question_to_objects_E6l.csv'))
    MF = pd.read_csv(L.P('results', 'stage_a', 'mask_facts_deriv_E6l.csv'), keep_default_na=False, na_values=[''])
    cards = q2o.assign(card=q2o.query_id.str[4:7]).groupby('desc_id').card.apply(lambda s: '|'.join(sorted(set(s))))
    flags = MF.groupby('target_id')['flags'].apply(lambda s: '|'.join(sorted(set('|'.join(s.astype(str)).split('|')) - {'', 'NONE'})) or 'NONE')
    Mi = M.set_index('desc_id')
    rows = []
    for r in D.itertuples():
        m = Mi.loc[r.desc_id] if r.desc_id in Mi.index else None
        imp = 'main_display' if r.primary72 else ('dose_panel' if r.dose72 else ('neighborhood' if r.nbhd72 else
                                                                              ('source_parent' if r.family == 'PARENT' else
                                                                               ('control' if r.family == 'OLD_RULE' else 'research_grid'))))
        rows.append(dict(desc_id=r.desc_id, exposure=r.evidence_exposure, mechanism_importance=imp, cards=cards.get(r.desc_id, 'NONE'),
                         effective_support_days=float(m['n']) if m is not None else np.nan,
                         D_2010_2014=float(m['D_2010-2014']) if m is not None else np.nan, D_2015_2018=float(m['D_2015-2018']) if m is not None else np.nan,
                         D_deriv=float(m['D']) if m is not None else np.nan, se_H=float(m['se_H']) if m is not None else np.nan,
                         mask_flags=flags.get(r.target_id, 'NONE'), unresolved_limits=FAMILY_LIMITS.get(r.family, ''),
                         post_segments='方式 B（record_B_preauthorized_E6l.json；进入前 --entry-post 核验）', gate_note='不设推导中位 ≤ 0 不进的门'))
    Dr = pd.DataFrame(rows)
    p = L.P('registration', 'record_B_draft_objects_E6l.csv')
    L.atomic_write_csv(p, Dr)
    need = ['exposure', 'mechanism_importance', 'effective_support_days', 'D_deriv', 'unresolved_limits']
    nonpar = Dr.mechanism_importance != 'source_parent'
    miss = {c: int(Dr.loc[nonpar, c].isna().sum() + (Dr.loc[nonpar, c].astype(str) == '').sum()) for c in need}
    ok = all(v == 0 for v in miss.values())
    a1 = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), stage='draft', all_pass=bool(ok), missing=miss)
    L.atomic_write_json(L.P('registration', 'a1_auto_draft_E6l.json'), a1)
    md = ['# E6l 记录 B 草稿（方式 B：推导两段算完、封存；后段按预授权直接进入）', '',
          '用途：brief §5 / W11。授权对象 = 冻结清单（`registration/B_package_manifest_E6l.json` + `P_package_manifest_E6l.json`）全部描述符 × 两后段 + '
          '附属 / 同资本 / 随机闭包；逐对象字段见 `registration/record_B_draft_objects_E6l.csv`（%d 行）。' % len(Dr), '',
          '- 生效条件（W11 方式 B）：Stage 0 六类全 PASS + A1-auto（pre / 草稿）全 PASS + 进入后段时冻结清单 sha 不变 → `record_B_entry_post_E6l.json`',
          '- 用户原话（`record_B_preauthorized_E6l.json`）：转交消息"记得好好思考提速优化方案 中途不需要停下来报告 避免空转"；执行端询问后用户选"方式 B：一口气跑完"',
          '- 草稿不含门：不设"推导中位 ≤ 0 不进"；新算子不 chosen；deployment_authorized = false', '',
          '| 机制重要性 | 描述符数 | 暴露分布 |', '|---|---|---|']
    for imp, g in Dr.groupby('mechanism_importance'):
        md.append('| %s | %d | %s |' % (imp, len(g), json.dumps(g.exposure.value_counts().to_dict(), ensure_ascii=False)))
    md += ['', 'A1-auto 草稿项（字段齐，PARENT 源锚行除外）：%s（缺失计数 %s）' % ('PASS' if ok else 'FAIL', json.dumps(miss))]
    pm = L.P('reports', 'E6l_record_B_draft.md')
    L.atomic_write_text(pm, '\n'.join(md) + '\n')
    L.write_receipt(L.next_rerun('record_b_draft'), [p, pm, L.P('registration', 'a1_auto_draft_E6l.json')], 'SUCCEEDED' if ok else 'FAILED', rows=len(Dr))
    print('草稿 %d 行；A1-auto 草稿项 %s' % (len(Dr), 'PASS' if ok else 'FAIL'), flush=True)
    return 0 if ok else 2


def entry_post():
    import e6l_seal as SEAL
    rgn = L.P('registration')
    sm = json.load(open(L.P('source_manifest.json'), encoding='utf-8'))
    a1n = 'a1_auto_E6l%s.json' % L.last_rerun('a1_auto_pre')[len('a1_auto_pre'):]
    a1 = json.load(open(os.path.join(rgn, a1n), encoding='utf-8'))
    a1d = json.load(open(os.path.join(rgn, 'a1_auto_draft_E6l.json'), encoding='utf-8'))
    pre = json.load(open(os.path.join(rgn, L.AUTH_PRE), encoding='utf-8'))
    man_sha = L.sha_file(os.path.join(rgn, L.MANIFEST_B))
    same = pre['frozen_manifests'][L.MANIFEST_B] == man_sha
    ok_seal, bad = SEAL.verify('deriv')
    rec = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), stage0_all_pass=bool(sm['stage0_all_pass']), a1_auto_pre=a1n,
               a1_auto_pre_all_pass=bool(a1['all_pass']), a1_auto_draft_all_pass=bool(a1d['all_pass']), frozen_manifest_sha256=man_sha,
               manifest_unchanged=bool(same), seal_deriv_verified=bool(ok_seal), seal_deriv_bad=bad[:5])
    rec['all_pass'] = bool(rec['stage0_all_pass'] and rec['a1_auto_pre_all_pass'] and rec['a1_auto_draft_all_pass'] and same and ok_seal)
    p = os.path.join(rgn, 'record_B_entry_post_E6l.json')
    if os.path.exists(p):
        raise RuntimeError('record_B_entry_post_E6l.json 已存在（只增不删）')
    L.atomic_write_json(p, rec)
    L.write_receipt('record_b_entry_post', [p], 'SUCCEEDED' if rec['all_pass'] else 'FAILED', all_pass=rec['all_pass'])
    print(json.dumps(rec, ensure_ascii=False), flush=True)
    return 0 if rec['all_pass'] else 2


if __name__ == '__main__':
    a = sys.argv
    if '--draft' in a:
        sys.exit(draft())
    if '--entry-post' in a:
        sys.exit(entry_post())
    raise SystemExit('用法：--draft | --entry-post')
