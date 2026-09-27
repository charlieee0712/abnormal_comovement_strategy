# -*- coding: utf-8 -*-
"""E6j A1-auto（brief v1.2 §5，七项机械对账；任一 FAIL 不得提交记录 B 草稿）+ 记录 B 草稿（逐对象：source exposure、机制重要性、
有效支持、推导读数、未解决限制；不设"两推导段中位 ≤ 0 不进"的门）+ 记录 B 生效条件核验回执（§7）。
  --draft     写 reports/E6j_record_B_draft.md 与 registration/record_B_draft_objects.csv（需推导段 B 统计）
  --a1        写 reports/routing_review_A1_auto.md 与 registration/a1_auto.json
  --conditions  核三条件 → registration/record_B_conditions_receipt.json（all_pass 才解锁后段）"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time

import numpy as np
import pandas as pd

import e6j_core as J

RES = J.RES
REG = os.path.join(RES, 'registry')
RGN = os.path.join(RES, 'registration')
RB_ = os.path.join(RES, 'results_B')
BLOCK_LIMITS = {
    'B1': 'S_source 方向为 E6i 对照方向事后转正；b / a / q 分量与 S 代数相关，分量账户的差不等于机制分离',
    'B2': 'amount 单位含市值信息；日内 / 隔夜 / 极差用同日 OHLC，一字板按 OBS 保留零极差',
    'B3A': 'λ 轴是构造权重，不是 α；COV/P 可负、P ≤ 0 回退',
    'B3B': 'β 非 Kyle λ；ρ 在 y 常数时未定义回退',
    'B3C': '可靠性 r 是留一稳定性，不是后验精度；COMMON-DOSE 与 r-shuffle 剂量控制另跑',
    'B4': '零收益日单列；侧别不足 3 日回退；asym 两边须正',
    'B5': '事件钟沿 E6i：段首前无已知触发，段首事件截断；基线冻结 [c−W, c−1]',
    'B6': 'T 槽位；A08 只参加本块；R1 的 T 在母体 S1 内重中性化',
    'B7': 'R_peer20 在 E6i 只作 SWAP，SLOT 为新；行业缺失 / 同行 < 3 回退',
}


def draft():
    rows = pd.read_csv(os.path.join(REG, 'rows_B.csv'))
    fc = pd.read_csv(os.path.join(RES, 'feature_contracts.csv'))
    cov = {r.member_id: (r.get('cov_pool0_2010-2014'), r.get('cov_pool0_2015-2018')) for _, r in fc.iterrows()}
    st = pd.concat([pd.read_csv(os.path.join(RB_, 'descriptor_stats_%s.csv' % s)) for s in J.DERIV_SEGS], ignore_index=True)
    objs = []
    for _, r in rows.iterrows():
        for mo in r.mothers.split('|'):
            s = st[(st.row_id == r.row_id) & (st.mother == mo)]
            main = s[np.isclose(s.alpha, 0.25) & (s.H == 5)].set_index('segment')
            D1 = float(main.loc['2010-2014', 'D']) if '2010-2014' in main.index else np.nan
            D2 = float(main.loc['2015-2018', 'D']) if '2015-2018' in main.index else np.nan
            n1 = float(main.loc['2010-2014', 'n']) if '2010-2014' in main.index else np.nan
            n2 = float(main.loc['2015-2018', 'n']) if '2015-2018' in main.index else np.nan
            full = (D1 * n1 + D2 * n2) / (n1 + n2) if np.isfinite(D1 + D2 + n1 + n2) else np.nan
            g = s.groupby(['alpha', 'H']).apply(lambda x: np.average(x.D, weights=x.n) if x.n.sum() > 0 else np.nan)
            c = cov.get(r.measurement_id, (np.nan, np.nan))
            objs.append(dict(row_id=r.row_id, block=r.block, mother=mo, slot=r.slot, measurement_id=r.measurement_id, direction=r.direction,
                             direction_role=r.direction_role, hypothesis_ids=r.hypothesis_ids,
                             source_exposure=('E6i 源成员（已暴露）' if r.source == 'E6I' else ('K0 锚（= 母体）' if 'K0 锚' in str(r.note) else 'E6j 新测量')),
                             mechanism_importance='%s；%s' % (r.direction_role, r.rationale),
                             support_cov_2010_2014=c[0], support_cov_2015_2018=c[1],
                             deriv_D_2010_2014=D1, deriv_D_2015_2018=D2, deriv_FULL=full,
                             grid_FULL_min=float(np.nanmin(g.values)) if len(g) else np.nan,
                             grid_FULL_median=float(np.nanmedian(g.values)) if len(g) else np.nan,
                             grid_FULL_max=float(np.nanmax(g.values)) if len(g) else np.nan,
                             n_grid=int(len(g)), unresolved_limits=BLOCK_LIMITS[r.block]))
    df = pd.DataFrame(objs)
    p = os.path.join(RGN, 'record_B_draft_objects.csv'); J.atomic_write_csv(p, df)
    lines = ['# E6j 记录 B 草稿（执行端；方式 B 事前整表授权下作记录，不等待任何人）', '',
             '用途：按 brief v1.2 §7 逐对象记录 source exposure、机制重要性、有效支持、推导读数、未解决限制。**不设"两推导段中位 ≤ 0 不进"的门**；'
             '授权对象 = B 包冻结清单全部对象（`registration/record_B_preauthorized_E6j.json`），本草稿不增删对象。',
             '写入 %s（47 时间）。逐对象表：`registration/record_B_draft_objects.csv`（%d 个 登记行 × 母体 对象）。' % (time.strftime('%Y-%m-%d %H:%M:%S'), len(df)), '',
             '推导读数口径：子 − 同 H 母体 8bp 日配对增量，段年化百分点；主配置 α .25 × H5；网格列为 α × H 各格的推导两段按有效日合并值的最小 / 中位 / 最大。'
             '随机参照在推导段随机分片完成后补入 part1，不改本草稿对象集合。', '',
             '| 块 | 对象数 | 推导合并（主配置）中位 | 主配置两段均 > 0 的对象数 | 网格中位的中位 |', '|---|---|---|---|---|']
    for b, g in df.groupby('block'):
        both = int(((g.deriv_D_2010_2014 > 0) & (g.deriv_D_2015_2018 > 0)).sum())
        lines.append('| %s | %d | %.3f | %d | %.3f |' % (b, len(g), float(np.nanmedian(g.deriv_FULL)), both, float(np.nanmedian(g.grid_FULL_median))))
    lines += ['', '未解决限制（按块）：'] + ['- %s：%s' % (k, v) for k, v in BLOCK_LIMITS.items()]
    J.atomic_write_text(os.path.join(RES, 'reports', 'E6j_record_B_draft.md'), '\n'.join(lines) + '\n')
    J.write_receipt('record_B_draft', [p, os.path.join(RES, 'reports', 'E6j_record_B_draft.md')], 'SUCCEEDED', n_objects=len(df))
    print('draft objects', len(df))


def a1():
    res = []

    def chk(i, what, ok, detail=''):
        res.append(dict(item=i, what=what, status='PASS' if ok else 'FAIL', detail=detail))

    a0 = json.load(open(os.path.join(REG, 'a0_manifest.json')))
    c = a0['checks']
    chk(1, '登记对账：问题→对象、任务→对象两表逐元组相等；B 每段计数 = 编译器现算；P = 528',
        c['question_eq_task'] and c['question_eq_registry'] and c['B_per_segment'] and c['P_528'],
        'B=%d（brief 写 13,230；plan §5.10 现算 13,398）P=%d' % (a0['counts']['B_per_segment'], a0['counts']['P']))
    rows = pd.read_csv(os.path.join(REG, 'rows_B.csv'))
    dB = pd.read_csv(os.path.join(REG, 'descriptors_B.csv'))
    need = ['measurement_id', 'direction', 'operator_id', 'rationale', 'bidirectional', 'hypothesis_ids']
    qs = set('Q%02d' % i for i in range(1, 18))
    ok2 = rows[need].notna().all(axis=None) and rows.rationale.str.len().min() > 5 and \
        all(set(h.split('|')) <= qs for h in rows.hypothesis_ids) and dB[['parent_id', 'alpha', 'H']].notna().all(axis=None)
    ex = pd.read_csv(os.path.join(REG, 'exposure_ledger.csv'))
    ok2 = ok2 and {'alias_of', 'direction_2of1', 'related_exposed', 'source_member_seen'} <= set(ex.exposure_type)
    chk(2, '五类身份齐全（measurement / orientation / operator / parent / account）；方向论证句与双向标记；hypothesis_id ⊂ Q01–Q17；exposure 标记齐', bool(ok2),
        'rows=%d；exposure 类型 %s' % (len(rows), sorted(set(ex.exposure_type))))
    ok3 = c['A08_only_B6'] and c['B6_only_T'] and c['B7_K_and_T'] and c['main_config_everywhere'] and c['H_set'] and c['alpha_set']
    chk(3, '槽位合法（A08 无 K、B6 只 T、B7 K / T 分域）；每对象含主配置 .25 × H5；H = {1,2,3,5,10,15,20}；α = {.125,.25,.5}', bool(ok3))
    L = a0['policy_locks']
    ok4 = (L['policy_aggregation'] == 'FULL_E6I_ALL4' and L['random_ref'].startswith('R-MATCH-SRC') and L['capital_ref'] == 'same_capital'
           and abs(L['delta'] - 0.10) < 1e-12 and L['delta_sensitivity'] == [0.05, 0.15] and L['policy_confirmation_status'] == 'confirmed_by_proceeding')
    chk(4, '锁定值非空且与 brief 一致', bool(ok4), json.dumps(L, ensure_ascii=False))
    sr = open(os.path.join(RES, 'source_resolution.md'), encoding='utf-8').read()
    ok5 = all(('| %d |' % i) in sr for i in range(1, 8)) and '## 2. 差异登记' in sr
    chk(5, 'source_resolution.md 覆盖 §1.3 七条源事实；差异逐条登记', ok5)
    sm = json.load(open(os.path.join(RES, 'source_manifest.json')))
    chk(6, 'Stage 0 六项锚全 PASS', bool(sm['stage0_all_pass']))
    dp = os.path.join(RGN, 'record_B_draft_objects.csv')
    if os.path.exists(dp):
        d = pd.read_csv(dp)
        f7 = ['source_exposure', 'mechanism_importance', 'support_cov_2010_2014', 'deriv_D_2010_2014', 'deriv_D_2015_2018', 'unresolved_limits']
        n_exp = int(sum(len(r.mothers.split('|')) for _, r in rows.iterrows()))
        ok7 = len(d) == n_exp and d[['source_exposure', 'mechanism_importance', 'unresolved_limits']].notna().all(axis=None)
        chk(7, 'B 草稿逐对象含 source exposure / 机制重要性 / 有效支持 / 推导读数 / 未解决限制；无"推导中位 ≤ 0"门', bool(ok7), '对象 %d / 应有 %d' % (len(d), n_exp))
    else:
        chk(7, 'B 草稿逐对象五项', False, '草稿未生成')
    df = pd.DataFrame(res)
    allp = bool((df.status == 'PASS').all())
    J.atomic_write_json(os.path.join(RGN, 'a1_auto.json'), dict(items=res, all_pass=allp, written_at=time.strftime('%Y-%m-%d %H:%M:%S')))
    md = ['# E6j routing_review_A1_auto（执行端机械对账七项；brief v1.2 §5）', '',
          '用途：替代中途人工 A1（决策端中途不动）；任一 FAIL 不得提交记录 B 草稿；语义级登记错误留整轮 REVIEW 事后降级。', '',
          '| 项 | 内容 | 状态 | 说明 |', '|---|---|---|---|'] + ['| %d | %s | %s | %s |' % (r['item'], r['what'], r['status'], str(r['detail']).replace('|', '/')) for r in res]
    md += ['', '结论：七项%s。' % ('全部 PASS' if allp else '未全过（不得提交记录 B 草稿）')]
    J.atomic_write_text(os.path.join(RES, 'reports', 'routing_review_A1_auto.md'), '\n'.join(md) + '\n')
    J.write_receipt('a1_auto', [os.path.join(RGN, 'a1_auto.json'), os.path.join(RES, 'reports', 'routing_review_A1_auto.md')],
                    'SUCCEEDED' if allp else 'FAILED', all_pass=allp)
    print(df.to_string())
    return 0 if allp else 2


def conditions():
    sm = json.load(open(os.path.join(RES, 'source_manifest.json')))
    a1j = json.load(open(os.path.join(RGN, 'a1_auto.json')))
    rb = json.load(open(os.path.join(RGN, 'record_B_preauthorized_E6j.json')))
    cur = J.sha_file(os.path.join(RGN, 'B_package_manifest.json'))
    amend = [f for f in os.listdir(RGN) if f.startswith('preregistration_amend_')]
    c1, c2, c3 = bool(sm['stage0_all_pass']), bool(a1j['all_pass']), (cur == rb['frozen_manifest_sha256'] and not amend)
    rec = dict(approval_id=rb['approval_id'], checked_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               condition_1_stage0_all_pass=c1, condition_2_a1_auto_all_pass=c2, condition_3_manifest_unchanged=c3,
               frozen_manifest_sha256=rb['frozen_manifest_sha256'], current_manifest_sha256=cur, amendments=amend,
               all_pass=bool(c1 and c2 and c3))
    J.atomic_write_json(os.path.join(RGN, 'record_B_conditions_receipt.json'), rec)
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0 if rec['all_pass'] else 2


if __name__ == '__main__':
    if '--draft' in sys.argv:
        draft(); sys.exit(0)
    if '--a1' in sys.argv:
        sys.exit(a1())
    if '--conditions' in sys.argv:
        sys.exit(conditions())
