# -*- coding: utf-8 -*-
"""E6m REPORT part1（推导两段）与记录 B 草稿（brief §5 S3 / W11；plan §13.4；e6l_report_part1 / e6l_record_b 同构，输出只写本轮目录）。
只读推导两段（2010-2014 / 2015-2018）的机器表；真实结果目录先过封存门（seal_deriv）。只给数，不设门、不写判词：新算子一律标
NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY（首评、重复使用的历史，非样本外）；deployment_authorized = false；replacement NOT_AUTHORIZED。
  part1     <out>/E6m_REPORT_part1.md + <out>/tables/E6M-P1-*.csv
  record-b  <out>/E6m_record_B_draft.md（方式 A：推导两段封存后请用户对两后段一句话授权；列冻结清单 sha、生效条件现状、后段将跑与不授权的事）
每张表带读法表头（主体 / 算子 / 分母 / 基准 / 子集 / 单位 / 日期 / H / 成本 / 支持 / exposure），表全文另存 CSV。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M

DERIV = tuple(M.DERIV_SEGS)
DATES = '2010-01-04 … 2018-12-28（推导两段）'
P_MECH = ('LEGACY_POLICY_RANDOM', 'CONTENT_ISK_P5')


def to_md(df, nd=4):
    def f(v):
        if isinstance(v, (float, np.floating)):
            return '' if np.isnan(v) else ('%.*f' % (nd, v))
        return str(v)
    cols = list(df.columns)
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '|'.join(['---'] * len(cols)) + '|']
    out += ['| ' + ' | '.join(f(v) for v in r) + ' |' for r in df.itertuples(index=False)]
    return '\n'.join(out)


class Report(object):
    def __init__(self, name, out):
        self.name, self.out, self.md, self.tables = name, out, [], []
        os.makedirs(os.path.join(out, 'tables'), exist_ok=True)

    def h(self, n, t):
        self.md += ['', '#' * n + ' ' + t, '']

    def p(self, t):
        self.md += [t, '']

    def table(self, df, head, qid, maxrows=40):
        p = os.path.join(self.out, 'tables', '%s.csv' % qid)
        M.atomic_write_csv(p, df)
        self.tables.append(p)
        self.md.append('**%s**　%s　（全表 `tables/%s.csv`，%d 行%s）' % (qid, '；'.join('%s：%s' % kv for kv in head.items()), qid, len(df),
                                                                  '' if len(df) <= maxrows else '；此处印前 %d 行' % maxrows))
        self.md += ['', to_md(df.head(maxrows)), '']

    def write(self, fname):
        p = os.path.join(self.out, fname)
        M.atomic_write_text(p, '\n'.join(self.md).strip() + '\n')
        return p


def head(subject, op, sub, H='见 H 列', base='同 H 实际父（8bp）', expo='见 exposure 列', support='原生'):
    return {'主体': subject, '算子': op, '分母': '两推导段有效配对日（n 加权）', '基准': base, '子集': sub, '单位': '年化百分点（ann_pp）', '日期': DATES, 'H': H,
            '成本': '源 8bp（冲击括号另列）', '支持': support, 'exposure': expo}


def load_deriv(stats):
    S = pd.concat([pd.read_csv(os.path.join(stats, 'descriptor_stats_%s.csv' % s), keep_default_na=False, na_values=[''], low_memory=False)
                   for s in DERIV], ignore_index=True)
    C = pd.concat([pd.read_csv(os.path.join(stats, 'comparison_stats_%s.csv' % s), keep_default_na=False, na_values=[''], low_memory=False)
                   for s in DERIV], ignore_index=True)
    R = pd.concat([pd.read_csv(os.path.join(stats, 'random_refs_%s.csv' % s), keep_default_na=False, na_values=['']).assign(segment=s)
                   for s in DERIV if os.path.exists(os.path.join(stats, 'random_refs_%s.csv' % s))], ignore_index=True)
    return S, C, R


def merge_deriv(S):
    S = S[S.status == 'COMPUTED'].copy()
    S['w'] = S.n.astype(float)
    out = []
    for did, g in S.groupby('desc_id'):
        w = g.w.values
        r = dict(desc_id=did, n_deriv=int(w.sum()))
        for s in DERIV:
            x = g[g.segment == s]
            r['D_%s' % s] = float(x.D.iloc[0]) if len(x) else np.nan
        for k in ('D', 'D_sc', 'D_imp', 'D_gross', 'turn_rel', 'port_size_lo_T', 'port_size_hi_T', 'edit_gap_mean_T', 'MDE80', 'se_H'):
            v = g[k].astype(float).values if k in g else np.full(len(g), np.nan)
            ok = np.isfinite(v) & (w > 0)
            r[k + '_deriv'] = float(np.sum(v[ok] * w[ok]) / np.sum(w[ok])) if ok.any() else np.nan
        out.append(r)
    return pd.DataFrame(out)


def rand_deriv(R):
    if not len(R):
        return pd.DataFrame(columns=['desc_id', 'mechanism'])
    R = R.assign(mcse2=R.mcse.astype(float) ** 2)
    g = R.groupby(['desc_id', 'mechanism'])
    out = g.agg(rmr_deriv=('real_minus_rand', 'mean'), mcse2=('mcse2', 'sum'), k=('mcse2', 'size'), paths_min=('n', 'min')).reset_index()
    out['mcse_deriv'] = np.sqrt(out.mcse2) / out.k                      # 两段等权均值的 MCSE
    return out.drop(columns=['mcse2', 'k'])


def part1(a):
    S, C, R = load_deriv(a.stats)
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    MD = merge_deriv(S).merge(D[['desc_id', 'block', 'family', 'measurement', 'parent', 'operator', 'param', 'alpha', 'memory', 'H', 'is_primary72',
                                 'primary_recipe', 'exposure']], on='desc_id', how='left')
    RD = rand_deriv(R)
    rp = Report('part1', a.out)
    rp.h(1, 'E6m REPORT part1 —— 推导两段（2010-2014 / 2015-2018）全部登记对象的作用量、对照与卡片初读')
    if 'stageS_dev' in os.path.realpath(a.stats):
        rp.p('**开发测试版：本文件全部数字来自 SYNTHETIC 合成账本（e6m_s_synth），不是收益，不得引用。**')
    rp.p('用途：plan §13.4 part1。只含推导两段；数字全部来自推导段机器表（seal_deriv 之后生成）。新对象标 `%s`；与 E6k / E6l 登记表交集对象标 `%s`，'
         '只作锚与基线。不设显著性门、不写判词；新算子 replacement_preference_status = NOT_AUTHORIZED，deployment_authorized = false。'
         '机器表目录：`%s`。' % (M.LABEL_FIRST_LOOK, M.LABEL_SECOND, M.san(M.rel(a.stats)) if a.stats.startswith(M.work()) else M.san(a.stats)))
    # §1 主展示 72
    rp.h(2, '1. 主展示 72 行（12 配方 × 六形态）')
    rr = RD.pivot_table(index='desc_id', columns='mechanism', values=['rmr_deriv', 'mcse_deriv'], aggfunc='first') if len(RD) else pd.DataFrame()
    if len(rr):
        rr.columns = ['%s_%s' % (x, y) for x, y in rr.columns]
    P72 = MD[MD.is_primary72 == 'True'].merge(rr, left_on='desc_id', right_index=True, how='left') if len(rr) else MD[MD.is_primary72 == 'True']
    for rec in sorted(set(P72.primary_recipe), key=lambda x: (int(x) if str(x).isdigit() else 999, str(x))):
        t = P72[P72.primary_recipe == rec].sort_values('parent')
        r0 = t.iloc[0]
        rec_lab = '%s %s|%s|%s|%s|%s' % (rec, r0.measurement, r0.operator, r0.param, r0.alpha, r0.memory)
        cols = ['parent', 'H'] + ['D_%s' % s for s in DERIV] + ['D_deriv', 'se_H_deriv', 'MDE80_deriv', 'D_sc_deriv', 'D_imp_deriv', 'D_gross_deriv', 'turn_rel_deriv',
                                                         'port_size_lo_T_deriv', 'port_size_hi_T_deriv', 'edit_gap_mean_T_deriv'] + \
            ['%s_%s' % (x, m) for m in P_MECH for x in ('rmr_deriv', 'mcse_deriv')] + ['exposure']
        rp.table(t[[c for c in cols if c in t.columns]], head('配方 %s × 六形态' % rec, rec_lab, 'primary72'), 'E6M-P1-72-%s' % str(rec).replace(':', '-').replace('|', '-'))
    # §2 全部登记描述符分布
    rp.h(2, '2. 全部登记描述符按 块 × 算子 × 记忆 × 参数 的分布（测量 × 母体 × H1…20 汇总）')
    grid = []
    reg = MD[MD.block != 'PARENT']
    for k, g in reg.groupby(['block', 'operator', 'memory', 'param', 'alpha']):
        x = g.D_deriv.astype(float)
        grid.append(dict(block=k[0], operator=k[1], memory=k[2], param=k[3], alpha=k[4], cells=int(x.notna().sum()),
                         share_pos=float((x > 0).mean()) if x.notna().any() else np.nan, q10_ann_pp=float(x.quantile(.1)), median_ann_pp=float(x.median()),
                         q90_ann_pp=float(x.quantile(.9)), median_MDE80_ann_pp=float(g.MDE80_deriv.median())))
    rp.table(pd.DataFrame(grid), head('全部登记描述符（不含 PARENT）', '各算子', '块 × 算子 × 记忆 × 参数', 'H 1…20'), 'E6M-P1-GRID', maxrows=60)
    # §3 比较视图
    rp.h(2, '3. 登记比较视图（comparison_manifest；左 − 右，日层配对后段均）')
    Cc = C[C.status == 'COMPUTED'] if 'status' in C else C
    cv = Cc.groupby(['view', 'segment']).agg(comparisons=('comparison_id', 'count'), median_D_ann_pp=('D_ann_pp', 'median'),
                                              share_pos=('D_ann_pp', lambda x: float((x > 0).mean())), median_se_H_ann_pp=('se_H_ann_pp', 'median'),
                                              median_mde80_ann_pp=('mde80_ann_pp', 'median')).reset_index()
    rp.table(cv, head('全部登记比较', '左 − 右', '视图 × 段', base='比较右端（见 comparison_manifest）'), 'E6M-P1-VIEWS', maxrows=80)
    # §4 随机参照
    rp.h(2, '4. 推导段随机参照（真实 − 随机；MCSE 与路径数）')
    if len(R):
        R2 = R.assign(hi=R.real_minus_rand >= 2 * R.mcse, lo=R.real_minus_rand <= -2 * R.mcse)
        rt = R2.groupby(['mechanism', 'segment']).agg(objects=('desc_id', 'count'), median_mcse=('mcse', 'median'), share_rmr_ge_2mcse=('hi', 'mean'),
                                                     share_rmr_le_neg2mcse=('lo', 'mean'), paths_min=('n', 'min'), paths_max=('n', 'max')).reset_index()
        rp.table(rt, head('登记随机行', '各机制', '机制 × 段', base='同对象随机路径均值'), 'E6M-P1-RANDOM')
    else:
        rp.p('推导段随机参照表缺（SOURCE_WAIT）。')
    # §5 ⑬
    rp.h(2, '5. 卡片 ⑬：推导段配对 MDE80（只是列，不作门；plan §9.5）')
    t13 = os.path.join(a.stats, 'cards_t13_deriv_E6m.csv')
    if os.path.exists(t13):
        rp.table(pd.read_csv(t13), head('18 卡绑定比较', '配对差', '卡 × 段', base='卡片绑定比较的右端'), 'E6M-P1-T13')
    # §6 状态
    rp.h(2, '6. 运行状态（Stage 0 S / A1-auto / 封存）')
    for nm, p in (('Stage 0 S 门', M.P('stage0_S', 'stage0_S_gate.json')), ('A1-auto（S）', M.P('registration', 'a1_auto_E6m_S.json')),
                  ('seal_deriv', M.P('seal_deriv.json'))):
        if os.path.exists(p):
            j = json.load(open(p, encoding='utf-8'))
            keep = {k: j[k] for k in ('counts', 'all_pass', 'all_ok', 'fail_items', 'source_wait_items', 'not_run_items', 'n_files', 'queue_missing',
                                      'failed_unresolved', 'mc_done', 'not_pass') if k in j}
            rp.p('- %s：`%s`' % (nm, M.san(json.dumps(keep, ensure_ascii=False))[:900]))
        else:
            rp.p('- %s：文件缺（SOURCE_WAIT）' % nm)
    p = rp.write('E6m_REPORT_part1.md')
    return p, rp.tables


def record_b(a):
    import e6m_s_gate as GT
    fz = M.P('registration', GT.FREEZE)
    cond = M.P('registration', GT.AUTH_COND)
    sd = M.P('seal_deriv.json')
    j = lambda p: json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    C_, S_ = j(cond), j(sd)
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str, usecols=['desc_id', 'block'])
    pre = j(M.P('registration', GT.AUTH_PRE))
    if pre:                                                                # 方式 B：冻结时已照录事前整表授权
        md = ['# E6m 记录 B（方式 B：事前整表授权，两包冻结时照录）', '',
              '用途：brief W11 / §5 S3。用户原话"%s"（%s），照录于 `registration/%s`；授权绑定冻结清单 sha `%s`，当前冻结清单 sha `%s`（%s）。'
              '本文件由执行端生成，只陈述授权与生效条件，不代写、不改写原话。' % (
                  pre.get('user_quote', ''), pre.get('user_quote_date', ''), GT.AUTH_PRE, str(pre.get('freeze_sha256', ''))[:16],
                  M.sha_file(fz)[:16] if os.path.exists(fz) else '—',
                  '一致' if os.path.exists(fz) and pre.get('freeze_sha256') == M.sha_file(fz) else '不一致：授权失效，须重新授权'), '',
              '## 1. 授权对象', '',
              '- 冻结清单：`registration/%s`，sha256 `%s`。' % (GT.FREEZE, M.sha_file(fz) if os.path.exists(fz) else 'SOURCE_WAIT（尚未冻结）'),
              '- 对象：主 %d（%s）+ 附属 384 + 登记比较 / 随机 / 对照全部，× 两后段（2019-2023 / 2024-2026）。' % (
                  len(D), '、'.join('%s %d' % kv for kv in D.block.value_counts().sort_index().items())),
              '- 推导段封存：`seal_deriv.json` %s（文件 %s 个，队列缺失 %s，MC 完成 %s）。' % (
                  'all_ok' if S_.get('all_ok') else '未完成或未通过', S_.get('n_files', '—'), len(S_.get('queue_missing', [])) if S_ else '—',
                  json.dumps(S_.get('mc_done', {}), ensure_ascii=False)), '',
              '## 2. 后段执行端会做的事（与推导段同一规则、同一代码 sha；方式 B 不停）', '',
              '两后段确定性账户 + 随机七机制首 1,024 路径 + MC 增补 → `seal_post` → 全段统计 / 政策 / bootstrap / 四账户 / T 重估桥 / MATCH_CAP / 前沿 → '
              'B3 并入（锚过后）→ B4（含签名 1–3）/ B5（含状态时钟）/ B6 读法 → 附属第 7 项连续链 → 副本包 → 七份 REPORT + cards + E7 准备页 → 交付。', '',
              '## 3. 生效条件现状（post_gate 每次进入后段时核）', '',
              '- 条件回执 `registration/%s`：%s' % (GT.AUTH_COND, M.san(json.dumps(C_, ensure_ascii=False))[:1200] if C_ else 'SOURCE_WAIT（未写）'),
              '- 授权绑定的清单 sha 与当前清单不一致即失效（任何语义 amendment），须用户重新授权。', '',
              '## 4. 不授权的事', '',
              '- 全部对象 `deployment_authorized = false`；新路线 `replacement_preference_status = NOT_AUTHORIZED`；生产 v2 / v3 / U34 / U35 / I11 / DEV / 源执行时钟不改；E7 HOLD。']
        p = os.path.join(a.out, 'E6m_record_B_draft.md')
        os.makedirs(a.out, exist_ok=True)
        M.atomic_write_text(p, '\n'.join(md) + '\n')
        return p
    md = ['# E6m 记录 B 草稿（方式 A：推导两段已算完并封存；两后段等用户一句话授权）', '',
          '用途：brief W11 / §5 S3。本文件由执行端生成，**不是授权**；用户对两后段的授权以用户原话为准，执行端照录到 '
          '`registration/%s`（原话 + 日期 + 冻结清单 sha），不代写、不改写。' % GT.AUTH_APPROVED, '',
          '## 1. 授权对象', '',
          '- 冻结清单：`registration/%s`，sha256 `%s`。' % (GT.FREEZE, M.sha_file(fz) if os.path.exists(fz) else 'SOURCE_WAIT（尚未冻结）'),
          '- 对象：主 %d（%s）+ 附属 384 + 登记比较 / 随机 / 对照全部，× 两后段（2019-2023 / 2024-2026）。' % (
              len(D), '、'.join('%s %d' % kv for kv in D.block.value_counts().sort_index().items())),
          '- 推导段封存：`seal_deriv.json` %s（文件 %s 个，队列缺失 %s，MC 完成 %s）。' % (
              'all_ok' if S_.get('all_ok') else '未完成或未通过', S_.get('n_files', '—'), len(S_.get('queue_missing', [])) if S_ else '—',
              json.dumps(S_.get('mc_done', {}), ensure_ascii=False)), '',
          '## 2. 授权后执行端会做的事（与推导段同一规则、同一代码 sha）', '',
          '两后段确定性账户 + 随机七机制首 1,024 路径 + MC 增补（MCSE ≤ .03 或 8,192）→ `seal_post` → 全段统计 / 政策 / bootstrap / 四账户 / '
          'T 重估桥 / MATCH_CAP / 前沿 → B3 并入（N8 已算、锚过后）→ B4 / B5 / B6 读法 → 副本包 → 七份 REPORT + cards + E7 准备页 → 交付。', '',
          '## 3. 生效条件现状（post_gate 每次进入后段时核）', '',
          '- 条件回执 `registration/%s`：%s' % (GT.AUTH_COND, M.san(json.dumps(C_, ensure_ascii=False))[:1200] if C_ else 'SOURCE_WAIT（未写）'),
          '- 冻结清单 sha 在授权到进入后段之间不得变化；任何语义 amendment 使授权失效、需新授权。', '',
          '## 4. 不授权的事', '',
          '- 全部对象 `deployment_authorized = false`；新路线 `replacement_preference_status = NOT_AUTHORIZED`；生产 v2 / v3 / U34 / U35 / I11 / DEV / 源执行时钟不改；E7 HOLD。', '',
          '## 5. 请用户确认的一句话（方式 A）', '',
          '> 授权 E6m 两后段按冻结清单（sha 见 §1）运行。', '',
          '（用户可用自己的话；执行端照录原话与日期。）']
    p = os.path.join(a.out, 'E6m_record_B_draft.md')
    os.makedirs(a.out, exist_ok=True)
    M.atomic_write_text(p, '\n'.join(md) + '\n')
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['part1', 'record-b'])
    ap.add_argument('--stats', default='')
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    a.out = a.out or M.P('reports')
    if a.task == 'part1':
        if os.path.realpath(a.stats).startswith(os.path.realpath(M.P('results')) + os.sep):
            import e6m_s_seal as SEAL                               # 真实结果：封存后才读
            SEAL.require('deriv')
        p, tabs = part1(a)
        outs = [p] + tabs
    else:
        p = record_b(a)
        outs = [p]
    M.write_receipt(os.environ.get('E6M_TASK', 'S_%s' % a.task.replace('-', '_')), outs, status='SUCCEEDED', code=[__file__, M.__file__],
                    wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(task=a.task, out=M.san(M.rel(p)), tables=len(outs) - 1, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
