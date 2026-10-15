# -*- coding: utf-8 -*-
"""E6n 报告（brief §5 S8、§9；plan §12.4）：七份 REPORT 全部由机器表生成（不手抄数字、不写判词式结论；读法按 plan §13.1 词表机械给出），
每张表带表头十项（主体 / 算子 / 分母 / 基准 / 子集 / 单位 / 日期 / H / 成本 / exposure）+ query_id；NaN 一律写 UNDEFINED（正文字面 nan / None 扫描命中即停，E02）。
  r0 | part1 | part2 | part3 | mechanisms | carried | review_input | all
页首固定："本轮无 E7 与部署授权；协议按 v1.5 候选执行（按流程建议、协议未正式裁定）"。读后段结果前过 post_gate（part1 只读推导段，可在 seal_deriv 后先出）。"""
import os
import re
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

HEADER_LINE = '> 本轮无 E7 与部署授权（deployment_authorized = false；新对象 replacement_preference_status = NOT_AUTHORIZED）；协议按 v1.5 候选执行（按流程建议、协议未正式裁定）。'
MAIN_DOMAIN = 'GATE_A4b_CVRv5_Q0HG10'
FRONT = 'ANCHOR|Q0|A4b_CVRv5|HG10|H5|s0|ALL|a0.25|f5|d+1'
B10_HEAD = dict(算子='诊断三分（中分布）低组 − 高组', 分母='有效配对形成日（等权）', 基准='同域同日（低组 − 高组；不相对父账户）', 单位='bp（H5 累计）',
                日期='2010-01-04 … 2018-12-28（推导两段）', H='5', 成本='不适用（前向源收益标签，未扣费）', exposure='FIRST_MEASUREMENT（B1-0 封存后只打标签）')


LIMITS = [  # (编号, 限制, 机器计数函数名, 引用报告)
    ('L-N1', '分钟数据始于 2013-08-01：2010-01-04..2013-07-31 无分钟；推导段 2010-2014 分钟覆盖约 1/3，新对象在未覆盖日逐股回 Q0 源分支；原政策需早段年数时标 POLICY_UNDECIDABLE_HISTORY',
     'cov_2010', ('E6n_REPORT_R0.md', 'E6n_REPORT_part1.md', 'E6n_REPORT_part3.md')),
    ('L-N2', '无宽基分钟指数（000852 / 000985 / 000300 在源分钟表是同号股票）→ TAIL_PUSH 的 β 残差诊断与公共标量减法诊断 UNKNOWN（A13）', None, ('E6n_REPORT_R0.md', 'E6n_REPORT_mechanisms.md')),
    ('L-N3', '沪市 2018-08-20 前官方收盘 = 最后一分钟成交量加权，末笔 ≠ 官方收盘；尾盘量与 TAIL_PUSH / Q_CLOSE_THIN 用官方收盘，官方桥分解只校验不拉伸', None,
     ('E6n_REPORT_R0.md', 'E6n_REPORT_part1.md')),
    ('L-N4', '5 分钟 bar 开盘价在部分年份为上一根收盘沿用价 → 路径起点改用开盘竞价价或 1 分钟第一笔成交开盘价', None, ('E6n_REPORT_R0.md',)),
    ('L-N5', 'B2 NEXT_RANK 替代名未核行业额度（质量列 INDUSTRY_CAP_UNCHECKED）；B2 只是冻结源账本诊断，不是可部署退出策略', None, ('E6n_REPORT_carried.md',)),
    ('L-N6', 'B5 LEAK_BRIDGE 72 对象取 E6m 已冻结结果（账户 sha 对 E6m 副本清单），本轮未用 E6m 算子重算', None, ('E6n_REPORT_carried.md',)),
    ('L-N7', 'CONTENT_QRANGE_P5 只覆盖登记 owner（主 72 新行 + 两构造 CORE 全 H）；配对随机差只有 IID / ISK', None, ('E6n_REPORT_part2.md',)),
    ('L-N8', 'MATCH_CAP_HOLDINGS_MIN 只对 H5 政策对象出附表', 'mchm_rows', ('E6n_REPORT_part3.md',)),
    ('L-N9', 'B2 同率随机 / 伯努利镜像各 64 路径（无 MCSE 目标）；CVR 水平对照为单条确定性', None, ('E6n_REPORT_carried.md',)),
    ('L-N10', 'B1-0 的 A2"同向同量"与"匹配后差消失"阈值（25%）为执行端在 Stage B 冻结前补登记的数值（brief 只给定性词）', None, ('E6n_REPORT_part1.md',)),
    ('L-N11', '四账户支持桥在 S_T 上只重排 Q（及新测量），旧 K（pcond 秩）不重排；门保留数按源 k_of 在 S ∩ 门域重算', None, ('E6n_REPORT_part2.md',)),
    ('L-N12', '原资格 e随机对新对象 = LEGACY_POLICY_RANDOM（对象自身 Q 槽 kf 当日 IID 置换；E6l / E6m 新测量同式）——执行端代拟，待决策端追认（P03）', None,
     ('E6n_REPORT_part3.md',)),
    ('L-N13', '随机推导段首 1,024 路径的回执 code 字段为写回执时文件 sha（执行版本 d64c295d；后续版本只加任务认领）', None, ('E6n_REPORT_R0.md',)),
]


