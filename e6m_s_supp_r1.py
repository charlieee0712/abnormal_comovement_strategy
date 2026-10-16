# -*- coding: utf-8 -*-
"""E6m REPORT supplement 1（决策端任务单 2026-10-12 §1：E01–E04；不改 REPORT、登记与封存件）。
  e03 --seg <段>   Δgross 三项表补算：沿 e6m_s_decomp.task_weightchange 逐日拆分（act_dense / split_day 原函数），合计改为只在权重有变化的列上求和
                   （预热期双方持仓全 0、超额收益 NaN，原写法 (ac − ap) @ x = 0 × NaN = NaN）；三项与原表逐格比对 → supp/R1/E03_weight_change_<段>.csv
  e01              16 张占位 query 的"卡 → 固定表"绑定与行数 → supp/R1/E01_binding.csv
  write            拼 supp/R1/E6m_REPORT_supplement_1.md（E01–E04）
  deliver          复制到 handoff/E6m/stageS_20261012_2222/reports/（md + E03 合并表），另写 E6m_REPORT_supplement_1.sha256；原交付文件一个不改"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import glob
import shutil
import hashlib
import argparse
import collections

import numpy as np
import pandas as pd

import e6m_core as M

OUT = M.P('supp', 'R1')
HAND = 'stageS_20261012_2222'
PLACE = ['E6M-Q09-a', 'E6M-Q09-b', 'E6M-Q10-a', 'E6M-Q10-b', 'E6M-Q11-a', 'E6M-Q11-b', 'E6M-Q12-a', 'E6M-Q12-b', 'E6M-B5A-a', 'E6M-Q13-d',
         'E6M-Q14-a', 'E6M-Q14-b', 'E6M-Q14-c', 'E6M-Q15-a', 'E6M-Q16-c', 'E6M-Q18-a']


# ------------------------------------------------------------------ E03
def task_e03(seg_name):
    import e6k_acct as AC
    import e6m_s_real as RL
    import e6m_s_decomp as DC
    os.makedirs(OUT, exist_ok=True)
    seg = RL.seg_of(seg_name, 'real')
    acct = AC.Acct(seg)
    SE = seg.SE
    T, Nc = SE.T, SE.Nc
    x_all = SE.r0 - SE.bench[:, None]
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    P72 = D[D.is_primary72 == 'True']
    O = pd.read_csv(M.P('results', 'full', 'decomp', 'weight_change_%s.csv' % seg_name), keep_default_na=False, na_values=['']).set_index('desc_id')
    rows = []
    for form, g in P72.groupby('parent'):
        z = np.load(M.P('masks', seg_name, '%s.npz' % form), allow_pickle=False)
        n = int(z['n_cells'][0])
        fin = {str(c): j for j, c in enumerate(z['config_ids'])}
        F0 = np.unpackbits(z['parent_final_bits'])[:n].astype(bool)
        tp = acct.target(F0)
        for r in g.itertuples():
            cfg = DC.SS.config_id(r.desc_id) if hasattr(DC.SS, 'config_id') else '|'.join(r.desc_id.split('|')[:6] + r.desc_id.split('|')[7:])
            if cfg not in fin:
                rows.append(dict(desc_id=r.desc_id, segment=seg_name, status='UNDEFINED'))
                continue
            H = int(r.H)
            kept = np.unpackbits(z['final_bits'][fin[cfg]])[:n].astype(bool)
            tc = acct.target(kept)
            ac = DC.act_dense(T, Nc, tc['t'], tc['c'], tc['w'], H)
            ap = DC.act_dense(T, Nc, tp['t'], tp['c'], tp['w'], H)
            parts = np.zeros((T, 4))
            tot = np.zeros(T)
            for j in range(2, T):
                parts[j] = DC.split_day(ac[j - 2], ap[j - 2], x_all[j])
                d = ac[j - 2] - ap[j - 2]
                nz = d != 0
                tot[j] = float(d[nz] @ x_all[j][nz]) if nz.any() else 0.0
            led_c = acct.ledgers(tc, (H,), impact=False, roll=False)[H]['gross']
            led_p = acct.ledgers(tp, (H,), impact=False, roll=False)[H]['gross']
            clo_parts = float(np.max(np.abs(parts[:, :3].sum(1) - tot)))
            clo_engine = float(np.nanmax(np.abs(tot - (led_c - led_p))))
            o = O.loc[r.desc_id]
            three = (float(np.mean(parts[:, 0])) * DC.ANN, float(np.mean(parts[:, 1])) * DC.ANN, float(np.mean(parts[:, 2])) * DC.ANN)
            rows.append(dict(desc_id=r.desc_id, segment=seg_name, H=H, added_ann_pp=three[0], removed_ann_pp=three[1], common_reweight_ann_pp=three[2],
                             dgross_ann_pp=float(np.mean(tot)) * DC.ANN, closure_parts_maxabs=clo_parts, closure_vs_engine_maxabs=clo_engine,
                             days_total_nan_original=int((~np.isfinite(parts[2:, 3])).sum()), days_total_nan_recomputed=int((~np.isfinite(tot[2:])).sum()),
                             three_parts_vs_delivered_maxabs=float(max(abs(three[0] - o.added_ann_pp), abs(three[1] - o.removed_ann_pp), abs(three[2] - o.common_reweight_ann_pp))),
                             status='COMPUTED' if (np.isfinite(clo_parts) and max(clo_parts, clo_engine) <= DC.TOL) else 'CLOSURE_FAIL'))
    df = pd.DataFrame(rows)
    p = os.path.join(OUT, 'E03_weight_change_%s.csv' % seg_name)
    M.atomic_write_csv(p, df)
    print(json.dumps(dict(seg=seg_name, rows=len(df), status=df.status.value_counts().to_dict(), max_three_vs_delivered=float(df.three_parts_vs_delivered_maxabs.max()),
                          max_closure_parts=float(df.closure_parts_maxabs.max()), max_closure_engine=float(df.closure_vs_engine_maxabs.max()),
                          nan_days_original=sorted(df.days_total_nan_original.unique().tolist())), ensure_ascii=False), flush=True)
    return 0


# ------------------------------------------------------------------ E01
def fam(cid):
    p = str(cid).split('|')
    return p[2] if len(p) > 2 else ''


def contrast_part(cid):
    p = str(cid).split('|')
    return '|'.join(p[2:]) if len(p) > 2 else str(cid)


def task_e01():
    os.makedirs(OUT, exist_ok=True)
    Q = M.read_csv_keep(M.P('registry', 'query_registry_E6m.csv'), dtype=str).set_index('query_id')
    R = M.read_csv_keep(M.P('registry', 'b3_contrasts_E6m.csv'), dtype=str)
    R['card'] = R.contrast_id.str.split('|').str[1]
    fams = {c: sorted(set('|'.join(g.cells).split('|'))) for c, g in R.groupby('card')}
    F = lambda t: pd.read_csv(M.P('reports', 'fixed_full', '%s.csv' % t), keep_default_na=False, dtype=str)  # noqa: E731
    cache = {}

    def tab(t):
        if t not in cache:
            cache[t] = F(t)
        return cache[t]
    rows = []

    def add(q, t, rule, X):
        rows.append(dict(query_id=q, card=Q.loc[q, 'card'], schema=Q.loc[q, 'schema'], fixed_table='reports/fixed_full/%s.csv' % t, rows_rule=rule,
                         rows=len(X), status=json.dumps(X.status.value_counts().to_dict(), ensure_ascii=False) if len(X) else '{}',
                         registry_machine_table=Q.loc[q, 'machine_table'], registry_object_rule=Q.loc[q, 'object_rule']))
    for q in PLACE:
        card, sch = Q.loc[q, 'card'], Q.loc[q, 'schema']
        if sch == 'B3_CELL':
            if card == 'Q12':
                for t in ('b3_mirror_cvr', 'b3_mirror_gap'):
                    add(q, t, '全表（族 %s）' % t.split('_', 1)[1].upper(), tab(t))
            else:
                X = tab('b3_cells')
                fs = fams.get(card, [])
                add(q, 'b3_cells', 'cell_id 第 3 段（族）∈ {%s}（该卡对比用到的格族，取自 registry/b3_contrasts_E6m.csv 的 cells 列）' % '、'.join(fs), X[X.cell_id.map(fam).isin(fs)])
        elif sch == 'B3_CONTRAST':
            for t in ('b3_pairs', 'b3_random'):
                X = tab(t)
                add(q, t, 'contrast_id 去掉"段|域|"前缀后以 B3C|%s| 开头' % card, X[X.contrast_id.map(contrast_part).str.startswith('B3C|%s|' % card)])
        elif q == 'E6M-B5A-a':
            X = tab('b5_state_ledger')
            add(q, 'b5_state_ledger', 'query_id == E6M-B5A-a', X[X.query_id == q])
        elif q == 'E6M-Q13-d':
            for t in ('b5_state_ledger', 'b5_delete_budget'):
                X = tab(t)
                add(q, t, 'query_id == E6M-Q13-d', X[X.query_id == q])
        elif sch == 'B4':
            t = {'E6M-Q14-a': 'b4_event_contrib', 'E6M-Q14-b': 'b4_signatures', 'E6M-Q14-c': 'symdec'}[q]
            X = tab(t)
            add(q, t, '全表（query_id 列值：%s）' % '、'.join(sorted(X.query_id.unique())), X)
        elif sch == 'B6':
            X = tab('b6_trigger_ledger')
            add(q, 'b6_trigger_ledger', '全表（query_id 列值：%s）' % '、'.join(sorted(X.query_id.unique())), X)
        elif q == 'E6M-Q16-c':
            for t in ('weight_change_attribution', 'match_cap_ledger'):
                X = tab(t)
                add(q, t, '全表（主 72 × 段；query_id 列值：%s）' % '、'.join(sorted(X.query_id.unique())[:3]), X)
        elif q == 'E6M-Q18-a':
            X = tab('hypothesis_lineage')
            add(q, 'hypothesis_lineage', '全表（逐卡；query_id 列值：%s）' % '、'.join(sorted(X.query_id.unique())[:3]), X)
    df = pd.DataFrame(rows)
    M.atomic_write_csv(os.path.join(OUT, 'E01_binding.csv'), df)
    print(df[['query_id', 'fixed_table', 'rows', 'status']].to_string(max_colwidth=60), flush=True)
    return 0


# ------------------------------------------------------------------ write / deliver
E02 = [
    (58, 'Q04', '更新', 'plan 未给：§12 E6M-Q04 只有动机 / 预期 / 收益假设 / 反解释 / 判别，没有"更新"句。'),
    (108, 'Q07', '更新', 'plan 未给"更新"：§12 E6M-Q07 以"限制"收尾——"每编辑收益"非每笔交易alpha；分母0不算比率。'),
    (145, 'Q09', '绑定视图', '无比较视图：B3 卡，对象是 B3 对比（registry/b3_contrasts_E6m.csv 中以 B3C|Q09 开头的 4 个），读数见 E01 绑定表。'),
    (161, 'Q10', '绑定视图', '无比较视图：B3 卡，对象是以 B3C|Q10 开头的 48 个 B3 对比，读数见 E01 绑定表。'),
    (176, 'Q11', '更新', 'plan 未给"更新"：§12 E6M-Q11 以"边界"收尾——不称已识别补涨leader-lag，不据此改I11触发。'),
    (177, 'Q11', '绑定视图', '无比较视图：B3 卡，对象是以 B3C|Q11 开头的 4 个 B3 对比，读数见 E01 绑定表。'),
    (193, 'Q12', '绑定视图', '无比较视图：B3 镜像卡（以 B3C|Q12 开头的 9 个对比、MIRROR_CVR / MIRROR_GAP 两族）加 B5a 状态账本，读数见 E01 绑定表。'),
    (228, 'Q14', '绑定视图', '无比较视图：B4 卡，读 b4_event_contrib / b4_signatures / symdec，见 E01 绑定表。'),
    (245, 'Q15', '绑定视图', '无比较视图：B6 卡，读 b6_trigger_ledger，见 E01 绑定表。'),
    (290, 'Q18', '判别', 'plan 未给"判别"：§12 E6M-Q18 是方法卡，对应句为"检查"——用户原话／CC解释／最终采纳／实际算子／对照／结果query／结论范围逐项绑定。'),
    (293, 'Q18', '绑定视图', '无比较视图：方法卡，读 hypothesis_lineage（逐卡一行），见 E01 绑定表。'),
]


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def task_write():
    B = pd.read_csv(os.path.join(OUT, 'E01_binding.csv'), keep_default_na=False, dtype=str)
    E3 = pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in sorted(glob.glob(os.path.join(OUT, 'E03_weight_change_*.csv')))], ignore_index=True)
    A1 = json.load(open(M.P('registration', 'a1_auto_E6m_S.json'), encoding='utf-8'))
    RC = json.load(open(M.P('registration', 'a1_auto_item2_reconciliation_E6m_S.json'), encoding='utf-8'))
    cards = open(M.P('reports', 'E6m_cards.md'), encoding='utf-8').read().split('\n')
    L = ['# E6m REPORT supplement 1（E01–E04；执行端，2026-10-12）', '',
         '用途：回应决策端 `exec_briefs/E6m_REVIEW.md` §2.1 的四处 DIFFERS（任务单 `执行端任务单_20261012_E6m补件与E6l阶段2.md` §1）。四处都在报告层，不触及读数。'
         '本 supplement 不改 REPORT、限制登记、固定表与任何封存件；机器数由 `e6m_s_supp_r1.py`（47 project_core）从机器表现取，中间表在工作目录 `supp/R1/`。', '']
    # E01
    L += ['## E01 卡层绑定：16 张占位 query 表', '',
          '- **运行器状态**：`e6m_s_queries.py` 只实现了 COMPARISON 与 FACT（掩码层事实）两种 schema。B3_CELL / B3_CONTRAST / B4 / B5 / B6 / LINEAGE 六种 schema，'
          '以及 FACT 中 machine_table 含 weight_change 的 Q16-c，一律写 1 行 status = NOT_RUN 的占位行。模块说明写的是"对应机器表到位前写 NOT_RUN"，但没有实现"到位后改读机器表"的分支，所以机器表齐了也仍是占位。'
          '登记表 `registry/query_registry_E6m.csv` 对这 16 条的 status 是 NOT_RUN_STAGE_N，machine_table / object_rule 已登记，下表即按登记绑定、并从固定表现数行数。',
          '- **卡 → 固定表**（行数取 `reports/fixed_full/*.csv`）：', '',
          '| query | 卡 | schema | 固定表 | 取哪些行 | 行数 | status |', '|---|---|---|---|---|---|---|']
    for r in B.itertuples():
        L.append('| %s | %s | %s | `%s` | %s | %s | %s |' % (r.query_id, r.card, r.schema, r.fixed_table.split('/')[-1], r.rows_rule, r.rows, r.status.replace('"', '')))
    L += ['', '- **对闭包门的建议**（下一轮代码，本轮不改）：S08 现只查"每个登记 query ≥ 1 行"，占位行也能过。建议加一条："全部行 status = NOT_RUN 的 query 判 FAIL，'
          '除非登记表把它标为占位（如 status = NOT_RUN_STAGE_N 且写明读数所在固定表）"；并让 queries 运行器在机器表到位后改读固定表。', '']
    # E02
    L += ['## E02 字面 nan：11 处的正确文本', '',
          '- **原因**：`e6m_s_reports.py` 第 362 行用 `%s` 直接印卡登记表（registry/cards_stageB_E6m.csv）的 t04_discriminator / t10_update / contrast_views；'
          '这些格为空时按空值读入成 NaN，印出来就是字面 nan。与经验 N2（None → NaN → 字面 nan）同类，只是这次落在报告正文、不在 CSV，状态词扫描（S06）只扫 CSV，没拦住。',
          '- **缺字段该印什么**：报告正文印"plan 未给"（plan 卡片里没有这一句）或"无比较视图"（非 COMPARISON 卡），不印空、也不印 NaN；机器表里同类空格用状态词 UNDEFINED。',
          '- **11 处的正确文本**（行号指交付的 `reports/E6m_cards.md`；"plan"指 `PLAN_COPY.md` §12 事前问题卡）：', '',
          '| 行 | 卡 | 字段 | 原印 | 应为 |', '|---|---|---|---|---|']
    for ln, card, fld, txt in E02:
        got = cards[ln - 1].strip() if ln - 1 < len(cards) else ''
        assert ('：nan' in got) and (fld in got), (ln, got[:40])
        L.append('| %d | %s | %s | `%s` | %s |' % (ln, card, fld, got.replace('|', '\\|')[:60], txt.replace('|', '\\|')))
    L += ['', '- 下一轮代码建议：报告编译同一步对正文做字面 nan / None 扫描，命中即停。', '']
    # E03
    ok = E3[E3.status != 'UNDEFINED']
    L += ['## E03 Δgross 三项表（E6M-MECH-WCHG）合计列为空、全表 CLOSURE_FAIL', '',
          '- **原因**：`e6m_s_decomp.task_weightchange` 逐日用 `split_day` 拆成新增 / 消失 / 共同重定权三项与总差。每段前 19 个交易日是 bench 预热期，超额收益 x = r0 − bench 整行为 NaN；'
          '这些天子 / 父持仓都还是 0，三项按布尔掩码求和、空集为 0，所以三项列有值；总差却用 `(ac − ap) @ x`，零向量乘 NaN 得 NaN。于是 dgross_ann_pp（总差均值）与 '
          'closure_parts_maxabs（三项和 − 总差）都是 NaN，`max(NaN, …) <= TOL` 为假，全表判 CLOSURE_FAIL。closure_vs_engine_maxabs 用的是 nanmax，所以有值且都在机器精度。'
          '**结论：CLOSURE_FAIL 是合计列缺失造成的，不是闭合真失败。**与连续链锚 ii（补丁十五）同一类 NaN 处理问题。',
          '- **补算**（不改原表）：同一函数、同一持仓与收益，逐日总差改为只在权重有变化的列上求和（权重差全 0 的日子总差 = 0），其余不动。附表 `E6m_REPORT_supplement_1_E03_weight_change.csv`（%d 行）。' % len(E3),
          '- **核对**（判据来源：基线 = 交付表，不变量 = 三项和 = 总差、总差 = 引擎 gross 差）：', '',
          '| 项 | 结果 |', '|---|---|',
          '| 行数 | %d（主 72 × 4 段；UNDEFINED %d） |' % (len(E3), int((E3.status == 'UNDEFINED').sum())),
          '| 三项与交付表逐格最大差 | %s |' % ('%.3g' % ok.three_parts_vs_delivered_maxabs.max()),
          '| 补算后 status | %s |' % json.dumps(E3.status.value_counts().to_dict(), ensure_ascii=False).replace('"', ''),
          '| closure_parts_maxabs（三项和 − 总差）最大 | %s |' % ('%.3g' % ok.closure_parts_maxabs.max()),
          '| closure_vs_engine_maxabs（总差 − 引擎 gross 差）最大 | %s |' % ('%.3g' % ok.closure_vs_engine_maxabs.max()),
          '| 原写法总差为 NaN 的天数（每对象每段） | %s |' % '、'.join(str(x) for x in sorted(ok.days_total_nan_original.unique())),
          '| 补算后总差为 NaN 的天数 | %s |' % '、'.join(str(x) for x in sorted(ok.days_total_nan_recomputed.unique())), '',
          '- dgross_ann_pp 的数值在附表里，本节不抄；读法同原表（主 72 × 段，单位 ann_pp）。', '']
    # E04
    cnt = A1.get('counts', {})
    L += ['## E04 限制登记 L-S8 状态栏', '',
          '- 原文：`PASS（A1-auto S：PASS 23 / SOURCE_WAIT 2 / FAIL 0）`。这是阶段 N（云机）时的计数，47 上重算后没回写限制登记。',
          '- 应为：`PASS（⑬b：8 张卡的反解释代拟在案）；A1-auto S 终版 PASS %d / FAIL %d——第 2 项（PX 原件逐句对）机械判据 FAIL，人工逐句核放行'
          '（registration/a1_auto_item2_reconciliation_E6m_S.json，%d 行全归类、结论 %s；用户 %s 原话）；生效条件回执（补丁十四）与闭包门 S05（补丁十七）按同一规则认可`。'
          % (cnt.get('PASS', 0), cnt.get('FAIL', 0), len(RC.get('rows', [])), RC.get('verdict'), RC.get('user_quote_date')),
          '- 机器依据：`registration/a1_auto_E6m_S.json` counts = %s，not_pass = %s。限制登记原件不改。' % (json.dumps(cnt, ensure_ascii=False).replace('"', ''),
                                                                                                    [x.get('item') for x in A1.get('not_pass', [])]), '']
    p = os.path.join(OUT, 'E6m_REPORT_supplement_1.md')
    open(p, 'w', encoding='utf-8').write('\n'.join(L))
    E3.to_csv(os.path.join(OUT, 'E6m_REPORT_supplement_1_E03_weight_change.csv'), index=False)
    print(json.dumps(dict(md=M.rel(p), lines=len(L), e03_rows=len(E3)), ensure_ascii=False))
    return 0


def task_deliver():
    import e6m_s_deliver as D
    dst = os.path.join(D.HANDOFF, HAND, 'reports')
    assert os.path.isdir(dst), dst
    names = ['E6m_REPORT_supplement_1.md', 'E6m_REPORT_supplement_1_E03_weight_change.csv']
    for n in names:
        assert not os.path.exists(os.path.join(dst, n)), '已存在：%s' % n
    lines = []
    for n in names:
        shutil.copy2(os.path.join(OUT, n), os.path.join(dst, n))
        lines.append('%s  reports/%s' % (sha(os.path.join(dst, n)), n))
    open(os.path.join(dst, 'E6m_REPORT_supplement_1.sha256'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['e03', 'e01', 'write', 'deliver'])
    ap.add_argument('--seg')
    a = ap.parse_args()
    return dict(e03=lambda: task_e03(a.seg), e01=task_e01, write=task_write, deliver=task_deliver)[a.task]()


if __name__ == '__main__':
    sys.exit(main())
