# -*- coding: utf-8 -*-
"""E6m 阶段 N · N7 交付：耗时外推（A6-1）、源合同草稿（engine_contract_draft.md，S1 定稿）、代码变更登记、阶段 N 经验条目、
stageN/README.md（数字全部从机器表读取）、交付清单 sha；--copy 时复制到 handoff/E6m/stageN_<ts>/ 并写 SHA256 清单。不读收益。"""
import os
import re
import sys
import json
import glob
import shutil
import inspect
import argparse

import numpy as np
import pandas as pd

import e6m_core as M

SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')
REASONS = {
    ('e6m_a0.py', 'UPDATE'): ('附属表 α 空值被 pandas 读成 NaN，状态词扫描 ⑲ 拦下 → 映射为 NOT_APPLICABLE', 'N3 a1 → a2；登记表语义不变（只改空值写法）'),
    ('e6m_a0_compile.py', 'UPDATE'): ('① 加 --attempt 参数（重跑写 _rerun 回执）；② 回执口径：编译对账成功 ≠ A1-auto 全过，A1-auto 结论另记', 'N3 a2 / a3；登记表内容不变'),
    ('e6m_ops.py', 'UPDATE'): ('PRIORITY_PASS 记忆版：Q 缺失者保留"记忆基门"身份（与 HARD 的 U_oldlag 同口径；附录 A3-6 端点 c = 1 ≡ OLD_LAG）', '合成测试 a1 → rerun；释义待决策端确认（README §3）'),
    ('e6m_synth_tests.py', 'UPDATE'): ('两处测试构造修正：A3-9c 改 HARD c.3（c.5 时复制 PASS 恰覆盖 U0）；A5-3 恒等路径按全部取值相等判（单遍方差舍入）', '合成测试 a1 → rerun'),
    ('e6m_closure.py', 'UPDATE'): ('数据读取判据收窄：只把行情 / 结果 / 缓存盘与工作目录下的非代码文件算作 import 期数据读取（系统时区文件不算）', '闭包 a1 → rerun；闭包模块清单不变'),
    ('e6m_stageN_deliver.py', 'UPDATE'): ('① 计时表 value 列混型（含布尔）→ 透视前转数值；② 模板里字面百分号未转义', 'N7 交付件；不涉及任何登记或核验产物'),
    ('e6m_stageN_gate.py', 'UPDATE'): ('① user@host 判据跳过矩阵乘写法（X@np.linalg…）；② 门输出（含存档副本）不自扫（E6l G10 同类）', 'N7 闭包门 a1 → 重跑'),
}


def timing_tables():
    tp = pd.concat([pd.read_csv(M.P('stage0', 'c6_timing_cloud_paths_%s.csv' % s)) for s in SEGS])
    tg = pd.concat([pd.read_csv(M.P('stage0', 'c6_timing_gate_%s.csv' % s)) for s in SEGS])
    vb = pd.concat([pd.read_csv(M.P('stage0', 'c6_vec_bench_%s.csv' % s)) for s in SEGS])
    seg = pd.concat([pd.read_csv(M.P('stage0', 'c6_timing_cloud_%s.csv' % s)) for s in SEGS])
    return tp, tg, vb, seg