def limit_counts():
    out = {}
    try:
        cv = pd.read_csv(N.P('results', 'coverage_by_feature_year_exchange.csv'), keep_default_na=False)
        x = cv[(cv.feature == 'PL_REL20_f5') & (cv.year <= 2014)]
        out['cov_2010'] = '机器计数（coverage_by_feature_year_exchange.csv，PL_REL20_f5 2010–2014 加权可算份额 %.3f）' % (x.computable.sum() / max(1, x.n_cells.sum()))
    except Exception:                                                            # noqa: BLE001
        out['cov_2010'] = '机器计数（coverage 表未就绪）'
    try:
        mc = pd.read_csv(N.P('results', 'full', 'match_cap_holdings_min.csv'), keep_default_na=False)
        out['mchm_rows'] = '机器计数（match_cap_holdings_min.csv %d 行）' % len(mc)
    except Exception:                                                            # noqa: BLE001
        out['mchm_rows'] = '机器计数（附表未就绪）'
    return out


def limits_section(rp, name):
    ids = [(i, t) for i, t, _, refs in LIMITS if name in refs]
    if ids:
        rp.h(2, '限制（引用 E6n_limit_register.md）')
        for i, t in ids:
            rp.p('- %s：%s' % (i, t))


def limit_register():
    cnt = limit_counts()
    L = ['# E6n 限制登记（状态栏由机器计数刷新；闭包门 S11 / N04 核引用与刷新）', '', '| 编号 | 限制 | 状态 | 引用于 |', '|---|---|---|---|']
    for i, t, k, refs in LIMITS:
        st = cnt.get(k, '机器计数（定性限制，无数值）') if k else '机器计数（定性限制，无数值）'
        L.append('| %s | %s | %s | 引用于：%s|' % (i, t.replace('|', '¦'), st, '、'.join(refs)))
    p = N.P('reports', 'E6n_limit_register.md')
    N.atomic_write_text(p, '\n'.join(L) + '\n')
    return p


def csv(p, **kw):
    p = p if os.path.isabs(p) else N.P(p)
    return pd.read_csv(p, keep_default_na=False, na_values=[''], low_memory=False, **kw) if os.path.exists(p) else None


def jload(p):
    p = p if os.path.isabs(p) else N.P(p)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def cat(pattern, segs):
    """逐段读；B2 按形态拆分的文件（<名>_<段>__<形态>.csv）一并读入。"""
    parts = []
    for s in segs:
        fs = [N.P(pattern % s)] if os.path.exists(N.P(pattern % s)) else []
        if '/b2/' in pattern:
            fs += sorted(glob.glob(N.P((pattern % s)[:-4] + '__*.csv')))
        for f in fs:
            x = csv(f)
            if x is not None:
                parts.append(x.assign(segment=s) if 'segment' not in x.columns else x)
    return pd.concat(parts, ignore_index=True) if parts else None


def fmt(v):
    if isinstance(v, (float, np.floating)):
        if not np.isfinite(v):
            return 'UNDEFINED'
        return ('%.4f' % v).rstrip('0').rstrip('.') if abs(v) < 1e4 else '%.0f' % v
    # 只把真正的缺失写法当缺失（区分大小写）：大写 NONE 是登记取值（无记忆 / 无 owner），不能渲染成 UNDEFINED
    if v is None or (isinstance(v, str) and v.strip() in ('nan', 'NaN', 'None', 'null', 'NULL', 'n/a', 'N/A', '')):
        return 'UNDEFINED'
    return re.sub(r'(?<![A-Za-z_])(nan|NaN|None|null)(?![A-Za-z_])', 'UNDEFINED', str(v)).replace('|', '¦')


