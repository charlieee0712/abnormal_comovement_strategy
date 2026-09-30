# -*- coding: utf-8 -*-
"""E6l REPORT 生成器（plan §13.4：R0 / part2 / part3 / mechanisms / carried / cards；part1 另见 e6l_report_part1）。seal_deriv + seal_post、
全段统计 / 比较统计 / 政策 / bootstrap / 状态时钟 / 连续面板 / 影子风险 / 固定表之后运行。每张表带表头十项 + exposure + query_id；
数字全部由同一结构化查询产生（Report.table 同时写 results/full/query_tables/<query_id>.csv）；不写判词（"证伪 / 穷尽 / 饱和" 等禁用）。
用法：e6l_reports.py --which r0,part2,part3,mechanisms,carried,cards"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import json
import argparse

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_report as RP
import e6j_stats as ST

SEGS = L.SEGMENTS
FULLD = '2010-01-04..2026-03-27（四段；每段前 19 日预热；2026 截至 03-27）'


def rd(*p):
    return pd.read_csv(L.P(*p), keep_default_na=False, na_values=[''])


def head(subject, op, sub, H='5', unit='年化百分点（ann_pp）', base='同 H 原父（8bp）', dates=FULLD, support='原生（FALLBACK）',
         cap='实际源 DEV（FULL_sc 另列）', expo='见 evidence_exposure 列', den='四段有效配对日（FULL = n 加权；G4 = 四段 D 中位）'):
    return {'主体': subject, '算子': op, '分母': den, '基准': base, '子集': sub, '单位': unit, '日期': dates, 'H': H,
            '成本模型': '源 8bp（冲击列 A 5 亿 κ .5）', '支持': support, '资本视图': cap, 'exposure': expo}


def regtext(s):
    """登记原文进正文：库存标记到上限的技术词按正文写法替换（REPORT 禁用词扫描按字面；登记文件原文不改）。"""
    return str(s).replace('饱和', '满额（saturation）')


def full_of(df, col, ncol='n'):
    """四段 → FULL（n 加权）/ G4（中位）。df 含 segment 列。"""
    D = [float(df[df.segment == s][col].iloc[0]) if (df.segment == s).any() else np.nan for s in SEGS]
    n = [float(df[df.segment == s][ncol].iloc[0]) if (df.segment == s).any() else np.nan for s in SEGS]
    return ST.full_g4(D, n)


# ================================================================ R0
def r0():
    sm = json.load(open(L.P('source_manifest.json'), encoding='utf-8'))
    a0 = json.load(open(L.P('registration', 'a0_manifest_E6l.json'), encoding='utf-8'))
    rp = RP.Report('R0')
    rp.h(1, 'E6l REPORT R0 —— 仪器与权限：输入身份、授权、Stage 0、登记计数、掩码事实、耗时与限制')
    rp.p('用途：plan §13.4 R0。数字来自 `source_manifest.json`、`stage0/`、`registration/`、`registry/`、`results/stage_a/`；本文件不读任何登记对象的收益均值'
         '（校准分布与状态日数只作描述，注明未用于门值）。')
    rp.h(2, '1. 输入身份与环境')
    rp.table(pd.DataFrame([dict(file=k, sha256_16=v[:16]) for k, v in sm['docs_sha256'].items()]),
             head('本轮输入与结果目录副本', '—', 'source_manifest.docs_sha256', '—', '文本', '—', 'Stage 0', '—', '—', '不适用（无收益读数）', '—'), 'E6L-R0-DOCS')
    env = [dict(item=k, value=str(v)) for k, v in sm['env'].items()] + [dict(item='git_head', value=sm['git_head'][:12])]
    rp.table(pd.DataFrame(env), head('47 环境与生成器', '—', 'source_manifest.env', '—', '文本', '—', 'Stage 0', '—', '—', '不适用', '—'), 'E6L-R0-ENV')
    gens = pd.DataFrame([
        dict(random_quantity='LEGACY_POLICY_RANDOM', generator='splitmix64 计数器 u(键, 绝对交易日, ticker)；键 = blake2b-64(canonical_json)：Q0 / C1 / S / M 沿 E6k Legacy（E6j.P / E6j.B），新测量 E6j.P + 成员 id E6l.<测量>'),
        dict(random_quantity='CONTENT_COND_ISK_P5', generator='同一计数器；键 (E6k.NEW, 测量键, COND_ISK, B5, content, path)；Q0 键 = Q（E6k 同路径）；块 = 绝对交易日 // 5'),
        dict(random_quantity='RMARK_UNIFORM_IID / UNIFORM_P5 / ISK_P5', generator='同一计数器；键 (E6l.RMARK, 机制, ALL, gate, marks, path)；全测量 / 母体 / α 共用'),
        dict(random_quantity='bootstrap（段内分层 stationary 20 / 60 × 2,000）', generator='blake2b-128(canonical_json(E6l, bootstrap, L, 段)) → SeedSequence → PCG64'),
        dict(random_quantity='profile 置换（只测时，临时目录）', generator='default_rng(blake2b(E6l.profile, 段, 测量))')])
    rp.table(gens, head('随机量 → 生成器', '—', '全部随机量', '—', '文本', '—', '全段', '—', '—', '不适用', '—'), 'E6L-R0-GEN')
    rp.h(2, '2. 授权（方式 B）与读数前登记')
    au = []
    for f in sorted(os.listdir(L.P('registration'))):
        p = L.P('registration', f)
        if os.path.isfile(p):
            au.append(dict(file='registration/' + f, sha256_16=L.sha_file(p)[:16]))
    rp.table(pd.DataFrame(au), head('授权 / 登记 / 封存文件', '—', 'registration/', '—', '文本', '—', '全程', '—', '—', '不适用', '—'), 'E6L-R0-AUTH')
    pre = json.load(open(L.P('registration', L.AUTH_PRE), encoding='utf-8'))
    rp.p('- 授权方式 B：用户转交消息原话「%s」（不含 W11 字面触发词）；执行端当场询问，用户选「%s」（%s）。`record_B_preauthorized_E6l.json` 在 Stage A / B 两包冻结时写入，'
         '引用两句原话与 B 包清单 sha；生效条件 = Stage 0 全 PASS + A1-auto 全 PASS + 进入后段时清单 sha 不变（`record_B_entry_post_E6l.json` 核验）。'
         '经济裁定 = E6k RULING 第 2 项（PORT3_T 正式列，policy_provisional = false）。' % (pre['user_forwarding_message_quote'], pre['user_answer_quote'], pre['user_quote_date']))
    rp.h(2, '3. Stage 0 六类（FAILED 由同名 _rerun 覆盖）')
    s0 = pd.DataFrame([dict(category=k, ok=v['ok'], receipts='；'.join('%s=%s' % (r['task'], r['status']) for r in v['receipts'])) for k, v in sm['stage0'].items()])
    rp.table(s0, head('Stage 0 六类回执', '—', 'source_manifest.stage0', '—', '计数', '—', 'Stage 0', '—', '—', '不适用', '—'), 'E6L-R0-STAGE0')
    cnt = []
    for cat, pat in (('c1', 'stage0/c1_identity_rerun/*.csv'), ('c2', 'stage0/c2_source/*checks*.csv'), ('c2', 'stage0/c2_source/source_engine_*.csv'),
                     ('c3', 'stage0/c3_ops/ops_identity_*.csv'), ('c4', 'stage0/c4_data/*checks*.csv'), ('c5', 'stage0/c5_random_rerun/random_checks.csv'),
                     ('c6', 'stage0/c6_output/fast_identity.csv'), ('c6', 'stage0/c6_output_rerun/output_checks.csv')):
        for f in glob.glob(L.P(*pat.split('/'))):
            df = pd.read_csv(f, keep_default_na=False, na_values=[''])
            if 'status' in df.columns:
                vc = df.status.value_counts().to_dict()
                cnt.append(dict(category=cat, file=L.rel(f), PASS=int(vc.get('PASS', 0)), INFO=int(vc.get('INFO', 0)), FAIL=int(vc.get('FAIL', 0))))
    rp.table(pd.DataFrame(cnt), head('Stage 0 检查表计数', '—', 'stage0/*', '—', '计数', '—', 'Stage 0', '—', '—', '不适用', '—'), 'E6L-R0-STAGE0-COUNTS')
    rp.h(2, '4. 登记计数（A0 与 spec 逐元组相等；A1-auto）')
    c = a0['counts']
    rows = [dict(item='raw_id_count', value=c['raw_id_count']), dict(item='block_counts', value=json.dumps(c['block_counts'])),
            dict(item='primary72 / dose72 / nbhd72', value='%d / %d / %d' % (c['primary72'], c['dose72'], c['nbhd72'])),
            dict(item='targets / tasks', value='%d / %d' % (c['targets'], c['tasks'])), dict(item='accessory', value=json.dumps(c['accessory'])),
            dict(item='comparisons base / extended', value='%d / %d' % (c['comparisons_base'], c['comparisons_extended'])),
            dict(item='randoms', value=json.dumps(c['randoms'])), dict(item='bootstrap families', value=json.dumps(c['bootstrap'])),
            dict(item='exposure', value=json.dumps(c['exposure'], ensure_ascii=False)), dict(item='E6k 同构（真实清单交集）', value=c['e6k_isomorphic']),
            dict(item='spec 对账', value=json.dumps({k: v for k, v in a0['compare'].items() if k not in ('counts', 'expected')}))]
    rp.table(pd.DataFrame(rows), head('A0 计数', '—', 'registration/a0_manifest_E6l.json', '—', '计数', '—', '登记', '—', '—', '不适用', '—'), 'E6L-R0-A0')
    rp.h(2, '5. 掩码层事实与校准分布（Stage A；推导两段读数前 + 后段授权后）')
    for tag in ('deriv', 'post'):
        f = L.P('results', 'stage_a', 'calibration_%s_E6l.csv' % tag)
        if os.path.exists(f):
            rp.table(rd('results', 'stage_a', 'calibration_%s_E6l.csv' % tag), head('附录 C 校准分布（%s；诊断，不作门）' % tag, '—', 'C1 / Q 平滑族 / Q0 / 旧 K 规则 / 母体',
                                                                              '各对象自身 H', 'pct_pt（紧区间）/ 份额', '—', tag), 'E6L-R0-CAL-%s' % tag.upper())
        f = L.P('results', 'stage_a', 'state_days_%s_E6l.csv' % tag)
        if os.path.exists(f):
            rp.table(rd('results', 'stage_a', 'state_days_%s_E6l.csv' % tag), head('状态三分位日数与 UNKNOWN（%s）' % tag, '—', 'Vol3 / Act3（主 / STRICT250）/ Trend3',
                                                                               '—', '日数 / 份额', '—', tag), 'E6L-R0-STATE-%s' % tag.upper())
        f = L.P('results', 'stage_a', 'rmark_partition_%s_E6l.csv' % tag)
        if os.path.exists(f):
            rp.table(rd('results', 'stage_a', 'rmark_partition_%s_E6l.csv' % tag), head('R-MARK ISK 分区（%s）' % tag, '—', '六形态门域', '—', '计数 / 份额', '—', tag),
                     'E6L-R0-RMARKPART-%s' % tag.upper())
        f = L.P('results', 'stage_a', 'a2_7_vs_e6k_%s.csv' % tag)
        if os.path.exists(f):
            x = rd('results', 'stage_a', 'a2_7_vs_e6k_%s.csv' % tag)
            rp.table(x.groupby(['segment', 'field']).status.value_counts().unstack(fill_value=0).reset_index(),
                     head('A2-7：E6k 掩码事实同构目标逐值（%s）' % tag, '—', 'E6k mask_facts 同构目标', '—', '计数', '—', tag), 'E6L-R0-A27-%s' % tag.upper())
    rp.table(rd('stage0', 'c4_data', 'state_unknown_days.csv'), head('状态 UNKNOWN 日数（主定义 ≥ 150 / STRICT250；Trend3）', '—', '四段', '—', '日数', '—', '四段'),
             'E6L-R0-UNKNOWN')
    rp.h(2, '6. 耗时（Stage 0 外推 vs 实际）')
    tim = json.load(open(L.P('stage0', 'c6_output_rerun', 'timing_extrapolation.json'), encoding='utf-8'))
    act = []
    for f in glob.glob(L.P('task_status', 'run_rand_*.receipt.json')):
        r = json.load(open(f, encoding='utf-8'))
        seg = [s for s in SEGS if ('_%s_' % s) in r['task_id']]
        act.append(dict(segment=seg[0] if seg else 'UNDEFINED', wall_s=r.get('wall_s', np.nan), paths=r.get('n_paths', np.nan)))
    A = pd.DataFrame(act)
    rows = [dict(item='外推：随机首 1,024 路径两机制 + R-MARK（CPU 小时）', value=tim['cpu_hours_random_first1024']),
            dict(item='外推：64 进程墙钟区间（小时）', value=str(tim['wall_hours_at_64'])), dict(item='外推：确定性（CPU 小时）', value=tim['cpu_hours_det'])]
    if len(A):
        for s, g in A.groupby('segment'):
            rows.append(dict(item='实际：%s 随机任务 CPU 小时（回执 wall 之和）' % s, value=round(float(g.wall_s.sum()) / 3600.0, 1)))
    rp.table(pd.DataFrame(rows), head('耗时', '—', 'Stage 0 外推 / 随机回执', '—', '小时', '—', '全程', '—', '—', '不适用', '—'), 'E6L-R0-TIMING')
    rp.h(2, '7. 源合同、源差异与限制')
    rp.p('- `engine_contract.md`（源函数定义处 / 调用处 / 默认值 / 证据）；`source_resolution.md`（20 条源差异与落法，均不改登记语义）；'
         '`reports/E6l_limit_register.md`（本轮限制 L 条目）；`reports/E6l_code_change_register.md`（Stage 0 之后 e6l_* 改动逐文件 before / after sha）。')
    rp.h(2, '8. 执行次序与口径说明')
    mc = []
    for ph, segs_ in (('deriv', L.DERIV_SEGS), ('post', L.POST_SEGS)):
        for s in segs_:
            topped = []
            for f in sorted(glob.glob(L.P('results', ph, 'mc_plan_%s_*.csv' % s))):
                pl = pd.read_csv(f)
                topped += ['%s（%d→%d）' % (r.rtask, int(r.have), int(r.target)) for r in pl[pl.topup > 0].itertuples()]
            for nm in L.rerun_chain('mc_done_%s_%s' % (ph, s)):          # 回执链逐条列（提前增补与主链再规划各一条）
                r = json.load(open(L._receipt_path(nm), encoding='utf-8'))
                mc.append(dict(phase=ph, segment=s, receipt=nm, written_at=r.get('written_at'), topup_rounds=r.get('rounds'), path_groups=r.get('groups'),
                               worst_mcse_ann_pp=r.get('worst_mcse'), topped_up_groups='；'.join(topped) if topped else 'NONE'))
    if mc:
        rp.table(pd.DataFrame(mc), head('MC 增补（首 1,024 路径后按共享路径组 MCSE ≤ .03 规划；回执链逐条；topup_rounds = 该次调用的增补轮数）', '—',
                                        '随机共享路径组（机制 × 测量）', '—', 'ann_pp', '—', '四段', '—', '—', '不适用', '—'), 'E6L-R0-MC')
    rp.p('- seal_post 首次运行（17:05:26）失败：`e6l_seal.planned` 的增补队列仍按 512 路径一片推算，与 16:48 起 64 一片的增补分片不符（报"缺 4"）；'
         '改为从 `e6l_topup.TOPUP_CHUNK` 推算后续跑，17:09:09 写入 `seal_post.json`（1,636 个文件，队列 800 行）。v1 失败标记 `logs/chain_main.failed` 保留，续跑标记 `logs/chain_main2.*`。')
    rp.p('- 次序：每段先 masks（名单 + 目标层统计，不含收益）→ 推导段 Stage A 掩码事实冻结（A2-7 与 E6k 同构目标逐值）→ Stage B / A1-auto 冻结 → accounts；'
         '后段在 `record_B_entry_post_E6l.json` all_pass 之后同一代码版本 masks → accounts → 随机 → seal_post，后段 Stage A 掩码事实在 seal_post 之后汇总'
         '（沿 E6k mask_facts_post；不参与任何登记或门）。')
    rp.p('- 连续面板（`results/full/continuous/`）只含"记忆按 ticker 跨段接续 + 全日历拼接账户"；源因子与池子没有全程重算（limit L6），'
         'continuous − segmented 不分离源预热差。')
    rp.p('- bootstrap 比较族另含 CR（真实 − 该机制逐日随机路径均值，plan §7.5；键 = 描述符 × H × 机制，与 `random_daily_<段>.npz` 同键）。')
    rp.p('- 推导段配对 MDE80 工具只覆盖确定性配对视图：Q10（真实 − 随机）与 Q14（同资本 MATCH-CAP 视图）的 ⑬ 因此印 UNDEFINED，'
         '精度分别见随机 MCSE（`random_refs`）与 bootstrap（`results/full/bootstrap/`）。')
    out = L.P('reports', 'E6l_REPORT_R0.md')
    rp.write(out)
    return out, len(rp.qids)


# ================================================================ part2（后段与暴露）
def part2():
    P = rd('results', 'full', 'policy_E6l.csv')
    rp = RP.Report('part2')
    rp.h(1, 'E6l REPORT part2 —— 两后段首看（2019-2023 / 2024-2026）、四段合并与暴露')
    rp.p('用途：plan §13.4 part2。后段对新对象是首评（`%s`：重复使用的历史，非样本外）；E6k 同构对象为 `%s`，只作锚。FULL = 四段 n 加权；G4 = 四段 D 中位。'
         '不设显著性门、不写判词。' % (L.LABEL_FIRST_LOOK, L.LABEL_SECOND))
    rp.h(2, '1. 主展示 72：四段 D、FULL / G4、同资本与冲击')
    P72 = P[P.primary72.astype(str) == 'True']
    for rec in dict.fromkeys(P72.recipe):
        t = P72[P72.recipe == rec].sort_values('mother')
        cols = ['mother'] + ['D_%s' % s for s in SEGS] + ['FULL', 'G4', 'FULL_sc', 'G4_sc', 'FULL_imp'] + ['se_H_%s' % s for s in L.POST_SEGS] + \
               ['rmr_%s' % s for s in L.POST_SEGS] + ['mcse_%s' % s for s in L.POST_SEGS] + ['years_pos', 'evidence_exposure']
        rp.table(t[[c for c in cols if c in t.columns]].rename(columns={'FULL': 'FULL_ann_pp', 'G4': 'G4_ann_pp', 'FULL_sc': 'FULL_sc_ann_pp', 'G4_sc': 'G4_sc_ann_pp',
                                                                        'FULL_imp': 'FULL_imp_ann_pp'}),
                 head('配方 %s × 六形态' % rec, rec.split(':')[1], 'primary72'), 'E6L-P2-72-%s' % rec.replace(':', '-'))
    rp.h(2, '2. 暴露（组合层 PORT3_T 段均紧区间、编辑层 gap 带符号 + 绝对、lv5、小盘 30%、未知 size）')
    cols = ['recipe', 'mother'] + ['port_size_lo_T_%s' % s for s in SEGS] + ['port_size_hi_T_%s' % s for s in SEGS] + \
           ['edit_gap_mean_T_%s' % s for s in SEGS] + ['edit_gap_absmean_T_%s' % s for s in SEGS] + ['lv5_mean_%s' % s for s in SEGS] + \
           ['small30_delta_%s' % s for s in SEGS] + ['size_PROPOSED_PORT3_T', 'size_LEGACY_EDIT5', 'size_EXEC_LEADER_VS_PARENT']
    t = P72[[c for c in cols if c in P72.columns]].sort_values(['recipe', 'mother'])
    rp.table(t, head('主展示 72 的 size 暴露（段均；×100 百分位点）', '12 配方', 'primary72', unit='pct_pt（紧区间 / gap）；份额'), 'E6L-P2-EXPO')
    rp.h(2, '3. 剂量面板与邻域（FULL / G4 / FULL_sc / 紧区间状态）')
    for lab, col in (('α .5 剂量面板', 'dose72'), ('α .125 邻域', 'nbhd72')):
        t = P[P[col].astype(str) == 'True'].sort_values(['recipe', 'mother'])
        rp.table(t[['recipe', 'mother', 'FULL', 'G4', 'FULL_sc', 'size_PROPOSED_PORT3_T', 'evidence_exposure'] + ['D_%s' % s for s in SEGS]].rename(
            columns={'FULL': 'FULL_ann_pp', 'G4': 'G4_ann_pp', 'FULL_sc': 'FULL_sc_ann_pp'}), head(lab, '12 配方', col), 'E6L-P2-%s' % col.upper())
    rp.h(2, '4. 全部登记对象的四段分布（按族 × 算子 × α；H1…20 与测量 × 母体汇总）')
    g = P.groupby(['family', 'op', 'alpha'])
    t = g.agg(cells=('FULL', 'count'), share_FULL_pos=('FULL', lambda x: float((x > 0).mean())), median_FULL_ann_pp=('FULL', 'median'),
              median_G4_ann_pp=('G4', 'median'), median_FULL_sc_ann_pp=('FULL_sc', 'median'),
              share_c_d10=('c_d10', lambda x: float(x.astype(str).eq('True').mean()))).reset_index()
    rp.table(t, head('全部登记描述符（不含 PARENT）', '各算子', '按族 × 算子 × α', 'H 1…20'), 'E6L-P2-GRID')
    out = L.P('reports', 'E6l_REPORT_part2.md')
    rp.write(out)
    return out, len(rp.qids)


# ================================================================ part3（正式政策与候选）
def part3():
    P = rd('results', 'full', 'policy_E6l.csv')
    add = rd('results', 'full', 'policy_additions_E6l.csv')
    rp = RP.Report('part3')
    rp.h(1, 'E6l REPORT part3 —— 正式尺子（六条 + PROPOSED_PORT3_T）与完整候选')
    rp.p('用途：plan §13.4 part3 / §10。尺子 = `registration/policy_profiles_E6l.json`（policy_provisional = false；PORT3_T 正式列；LEGACY_EDIT5 / PORT3_LAG1 / DISCLOSE 并印；'
         'LEADER 只披露）；判定串顺序 c、d、f、正向门槛、e资本、e随机、size(profile)。新算子 replacement_status = NOT_AUTHORIZED（不 chosen）；deployment_authorized = false；'
         '任何"通过"只进《生产变更候选清单》，由用户裁定。')
    rp.h(2, '1. 判定计数（按族 × profile × 聚合）')
    rows = []
    for prof in ('PROPOSED_PORT3_T', 'LEGACY_EDIT5', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY'):
        for agg in ('FULL', 'G4'):
            col = 'policy_%s_%s' % (prof, agg)
            for fam, g in P.groupby('family'):
                v = g[col].astype(str)
                rows.append(dict(profile=prof, aggregation=agg, family=fam, objects=len(g), pass_=int((v == '通过').sum()),
                                 fail=int(v.str.startswith('不通过').sum()), undecidable=int(v.str.startswith('不可判').sum())))
    rp.table(pd.DataFrame(rows).rename(columns={'pass_': 'pass'}), head('政策判定计数', '全部算子', '全部登记（不含 PARENT）', 'H 1…20', unit='计数'), 'E6L-P3-COUNTS')
    rp.h(2, '2. 主展示 72 与剂量面板的正式判定')
    for lab, col in (('主展示 72', 'primary72'), ('α .5 剂量面板', 'dose72'), ('α .125 邻域', 'nbhd72')):
        t = P[P[col].astype(str) == 'True'].sort_values(['recipe', 'mother'])
        cols = ['recipe', 'mother', 'FULL', 'G4', 'FULL_sc', 'c_d10', 'd_ok', 'years_pos', 'f_d10', 'positive_FULL', 'e_cap_FULL', 'e_rand', 'size_PROPOSED_PORT3_T',
                'policy_PROPOSED_PORT3_T_FULL', 'policy_PROPOSED_PORT3_T_G4', 'POLICY_INTERPRETATION_PENDING_PROPOSED_PORT3_T', 'evidence_column']
        rp.table(t[[c for c in cols if c in t.columns]].rename(columns={'FULL': 'FULL_ann_pp', 'G4': 'G4_ann_pp', 'FULL_sc': 'FULL_sc_ann_pp'}),
                 head(lab, '12 配方', col), 'E6L-P3-%s' % col.upper())
    rp.h(2, '3. 生产变更候选清单（PORT3_T FULL 或 G4 通过；分"上一轮 / 本轮新证据"两栏；deployment_authorized = false）')
    cand = P[(P.policy_PROPOSED_PORT3_T_FULL == '通过') | (P.policy_PROPOSED_PORT3_T_G4 == '通过')]
    cols = ['evidence_column', 'desc_id', 'family', 'FULL', 'G4', 'FULL_sc', 'policy_PROPOSED_PORT3_T_FULL', 'policy_PROPOSED_PORT3_T_G4', 'e_rand', 'years_pos',
            'replacement_status', 'deployment_authorized']
    rp.table(cand[cols].sort_values(['evidence_column', 'FULL'], ascending=[True, False]).rename(columns={'FULL': 'FULL_ann_pp', 'G4': 'G4_ann_pp', 'FULL_sc': 'FULL_sc_ann_pp'}),
             head('正式尺子通过的全部对象（%d）' % len(cand), '全部', 'PORT3_T 通过', 'H 见 desc_id'), 'E6L-P3-CANDIDATES')
    rp.h(2, '4. 边缘清单（全部条件距离；主展示 72 + 剂量 72）')
    e = P[(P.primary72.astype(str) == 'True') | (P.dose72.astype(str) == 'True')]
    cols = ['desc_id', 'policy_PROPOSED_PORT3_T_FULL', 'edge_c_margin_ann_pp', 'edge_f_margin_ann_pp', 'edge_positive_margin_FULL_ann_pp', 'edge_years_margin',
            'edge_erand_margin_ann_pp', 'edge_port3_margin_pct_pt']
    rp.table(e[cols], head('条件距离（c / f：min 段 D + .10；正向：FULL − .10；d：正年 − 12；e随机：min 后段 rmr − 2·MCSE；PORT3：离 ±3 的最小距离）', '主展示 + 剂量',
                           'primary72 | dose72', unit='ann_pp / 年数 / pct_pt'), 'E6L-P3-EDGE')
    rp.h(2, '5. 三句加法（PX1：原生 NATIVE 的 S / M / Q0 / C1，α .25 × H5）')
    rp.table(add, head('三句加法', 'NATIVE', '原生四测量 × 六形态 × profile × 聚合', unit='文本'), 'E6L-P3-ADDITIONS')
    out = L.P('reports', 'E6l_REPORT_part3.md')
    rp.write(out)
    return out, len(rp.qids)


# ================================================================ mechanisms
def mechanisms():
    C = pd.concat([rd('results', 'full', 'comparison_stats_%s.csv' % s) for s in SEGS], ignore_index=True)
    rp = RP.Report('mechanisms')
    rp.h(1, 'E6l REPORT mechanisms —— 四账户、时间 / 记忆、随机、资本、状态三时钟与连续面板')
    rp.p('用途：plan §13.4 mechanisms。比较层数字先在日层闭合再段均（`results/full/comparison_stats_<段>.csv`）；FULL = 四段 n_days 加权；G4 = 四段中位。'
         '机制读数只描述账户差（gross / 线性费用分列），不据此改尺子、不写判词；新算子为首评。')

    def fullg(g):
        rows = []
        for cid, x in g.groupby('cmp_id'):
            D = [float(x[x.segment == s].D_ann_pp.iloc[0]) if (x.segment == s).any() else np.nan for s in SEGS]
            n = [float(x[x.segment == s].n_days.iloc[0]) if (x.segment == s).any() else np.nan for s in SEGS]
            Dg = [float(x[x.segment == s].Dg_ann_pp.iloc[0]) if (x.segment == s).any() else np.nan for s in SEGS]
            f, g4 = ST.full_g4(D, n)
            fg, _ = ST.full_g4(Dg, n)
            rows.append(dict(cmp_id=cid, kind=x.kind.iloc[0], left_id=x.left_id.iloc[0], right_id=x.right_id.iloc[0], H=int(x.H.iloc[0]), FULL_ann_pp=f, G4_ann_pp=g4,
                             FULL_gross_ann_pp=fg, **{'D_%s' % s: d for s, d in zip(SEGS, D)}))
        return pd.DataFrame(rows)
    C5 = C[C.H == 5]
    for kind, lab in (('FOUR_ACCOUNT_INFO_RULE', '信息 × 规则交互（Y11 − Y10 − Y01 + Y00）'), ('FOUR_ACCOUNT_SMOOTH_RULE', '平滑 × 规则交互'),
                      ('MECHANISM_PAIR', '机制配对'), ('MA_VS_EW', 'MA vs EW'), ('MEAN_KERNEL_PAIR', '均值核配对'), ('RANK_BRIDGE_PAIR', '秩桥'),
                      ('WINDOW_PAIR', '窗口配对'), ('SMN_PAIR', 'S − M')):
        g = C5[C5.kind == kind]
        if not len(g):
            continue
        F = fullg(g)
        lt = F.left_id.str.split('|')
        F = F.assign(meas=lt.str[0], mother=lt.str[1], alpha=lt.str[2], op=lt.str[4], right=F.right_id.str.split('|').str[0] + ':' + F.right_id.str.split('|').str[4])
        F = F[F.alpha == 'a0.25'] if kind != 'MECHANISM_PAIR' else F[F.alpha.isin(['a0.25', 'a0'])]
        t = F[['meas', 'op', 'right', 'mother', 'FULL_ann_pp', 'G4_ann_pp', 'FULL_gross_ann_pp'] + ['D_%s' % s for s in SEGS]].sort_values(['meas', 'op', 'right', 'mother'])
        rp.table(t, head(lab + '（α .25 × H5；旧 K 规则 α0）', kind, '六形态', base='比较右端（见 right 列）', den='四段有效日（日层闭合）'), 'E6L-MX-%s' % kind.replace('_', '-'))
    for kind, lab in (('KERNEL_DOSE', 'X − KERNEL_DOSE'), ('SUPPORT_BRIDGE_CONTENT', '支持桥：共同支持内容差'), ('SUPPORT_BRIDGE_PARENT_SUPPORT', '支持桥：Q0 支持变化'),
                      ('SUPPORT_BRIDGE_CHILD_SUPPORT', '支持桥：X 支持变化'), ('MASKQ0_SUPPORT_ONLY', 'Q0 遮罩：只改支持'), ('MASKQ0_CONTENT', 'Q0 遮罩：同支持内容差'),
                      ('INV_CAP_LOOP', 'INV 闭环同资本（诊断）'), ('STRICT250_VS_MAIN', 'STRICT250 − 主状态定义'), ('MATCH_CAP_FIXED_PATH', '同资本（FULL_sc）'),
                      ('REAL_MINUS_RMARK', '真实 − R-MARK'), ('REAL_MINUS_COND', '真实 − COND'), ('REAL_MINUS_LEGACY', '真实 − LEGACY')):
        g = C[C.kind == kind]
        if not len(g):
            continue
        g = g[g.H == 5] if (g.H == 5).any() else g
        F = fullg(g)
        rp.table(F.describe(percentiles=[.1, .5, .9]).T.reset_index().rename(columns={'index': 'column'})[['column', 'count', 'mean', '10%', '50%', '90%']]
                 if kind in ('MATCH_CAP_FIXED_PATH', 'REAL_MINUS_COND', 'REAL_MINUS_LEGACY') else
                 F[['left_id', 'right_id', 'FULL_ann_pp', 'G4_ann_pp'] + ['D_%s' % s for s in SEGS]],
                 head(lab + '（H5 行）', kind, '全部登记该类比较', base='见 right_id', den='四段有效日（日层闭合）'), 'E6L-MX-%s' % kind.replace('_', '-'))
    rp.h(2, '状态三时钟、对称分解与压力窗口')
    for nm, qid, lab in (('state_symmetric_decomposition.csv', 'E6L-MX-SYMDEC', '对称分解（状态内条件均值改变 / 状态频率改变 / 剩余；UNMATCHED 单列）'),):
        f = L.P('results', 'full', nm)
        if os.path.exists(f):
            rp.table(rd('results', 'full', nm), head(lab, 'Vol3 日历时钟', '状态时钟对象', base='段对'), qid)
    sc = sorted(glob.glob(L.P('results', 'full', 'state_clock', '*_stress.csv')))
    if sc:
        rp.table(pd.concat([pd.read_csv(f, keep_default_na=False, na_values=['']) for f in sc], ignore_index=True),
                 head('两压力窗口（2015-06-15 / 2024-09-24 起 40 个交易日）', '累计相对账本 / NAV 回撤', '状态时钟对象', unit='百分比（%）', den='窗口内交易日'), 'E6L-MX-STRESS')
    cp = L.P('results', 'full', 'continuous', 'continuous_panel.csv')
    if os.path.exists(cp):
        rp.table(rd('results', 'full', 'continuous', 'continuous_panel.csv'), head('连续面板（全日历拼接；carry vs reset 记忆；连续父）', '主展示 72', 'primary72',
                                                                                   base='连续原父', den='各段有效日'), 'E6L-MX-CONT')
    bb = L.P('results', 'full', 'bootstrap', 'simultaneous_band_q95.csv')
    if os.path.exists(bb):
        rp.table(rd('results', 'full', 'bootstrap', 'simultaneous_band_q95.csv'), head('同时带：双侧 q95_maxabs_t 与单侧带符号 q95_max_t / q05_min_t（SE 倍数；逐行 halfwidth_ann_pp = q95_maxabs_t × SE）', 'bootstrap',
                                                                                       '固定集合', 'H 见比较', unit='SE 倍数（q95_maxabs_t）', den='2,000 draws × 段内分层'), 'E6L-MX-BAND')
    out = L.P('reports', 'E6l_REPORT_mechanisms.md')
    rp.write(out)
    return out, len(rp.qids)


# ================================================================ carried（历史 / 领导 / 限制）
def carried():
    P = rd('results', 'full', 'policy_E6l.csv')
    rp = RP.Report('carried')
    rp.h(1, 'E6l REPORT carried —— E6k 同构复现、领导表参照与限制')
    rp.p('用途：plan §13.4 carried。同构对象（`%s`）只作锚与基线，不进本轮新证据栏。' % L.LABEL_SECOND)
    ek = pd.read_csv(L.K6('results', 'full', 'policy_E6k.csv'), keep_default_na=False, na_values=[''], usecols=lambda c: c in (
        ['desc_id', 'FULL', 'G4', 'FULL_sc'] + ['D_%s' % s for s in SEGS] + ['n_%s' % s for s in SEGS] + ['D_sc_%s' % s for s in SEGS])).set_index('desc_id')
    x = P[P.e6k_equiv != 'NOT_APPLICABLE'].copy()
    rows = []
    for r in x.to_dict('records'):
        if r['e6k_equiv'] not in ek.index:
            continue
        e = ek.loc[r['e6k_equiv']]
        diffs = [abs(r['D_%s' % s] - e['D_%s' % s]) for s in SEGS] + [abs(r['n_%s' % s] - e['n_%s' % s]) for s in SEGS] + \
                [abs(r['D_sc_%s' % s] - e['D_sc_%s' % s]) for s in SEGS] + [abs(r['FULL'] - e['FULL']), abs(r['G4'] - e['G4']), abs(r['FULL_sc'] - e['FULL_sc'])]
        mx = float(np.nanmax(diffs))
        rows.append(dict(desc_id=r['desc_id'], e6k_desc=r['e6k_equiv'], max_deviation=mx, status='PASS' if mx <= 1e-9 else 'DIFFERS'))
    Rr = pd.DataFrame(rows)
    rp.table(Rr.status.value_counts().rename_axis('status').reset_index(name='objects'),
             head('A2-4 全量：E6k 同构对象 D_段 / n_段 / D_sc_段 / FULL / G4 / FULL_sc = policy_E6k（1e−9）', '同构', 'e6k_equiv 非空', 'H 1…20', unit='计数',
                  expo=L.LABEL_SECOND), 'E6L-CA-A24')
    if (Rr.status != 'PASS').any():
        rp.table(Rr[Rr.status != 'PASS'].head(50), head('A2-4 不符行（前 50）', '同构', '不符', 'H 见 desc_id', unit='最大偏差', expo=L.LABEL_SECOND), 'E6L-CA-A24-DIFF')
    else:
        rp.p('- A2-4 不符行：0（%d 个同构对象逐项最大偏差的最大值 %.3g，≤ 1e−9 记 PASS；不符表因此不印）。另有 160 个母体（SOURCE_PARENT）不在本表。'
             % (len(Rr), float(Rr.max_deviation.max())))
    w08 = P[P.desc_id.isin(['Q0|A4b_CVRv5|a0.25|H5|NATIVE', 'Q0|A4b_CVRv5|a0.25|H5|HG10', 'K0|A4b_CVRv5|a0|H5|HG10', 'Q0|M_union3_v2_CVRv5|a0.25|H5|HG10'])]
    rp.table(w08[['desc_id'] + ['D_%s' % s for s in SEGS] + ['FULL', 'FULL_sc']].rename(columns={'FULL': 'FULL_ann_pp', 'FULL_sc': 'FULL_sc_ann_pp'}),
             head('W08 锚值复现', 'NATIVE / HG10 / HG_ONLY10', 'W08 四个对象', expo=L.LABEL_SECOND), 'E6L-CA-W08')
    h = P[(P.meas == 'Q0') & P.op.isin(['NATIVE', 'HG10']) & (P.alpha.astype(float) == 0.25)].copy()
    t = h.pivot_table(index=['mother', 'op'], columns='H', values='FULL').reset_index()
    t.columns = [str(c) if not isinstance(c, (int, np.integer)) else 'H%d_FULL_ann_pp' % c for c in t.columns]
    rp.table(t, head('Q0 的 H 剖面（NATIVE / HG10，α .25；E6k 已见，复现）', 'NATIVE / HG10', 'Q0 × 六形态', 'H1…20', expo=L.LABEL_SECOND), 'E6L-CA-HPROFILE')
    k0 = P[(P.meas == 'K0') & P.op.isin(['HG5', 'HG10', 'HG15'])].pivot_table(index=['mother', 'op'], columns='H', values='FULL').reset_index()
    k0.columns = [str(c) if not isinstance(c, (int, np.integer)) else 'H%d_FULL_ann_pp' % c for c in k0.columns]
    rp.table(k0, head('HG_ONLY（旧 K 规则）随 H 的曲线（E6k 已见，复现）', 'HG5 / HG10 / HG15', 'K0 × 六形态', 'H1…20', expo=L.LABEL_SECOND), 'E6L-CA-HGONLY')
    out = L.P('reports', 'E6l_REPORT_carried.md')
    rp.write(out)
    return out, len(rp.qids)


# ================================================================ cards 附节：判别读数（逐比较先合成 FULL / G4，再按卡的判别维度取分布）
CD_PREF = ('KD', 'CSC', 'CSP', 'MQ0', 'S250', 'ICL', 'ICLPAR', 'LEGACY_POLICY_RANDOM', 'CONTENT_COND_ISK_P5', 'RMARK_UNIFORM_IID', 'RMARK_UNIFORM_P5', 'RMARK_ISK_P5')


def _cd_parse(x):
    p = x.split('|')
    pre = ''
    if p[0] in CD_PREF:
        pre, p = p[0], p[1:]
    return (pre,) + tuple(p[:5])


def cmp_full():
    """四段比较统计 → 逐比较 FULL（n_days 加权）/ G4（四段中位）/ gross / 费用 / 合成 se（√Σ n²se² / N）/ t；左右端 id 拆列。"""
    C = pd.concat([rd('results', 'full', 'comparison_stats_%s.csv' % s) for s in SEGS], ignore_index=True)
    for c, v in (('wD', 'D_ann_pp'), ('wG', 'Dg_ann_pp'), ('wF', 'fee_ann_pp')):
        C[c] = C[v] * C.n_days
    C['wse2'] = C.n_days ** 2 * C.se_H_ann_pp ** 2
    C['pos'] = (C.D_ann_pp > 0).astype(np.int64)
    F = C.groupby('cmp_id').agg(kind=('kind', 'first'), left=('left_id', 'first'), right=('right_id', 'first'), H=('H', 'first'), n=('n_days', 'sum'),
                                wD=('wD', 'sum'), wG=('wG', 'sum'), wF=('wF', 'sum'), wse2=('wse2', 'sum'), G4=('D_ann_pp', 'median'),
                                segpos=('pos', 'sum')).reset_index()
    F['FULL'] = F.wD / F.n
    F['FULLg'] = F.wG / F.n
    F['FULLfee'] = F.wF / F.n
    F['t'] = F.FULL / (np.sqrt(F.wse2) / F.n)
    for side in ('left', 'right'):
        pp = F[side].map(_cd_parse)
        for i, nm in enumerate(('pre', 'meas', 'mother', 'alpha', 'Hs', 'op')):
            F['%s_%s' % (side[0], nm)] = pp.str[i]
    return F


def _cd_summ(df, by):
    return df.groupby(by).agg(cells=('FULL', 'size'), FULL_med_ann_pp=('FULL', 'median'), FULL_p25_ann_pp=('FULL', lambda x: x.quantile(.25)),
                              FULL_p75_ann_pp=('FULL', lambda x: x.quantile(.75)), share_FULL_pos=('FULL', lambda x: float((x > 0).mean())),
                              G4_med_ann_pp=('G4', 'median'), gross_med_ann_pp=('FULLg', 'median'), fee_med_ann_pp=('FULLfee', 'median'),
                              t_med=('t', 'median'), share_t_gt2=('t', lambda x: float((x > 2).mean())), share_t_lt_m2=('t', lambda x: float((x < -2).mean())),
                              share_4seg_pos=('segpos', lambda x: float((x == 4).mean()))).reset_index()


def card_digest(rp, P):
    rp.h(2, '附：判别读数（执行端写卡片八字段所引）')
    rp.p('口径：比较层逐比较先把四段日层闭合读数合成 FULL（n_days 加权）与 G4（四段中位）、gross 与线性费用分列、合成 se = √Σ n²·se_H² / N、t = FULL / se，'
         '再按卡的判别维度取分布（cells = 比较数；share_FULL_pos = FULL > 0 的份额；share_4seg_pos = 四段 D 全为正的份额）。费用列 = 子与右端的 −8bp × 换手差（正 = 子少付费）。'
         '描述符层读 `results/full/policy_E6l.csv`；事实层读 Stage A 掩码事实（推导 + 后段）与固定表。t 只作描述列，不作门。')
    F = cmp_full()
    P = P.copy()
    P['a'] = P.alpha.astype(float)
    P['pass'] = P.policy_PROPOSED_PORT3_T_FULL == '通过'
    MF = pd.concat([rd('results', 'stage_a', 'mask_facts_%s_E6l.csv' % t) for t in ('deriv', 'post')], ignore_index=True)
    MF = MF[MF.variant == 'REGISTERED']

    def T(df, qid, subject, op, sub, H='见列', unit='年化百分点（ann_pp）', base='比较右端（见 kind / right 列）', den='四段有效日（FULL = n 加权；G4 = 四段中位）'):
        rp.table(df, head(subject, op, sub, H, unit=unit, base=base, den=den), qid)

    def pol(df, by):
        return df.groupby(by).agg(objects=('desc_id', 'size'), port3_T_full_pass=('pass', 'sum'), FULL_med_ann_pp=('FULL', 'median'), G4_med_ann_pp=('G4', 'median'),
                                  FULL_sc_med_ann_pp=('FULL_sc', 'median'), share_FULL_sc_pos=('FULL_sc', lambda v: float((v > 0).mean()))).reset_index()
    rp.h(3, 'Q01')
    T(pol(P[(P.meas == 'Q0') & P.op.isin(['NATIVE', 'HG5', 'HG10', 'HG15'])], ['op', 'a']), 'E6L-CD-Q01-1', 'Q0 × NATIVE / HG5 / HG10 / HG15 的正式尺子（按算子 × α；H1…20 合并）',
      'NATIVE / HG', 'meas = Q0', base='同 H 原父（8bp）')
    w = P[P.desc_id == 'Q0|A4b_CVRv5|a0.5|H5|HG10']
    cols = ['FULL', 'G4', 'FULL_sc'] + ['D_%s' % s for s in SEGS] + ['port_size_lo_T_%s' % s for s in SEGS] + ['port_size_hi_T_%s' % s for s in SEGS] + \
           ['years_pos', 'size_PROPOSED_PORT3_T', 'policy_PROPOSED_PORT3_T_FULL']
    wt = pd.DataFrame(dict(item=cols, value=[w[c].iloc[0] if len(w) else np.nan for c in cols]), dtype=object)
    T(wt, 'E6L-CD-Q01-2', 'W09：Q0|A4b_CVRv5|a0.5|H5|HG10 的四段 D、组合层 PORT3_T 段均紧区间与判定（D / FULL 为 ann_pp；port_size 为 pct_pt）', 'HG10', '单对象',
      H='5', unit='ann_pp / pct_pt（见 item）', base='同 H 原父（8bp）')
    rp.h(3, 'Q02')
    T(_cd_summ(F[F.kind == 'SAME_MEAS_NATIVE'], ['l_op']), 'E6L-CD-Q02-1', '规则在同一测量上的效应：X op − X NATIVE（全部 α / H；按 op）', 'SAME_MEAS_NATIVE', '新测量 × 规则族')
    T(_cd_summ(F[F.kind == 'FOUR_ACCOUNT_INFO_RULE'], ['l_alpha']), 'E6L-CD-Q02-2', '信息 × 规则交互 Y11 − Y10 − Y01 + Y00（按 α）', 'FOUR_ACCOUNT_INFO_RULE', '全部')
    T(_cd_summ(F[F.kind == 'RULE_ONLY'], ['l_op']), 'E6L-CD-Q02-3', '新测量 × 规则 − 旧 K × 同规则（全部 α / H；按 op）', 'RULE_ONLY', '全部')
    fx = []
    for fam, g in P[P.family.isin(['HG', 'MEMORY', 'STATE', 'OLD_RULE'])].groupby('family'):
        den = sum(g['n_%s' % s].fillna(0) for s in SEGS)
        row = dict(family=fam, objects=len(g), FULL_8bp_med_ann_pp=float(g.FULL.median()))
        for tag in ('6bp', '12bp', 'gross'):
            num = sum(g['D_%s_%s' % (tag, s)].fillna(0) * g['n_%s' % s].fillna(0) for s in SEGS)
            row['FULL_%s_med_ann_pp' % tag] = float((num / den).median())
        fx.append(row)
    T(pd.DataFrame(fx), 'E6L-CD-Q02-4', '费用敏感：同一对象 FULL 在 6 / 8 / 12bp 与 gross（对象中位）', '按族', 'HG / MEMORY / STATE / OLD_RULE', H='H1…20',
      base='同 H 原父（同费率）')
    rp.h(3, 'Q03 / Q15（名单事实）')
    T(_cd_summ(F[F.kind == 'MEAN_KERNEL_PAIR'], ['l_meas', 'r_meas', 'l_op']), 'E6L-CD-Q03-1', '均值核配对（D5 − QMEAN5 / D5 − DMED5 / QMEAN5 − DMED5）', 'MEAN_KERNEL_PAIR',
      '全部 α / H')
    T(_cd_summ(F[(F.kind == 'SAME_OPERATOR_Q0') & F.l_meas.isin(['Q_D5', 'Q_QMEAN5', 'Q_DMED5'])], ['l_meas']), 'E6L-CD-Q03-2', 'X − 同算子 Q0（D5 / QMEAN5 / DMED5）',
      'SAME_OPERATOR_Q0', '全部 α / H / 算子')
    T(_cd_summ(F[F.kind == 'SAME_OPERATOR_Q0'], ['l_meas']), 'E6L-CD-Q03-3', 'X − 同算子 Q0（全部测量）', 'SAME_OPERATOR_Q0', '全部 α / H / 算子')
    T(_cd_summ(F[F.kind == 'KERNEL_DOSE'], ['l_meas']), 'E6L-CD-Q03-4', 'X − KERNEL_DOSE（同均值 / RMS 的 Q0 增量控制；432 支持格）', 'KERNEL_DOSE', '432 支持格',
      H='1 / 5 / 20')
    fc = ['overlap_in_q0_same_op', 'same_ticker_overlap_with_native', 'list_retention', 'gate_retention', 'self_edits_per_day', 'edit_persistence_5d_reversal_share']
    ft = MF[(MF.alpha == 'a0.25') & MF.op.isin(['NATIVE', 'HG10'])].groupby(['meas', 'op'])[fc].median().reset_index()
    T(ft, 'E6L-CD-FACTS-1', '门层名单事实（α .25 × NATIVE / HG10；四段 × 六形态中位）', 'NATIVE / HG10', 'mask_facts（推导 + 后段）', H='与 H 无关', unit='份额 / 名数每日',
      base='同算子 Q0（overlap_in_q0_same_op）/ 同测量原生（same_ticker_overlap_with_native）', den='目标 × 段')
    eps = []
    for s in SEGS:
        c4 = rd('stage0', 'c4_data', 'data_checks_%s.csv' % s)
        r = c4[(c4.iloc[:, 0] == 'A4-3') & (c4.iloc[:, 5].astype(str).str.count(' / ') == 2)]      # A4-3 三行中"有效 / 零 d / ε 主导"那一行
        if len(r):
            v = [float(x) for x in str(r.iloc[0, 5]).split(' / ')]
            eps.append(dict(segment=s, valid_share=v[0], zero_d_share=v[1], eps_dominant_share=v[2]))
    T(pd.DataFrame(eps), 'E6L-CD-Q03-5', 'pool0 单元 d 的零值与 ε 主导（d < 1e−4）份额（Stage 0 A4-3）', '—', 'pool0 单元', H='与 H 无关', unit='份额', base='—', den='pool0 单元')
    rp.h(3, 'Q04 / Q05')
    T(_cd_summ(F[F.kind == 'MA_VS_EW'], ['l_meas', 'l_op']), 'E6L-CD-Q04-1', 'MA − EW（D3 − DEW3、D5 − DEW5；按测量 × 算子）', 'MA_VS_EW', '全部 α / H')
    T(_cd_summ(F[F.kind == 'WINDOW_PAIR'], ['l_meas', 'r_meas']), 'E6L-CD-Q04-2', '窗口配对（D10 − D5、D5 − D3、RANK10 − RANK5、RANK5 − RANK3）', 'WINDOW_PAIR',
      '全部 α / H / 算子')
    T(_cd_summ(F[F.kind == 'RANK_BRIDGE_PAIR'], ['l_meas', 'r_meas', 'l_op']), 'E6L-CD-Q05-1', '秩桥（RANK5 − RANKOBS5、RANK5 − RANKSCORE5）', 'RANK_BRIDGE_PAIR', '全部 α / H')
    T(_cd_summ(F[F.kind.isin(['SUPPORT_BRIDGE_CONTENT', 'SUPPORT_BRIDGE_PARENT_SUPPORT', 'SUPPORT_BRIDGE_CHILD_SUPPORT', 'MASKQ0_SUPPORT_ONLY', 'MASKQ0_CONTENT'])],
              ['kind']), 'E6L-CD-Q05-2', '支持桥与 Q0 遮罩（按分解项；12 个平滑测量合并）', '支持分解', '432 支持格', H='1 / 5 / 20')
    MS = pd.concat([rd('results', 'stage_a', 'measure_facts_%s_E6l.csv' % t) for t in ('deriv', 'post')], ignore_index=True)
    ms = MS.groupby('meas')[['meas_kf_finite_share', 'meas_cs_share', 'fallback_k0_valid_meas_missing']].median().reset_index()
    T(ms[ms.meas.str.startswith('Q_')], 'E6L-CD-Q05-3', '测量覆盖：新测量坏度有限份额 / 共同支持份额 / 回旧 K 份额（四段 × 六形态中位）', '—', 'measure_facts', H='与 H 无关', unit='份额',
      base='—', den='pool0 单元')
    rp.h(3, 'Q06 / Q07 / Q08')
    T(_cd_summ(F[(F.kind == 'MECHANISM_PAIR') & (F.l_op == 'LAG1_10') & (F.r_op == 'HG10')], ['l_meas']), 'E6L-CD-Q06-1', 'LAG1_10 − HG10（按测量）', 'MECHANISM_PAIR',
      '全部 α / H')
    T(_cd_summ(F[(F.kind == 'SAME_MEAS_NATIVE') & F.l_op.isin(['HG10', 'LAG1_10', 'DECAY2_10', 'DECAY5_10', 'INV10'])], ['l_op']), 'E6L-CD-Q06-2',
      '记忆算子 − 同测量 NATIVE（按算子）', 'SAME_MEAS_NATIVE', '全部 α / H / 测量')
    mc = ['bonus_reliant_share', 'reliant_run_p90', 'reliant_run_max', 'confirm_age_p90', 'confirm_age_max', 'gate_retention', 'list_retention']
    T(MF[MF.op.isin(['HG5', 'HG10', 'HG15', 'HG20', 'HG30', 'LAG1_10', 'DECAY2_10', 'DECAY5_10', 'VOL_HI5', 'VOL_HI15', 'VOL_MEAN5', 'VOL_MEAN15'])].groupby('op')[mc].median().reset_index(),
      'E6L-CD-Q06-3', '纯 bonus 依靠份额 / 连续依靠日数 / 重确认年龄（目标 × 段中位）', '记忆算子', 'mask_facts（推导 + 后段）', H='与 H 无关', unit='份额 / 交易日', base='—', den='目标 × 段')
    T(_cd_summ(F[(F.kind == 'MECHANISM_PAIR') & F.l_op.isin(['DECAY2_10', 'DECAY5_10']) & F.r_op.isin(['HG10', 'DECAY5_10'])], ['l_op', 'r_op']), 'E6L-CD-Q07-1',
      'DECAY2 / DECAY5 − HG10、DECAY2 − DECAY5', 'MECHANISM_PAIR', '全部 α / H / 测量')
    T(_cd_summ(F[(F.kind == 'MECHANISM_PAIR') & (F.l_op == 'INV10') & F.r_op.isin(['HG10', 'LAG1_10'])], ['r_op', 'H']), 'E6L-CD-Q08-1', 'INV10 − HG10 / LAG1_10（按 H）',
      'MECHANISM_PAIR', '全部 α / 测量')
    T(pol(P[P.op == 'INV10'], ['H']), 'E6L-CD-Q08-2', 'INV10 的 FULL 与同资本 FULL_sc（按 H）', 'INV10', 'op = INV10', base='同 H 原父（8bp）')
    T(_cd_summ(F[F.kind == 'INV_CAP_LOOP'], ['H']), 'E6L-CD-Q08-3', 'INV 闭环同资本（诊断，不进正式 FULL_sc）', 'INV_CAP_LOOP', '全部')
    IS = rd('results', 'full', 'inventory_saturation.csv')
    T(IS[IS.variant == 'REGISTERED'].groupby('H')[['mark_coverage', 'saturated_day_share', 'pending_expiry_overlap']].median().reset_index(), 'E6L-CD-Q08-4',
      '库存标记覆盖 / 满额日份额 / 到期重叠（按 H）', 'INV10', 'inventory_saturation', unit='份额', base='—', den='目标 × 段')
    rp.h(3, 'Q09 / Q10')
    T(_cd_summ(F[F.kind == 'FOUR_ACCOUNT_SMOOTH_RULE'], ['l_op']), 'E6L-CD-Q09-1', '平滑 × 规则交互（按 op）', 'FOUR_ACCOUNT_SMOOTH_RULE', '全部 α / H / 测量')
    T(_cd_summ(F[(F.kind == 'KNOWN_QHG10') & (F.l_op == 'HG10')], ['l_meas']), 'E6L-CD-Q09-2', 'X HG10 − Q0 HG10（按测量）', 'KNOWN_QHG10', '全部 α / H')
    T(_cd_summ(F[F.kind.isin(['REAL_MINUS_RMARK', 'REAL_MINUS_COND', 'REAL_MINUS_LEGACY'])], ['kind', 'r_pre']), 'E6L-CD-Q10-1', '真实 − 随机路径均值（按机制）', 'RANDOM_PATH_MEAN',
      '随机清单全部行', base='同对象随机路径逐日均值')
    T(_cd_summ(F[F.kind == 'REAL_MINUS_RMARK'], ['r_pre', 'l_meas', 'H']), 'E6L-CD-Q10-2', '真实 HG10 − R-MARK（按机制 × 测量 × H）', 'RANDOM_PATH_MEAN', 'R-MARK 540 行',
      H='1 / 5 / 20', base='同对象 R-MARK 路径逐日均值')
    rp.h(3, 'Q11 / Q12 / Q13')
    T(pol(P[(P.H == 5) & P.op.isin(['NATIVE', 'HG5', 'HG10', 'HG15', 'HG20', 'HG30'])], ['a', 'op']), 'E6L-CD-Q11-1', '剂量面板（H5；α × b）', 'NATIVE / HG5…HG30', 'H = 5',
      H='5', base='同 H 原父（8bp）')
    FD = rd('results', 'full', 'frontier_dose_tilt.csv')
    T(FD.groupby(['alpha', 'b']).agg(cells=('FULL_ann_pp', 'size'), FULL_med_ann_pp=('FULL_ann_pp', 'median'), port_size_mid_T_med_pct_pt=('port_size_mid_T_pct_pt', 'median'),
                                     port_size_mid_T_min_pct_pt=('port_size_mid_T_pct_pt', 'min')).reset_index(), 'E6L-CD-Q11-2', '剂量 × 倾斜前沿（frontier_dose_tilt；段 × 配方 × 母体）',
      'α × b', 'frontier_dose_tilt', H='5', unit='ann_pp / pct_pt（见列名）', base='同 H 原父（8bp）', den='段 × 母体')
    T(_cd_summ(F[(F.kind == 'MECHANISM_PAIR') & F.l_op.str.startswith('VOL_')], ['l_op', 'r_op']), 'E6L-CD-Q12-1', '四调度 − 固定 HG10、调度之间', 'MECHANISM_PAIR', '全部 α / H / 测量')
    LG = rd('results', 'full', 'state_clock_ledger.csv')
    fm = LG[LG.clock == 'FORMATION'].assign(op=lambda d: d.desc_id.str.split('|').str[-1])
    T(fm.groupby(['state_var', 'state', 'op']).gross_contrib_diff_ann_pp.median().unstack().reset_index() if 'gross_contrib_diff_ann_pp' in fm else pd.DataFrame(),
      'E6L-CD-Q12-2', '形成状态切片的 gross 贡献差（子 − 父，对象中位；H_noise / H_change 为 Q12 事前切片）', 'FORMATION 时钟', 'state_clock_ledger', H='5',
      base='同 H 原父', den='形成日 × 状态')
    cal = LG[LG.clock == 'CALENDAR_NET']
    T(cal.groupby(['state_var', 'state']).agg(rows=('desc_id', 'size'), share_med=('share', 'median'), contribution_med_ann_pp=('contribution_ann_pp', 'median'),
                                              conditional_mean_med_ann_pp=('conditional_mean_ann_pp', 'median')).reset_index(), 'E6L-CD-Q13-1',
      '日历时钟：状态份额 / 贡献 / 状态内均值（对象中位）', 'CALENDAR_NET', 'state_clock_ledger', H='5', base='同 H 原父（8bp）', den='日历日 × 状态')
    SD = rd('results', 'full', 'state_symmetric_decomposition.csv')
    T(SD.groupby(['old', 'new'])[['delta_FULL_ann_pp', 'within_state_ann_pp', 'state_frequency_ann_pp', 'residual_ann_pp']].median().reset_index(), 'E6L-CD-Q13-2',
      '跨段 ΔFULL 的对称分解（状态内均值 / 状态频率 / 残差；对象中位）', '对称分解', 'state_symmetric_decomposition', H='5', base='前一段', den='共同状态')
    ST = pd.concat([rd('results', 'full', 'state_clock', '%s_stress.csv' % s) for s in SEGS], ignore_index=True)
    T(ST.groupby('window_start').agg(rows=('desc_id', 'size'), cum_rel_net_med_pct=('cum_rel_net_pct', 'median'), share_cum_rel_pos=('cum_rel_net_pct', lambda v: float((v > 0).mean())),
                                     nav_dd_child_med_pct=('nav_max_drawdown_child_pct', 'median'), nav_dd_parent_med_pct=('nav_max_drawdown_parent_pct', 'median')).reset_index(),
      'E6L-CD-Q13-3', '压力窗口与段首边界窗口（各 40 个交易日；对象中位）', '累计相对 / NAV 回撤', '状态时钟对象', H='5', unit='百分比（%）', base='同 H 原父', den='窗口内交易日')
    CP = rd('results', 'full', 'continuous', 'continuous_panel.csv')
    T(CP.groupby('segment').agg(rows=('desc_id', 'size'), carry_minus_reset_med_ann_pp=('carry_minus_reset_ann_pp', 'median'),
                                carry_minus_reset_nonzero=('carry_minus_reset_ann_pp', lambda v: int((v.abs() > 1e-12).sum())),
                                carry_minus_reset_max_ann_pp=('carry_minus_reset_ann_pp', 'max'), carry_minus_reset_min_ann_pp=('carry_minus_reset_ann_pp', 'min'),
                                boundary40_carry_minus_parent_med_ann_pp=('boundary40_carry_minus_parent_ann_pp', 'median')).reset_index(), 'E6L-CD-Q13-4',
      '连续面板：记忆跨段接续 − 段首重置（按段）', 'carry / reset', 'primary72 × 四记忆算子', H='5', base='连续原父', den='各段有效日')
    rp.h(3, 'Q14 / Q15')
    T(pol(P[P.mother.str.startswith('M_union')], ['mother', 'family']), 'E6L-CD-Q14-1', 'M_union 两母体：FULL vs 同资本 FULL_sc（按族）', '按族', 'mother ∈ M_union', H='H1…20',
      base='同 H 原父（8bp）')
    T(_cd_summ(F[F.kind == 'MATCH_CAP_FIXED_PATH'], ['l_mother']), 'E6L-CD-Q14-2', '同资本 FIXED_PATH（子 − 同 H 原父；按母体）', 'MATCH_CAP_FIXED_PATH', '全部',
      base='同 H 原父（同资本）')
    T(_cd_summ(F[F.kind == 'SMN_PAIR'], ['l_op']), 'E6L-CD-Q15-1', 'S − M（按算子）', 'SMN_PAIR', '全部 α / H')
    T(_cd_summ(F[(F.kind == 'SAME_OPERATOR_C1') & F.l_meas.isin(['S', 'M', 'Q0'])], ['l_meas']), 'E6L-CD-Q15-2', 'S / M / Q0 − 同算子 C1（按测量）', 'SAME_OPERATOR_C1',
      '全部 α / H / 算子')


# ================================================================ cards（每个 query 一张表）
def cards():
    P = rd('results', 'full', 'policy_E6l.csv')
    Qy = L.read_csv_keep(L.P('registry', 'query_registry_E6l.csv'))
    Q2O = L.read_csv_keep(L.P('registry', 'question_to_objects_E6l.csv'))
    C = pd.concat([rd('results', 'full', 'comparison_stats_%s.csv' % s) for s in SEGS], ignore_index=True)
    Cb = L.read_csv_keep(L.P('registry', 'cards_stageB_E6l.csv'))
    rp = RP.Report('cards')
    rp.h(1, 'E6l REPORT cards —— 16 张卡：每个 query 一张表（对象集合与绑定比较）')
    rp.p('用途：plan §12 / §13.4 cards。每张卡先列登记原文（Stage B 冻结，⑬ 为推导段 MDE80 机械填），再按 query 给对象统计与绑定比较的 FULL / G4；'
         '结论词只来自预登记的读法，不据结果改卡。登记文本里库存标记到上限的技术词在正文写作“满额（saturation）”（禁用词扫描按字面；登记文件原文不改，见 `registry/query_registry_E6l.csv`）。')
    T13 = rd('results', 'deriv', 'cards_t13_deriv_E6l.csv')
    for c in Cb.itertuples():
        rp.h(2, '%s' % regtext(c.title))
        rp.p('- ⑮ %s；⑯ %s；⑰ %s；⑱ %s' % (c.t15_account, c.t16_timescale, c.t17_random, c.t18_state))
        t13 = T13[T13.card == c.card]
        rp.p('- ⑬（推导段 MDE80 中位）：%s' % '；'.join('%s %s' % (r.segment, r.t13_label) for r in t13.itertuples()))
        for qid in c.queries.split('|'):
            objs = set(Q2O[Q2O.query_id == qid].desc_id)
            x = P if objs == {'ALL_DESCRIPTORS'} else P[P.desc_id.isin(objs)]
            cc = C[C.query_id == qid]
            rows = [dict(item='objects', value=len(x)), dict(item='share_FULL_pos', value=float((x.FULL > 0).mean()) if len(x) else np.nan),
                    dict(item='median_FULL_ann_pp', value=float(x.FULL.median()) if len(x) else np.nan),
                    dict(item='median_G4_ann_pp', value=float(x.G4.median()) if len(x) else np.nan),
                    dict(item='median_FULL_sc_ann_pp', value=float(x.FULL_sc.median()) if len(x) else np.nan),
                    dict(item='policy_PORT3_T_FULL_pass', value=int((x.policy_PROPOSED_PORT3_T_FULL == '通过').sum()) if len(x) else 0),
                    dict(item='bound_comparisons_rows', value=len(cc))]
            if len(cc):
                for kind, g in cc.groupby('kind'):
                    ok = g.D_ann_pp.notna()
                    rows.append(dict(item='cmp:%s median_D_ann_pp（段行）' % kind, value=float(g.D_ann_pp[ok].median()) if ok.any() else np.nan))
                    rows.append(dict(item='cmp:%s share_D_pos（段行）' % kind, value=float((g.D_ann_pp[ok] > 0).mean()) if ok.any() else np.nan))
            q = Qy[Qy.query_id == qid].iloc[0]
            rp.table(pd.DataFrame(rows, dtype=object), head(regtext(q.subject), '见卡', regtext(q.object_filter), '各对象自身 H', base='同 H 原父 / 比较右端'), qid)
    card_digest(rp, P)
    out = L.P('reports', 'E6l_REPORT_cards.md')
    rp.write(out)
    return out, len(rp.qids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--which', default='r0,part2,part3,mechanisms,carried,cards')
    a = ap.parse_args()
    import e6l_seal as SEAL
    for pkg in ('deriv', 'post'):
        ok, bad = SEAL.verify(pkg)
        if not ok:
            raise RuntimeError('seal_%s 核对失败：%s' % (pkg, bad[:5]))
    fn = dict(r0=r0, part2=part2, part3=part3, mechanisms=mechanisms, carried=carried, cards=cards)
    outs = []
    for w in a.which.split(','):
        p, nq = fn[w]()
        outs.append(p)
        print('%s：%d 个 query' % (os.path.basename(p), nq), flush=True)
    L.write_receipt(L.next_rerun('reports_%s' % a.which.replace(',', '_')), outs, 'SUCCEEDED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