def extrapolate(tp, vb):
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'))
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'))
    fam = lambda p: 'A4b' if p.startswith('A4b') else ('Munion' if p.startswith('M_union') else 'Mmean')
    D['fam'] = D.parent.map(fam)
    cfgkey = ['measurement', 'parent', 'operator', 'param', 'alpha', 'memory', 'adapter', 'condition']
    cfg = D.drop_duplicates(cfgkey).groupby('fam').size().to_dict()
    ndesc = D.groupby('fam').size().to_dict()
    rnd = A[A['item'].astype(int).isin([2, 3, 4]) & (A.mechanism != 'NO_NEW_CONTENT_TO_PERMUTE')].copy()
    rnd['parent'] = rnd.owner_id.map(lambda o: o.split('|')[1] if '|' in o and not o.startswith('SUPP:') else 'A4b_CVRv5')
    rnd['fam'] = rnd.parent.map(fam)
    rnd['cfg'] = rnd.owner_id.map(lambda o: re.sub(r'\|H\d+\|', '|', o)) + '|' + rnd.mechanism
    robj = rnd.groupby('fam').size().to_dict()
    rcfg = rnd.drop_duplicates('cfg').groupby('fam').size().to_dict()
    P = 1024
    v = tp.pivot(index='item', columns='segment', values='value')
    sp = vb[vb.op == 'band'].groupby('segment').speedup.mean().to_dict()
    rows = []
    tot = dict(A=0., B=0., det=0.)
    for s in SEGS:
        for f in ('A4b', 'Mmean', 'Munion'):
            g = v.loc['%s_random_path_gate_s_per_path' % f, s]
            dn = v.loc['%s_random_path_downstream_s_per_path' % f, s]
            dv = v.loc['%s_random_path_dev_s_per_path' % f, s]
            lg = v.loc['%s_random_path_ledger_s_per_path' % f, s]
            pm = v.loc['%s_random_path_permute_s_per_path' % f, s]
            det = cfg.get(f, 0) * (g + dn + dv) + ndesc.get(f, 0) * lg
            ra = rcfg.get(f, 0) * P * (pm + g + dn + dv) + robj.get(f, 0) * P * lg
            rb = rcfg.get(f, 0) * P * (g / sp.get(s, 1.0) + dn + dv) + robj.get(f, 0) * P * lg
            tot['det'] += det
            tot['A'] += ra
            tot['B'] += rb
            rows.append(dict(segment=s, family=f, gate_configs=cfg.get(f, 0), descriptors=ndesc.get(f, 0), random_configs=rcfg.get(f, 0), random_objects=robj.get(f, 0),
                             deterministic_cpu_h=round(det / 3600, 2), random_A_source_per_path_cpu_h=round(ra / 3600, 1),
                             random_B_vector_gate_cpu_h=round(rb / 3600, 1)))
    E6L_RAND_CPU_H, E6L_DET_CPU_H = 131.6, 12.0
    e6l_rand_objs = 4 * (9720 * 2 + 180 * 3)
    e6m_rand_objs = int(sum(robj.values())) * 4
    est_engine = E6L_RAND_CPU_H * e6m_rand_objs / e6l_rand_objs
    est_det = E6L_DET_CPU_H * (len(D) + 384) / 34120
    summ = dict(deterministic_source_speed_cpu_h=round(tot['det'] / 3600, 1), random_A_cpu_h=round(tot['A'] / 3600, 0), random_B_cpu_h=round(tot['B'] / 3600, 0),
                e6l_reference=dict(random_cpu_h=E6L_RAND_CPU_H, deterministic_cpu_h=E6L_DET_CPU_H, random_objects_4seg=e6l_rand_objs, descriptors=34120),
                e6m_random_objects_4seg=e6m_rand_objs, engine_scaled_random_cpu_h=round(est_engine, 1), engine_scaled_deterministic_cpu_h=round(est_det, 1),
                wall_h_cloud_24=round((est_engine + est_det) / 24, 1), wall_h_47_64=round((est_engine + est_det) / 64, 1), paths_first=P,
                note='A = 源函数逐路径（云机实测单价）；B = 门向量化（实测加速比）+ 源下游 / DEV / 记账；引擎折算 = E6l 实际耗时 × 对象数比（首 1,024 路径；增补另计）')
    return pd.DataFrame(rows), summ