class Report(object):
    def __init__(self, name, title):
        self.name, self.L = name, ['# ' + title, '', HEADER_LINE, '']

    def h(self, lv, t):
        self.L += ['#' * lv + ' ' + t, '']

    def p(self, t):
        # 机器值渲染：JSON / 字典文本里的 NaN / None 写成状态词 UNDEFINED（E02：正文不留字面 nan / None）
        self.L += [re.sub(r'(?<![A-Za-z_])(nan|NaN|None|null)(?![A-Za-z_])', 'UNDEFINED', t), '']

    def table(self, df, head, qid, maxrows=400):
        hh = dict(主体='—', 算子='—', 分母='各段有效配对日', 基准='同 H 原父（α = 0；8bp）', 子集='—', 单位='年化百分点（ann_pp）', 日期='2010-01-04 … 2026-03-27',
                  H='见 H 列', 成本='源 8bp', exposure='见 exposure 列 / 首评（NEW_OPERATOR_FIRST_EVALUATION_ON_REUSED_HISTORY）')
        hh.update(head)
        self.L.append('表头：' + '；'.join('%s = %s' % (k, v) for k, v in hh.items()) + '；query_id = `%s`' % qid)
        self.L.append('')
        if df is None or not len(df):
            self.L += ['（表空：status = NOT_COMPUTABLE / 未生成）', '']
            return
        d = df.head(maxrows)
        cols = list(d.columns)
        self.L.append('| ' + ' | '.join(cols) + ' |')
        self.L.append('|' + '---|' * len(cols))
        for r in d.itertuples(index=False):
            self.L.append('| ' + ' | '.join(fmt(v) for v in r) + ' |')
        if len(df) > maxrows:
            self.L.append('')
            self.L.append('（只印前 %d 行；全表见机器表，行数 %d）' % (maxrows, len(df)))
        self.L.append('')

    def write(self):
        limits_section(self, 'E6n_REPORT_%s.md' % self.name)
        txt = '\n'.join(self.L) + '\n'
        bad = re.findall(r'(?<![A-Za-z_])(nan|NaN|None)(?![A-Za-z_])', txt)
        if bad:
            raise RuntimeError('报告 %s 正文含字面 %s（E02）' % (self.name, sorted(set(bad))))
        p = N.P('reports', 'E6n_REPORT_%s.md' % self.name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        N.atomic_write_text(p, txt)
        return p


# ====================================================================== R0
def r0():
    rp = Report('R0', 'E6n REPORT R0 —— 身份、授权、Stage 0、数据合同、封存、覆盖与限制')
    rp.h(2, '1. 授权、冻结与记录 B')
    for nm, p in (('方式登记（照录用户原话）', 'registration/authorization_status_E6n.json'), ('冻结清单', 'registration/stageB_freeze_E6n.json'),
                  ('方式 B 事前授权', 'registration/record_B_preauthorized_E6n.json'), ('生效条件回执', 'registration/record_B_conditions_receipt_E6n.json'),
                  ('seal_B1_0', 'registration/seal_B1_0.json'), ('seal_deriv', 'registration/seal_deriv.json'), ('seal_post', 'registration/seal_post.json')):
        j = jload(p)
        if j is None:
            rp.p('- %s：文件缺（`%s`）' % (nm, p))
            continue
        keep = {k: j[k] for k in ('w10_mode', 'mode', 'user_quote', 'user_quote_date', 'all_pass', 'written_at', 'n_files', 'queued_missing', 'n_receipts', 'all_ok',
                                  'freeze_sha256', 'frozen_manifest_sha256', 'first_stage_status') if k in j}
        rp.p('- %s：`%s`（sha256 前 16 = %s）；%s' % (nm, p, N.sha_file(N.P(p))[:16], N.san(json.dumps(keep, ensure_ascii=False))[:700]))
    rp.h(2, '2. Stage 0 七类与 A1-auto')
    g = jload('stage0/stage0_gate.json')
    rp.p('- Stage 0 门：%s' % (N.san(json.dumps({k: g[k] for k in ('counts', 'all_pass', 'c7_fail') if k in g}, ensure_ascii=False)) if g else '未汇总'))
    a1 = jload('registration/a1_auto_E6n.json')
    rp.p('- A1-auto：%s' % (json.dumps({k: a1[k] for k in ('counts', 'all_pass') if k in a1}, ensure_ascii=False) if a1 else '缺'))
    rp.table(csv('stage0/stage0_summary.csv'), dict(主体='Stage 0 检查表（stage0/checks/checks_*.csv）', 单位='行数', 子集='附录 A 各项'), 'E6N-H01-b')
    rp.h(2, '3. 分钟数据合同（A7；stage0/data_contract.json）')
    dc = jload('stage0/data_contract.json')
    if dc:
        for k in ('window', 'cutoff', 'coverage', 'units', 'auction', 'timestamp_convention', 'revisions', 'after_hours', 'five_states', 'open_bar_fact'):
            rp.p('- %s：%s' % (k, N.san(str(dc.get(k)))))
        rp.p('- index_minutes（A13）：%s' % N.san(json.dumps(dc.get('index_minutes'), ensure_ascii=False)))
        rp.p('- 制度表：%s' % N.san(json.dumps(dc.get('regime_table'), ensure_ascii=False)))
    c7 = jload('stage0/c7_minute/c7_summary.json')
    if c7:
        rp.table(pd.DataFrame([dict(item=x['item'], status=x['status'], check=x['check'][:120]) for x in c7['items']]),
                 dict(主体='分钟数据合同实测（stage0/c7_minute）', 单位='状态', 子集='抽样日'), 'E6N-H01-a')
    rp.table(csv('results/coverage_by_feature_year_exchange.csv'), dict(主体='成员可算份额', 单位='decimal', 子集='特征 × 年 × 交易所 × pool0'), 'E6N-H01-c', maxrows=120)
    rp.p('数据请求：`stage0/data_request_E6n.md`（缺口：2010-01..2013-07 分钟、宽基分钟指数、板块历史映射、竞价 / 盘后显式标志与修订规则）。')
    rp.h(2, '4. 跨轮锚（Stage 0 第 2 类）')
    rp.table(csv('stage0/c2/a2_1_pool2_bytes.csv'), dict(主体='六形态 α = 0 → pool2 字节', 单位='sha256', 子集='四段拼接'), 'E6N-H02-a')
    ck = csv('stage0/checks/checks_c2_a21_a234_a25.csv')
    if ck is not None:
        rp.table(ck[['item', 'object', 'metric', 'got', 'status']], dict(主体='A2 锚', 单位='见 metric'), 'E6N-H02-a')
    ck6 = csv('stage0/checks/checks_c2_a26.csv')
    if ck6 is not None:
        rp.table(ck6[['item', 'object', 'metric', 'got', 'status']], dict(主体='A2-6 源随机逐路径复现', 单位='ann_pp'), 'E6N-H02-a')
    rp.h(2, '5. 随机层与向量化核验')
    for f in sorted(glob.glob(N.P('stage0', 'c5_random', 'selftest_*.csv'))):
        D = csv(f)
        rp.table(D.groupby(['item', 'status']).size().reset_index(name='n'), dict(主体='e6n_rand selftest %s' % os.path.basename(f)[9:-4], 单位='项数'), 'E6N-H01-b')
    rp.h(2, '6. 外部输入与环境')
    X = csv('registry/external_inputs_E6n.csv')
    if X is not None:
        rp.table(X.groupby(['id', 'status']).size().reset_index(name='files'), dict(主体='registry/external_inputs_E6n.csv', 单位='文件数'), 'E6N-H01-b')
    rp.p('环境锁：Python 3.10.13 / NumPy 1.26.1 / pandas 2.2.3 / SciPy 1.11.3 / statsmodels 0.14.0 / numba 0.58.1（stage0/checks/checks_c1.csv A1-6）。')
    return rp.write()


# ====================================================================== part1（B1-0 + 推导段）
def part1():
    rp = Report('part1', 'E6n REPORT part1 —— 第一道分钟测量 B1-0（封存）与推导两段')
    s10 = jload('registration/seal_B1_0.json')
    rp.p('B1-0 封存：`registration/seal_B1_0.json` written_at = %s；只打 A2 标签，不改任何对象 / 阈值 / 频率（plan §2.2）。' % (s10 or {}).get('written_at', 'UNDEFINED'))
    G = csv('registration/probe_ledger.csv')
    rp.h(2, '1. A2 第一道读法真值表（主域 = QGOOD ∩ Q0|A4b_CVRv5|α.25|HG10 形成集；FWD_SOURCE h5 低 − 高；单位 bp / 持有期）')
    if G is not None:
        rp.table(G[['member', 'seg1_value', 'seg2_value', 'n_seg1', 'n_seg2', 'overall', 'same_sign', 'label']],
                 dict(B10_HEAD, 主体='B1-0 成员', 子集=MAIN_DOMAIN + ' ∩ QGOOD'), 'E6N-H03-a')
    P = csv('results/b1_0/b1_0_pairs.csv')
    if P is not None:
        x = P[(P.label == 'FWD_SOURCE') & (P.H == 5) & (P.stat == 'low_minus_high_bp') & P.domain.isin(['POOL0', 'CLEAN', MAIN_DOMAIN, 'GATE_A4b_CVRv5_NATIVE',
                                                                                                      'REJ_A4b_CVRv5_Q0HG10'])]
        piv = x.pivot_table(index=['member', 'scope'], columns=['domain', 'segment'], values='value', aggfunc='first')
        piv.columns = ['%s|%s' % c for c in piv.columns]
        rp.h(2, '2. 四域并排（低 − 高，bp；QGOOD / ALL）')
        rp.table(piv.reset_index(), dict(B10_HEAD, 主体='B1-0 成员', 子集='pool0 / clean / 门内（原生 / Q0 HG）/ 拒绝集'), 'E6N-H03-a')
    M_ = csv('results/b1_0/b1_0_matched.csv')
    if M_ is not None:
        x = M_[(M_.label == 'FWD_SOURCE') & (M_.H == 5) & (M_.stat == 'matched_low_minus_high_bp')]
        piv = x.pivot_table(index=['member', 'domain', 'scope'], columns=['layer', 'segment'], values='value', aggfunc='first')
        piv.columns = ['%s|%s' % c for c in piv.columns]
        rp.h(2, '3. 两层匹配与 GAP 桥（同日 / 同 Q 诊断组 / 同一级行业；低组对高组无放回）')
        rp.table(piv.reset_index(), dict(B10_HEAD, 主体='B1-0 匹配', 算子='两层匹配后低组 − 高组（linear_sum_assignment，L1 / IQR 尺度）'), 'E6N-H03-b')
    for nm, q, t in (('b1_0_bridges', 'E6N-H08-a', '4. OHLC / range 桥并排'), ('b1_0_regimes', 'E6N-H15-a', '5. 制度期（SH 改革前 / 后、SZ）')):
        D = csv('results/b1_0/%s.csv' % nm)
        if D is not None and nm == 'b1_0_bridges':
            D = D[(D.label == 'FWD_SOURCE') & (D.H == 5) & D.domain.isin(['POOL0', MAIN_DOMAIN]) & (D.scope == 'QGOOD')]
        rp.h(2, t)
        rp.table(D, dict(B10_HEAD, 主体='B1-0'), q)
    rp.h(2, '6. 推导两段账户：主 72（D 相对原父，ann_pp）与随机参照')
    S = cat('results/deriv/descriptor_stats_%s.csv', N.DERIV_SEGS)
    D72 = csv('registry/descriptors_E6n.csv')
    if S is not None and D72 is not None:
        p72 = set(D72.desc_id[D72.is_primary72.astype(str) == 'True'])
        x = S[S.desc_id.isin(p72)][['desc_id', 'segment', 'D_ann_pp', 'n', 'se_H_ann_pp', 'net8_ann_pp', 'turn_mean_decimal']]
        rp.table(x.sort_values(['desc_id', 'segment']), dict(主体='主 72', 子集='推导两段', 日期='2010-01-04 … 2018-12-28（推导两段）'), 'E6N-H02-b')
    R = cat('results/deriv/random_refs_%s.csv', N.DERIV_SEGS)
    if R is not None:
        R = R[R.kind == 'OBJECT']
        R['pos_2mcse'] = (R.rmr > 2 * R.mcse)
        g = R.groupby(['mechanism', 'segment']).agg(objects=('desc_id', 'nunique'), share_rmr_gt_2mcse=('pos_2mcse', 'mean'), worst_mcse=('mcse', 'max')).reset_index()
        rp.table(g, dict(主体='随机参照（推导段）', 单位='份额 / ann_pp', 日期='2010-01-04 … 2018-12-28（推导两段）'), 'E6N-H10-a')
    sd = jload('registration/seal_deriv.json')
    rp.p('seal_deriv：%s' % (json.dumps({k: sd[k] for k in ('written_at', 'n_files', 'queued_missing', 'n_receipts', 'all_ok') if k in sd}, ensure_ascii=False) if sd else '未写'))
    return rp.write()


# ====================================================================== part2（完整账户与对照）
def part2():
    rp = Report('part2', 'E6n REPORT part2 —— 完整账户（四段）、对照、四账户与随机')
    S = cat('results/full/descriptor_stats_%s.csv', N.SEGMENTS)
    Df = csv('results/full/descriptor_stats_FULL.csv')
    D72 = csv('results/full/primary72_E6n.csv')
    if Df is not None and D72 is not None:
        x = D72.merge(Df, on='desc_id', how='left')
        rp.h(2, '1. 主 72（12 配方 × 六形态；FULL = Σ n_s D_s / Σ n_s，G4 = 段中位）')
        rp.table(x, dict(主体='主 72', 子集='四段'), 'E6N-H02-b')
    CF = csv('results/full/comparison_full.csv')
    if CF is not None:
        rp.h(2, '2. 比较族汇总（每视图：FULL 中位 / 正份额 / 条数）')
        CF['pos'] = pd.to_numeric(CF.FULL_ann_pp, errors='coerce') > 0
        g = CF.groupby('view').agg(n=('comparison_id', 'size'), FULL_median_ann_pp=('FULL_ann_pp', 'median'), share_FULL_pos=('pos', 'mean')).reset_index()
        rp.table(g, dict(主体='comparison_manifest_E6n 全部比较', 单位='ann_pp / 份额'), 'E6N-H10-a')
        key = CF[CF.left_desc_id.str.contains(r'\|A4b_CVRv5\|HG10\|H5\|s0\.25\|QGOOD\|a0\.25\|f5\|d\+1$', regex=True)]
        rp.h(2, '3. 主母体 A4b_CVRv5 × HG10 × H5 × .25 × QGOOD 的全部比较（单对象差，不以族中位替代）')
        rp.table(key[['comparison_id', 'view', 'left_desc_id', 'right_desc_id', 'FULL_ann_pp', 'G4_ann_pp', 'n_total']], dict(主体='主母体新行'), 'E6N-H04-c')
    for nm, q, t in (('four_account_ledger_%s.csv', 'E6N-H09-c', '4. 信息 × 记忆四账户 / 合用四账户（逐日先闭合再年化）'),
                     ('support_four_accounts_%s.csv', 'E6N-H10-b', '5. 支持桥 C_N − P_N = (C_S − P_S) + (C_N − C_S) − (P_N − P_S)'),
                     ('component_dose_ledger_%s.csv', 'E6N-H04-d', '6. COMPONENT_DOSE 账本')):
        D = csv('results/full/' + nm.replace('_%s', ''))
        rp.h(2, t)
        if D is not None and 'closure_maxabs' in D.columns:
            rp.p('闭合：max |残差| = %s（全部行）' % fmt(float(pd.to_numeric(D.closure_maxabs, errors='coerce').max())))
        if D is not None and nm.startswith('four'):
            num = [c for c in ('I_ann_pp', 'R_ann_pp', 'X_ann_pp', 'total_ann_pp') if c in D.columns]
            D = D.groupby(['kind', 'feature', 'memory', 'segment'])[num].median().reset_index()
        elif D is not None and nm.startswith('support'):
            num = [c for c in ('native_diff_ann_pp', 'support_diff_ann_pp', 'child_shrink_ann_pp', 'parent_shrink_ann_pp') if c in D.columns]
            D['feature'] = D.owner_desc_id.str.split('|').str[1]
            D = D.groupby(['feature', 'segment'])[num].median().reset_index() if num else D
        elif D is not None:
            D['feature'] = D.comp_id.str.split('|').str[1]
            D = D.groupby(['feature', 'segment'])[['D_ann_pp', 'owner_minus_cdose_ann_pp']].median().reset_index() if 'D_ann_pp' in D else D
        rp.table(D, dict(主体=nm.split('_%')[0], 单位='ann_pp（族中位；单对象见机器表）'), q)
    R = csv('results/full/random_refs.csv')
    if R is not None:
        R = R[(R.kind == 'OBJECT')]
        R['pos_2mcse'] = pd.to_numeric(R.rmr, errors='coerce') > 2 * pd.to_numeric(R.mcse, errors='coerce')
        g = R.groupby(['mechanism', 'segment']).agg(objects=('desc_id', 'nunique'), share_rmr_gt_2mcse=('pos_2mcse', 'mean'), worst_mcse=('mcse', 'max'),
                                                    paths_min=('paths_run', 'min'), paths_max=('paths_run', 'max')).reset_index()
        rp.h(2, '7. 随机参照（新增内容随机 = 诊断；LEGACY_POLICY_RANDOM = 原资格 e随机）')
        rp.table(g, dict(主体='random_refs.csv', 单位='份额 / ann_pp / 路径数'), 'E6N-H10-a')
    B = csv('results/full/bootstrap/simultaneous_band_q95.csv')
    rp.h(2, '8. bootstrap 同时带（段内平稳，L = 20 / 60，各 2,000）')
    rp.table(B, dict(主体='bootstrap', 单位='t 分位'), 'E6N-H16-a')
    return rp.write()


# ====================================================================== part3（资格与前沿）
def part3():
    rp = Report('part3', 'E6n REPORT part3 —— 资格（六条 + PROPOSED_PORT3_T）、实质改善与前沿')
    P = csv('results/full/policy_E6n.csv')
    if P is not None:
        P['head'] = P.policy_result.astype(str).str.split('（').str[0]
        rp.h(2, '1. 政策结果计数（PROPOSED_PORT3_T × FULL）')
        rp.table(P.groupby(['kind', 'head']).size().reset_index(name='objects'), dict(主体='policy_E6n.csv', 单位='对象数'), 'E6N-H02-b')
        rp.table(P[P.is_primary72.astype(str) == 'True'][['desc_id', 'FULL_ann_pp', 'G4_ann_pp', 'FULL_sc_ann_pp', 'years_pos', 'e_rand', 'policy_result',
                                                         'diag_CONTENT_IID_post', 'diag_CONTENT_ISK_P5_post']],
                 dict(主体='主 72 政策', 单位='ann_pp / 状态'), 'E6N-H02-b')
        und = P[P.policy_result.astype(str).str.contains('POLICY_UNDECIDABLE_HISTORY')]
        rp.p('POLICY_UNDECIDABLE_HISTORY 对象数：%d（分钟成员在未覆盖段 / 年上不能由回源 Q0 代替证明通过；可用期研究表 `results/full/policy_available_period_E6n.csv` 只报数）。' % len(und))
    I = csv('results/full/improvement_E6n.csv')
    rp.h(2, '2. 实质改善表（对当前 Q0 HG10 / LAG1_10，同形态 / α / H；与资格表分列）')
    if I is not None and 'dnet8_FULL_ann_pp' in I.columns:
        I['feature'] = I.desc_id.str.split('|').str[1]
        g = I.groupby(['versus', 'feature']).agg(n=('desc_id', 'size'), dFULL_median=('dnet8_FULL_ann_pp', 'median'),
                                                 share_pos=('improves_frontier_FULL', 'mean')).reset_index()
        rp.table(g, dict(主体='improvement_E6n.csv', 单位='ann_pp / 份额'), 'E6N-H04-c')
    F = csv('results/full/frontier_E6n.csv')
    rp.h(2, '3. 前沿表（相对 %s）' % FRONT)
    if F is not None and 'd_vs_frontier_FULL_ann_pp' in F.columns:
        rp.table(F.sort_values('d_vs_frontier_FULL_ann_pp', ascending=False).head(60), dict(主体='frontier_E6n.csv（前 60）', 单位='ann_pp'), 'E6N-H04-c')
    MC = csv('results/full/match_cap_holdings_min.csv')
    rp.h(2, '4. MATCH_CAP_HOLDINGS_MIN（附表；不替代源 FULL_sc）')
    if MC is not None and 'D_holdings_min_ann_pp' in MC.columns:
        rp.table(MC.groupby('segment').D_holdings_min_ann_pp.describe().reset_index(), dict(主体='H5 政策对象', 单位='ann_pp'), 'E6N-H10-b')
    return rp.write()


# ====================================================================== mechanisms（卡）
def mechanisms():
    rp = Report('mechanisms', 'E6n REPORT mechanisms —— 16 张卡、10 条方向断言、CC 原预测携带')
    K = csv('registration/cards_stageB_E6n.csv')
    A = csv('registration/claims_E6n.csv')
    G = csv('registration/probe_ledger.csv')
    CF = csv('results/full/comparison_full.csv')
    rp.h(2, '1. 10 条方向断言（plan §13.1；负点估 = 方向 miss；正而区间宽 = 方向相符但证据有限；域 / 制度分歧 = mixed；未覆盖 = 未检验）')
    rows = []
    gl = G.set_index('member') if G is not None else None

    def b10(member):
        if gl is None or member not in gl.index:
            return np.nan, 'NOT_RUN'
        r = gl.loc[member]
        return float(r.overall), str(r.label)

    def cmpv(view, left):
        if CF is None:
            return np.nan
        x = CF[(CF.view == view) & (CF.left_desc_id == left)]
        return float(x.FULL_ann_pp.iloc[0]) if len(x) else np.nan
    L_PATH = 'CORE|Q_PATH|A4b_CVRv5|HG10|H5|s0.25|QGOOD|a0.25|f5|d+1'
    L_THIN = 'CORE|Q_CLOSE_THIN|A4b_CVRv5|HG10|H5|s0.25|QGOOD|a0.25|f5|d+1'
    B2c = cat('results/%s/b2/b2_controls_%%s.csv' % 'deriv', N.DERIV_SEGS)
    B3 = csv('results/full/b3/b3_same_count.csv')
    for aid, member in (('H03-P', 'PL_REL20_f5'), ('H05-P', 'TAIL_PUSH'), ('H06-P1', 'TAIL_VOL_REL20'), ('H06-P2', 'JSD_PROFILE20')):
        v, lab = b10(member)
        rows.append(dict(assertion_id=aid, estimand='B1-0 主域 %s 低 − 高 H5（两推导段 n 加权）' % member, value=v, unit='bp', reading=lab, query_id='E6N-%s-a' % aid[:3]))
    for aid, view, left in (('H04-P1', 'VS_SAME_MEMORY_Q0', L_PATH), ('H04-P2', 'PATH_MINUS_Q_RV', L_PATH), ('H07-P1', 'VS_SAME_MEMORY_Q0', L_THIN),
                            ('H07-P2', 'THIN_MINUS_LEVEL', L_THIN)):
        v = cmpv(view, left)
        rows.append(dict(assertion_id=aid, estimand='%s FULL：%s' % (view, left), value=v, unit='ann_pp',
                         reading=('UNDEFINED' if not np.isfinite(v) else ('方向相符（正点估；证据强度见 bootstrap 带）' if v > 0 else '方向 miss（负 / 零点估）')), query_id='E6N-%s-c' % aid[:3]))
    if B2c is not None and len(B2c):
        x = B2c[(B2c.form == 'A4b_CVRv5') & (B2c.object_key == 'HG10|a0.25|Q0') & (B2c.H == 5) & (B2c.control == 'SAME_RATE_RANDOM')]
        v = float(np.average(x.real_minus_control_bp, weights=x.n_events_real)) if len(x) and x.n_events_real.sum() > 0 else np.nan
        rows.append(dict(assertion_id='H12-P', estimand='Q0 HG 主母体 H5：CVR 跳升触发条件改善 − 同率随机（两推导段事件加权）', value=v, unit='bp / 事件',
                         reading='UNDEFINED' if not np.isfinite(v) else ('方向相符' if v > 0 else '方向 miss'), query_id='E6N-H12-d'))
    if B3 is not None and len(B3):
        x = B3[(B3.core == 'A4b') & (B3.object_key == 'HG10|a0.25|Q0') & (B3.H == 5) & (B3.weights == 'REDO_DEV')]
        rr = x[x.control == 'CVR_REAL'].set_index('segment').D_vs_parent_ann_pp
        cc = x[x.control == 'RANDOM_LEGAL_CVR'].set_index('segment').D_vs_parent_ann_pp
        dd = (rr - cc).dropna()
        v = float(dd.mean()) if len(dd) else np.nan
        rows.append(dict(assertion_id='H13-P', estimand='Q0 HG 主裸 A4b + CVR20 k5 − 同日同父同数随机删除（REDO_DEV，H5；段等权近似）', value=v, unit='ann_pp',
                         reading='UNDEFINED' if not np.isfinite(v) else ('方向相符' if v > 0 else '方向 miss'), query_id='E6N-H13-a'))
    rp.table(pd.DataFrame(rows), dict(主体='10 条方向断言', 算子='见 estimand 列', 分母='B1-0 行：有效配对形成日；账户行：各段有效配对日（FULL = n 加权四段）',
                                      基准='见 estimand 列（B1-0 = 同域同日低 − 高；账户 = 所列视图的右端）', 单位='见 unit 列',
                                      日期='B1-0 行 2010-01-04 … 2018-12-28；H12 行推导两段；其余 2010-01-04 … 2026-03-27', H='5',
                                      成本='账户行源 8bp；B1-0 行不适用（前向源收益标签）'), 'E6N-H16-a')
    rp.h(2, '2. 16 张卡（字段原文取自 PLAN_COPY；结果列 = 绑定 query 的机器表）')
    if K is not None:
        rp.table(K[['card', 'title', 'card_type', 'first_stage_evidence', 'query']],
                 dict(主体='cards_stageB_E6n.csv（Stage B 冻结时的登记状态）', 分母='不适用（卡片字段）', 基准='不适用', 单位='—', 日期='冻结 2026-10-15 11:19', H='不适用',
                      成本='不适用', exposure='登记（读数在所列 query）'), 'E6N-H16-a')
    rp.h(2, '3. CC 原预测携带（plan §10.1；原句逐字归档于 registration/source_claim_reconciliation.csv；不重复计命中）')
    C = csv('registry/cc_carry_E6n.csv')
    if C is not None:
        rp.table(C[['carry_id', 'source_locator', 'plan_treatment', 'scoring_rule', 'status']],
                 dict(主体='CC 携带表（registry/cc_carry_E6n.csv）', 分母='不适用（登记字段）', 基准='不适用', 单位='—', 日期='冻结 2026-10-15 11:19', H='不适用', 成本='不适用',
                      exposure='携带（不重复计命中）'), 'E6N-H16-b')
    return rp.write()


# ====================================================================== carried（B2–B6）
def carried():
    rp = Report('carried', 'E6n REPORT carried —— B2 退出账本诊断、B3 同数对照、B4 全 A、B5 收尾、B6 2024–26')
    for ph, segs in (('deriv', N.DERIV_SEGS), ('full', N.POST_SEGS)):
        ov = cat('results/%s/b2/b2_order_overlay_%%s.csv' % ph, segs)
        if ov is not None and 'net_ann_pp' in ov.columns:
            x = ov[(ov.trigger == 'CVR_JUMP') & (ov.H == 5)]
            rp.h(2, 'B2 订单 overlay（%s；CVR_JUMP，H5；SOLO / JOINT_FROZEN 分列不相加）' % ph)
            rp.table(x[['segment', 'form', 'object_key', 'horizon_mode', 'mirror', 'fee_mode', 'n_events', 'gross_ann_pp', 'fee_delta_ann_pp', 'net_ann_pp',
                        'gross_bp_per_event', 'right_censored_events', 'next_rank_unfilled']], dict(主体='B2 冻结源账本 overlay', 单位='ann_pp / bp'), 'E6N-H12-b')
        ct = cat('results/%s/b2/b2_controls_%%s.csv' % ph, segs)
        if ct is not None and len(ct):
            rp.table(ct[(ct.H == 5)], dict(主体='B2 对照（同率随机 / CVR 水平 / 伯努利）', 单位='bp / 事件'), 'E6N-H12-d')
    for ph, segs in (('deriv', N.DERIV_SEGS), ('full', N.POST_SEGS)):
        b3 = cat('results/%s/b3/b3_same_count_%%s.csv' % ph, segs)
        if b3 is not None and len(b3):
            rp.h(2, 'B3 同数对照（%s；H5）' % ph)
            rp.table(b3[b3.H == 5][['segment', 'core', 'object_key', 'control', 'weights', 'D_vs_parent_ann_pp', 'D_sd_paths', 'paths', 'deleted_cells', 'status']],
                     dict(主体='B3', 单位='ann_pp（相对裸父）'), 'E6N-H13-a')
        b4 = cat('results/%s/b4/b4_bridges_%%s.csv' % ph, segs)
        if b4 is not None and len(b4):
            rp.h(2, 'B4 全 A 域桥（%s；FWD_SOURCE h5）' % ph)
            rp.table(b4[(b4.label == 'FWD_SOURCE') & (b4.H == 5)], dict(主体='B4', 单位='decimal / bp'), 'E6N-H14-a')
    for nm, q in (('results/full/b5/b5_dedupe.csv', 'E6N-H16-a'), ('results/full/b5/b5_leak_bridge.csv', 'E6N-H16-a'), ('results/full/b6/b6_event_contrib.csv', 'E6N-H15-b')):
        rp.h(2, os.path.basename(nm))
        rp.table(csv(nm), dict(主体=os.path.basename(nm)), q)
    return rp.write()


# ====================================================================== REVIEW_input（索引）
def review_input():
    rp = Report('REVIEW_input', 'E6n REVIEW_input —— query / 路径 / 单位索引')
    Q = csv('registry/query_registry_E6n.csv')
    rp.table(Q, dict(主体='query_registry_E6n.csv', 单位='—'), 'E6N-H16-a')
    S = csv('reports/queries_full/_summary.csv')
    rp.table(S, dict(主体='query 表生成汇总', 单位='行数 / 状态'), 'E6N-H16-a')
    rp.p('SCHEMA：`reports/SCHEMA.md`（文件 / 类型 / 行数 / 键列 / 列名 / 单位 / 生成脚本；交付时实测刷新，闭包门 ⑤ 核）。')
    return rp.write()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('which', choices=['r0', 'part1', 'part2', 'part3', 'mechanisms', 'carried', 'review_input', 'limits', 'all'])
    a = ap.parse_args()
    import e6n_gate as GT
    if a.which not in ('part1', 'r0', 'limits'):
        for s in N.POST_SEGS:
            GT.post_gate(s, 'reports')
    fns = dict(r0=r0, part1=part1, part2=part2, part3=part3, mechanisms=mechanisms, carried=carried, review_input=review_input, limits=limit_register)
    todo = list(fns) if a.which == 'all' else [a.which]
    outs = [fns[k]() for k in todo]
    N.write_receipt('E6n_reports_%s' % a.which, outs, code=[__file__])
    print(json.dumps(dict(reports=[N.rel(p) for p in outs]), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
