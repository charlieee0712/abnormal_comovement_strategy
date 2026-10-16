# -*- coding: utf-8 -*-
"""E6m A1-auto 阶段 S 重判（brief §5 S2；附录 A1-auto）。阶段 N 的 25 项原样继承（registration/a1_auto_E6m_stageN.csv），只重判：
  第 2 项   PX1–PX8 原件逐句对：E6l registration/policy_profiles_E6l.json（X19）全部字符串叶子 vs 本轮转录 policy_profiles_E6m_stageN.json；
            机械判据 = 原件里每个数值记号（.10 / 12/17 / 2·MCSE / 8,192 …，规范化后）都出现在转录里；并排表供人工逐句核
  第 7 项   SECOND_EVALUATION 对象 = 与 E6k / E6l 登记表真实交集（stage0_S/c2_c4/anchor_map_E6m.csv：注册交集候选全部定标签、无 SOURCE_WAIT）
  第 3/⑬b 项  plan 未单列"反解释"的 8 张卡：决策端文件 registration/counter_explanations_decision_E6m.json（每卡一条：补写原文或"确认以原文预期 / 更新句代替"
            + 决策端角色 + 日期）齐全才 PASS；执行端不代写
输出 registration/a1_auto_E6m_S.csv / .json（all_pass）；回执 S_a1_auto。不读收益。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import json
import time

import pandas as pd

import e6m_core as M
import e6m_stage0_S as S0

CARDS_13B = ('Q01', 'Q05', 'Q06', 'Q09', 'Q14', 'Q16', 'Q17', 'Q18')
NUM = re.compile(r'[+−\-]?\d[\d,]*(?:\.\d+)?|[+−\-]?\.\d+')


def leaves(x, pre=''):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, '%s/%s' % (pre, k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, '%s[%d]' % (pre, i))
    else:
        yield pre, str(x)


def norm_num(t):
    t = t.replace('−', '-').replace(',', '')
    try:
        return '%g' % float(t)
    except ValueError:
        return t


def item2(root):
    p = os.path.join(root, S0.RN['L'], 'registration', 'policy_profiles_E6l.json')
    if not os.path.exists(p):
        return 'SOURCE_WAIT', 'X19 未到', None
    src = list(leaves(json.load(open(p, encoding='utf-8'))))
    mine = ' '.join(v for _, v in leaves(json.load(open(M.P('registration', 'policy_profiles_E6m_stageN.json'), encoding='utf-8'))))
    have = set(norm_num(t) for t in NUM.findall(mine))
    rows, miss = [], []
    for path, v in src:
        toks = sorted(set(norm_num(t) for t in NUM.findall(v)))
        lack = [t for t in toks if t not in have]
        miss += lack
        rows.append(dict(e6l_path=path, e6l_text=v[:500], numeric_tokens='|'.join(toks), missing_in_transcription='|'.join(lack) or 'NONE'))
    T = pd.DataFrame(rows)
    M.atomic_write_csv(M.P('registration', 'px_reconciliation_E6m.csv'), T)
    return ('PASS' if not miss else 'FAIL'), '原件 %d 条字符串叶子；转录缺数值记号 %d 个：%s（并排表 registration/px_reconciliation_E6m.csv）' % (
        len(T), len(set(miss)), sorted(set(miss))[:10]), T


def item7():
    p = M.P('stage0_S', 'c2_c4', 'anchor_map_E6m.csv')
    if not os.path.exists(p):
        return 'NOT_RUN', '先跑 e6m_stage0_S_feat anchormap'
    A = M.read_csv_keep(p, dtype=str)
    c = A[A.exposure == 'SOURCE_WAIT_REGISTRY_INTERSECTION']
    left = int((c.exposure_S1 == 'SOURCE_WAIT_REGISTRY_INTERSECTION').sum())
    return ('PASS' if left == 0 else 'SOURCE_WAIT'), '注册交集候选 %d：%s' % (len(c), json.dumps(c.exposure_S1.value_counts().to_dict(), ensure_ascii=False))


def item13b():
    p = M.P('registration', 'counter_explanations_decision_E6m.json')
    if not os.path.exists(p):
        return 'FAIL', '决策端文件未到：8 张卡 %s 的反解释（补写或确认以原文代替）' % list(CARDS_13B)
    d = json.load(open(p, encoding='utf-8'))
    got = {e.get('card'): e for e in d.get('cards', [])}
    bad = [c for c in CARDS_13B if not (got.get(c, {}).get('text') and got.get(c, {}).get('role') and got.get(c, {}).get('date'))]
    return ('PASS' if not bad else 'FAIL'), '决策端文件 sha %s；不全的卡：%s' % (M.sha_file(p)[:16], bad)


def main():
    t0 = time.time()
    root = S0.default_root()
    N = M.read_csv_keep(M.P('registration', 'a1_auto_E6m_stageN.csv'), dtype=str)
    rows = []
    for r in N.to_dict('records'):
        it, ck = str(r['item']), str(r['check'])
        if it == '2' and 'PX1–PX8' in ck:                          # 同号的其它行（阶段 N 已判）原样继承
            st, det, _ = item2(root)
            rows.append(dict(r, status=st, detail=det, stage='S'))
        elif it == '7' and 'SECOND_EVALUATION' in ck:
            st, det = item7()
            rows.append(dict(r, status=st, detail=det, stage='S'))
        elif it.startswith('3/⑬b'):
            st, det = item13b()
            rows.append(dict(r, status=st, detail=det, stage='S'))
        else:
            rows.append(dict(r, stage='N（继承）'))
    df = pd.DataFrame(rows)
    p1 = M.P('registration', 'a1_auto_E6m_S.csv')
    M.atomic_write_csv(p1, df)
    cnt = df.status.value_counts().to_dict()
    j = dict(stage='S', written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_items=len(df), counts=cnt, all_pass=bool((df.status == 'PASS').all()),
             not_pass=df[df.status != 'PASS'][['item', 'status', 'detail']].to_dict('records'))
    p2 = M.P('registration', 'a1_auto_E6m_S.json')
    M.atomic_write_json(p2, j)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_a1_auto'), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__], counts=cnt, all_pass=j['all_pass'],
                    wall_s=round(time.time() - t0, 1), note='all_pass = false 是检查结果，不是任务失败')
    print(json.dumps(dict(counts=cnt, all_pass=j['all_pass'], not_pass=[(x['item'], x['status']) for x in j['not_pass']]), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