def engine_contract():
    import e6j_prod as PR
    import comprehensive_factor_diagnosis as C
    import pool_screening_v2 as PS
    import e6j_features as EF
    import e6j_slot as SL
    import e6l_state as LS
    import data_loader as DL

    def loc(fn):
        f = inspect.getsourcefile(fn)
        return '%s:%d' % (os.path.basename(f), inspect.getsourcelines(fn)[1])

    def grep(fname, pat):
        p = os.path.join(M.CODE, fname)
        for i, ln in enumerate(open(p, encoding='utf-8'), 1):
            if re.search(pat, ln):
                return '%s:%d' % (fname, i)
        return '%s:NOT_FOUND' % fname
    items = [
        ('生产路径与六形态', loc(PR.build_period) + ' / ' + loc(PR.form_masks), 'e6m_stage0_data.task_seg；e6m_adapter.Downstream', '六形态 α = 0 → 仓库交付包六 pool2 + pool1 逐字节（c2_cloud_rebuild_anchor_a1.csv）'),
        ('源门（分两组取低半）', loc(C.build_factor_strategy_holdings_cached), 'e6m_adapter.Gate.source_kept', 'n_t = ceil(N/2)、平局 = rank(method=first) 出现顺序；适配器逐日 0 处不符（checks/real_gate_*.csv A3-1）'),
        ('源中性化', loc(C.precompute_neutralized_factor) + ' / ' + loc(PS.neutralize_by_mcap), 'e6m_adapter.q_source', 'pool0 < 6 跳过；有效对 < 10 原值直返；四段 RAW 分支 0 日、SKIP 19 日（c4_data_kq_*.csv）'),
        ('Q 源（J_B1_qCC）', loc(EF.b1), 'e6m_adapter.q_source', 'q = 1/(d + 1e−4)；x / d 有效日 = e6i_features.Base 原式（%s，云机 import 不起来，读源转录）' % grep('e6i_features.py', r'class Base')),
        ('坐标方向', loc(SL.pct_dir), 'e6m_adapter.q_source', "'lo'：(−s).rank(pct=True)；kQ 大值更差"),
        ('K 混合 FALLBACK', loc(SL.blend_q), 'e6m_adapter.blend / Gate.native_s', 'kQ 缺失处 = k0；Mmean 用真实三腿均值（可得腿）'),
        ('HG 门（账户侧）', grep('e6k_ops.py', r'def hg_gate'), '（阶段 S 用源）', 's − b_eff·1(上一形成日本账户门内)；稳定 argsort 取 dom.K[d]；b_eff = b·bunit（A4b / union 1/100，mean 1/(100·3)）'),
        ('门结构 Struct（账户侧）', grep('e6k_env.py', r'class Struct'), '（阶段 S 对 legal() / dom.K[d] 逐日核）', 'A4b 门 = K 第一关；union = K keep 50 ∧ T / cr20 ∧ ~CVR；mean = 综合分 ∧ ~否决'),
        ('DEV', loc(PR.assign_weights_dev), 'e6j_prod.weights_of', 'w0 = min(1/n, 1%)；行业组和 > clean 份额 + 3% 按比例压缩，不归一'),
        ('记账（费用 / 库存时钟）', loc(C.compute_calendar_pnl), '（阶段 S）', 'T 收盘出信号、T+1 VWAP 进；持仓 = 近 H 日权重均值 shift(2)；换手 = |Δ持仓|/2；成本 = 换手 × 8bp'),
        ('前向标签 FWD_SOURCE', loc(C.compute_forward_5d_excess), 'B3（N8 / S）', '后复权 VWAP 逐日超额按日相加（bp）；任一日缺失 → 缺失（c4_data_fwd.csv 合成例）'),
        ('V 源（Parkinson20）', loc(PS.compute_parkinson_vol), 'B5b（S）', '源返回 −vol（pool0 有限格 100% 为负；checks/real_gate_*.csv A2-8）；经济方向取负还原'),
        ('状态序列', loc(LS.compute) + ' / ' + loc(LS.build_cache), 'e6m_stage0_full.task_state', 'build_cache 函数体逐行复刻（输出改写工作目录）；PIT 截断三日期逐位；2010-2014 UNKNOWN 186 / 202、STRICT250 286 / 302、标签差 100 日'),
        ('取数与截断', loc(DL.load_all_daily_data), 'e6m_stage0_data.prep_cache / e6m_stage0_full.load_full', '`.loc[start:end]` 截断（%s）；云机 PATHS[cache_dir] 进程内指向 resonance 缓存（命中即读、不回写）' % grep('data_loader.py', r'data\[key\] = data\[key\]\.loc')),
    ]
    lines = ['# E6m 源合同草稿（阶段 N；S1 定稿）', '',
             '用途：brief §1.3 的 engine_contract.md / source_resolution.md 的阶段 N 草稿。每条：定义处（文件:行，读源核）/ 调用处（本轮模块）/ 默认值与证据。',
             '账户侧（e6k_* / e6j_engine）在云机 import 不起来（brief W15），只读源码登记行号，阶段 S 在源上复核。', '',
             '| 合同 | 定义处 | 调用处（E6m） | 默认值 / 证据 |', '|---|---|---|---|']
    for a, b, c, d in items:
        lines.append('| %s | `%s` | %s | %s |' % (a, b, c, d))
    return '\n'.join(lines) + '\n'


def code_register():
    L = pd.read_csv(M.P('code_register', 'deploy_log.csv'), dtype=str, keep_default_na=False)
    lines = ['# E6m 阶段 N 代码变更登记（从第一次部署起；E6l #47 / 附录 D-3）', '',
             '每次部署的文件全文存档于 `code_register/versions/<文件>.<sha16>`；反向还原 = 取上一版本存档文件（逐字节）。新文件只放云机代码目录（未跟踪），不改任何 tracked 文件。', '',
             '| 时间 | 文件 | 动作 | sha256（前 16） | 上一版 | 触发 / 范围 | 影响面 |', '|---|---|---|---|---|---|---|']
    for r in L.itertuples():
        why, eff = REASONS.get((r.file, r.action), ('首次部署', '—') if r.action == 'NEW' else ('（未登记原因）', ''))
        lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (r.time, r.file, r.action, r.sha256[:16], r.prev_sha256[:16] or '—', why, eff))
    vers = sorted(os.listdir(M.P('code_register', 'versions')))
    ok = all(os.path.exists(M.P('code_register', 'versions', '%s.%s' % (r.file, r.sha256[:16]))) for r in L.itertuples() if r.action != 'SAME')
    lines += ['', '存档文件 %d 个；每条部署都有对应存档：%s。' % (len(vers), '是' if ok else '否')]
    return '\n'.join(lines) + '\n'


LESSONS = [
    ('A', '超长 heredoc 追加代码在中途被截断（停在函数中间），文件留下残缺尾部', '大段代码一律整文件写入或分模块；追加后先做语法检查再部署', 'e6m_a0.py 首写（未部署前修复）'),
    ('A', '附属表的 None 被 pandas 转成 NaN，写出成字面 nan；状态词扫描在 A1-auto 拦下', '写出前对 None / NaN 统一映射状态词（NOT_APPLICABLE）；扫描放在编译同一步', 'N3 a1 → a2'),
    ('A', 'import 闭包"数据读取"判据写宽，把 pandas 读系统时区文件算成数据读取', '判据限定在行情 / 结果 / 缓存盘与工作目录', 'N4 闭包 a1 → rerun'),
    ('F', '两处合成测试构造错误（复制资格 c.5 时恰覆盖 U0；常数路径 sd 浮点不为 0）', '端点 / 反例先手算一例再写断言；恒等路径按"全部取值相等"判', 'N4 合成 a1 → rerun'),
    ('C', 'E6l 盘点只查了 results/，把 E5a"不在"读成锚不可核；E5a 交付包其实在仓库 delivery/ 里（git 跟踪）', '盘点锚文件同时查仓库内交付目录；本轮据此把 A2-1 在云机做成逐字节对账', 'c2_cloud_rebuild_anchor_a1.csv'),
    ('C', 'e6l_state.build_cache() 在函数内 import e6f_core（import 期读 roles.csv）且写 E6l 结果目录；brief W15 只看了模块级 import', '闭包核验要覆盖"函数内延迟 import"；状态序列改为 compute(data=…) + build_cache 函数体复刻、输出改写工作目录', 'c4_data_pit.csv'),
    ('B', 'PRIORITY_PASS 记忆版对 Q 缺失者"原身份"的口径在 plan §5.4 未写明，附录 A3-6 端点要求 c = 1 ≡ OLD_LAG', '采用与 HARD 记忆版同口径（缺失者保留记忆基门身份），登记为待决策端确认的释义', 'e6m_ops.py UPDATE'),
    ('A', 'nohup 日志没有经过写出层脱敏，带出家目录与用户目录名；闭包门 G06 拦下', '收尾用同一脱敏函数原地替换路径段（只改路径）；以后启动命令把输出经脱敏管道写日志', 'logs/（5 个文件）'),
    ('A', '闭包门把矩阵乘写法当 user@host，又把存档的上一次门输出当成扫描对象（E6l G10 同类，重犯）', '判据收窄；门输出（当前与存档）一律不扫', 'stageN/closure_gate_stageN.json'),
]


def readme(tp, tg, vb, ext_summ, ext_rows):
    j = lambda p: json.load(open(M.P(*p.split('/')), encoding='utf-8'))
    ident = j('identity_at_start.json')
    auth = j('registration/authorization_status_E6m.json')
    pt = pd.read_csv(M.P('stage0', 'plan_tests', 'plan_tests_counts_a1.csv'), dtype=str, keep_default_na=False).set_index('item')['got']
    man = j('registration/a0_manifest_E6m.json')
    a1 = j('registration/a1_auto_E6m.json')
    anc = pd.read_csv(M.P('stage0', 'c2_cloud_rebuild_anchor_a1.csv'), dtype=str, keep_default_na=False)
    syn = pd.concat([pd.read_csv(f) for f in glob.glob(M.P('checks', 'synthetic_*.csv')) if not f.endswith('summary.csv')])
    real = pd.concat([pd.read_csv(M.P('checks', 'real_gate_%s.csv' % s), keep_default_na=False) for s in SEGS])
    clo = j('registry/import_closure_E6m.json')
    ext = M.read_csv_keep(M.P('registry', 'external_inputs_E6m.csv'))
    rp = j('replica/replica_manifest_P0_dryrun.json')
    pit = pd.read_csv(M.P('stage0', 'c4_data_pit.csv'), keep_default_na=False)
    unk = pd.read_csv(M.P('stage0', 'c4_data_state_unknown.csv'), keep_default_na=False).set_index('segment')
    win = pd.read_csv(M.P('stage0', 'c4_data_windows.csv'), keep_default_na=False).set_index('window')
    fld = pd.concat([pd.read_csv(M.P('stage0', 'c4_data_fields_%s.csv' % s), keep_default_na=False).set_index('metric')['value'].rename(s) for s in SEGS], axis=1)
    kqb = pd.concat([pd.read_csv(M.P('stage0', 'c4_data_kq_%s.csv' % s), keep_default_na=False).branch.value_counts().rename(s) for s in SEGS], axis=1).fillna(0).astype(int)
    seg = pd.concat([pd.read_csv(M.P('stage0', 'c6_timing_cloud_%s.csv' % s)) for s in SEGS]).assign(value=lambda d: pd.to_numeric(d['value'], errors='coerce')).pivot(index='item', columns='segment', values='value')
    fails = [x for x in a1['items'] if x['status'] == 'FAIL']
    sw = [x for x in a1['items'] if x['status'] == 'SOURCE_WAIT']
    a36 = real[(real.appendix_item == 'A3-7') & (real.status == 'INFO')]
    vbm = vb.groupby('op').speedup.agg(['min', 'max'])
    L = []
    L += ['# E6m 阶段 N 交付说明（云机 autodl-factor；执行端）', '',
          '用途：brief §5 阶段 N（N1–N7）的交付说明。决策端按本文 §7 的命令与 sha 可复现每个产物；阶段 N 不读任何收益，N8（B3 先行）未获授权、未跑。', '',
          '- 工作目录：`factor_runs/resonance/E6m_stageN_20261005_0556/`（以下路径均相对它）。',
          '- 开工身份（`identity_at_start.json`）：HEAD = origin/main = `%s`；tracked 改动 %d；开工时未跟踪 %d 个（交付时 26 + 本轮 e6m 文件）；环境锁六项 %s；交接件 %d 件 sha 全部相符。'
          % (ident['git_head'][:7], ident['tracked_changes'], ident['untracked_n'], '全部 PASS' if ident['env_lock_pass'] else '有不符', ident['handoff_rows']),
          '- 授权登记（`registration/authorization_status_E6m.json`）：W11 = 方式 %s（转交消息不含方式 B 用语）；N8 = %s（转交消息不含"含云机 B3 先行"）。'
          % (auth['w11_mode'], auth['n8_b3_prelim']), '']
    L += ['## 1. 做了什么', '', '| 卡 | 产物 | 结果 |', '|---|---|---|',
          '| N1 | WORKLOG 开工行；`identity_at_start.json`；`PLAN_COPY.md` | 经验册（#61–#109、纪律 67–78 等）与 brief / 附录 / plan 已读 |',
          '| N2 | `stage0/plan_tests/` | spec 脚本在 factor 环境 %s / %s 通过；计数 %s / %s / %s / %s |' % (pt['passed'], pt['tests'], pt['main_descriptors'], pt['primary'],
                                                                                                 pt['mandatory_v11_addenda'], pt['compiled_base_comparisons']),
          '| N3 | `registry/`、`reports_skeleton/`、`registration/a0_manifest_E6m.json`、`registration/a1_auto_E6m.json` | 主 %d / 附属 %d / 基础比较 %d（与 spec 语义元组、semantic_id 逐一相同）；比较视图共 %d 行；附属八项清单；18 卡；%d 个 query、%d 张骨架；A1-auto %s |'
          % (man['raw_id_count'], man['supplemental'], man['comparisons_base'], man['comparisons_total'], man['queries'], man['skeletons'], json.dumps(a1['counts'], ensure_ascii=False)),
          '| N4 | `e6m_ops.py` / `e6m_adapter.py` / `e6m_b3_tools.py` / `e6m_ops_vec.py`；`checks/synthetic_*.csv`、`checks/real_gate_*.csv`；`registry/import_closure_E6m.*` | 合成 %d / %d 通过；真实数据门层 %d 项通过、%d 项信息、%d 项失败；闭包：%s |'
          % ((syn.status == 'PASS').sum(), len(syn), (real.status == 'PASS').sum(), (real.status == 'INFO').sum(), (real.status == 'FAIL').sum(), clo['verdict']),
          '| N5 | `stage0/c2_*`、`stage0/c4_data_*`、`stage0/c6_*`、`stage0/cache_cloud/`（ANCHOR_PENDING） | 见 §2 |',
          '| N6 | `registry/external_inputs_E6m.csv`；`replica/` | 外部输入 %d 行（%s）；P0 dry-run %d 个文件复制后重算 sha，不符 %d |'
          % (len(ext), json.dumps(ext.status.value_counts().to_dict(), ensure_ascii=False), rp['file_count'], len(rp['dry_run']['mismatched'])),
          '| N7 | 本文；`stageN/closure_gate_stageN.json`；`stageN/code_change_register_stageN.md`；`stageN/lessons_stageN.md`；`stageN/engine_contract_draft.md`；`stageN/stageN_manifest.csv` | 复制到 `handoff/E6m/stageN_<时间>/` 并记 sha |', '']
    L += ['## 2. 关键结果（全部名单 / 特征层，不含收益）', '',
          '- **A2-1 云机版**：四段按源 `build_period` / `form_masks` / DEV 重建六形态，拼接后与仓库交付包（`delivery/I11_candidate_pools_v2_20260903/*.tar.gz`，git 跟踪）的六个 pool2 与 pool1 **逐字节相同**（%d / %d 文件；pool1 md5 = 交付 README 所记）。E5a 结果目录原件仍 SOURCE_WAIT。'
          % ((anc.status == 'PASS').sum(), len(anc)),
          '- **段日历**：四段 %s 日；每段前 19 日 pool0 为空（Q 中性化分支 SKIP %s 日，RAW 回退 0 日）。日历文件两所各 3,940 天 = 行情索引。'
          % (' / '.join(str(int(seg.loc['n_dates', s])) for s in SEGS), ' / '.join(str(int(kqb.loc['SKIP_POOL_LT6', s])) for s in SEGS)),
          '- **适配器**（A3-1）：三母体族四段逐日 source_U = 冻结总序前 ceil(N/2)，与源门 0 处不符。端点（BAND w0、BAND_BLEND α0、COPY、PRIORITY c1、HARD c1）门层逐日 ≡ 源门，经下游源函数后 ≡ 源六形态。',
          '- **A3-7 HARD c.5（A4b）**：最终人数相对父 %s。' % '；'.join('%s：%s' % (r.segment, r.detail) for r in a36.itertuples()),
          '- **记忆（A3-10）**：HG（昨日实际 G）与 LAG（昨日自然 U）在真实数据上分开；断点续跑逐日相同。PROTECTED_LAG10 带外编辑 0；UNPROTECTED 桥有带外编辑的日子见 real_gate 表。',
          '- **状态序列**（A4-3）：PIT 截断三日期重算逐位相同（%s）；2010-2014 段 UNKNOWN 主定义 vol %d / act %d、STRICT250 %d / %d、标签差 %d 日（与 E6l 文本印出值相同），其余三段 0。'
          % ('、'.join(pit.status), unk.loc['2010-2014', 'vol_unknown_main'], unk.loc['2010-2014', 'act_unknown_main'], unk.loc['2010-2014', 'vol_unknown_strict250'],
             unk.loc['2010-2014', 'act_unknown_strict250'], unk.loc['2010-2014', 'vol_label_diff_main_vs_strict']),
          '- **W1 / W2**（A4-4）：W1 %s → %s，%d 个交易日；W2 %s → %s，%d 个交易日（中心为交易日）。' % (win.loc['W1', 'first'], win.loc['W1', 'last'], win.loc['W1', 'days'],
                                                                                  win.loc['W2', 'first'], win.loc['W2', 'last'], win.loc['W2', 'days']),
          '- **B3 字段语义**（A4-1）：turnover_rate 为小数（pool0 中位 %s）；chgPct 为四位小数舍入的分数（与 C/lclose − 1 最大差 %s）；Q 源用 log(C/lclose)，不用 chgPct；北交所 0；真实零 d 份额约 %s。'
          % (fld.loc['turnover_rate_median_pool0valid', '2019-2023'], fld.loc['change_pct_absdiff_vs_fraction_max', '2019-2023'], fld.loc['d_true_zero_share_pool0valid', '2019-2023']),
          '- **V 源符号**（A2-8）：`compute_parkinson_vol` 返回 −vol，pool0 有限格 100% 为负；经济方向须取负还原。',
          '- **kQ 重算**（A2-5）：两次独立重算逐位相同；对 E6j `J_B1_qCC` 的锚 = ANCHOR_PENDING。', '']
    L += ['## 3. 未过与待决策端', '']
    for x in fails:
        L.append('- **A1-auto 第 %s 项 FAIL**：%s（%s）。plan 原文没有单列"反解释"，执行端不代写；cards_E6m.csv 里这 8 张卡的反解释字段暂取原文"预期 / 更新"句并标 `counter_explicit_in_plan = False`。需要决策端补写或确认以原文代替。' % (x['item'], x['check'], x['detail']))
    for x in sw:
        L.append('- A1-auto 第 %s 项 SOURCE_WAIT：%s（%s）。' % (x['item'], x['check'], x['detail']))
    L += ['- **释义待确认（代码变更登记 e6m_ops.py UPDATE）**：PRIORITY_PASS 带记忆时 Q 缺失者的身份按"记忆基门"（与 HARD 的 U_oldlag 同口径），使附录 A3-6 端点 c = 1 ≡ OLD_LAG 成立；plan §5.4 只写了无记忆版。',
          '- **盘点更正**：E6l 云机盘点把 E5a 记为"不在"，但仓库 `delivery/` 里有 E5a v2 交付包；本轮据此在云机完成 A2-1 逐字节对账（结果目录原件仍待 47）。',
          '- **brief W15 补充**：`e6l_state.build_cache()` 在函数内 import e6f_core（经 e6e_core 在 import 期读 roles.csv），且写 E6l 结果目录；云机改为 compute(data=…) + build_cache 函数体复刻，输出写本工作目录。', '']
    L += ['## 4. 等 47（或 X01 + P3 到云机）的项', '',
          '- 外部输入 SOURCE_WAIT %d 行（`registry/external_inputs_E6m.csv`）：X01 `roles.csv`（账户侧 import 期）、E6k / E6l / E6j / E6i / E5a 结果目录原件。' % int((ext.status == 'SOURCE_WAIT').sum()),
          '- Stage 0 标 S 的全部项：源锚（A2-1 结果目录原件、A2-2–A2-4、A2-6、A2-7、A2-9）、真实数据账户层恒等、E6k 随机复现、P44 核、Struct.legal() / dom.K[d] 对适配器、ANCHOR_PENDING 的 kQ 与状态序列对原缓存逐位。',
          '- Stage A / B、推导段、封存、记录 B（方式 A：推导段封存后停等用户一句话）、后段、政策、报告、交付。', '']
    L += ['## 5. 授权', '', '- W11：方式 %s。阶段 S 推导两段算完、封存、记录 B 草稿后停等用户一句话；若用户转交时给出方式 B 用语（含两后段），改写 `record_B_preauthorized_E6m.json`。' % auth['w11_mode'],
          '- N8：%s。如要做，转交消息需含"含云机 B3 先行"；B3 的 query / cell / contrast 清单已在 N3 冻结（`registry/b3_cells_E6m.csv` %d 格、`b3_contrasts_E6m.csv` %d 行），坐标会标 ANCHOR_PENDING、输出立即封存不读。'
          % (auth['n8_b3_prelim'], man['b3']['cells'], man['b3']['contrast_rows']), '']
    L += ['## 6. 耗时实测与阶段 S 外推（A6-1 / A6-2）', '',
          '- 云机实测（`stage0/c6_timing_*`）：每段 build_period %s 秒；form_masks %s 秒；峰值内存 %s GB。'
          % (' / '.join('%.0f' % seg.loc['build_period_s', s] for s in SEGS), ' / '.join('%.0f' % seg.loc['form_masks_s', s] for s in SEGS),
             ' / '.join('%.1f' % seg.loc['rss_peak_gb', s] for s in SEGS)),
          '- 每条随机路径（源函数，逐路径；合成价格计时）：A4b %s 秒（其中下游 T 重估 %s 秒）；Munion %s 秒；Mmean %s 秒；记账一步 %s 秒。'
          % tuple(' / '.join('%.1f' % tp[(tp.segment == s) & (tp['item'] == it)].value.iloc[0] for s in SEGS)
                  for it in ('A4b_random_path_total_s_per_path', 'A4b_random_path_downstream_s_per_path', 'Munion_random_path_total_s_per_path',
                             'Mmean_random_path_total_s_per_path', 'A4b_random_path_ledger_s_per_path')),
          '- 门的路径向量化原型（`e6m_ops_vec.py`，`stage0/c6_vec_bench_*.csv`）：四段 × 两族 × 四算子与逐路径版**逐日逐位相同**，64 路径时加速 %s。'
          % '；'.join('%s %.0f–%.0f×' % (op, r['min'], r['max']) for op, r in vbm.iterrows()),
          '- 外推（`stage0/c6_timing_extrapolation.csv`，首 1,024 路径，增补另计）：按源函数逐路径约 %s CPU 小时、门向量化后约 %s CPU 小时——都不可行；'
          '按 E6l 引擎实际耗时折算（随机对象数比 %d / %d）随机层约 %s CPU 小时、确定性约 %s CPU 小时 → 云机 ≤ 24 并发约 %s 小时，47（64 并发）约 %s 小时。'
          % (ext_summ['random_A_cpu_h'], ext_summ['random_B_cpu_h'], ext_summ['e6m_random_objects_4seg'], ext_summ['e6l_reference']['random_objects_4seg'],
             ext_summ['engine_scaled_random_cpu_h'], ext_summ['engine_scaled_deterministic_cpu_h'], ext_summ['wall_h_cloud_24'], ext_summ['wall_h_47_64']),
          '- 提速要点（阶段 S）：① 门掩码不依赖 H，按配置算一次、20 个 H 复用；② 随机层必须用引擎的快速件（e6j_fast.stage2_fast、numba 记账；账户侧，云机需 X01）——源函数下游与记账占每路径耗时的 80%% 以上；'
          '③ 新算子的门用路径向量化版（已逐位对拍）；④ 置换按路径批量生成（现原型逐日 Python 置换约 0.3–0.7 秒 / 路径，可再向量化）。若阶段 S 在云机跑，24 并发约 %s 小时，需要更快可按云机指南另租临时机器。' % ext_summ['wall_h_cloud_24'], '']
    L += ['## 7. 复现', '', '在云机：`source …/conda.sh && conda activate factor`；`export E6M_WORK=<工作目录>`；代码目录下依次：', '',
          '```', 'python e6m_stage0_identity.py', 'python e6m_plan_tests.py --attempt <新>', 'python e6m_stage0_data.py --task seg --seg <段>   # 四段', 'python e6m_stage0_data.py --task merge --attempt <新>',
          'python e6m_a0_compile.py --attempt <新>', 'python e6m_synth_tests.py', 'python e6m_closure.py', 'python e6m_stage0_real.py --seg <段>', 'python e6m_stage0_full.py --attempt <新>',
          'python e6m_replica.py', 'python e6m_timing.py --seg <段> --paths 8', 'python e6m_vec_bench.py --seg <段> --paths 64', 'python e6m_stageN_gate.py', 'python e6m_stageN_deliver.py',
          '```', '', '每个产物的 sha 见 `stageN/stageN_manifest.csv`；每次运行的回执（参数 / 输入 / 输出 sha / 代码 sha）在 `task_status/`；历次 attempt 存于 `attempts/`。', '']
    return '\n'.join(L) + '\n'


def manifest():
    W = M.work()
    rows = []
    for root, _, fs in os.walk(W):
        rel = os.path.relpath(root, W)
        if rel.split(os.sep)[0] in ('tmp', 'replica') and not (rel == 'replica'):
            continue
        for f in fs:
            p = os.path.join(root, f)
            r = os.path.normpath(os.path.relpath(p, W))
            if r.startswith(os.path.join('stageN', 'stageN_manifest')) or r.startswith(os.path.join('task_status', 'N7_')):
                continue                                     # N7 自身回执在清单之后写，单独计 sha
            rows.append(dict(path=r, sha256=M.sha_file(p), bytes=os.path.getsize(p)))
    return pd.DataFrame(rows).sort_values('path')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--copy', action='store_true')
    a = ap.parse_args()
    os.makedirs(M.P('stageN'), exist_ok=True)
    if a.copy:
        mf = M.read_csv_keep(M.P('stageN', 'stageN_manifest.csv'))
        ts = M.time.strftime('%Y%m%d_%H%M')
        dst = os.path.expanduser('~/autodl-tmp/factor_runs/resonance/handoff/E6m/stageN_%s' % ts)
        if os.path.exists(dst):
            raise RuntimeError('目标已存在')
        take = mf[~mf.path.str.startswith(('attempts', 'stage0/cache_cloud', 'stage0/anchor_repo_delivery', 'logs')) & ~mf.path.str.contains('raw_a1')]
        for r in take.itertuples():
            d = os.path.join(dst, r.path)
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(M.P(r.path), d)
        bad = [r.path for r in take.itertuples() if M.sha_file(os.path.join(dst, r.path)) != r.sha256]
        extra = sorted(f for f in os.listdir(M.P('task_status')) if f.startswith('N7_'))       # N7 自身回执：清单之后写，单独复制并计 sha
        for f in extra:
            shutil.copy2(M.P('task_status', f), os.path.join(dst, 'task_status', f))
        with open(os.path.join(dst, 'stageN_SHA256.txt'), 'w', encoding='utf-8') as fh:
            for r in take.itertuples():
                fh.write('%s %s\n' % (r.sha256, r.path))
            for f in extra:
                fh.write('%s %s\n' % (M.sha_file(os.path.join(dst, 'task_status', f)), 'task_status/' + f))
        print(json.dumps(dict(copied=len(take), mismatched=len(bad), dest=M.san(dst)), ensure_ascii=False))
        M.write_receipt(os.environ.get('E6M_TASK', 'N7_handoff_copy'), [os.path.join(dst, 'stageN_SHA256.txt')], status='SUCCEEDED' if not bad else 'FAILED', copied=len(take))
        return 0 if not bad else 1
    tp, tg, vb, seg = timing_tables()
    ext_rows, ext_summ = extrapolate(tp, vb)
    M.atomic_write_csv(M.P('stage0', 'c6_timing_extrapolation.csv'), ext_rows)
    M.atomic_write_json(M.P('stage0', 'c6_timing_extrapolation_summary.json'), ext_summ)
    M.atomic_write_text(M.P('stageN', 'engine_contract_draft.md'), engine_contract())
    M.atomic_write_text(M.P('stageN', 'code_change_register_stageN.md'), code_register())
    les = ['# E6m 阶段 N 经验条目（执行端；六类标注 A 仪器 / B 未匹配比较 / C 机制未读源码 / D 前提外推 / E 过早收口 / F 节奏文档；不写共享 memory）', '',
           '| # | 类 | 事件（本阶段实际发生） | 做法 / 改法 | 证据 |', '|---|---|---|---|---|']
    for i, (c, e, f, ev) in enumerate(LESSONS, 1):
        les.append('| N%d | %s | %s | %s | %s |' % (i, c, e, f, ev))
    M.atomic_write_text(M.P('stageN', 'lessons_stageN.md'), '\n'.join(les) + '\n')
    M.atomic_write_text(M.P('stageN', 'README.md'), readme(tp, tg, vb, ext_summ, ext_rows))
    mf = manifest()
    M.atomic_write_csv(M.P('stageN', 'stageN_manifest.csv'), mf)
    M.write_receipt(os.environ.get('E6M_TASK', 'N7_deliver'), [M.P('stageN', f) for f in ('README.md', 'engine_contract_draft.md', 'code_change_register_stageN.md',
                                                                                           'lessons_stageN.md', 'stageN_manifest.csv')]
                    + [M.P('stage0', 'c6_timing_extrapolation.csv'), M.P('stage0', 'c6_timing_extrapolation_summary.json')], code=[__file__, M.__file__], files=len(mf))
    print(json.dumps(ext_summ, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
