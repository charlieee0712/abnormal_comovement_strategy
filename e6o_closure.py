# -*- coding: utf-8 -*-
"""E6o §C 收尾（brief §8；附录 B.11 / B.15 / C）：
  python3 e6o_closure.py identities   全部账户的经济 / 技术恒等 + Stage 0 恒等 → verify/identities_E6o.csv
  python3 e6o_closure.py schema       reports/SCHEMA.md（由实际文件生成）+ SCHEMA_DEVIATIONS.md + reports/E6o_REVIEW_input.md（文件索引）
  python3 e6o_closure.py gate         闭包门（E6n 27 项适配 + 本轮 18 项）→ verify/closure_E6o.csv / .json（任一 FAIL → 退出码 1）
  python3 e6o_closure.py handoff      副本包 replica/E6o/<ts>/ + 交接目录 handoff/E6o_<ts>/ + HANDOFF_SHA256.txt
  python3 e6o_closure.py dscript <handoff>  决策端脚本：核 sha → py_compile → 运行 → 输出入 handoff 并追加 sha"""
import os
import re
import sys
import json
import glob
import time
import shutil
import hashlib
import subprocess

import numpy as np
import pandas as pd

import e6o_core as O
import e6o_engine as E

V0 = 1e8
CONTRACT = ['registration/registry_E6o.csv', 'registration/comparisons_E6o.csv', 'registration/ledger_G_E6o.csv', 'registration/ledger_E_E6o.csv',
            'statistics/account_summary_E6o.csv', 'statistics/randoms_E6o.csv', 'statistics/random_paths_main_E6o.csv', 'diagnostics/stage0_E6o.csv',
            'statistics/policy_E6o.csv', 'statistics/main72_E6o.csv', 'verify/identities_E6o.csv', 'events/event_counts_E6o.csv', 'reports/claims_E6o.csv',
            'reports/query_registry_E6o.csv', 'accounts/daily/INDEX.csv', 'code_register/deploy_log.csv',
            'diagnostics/D1_size_dose_E6o.csv', 'diagnostics/D2_age_weight_E6o.csv', 'diagnostics/D3_capacity_E6o.csv', 'diagnostics/D4_regime_E6o.csv',
            'diagnostics/D5_veto_exit_E6o.csv', 'diagnostics/D6_minute_kleg_E6o.csv', 'diagnostics/G1_E6o.csv']
EXTRA_TABLES = ['registration/comparisons_extra_E6o.csv', 'registration/run_plan_E6o.csv', 'registration/level_worst_refs_E6o.csv', 'registration/random_scope_E6o.csv',
                'registration/trigger_definitions_E6o.csv', 'registration/cards_E6o.csv', 'registration/cc_carried_E6o.csv', 'statistics/yearly_D_E6o.csv',
                'statistics/contrasts_E6o.csv', 'diagnostics/stage0_accounting_bridge_E6o.csv', 'diagnostics/S0_10_age_remaining_E6o.csv', 'verify/refcheck_E6o.csv',
                'verify/identities_E6o_stage0.csv']
JSONS = ['registration/freeze_E6o.json', 'registration/seal_A2.json', 'registration/seal_final.json', 'registration/policy_profile_E6o.json',
         'registration/registry_facts_E6o.json', 'diagnostics/source_fn_sha256_E6o.json']
REPORTS = ['E6o_REPORT_R0.md', 'E6o_REPORT_part1.md', 'E6o_REPORT_part2.md', 'E6o_REPORT_part3.md', 'E6o_REPORT_mechanisms.md', 'E6o_REPORT_carried.md', 'E6o_cards.md',
           'E6o_REVIEW_input_notes.md', 'E6o_limit_register.md', 'E6o_lessons_delta.md', 'E6o_executor_retrospective.md', 'E6o_code_change_register.md',
           'SCHEMA.md', 'SCHEMA_DEVIATIONS.md', 'E6o_REVIEW_input.md', 'E6o_commit_whitelist.md']
STATUS = {'COMPUTED', 'UNKNOWN', 'NOT_APPLICABLE', 'UNMATCHED', 'MC_LIMIT', 'SOURCE_BINDING_PENDING', 'POLICY_MAPPING_UNRESOLVED', 'RIGHT_CENSORED', 'NOT_RUN',
          'NO_RANDOM_BY_SCOPE', 'BLOCKED', 'PASS', 'DIFFERS', 'INFO'}


def rd(rel):
    return pd.read_csv(O.P(rel), keep_default_na=False, na_values=[''])


def sens_pattern():
    """敏感串：IPv4、凭据类词（拼接生成，代码文本里不出现原词）、运行时取得的用户目录名（不写字面量）。"""
    words = ['pass' + 'w', chr(0x53e3) + chr(0x4ee4), chr(0x5bc6) + chr(0x7801), 'PRIVATE' + ' KEY', 'ssh' + '-rsa', 'ssh' + '-ed25519', 'tok' + 'en=', 'BEGIN ' + 'OPENSSH']
    names = {os.path.basename(os.path.expanduser('~')), os.environ.get('USER', ''), os.environ.get('LOGNAME', ''),
             os.path.basename(os.path.dirname(os.path.abspath(O.RES_ROOT))), os.path.basename(sys.prefix)}
    names = [re.escape(n) for n in names if n and len(n) >= 4 and n not in ('root', 'results', 'mnt', 'sda2')]
    return re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|' + '|'.join(re.escape(w) for w in words) + ('|' + '|'.join(names) if names else ''), re.I)


def identities(deriv=False):
    """deriv = True：B 前预测——用 A2 推导段账户（accounts_run/deriv，前 d19 行）核同一组恒等，写 tmp/dryrun/verify/。"""
    R = rd('registration/registry_E6o.csv')
    st0 = rd('verify/identities_E6o_stage0.csv')
    rows = []
    worst = dict(cash=0.0, tele=0.0, tk=0.0, lk=0.0, fee=0.0, nav=0.0)
    where = dict(cash='', tele='', tk='', lk='', fee='', nav='')
    n = 0
    maxdate = ''
    dates_ = np.load(os.path.join(O.cache_dir(), 'panels', 'dates.npy'))
    dcut = int(np.searchsorted(dates_, '2019-01-01')) if deriv else len(dates_)
    root = O.P('tmp', 'dryrun') if deriv else O.work()
    for r in R[R.series != 'P_SOURCE'].itertuples():
        z = np.load(O.P('accounts_run', 'deriv' if deriv else 'full', r.exec_hash[:2], '%s.npz' % r.exec_hash), allow_pickle=False)
        DY = z['DY'][:dcut]
        prev_w = dict(worst)
        n += 1
        nav = DY[:, E.DYI['nav_post']]
        cash = DY[:, E.DYI['cash_share']] * nav
        prev = np.r_[V0, cash[:-1]]
        flow = DY[:, E.DYI['sell_val']] - DY[:, E.DYI['buy_val']] - DY[:, E.DYI['fee']]
        worst['cash'] = max(worst['cash'], float(np.max(np.abs(cash - prev - flow)) / V0))
        worst['tele'] = max(worst['tele'], float(abs(np.prod(1.0 + DY[:, E.DYI['r_net']]) - nav[-1] / V0)))
        worst['nav'] = max(worst['nav'], float(np.max(np.abs(DY[:, E.DYI['nav_pre']] - DY[:, E.DYI['fee']] - nav)) / V0))
        worst['fee'] = max(worst['fee'], float(np.max(np.abs(DY[:, E.DYI['fee']] - O.FEE_RATE * DY[:, E.DYI['traded']])) / V0))
        tg = DY[:, E.DYI['tag_amt']]
        tk = np.abs(tg[1:] - (tg[:-1] + DY[1:, E.DYI['tag_new']] - DY[1:, E.DYI['tag_use_reg']] - DY[1:, E.DYI['tag_use_ext']] - DY[1:, E.DYI['tag_matured']]))
        worst['tk'] = max(worst['tk'], float(tk.max() / V0))
        lk = DY[:, E.DYI['lock_amt']]
        lkd = np.abs(lk[1:] - (lk[:-1] + DY[1:, E.DYI['lock_new']] - DY[1:, E.DYI['lock_matured']]))
        worst['lk'] = max(worst['lk'], float(lkd.max() / V0))
        for k_ in worst:
            if worst[k_] > prev_w[k_]:
                where[k_] = r.exec_id
    # 复制 Stage 0 行（源 / 攻击 / 桥 / 锚）
    keep = ['SOURCE_REPLICATION', 'SOURCE_ANCHOR_FRONTIER', 'SOURCE_HOLDINGS_SHA', 'NOEXIT_EQ_PARENT', 'ACCOUNTING_BRIDGE', 'REENTRY_EPISODE_CASES', 'TICKET_DOUBLE_SPEND',
            'TICKET_MATURITY_REUSE', 'JOURNAL_REPLAY', 'WRONG_MOTHER_MERGE', 'FUTURE_DATA_PLANT', 'UNIT_PLANT']
    for r in st0[st0.check_id.isin(keep)].itertuples():
        rows.append(dict(check_id=r.check_id, description=r.description, exec_id=r.exec_id, value=r.value, max_abs_diff=r.max_abs_diff, tolerance=r.tolerance, status=r.status))
    def add(cid, desc, val, mx, tol, ok):
        rows.append(dict(check_id=cid, description=desc, exec_id='', value=val, max_abs_diff=mx, tolerance=tol, status='PASS' if ok else 'DIFFERS'))
    add('CASH_EQUATION', '全部 %d 个账户（P_ACCOUNT + C_ACCOUNT）逐日：现金 = 昨现金 + 卖款 − 买款 − 费（/ V0）' % n, n, worst['cash'], 1e-6, worst['cash'] <= 1e-6)
    add('NAV_TELESCOPE', '全部账户：Π(1 + R_net) = V⁺_终 / V0', n, worst['tele'], 1e-9, worst['tele'] <= 1e-9)
    add('TICKET_CONSERVATION', '全部账户逐日：标签余额 = 昨余 + 新建 − 常规耗 − 额外耗 − 到期重分类；锁定同理（/ V0；取两者最大）', n, max(worst['tk'], worst['lk']), 1e-6,
        max(worst['tk'], worst['lk']) <= 1e-6)
    add('FEE_NET_ORDER', '全部账户逐日：费用 = 4e−4 × Σ|证券净市场订单名义|（同日同证券先内部转移）（/ V0）', n, worst['fee'], 1e-9, worst['fee'] <= 1e-9)
    rows.append(dict(check_id='FIRSTDAY_ALLEXIT_VS_H1', description='"全部首日退出 = H1"只在资本投入 / 初始化 / 交易等同时成立；本账户从 CASH_V0、按 NAV × w / H 分批建仓，与 H1 不等同（spec test_firstday_h5_not_h1_cash_start）→ 只记、不作恒等',
                     exec_id='', value='NOT_EQUIVALENT_BY_DESIGN', max_abs_diff='', tolerance='', status='INFO'))
    # E7 守卫：全部交付表 / 日序列的最大日期
    for p in glob.glob(os.path.join(root, 'accounts', 'daily', '*.csv')) + [os.path.join(root, 'statistics', 'yearly_D_E6o.csv')]:
        try:
            d = pd.read_csv(p, usecols=lambda c: c in ('date', 'date_max'), dtype=str)
            for c in d.columns:
                m = d[c].max()
                if isinstance(m, str) and m > maxdate:
                    maxdate = m
        except Exception:
            pass
    maxdate = max(maxdate, str(max(dates_.tolist())))
    rows.append(dict(check_id='E7_GUARD', description='全部交付日序列与面板的最大日期；分钟读取接口对 > 2026-03-27 拒绝（FUTURE_DATA_PLANT）', exec_id='', value=maxdate[:10],
                     max_abs_diff=0.0, tolerance=0.0, status='PASS' if maxdate[:10] <= O.CUTOFF else 'DIFFERS'))
    D = pd.DataFrame(rows)[['check_id', 'description', 'exec_id', 'value', 'max_abs_diff', 'tolerance', 'status']]
    O.atomic_write_csv(os.path.join(root, 'verify', 'identities_E6o.csv'), D)
    print(json.dumps(dict(deriv=deriv, rows=len(D), worst=worst, worst_at={k: v.split('|')[:6] for k, v in where.items() if v}, maxdate=maxdate[:10],
                          statuses=D.groupby('check_id').status.agg(lambda s: ','.join(sorted(set(s)))).to_dict()), ensure_ascii=False), flush=True)


def phys_rows(p):
    with open(p, 'rb') as fh:
        return max(sum(1 for _ in fh) - 1, 0)


GEN = {'registry': 'e6o_registry.py', 'comparisons': 'e6o_registry.py', 'run_plan': 'e6o_registry.py', 'level_worst': 'e6o_registry.py', 'random_scope': 'e6o_registry.py',
       'trigger_def': 'e6o_registry.py', 'ledger': 'e6o_a1.py / e6o_claims.py', 'cards': 'e6o_a1.py', 'cc_carried': 'e6o_a1.py', 'account_summary': 'e6o_stats.py',
       'yearly': 'e6o_stats.py', 'event_counts': 'e6o_stats.py', 'INDEX': 'e6o_stats.py', 'randoms': 'e6o_policy.py', 'random_paths_main': 'e6o_policy.py',
       'policy': 'e6o_policy.py', 'main72': 'e6o_policy.py', 'claims': 'e6o_claims.py', 'query_registry': 'e6o_claims.py', 'contrasts': 'e6o_claims.py',
       'stage0': 'e6o_stage0.py / e6o_stage0b.py', 'S0_10': 'e6o_stage0b.py', 'accounting_bridge': 'e6o_stage0.py', 'identities': 'e6o_closure.py',
       'refcheck': 'e6o_refcheck.py', 'G1': 'e6o_g1.py', 'D1': 'e6o_diag.py', 'D2': 'e6o_diag.py', 'D3': 'e6o_diag.py', 'D4': 'e6o_diag.py', 'D5': 'e6o_diag.py',
       'D6': 'e6o_diag.py', 'deploy_log': 'e6o_notes.py'}
KEYS = {'registry_E6o.csv': 'exec_id', 'comparisons_E6o.csv': 'comparison_id', 'account_summary_E6o.csv': 'exec_id × segment', 'randoms_E6o.csv': 'owner_exec_id × mechanism × segment',
        'policy_E6o.csv': 'exec_id × execution_profile × profile_name', 'main72_E6o.csv': 'exec_id', 'identities_E6o.csv': 'check_id（可多行）', 'event_counts_E6o.csv': 'exec_id',
        'claims_E6o.csv': 'claim_id', 'query_registry_E6o.csv': 'query_id', 'INDEX.csv': 'exec_hash', 'stage0_E6o.csv': 'probe_id × key', 'ledger_G_E6o.csv': 'g_id',
        'ledger_E_E6o.csv': 'e_id', 'deploy_log.csv': 'file'}


def gen_of(rel):
    for k, v in GEN.items():
        if k in rel:
            return v
    return 'e6o_*'


def schema():
    rows = ['# SCHEMA（由脚本从实际文件生成；附录 B.15）\n',
            '\n| 文件（相对结果目录） | 类型 | 行数或键数 | 键列 | 列名全列 | 单位列说明 | 生成脚本 | query_id 列是否存在 |\n|---|---|---|---|---|---|---|---|\n']
    tables = CONTRACT + EXTRA_TABLES
    for rel in tables:
        p = O.P(rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding='utf-8') as fh:
            hdr = fh.readline().rstrip('\n').split(',')
        unit = 'unit 列' if 'unit' in hdr else ('ann_pp（D / net 类列）' if any(c.endswith('_ann_pp') for c in hdr) else '—')
        rows.append('| %s | csv | %d | %s | %s | %s | %s | %s |\n' % (rel, phys_rows(p), KEYS.get(os.path.basename(rel), '—'), ' / '.join(hdr), unit, gen_of(rel),
                                                                     '是' if 'query_id' in hdr else '否'))
    for rel in JSONS:
        p = O.P(rel)
        if os.path.exists(p):
            j = json.load(open(p))
            rows.append('| %s | json | %d | — | %s | — | %s | 否 |\n' % (rel, len(j), ' / '.join(sorted(j.keys())), gen_of(rel)))
    nd = len(glob.glob(O.P('accounts', 'daily', '*.csv'))) - 1
    rows.append('\n日序列文件 `accounts/daily/<exec_hash>.csv` 共 %d 个（列：date / nav_pre / nav_post / fee / exposure / bench_ret / net_excess_ret / cash_share / n_holdings / n_exits_today；'
                '索引 `accounts/daily/INDEX.csv`）。\n' % nd)
    rows.append('\n口径说明：account_summary 的 G4 / G4_2013 行 status = INFO（其 net / parent_net 为四段中位，不满足 D = net − parent_net；D = 四段 D 中位）；'
                'P_SOURCE 行的父 = 自身（D ≡ 0）；P_ACCOUNT 行的父 = P_SOURCE（D = 会计桥）。account_summary 另加列：D_imp_ann_pp、D_imp_stress_ann_pp、size_dev_pp、'
                'size_unknown_share、boot60_lo、boot60_hi（附录允许加列）。\n')
    O.atomic_write_text(O.P('reports', 'SCHEMA.md'), ''.join(rows))
    dev = ['# SCHEMA 偏离声明\n', '\n| 表 | 列 | 原因 | 影响的探针 |\n|---|---|---|---|\n', '| 无 | — | 合同表、列名、状态词与复合键均按附录 B；加列 / 加表不属偏离 | — |\n']
    O.atomic_write_text(O.P('reports', 'SCHEMA_DEVIATIONS.md'), ''.join(dev))
    print('schema rows', len(rows))


def review_index(hd):
    lines = ['# E6o REVIEW 输入索引（交付文件与 sha256 前 16）\n', '\n> 协议 v1.6 · 方式 B · 未读 E7 · deployment_authorized = false\n\n| 文件 | sha256 前 16 | 行数 |\n|---|---|---|\n']
    for p in sorted(glob.glob(os.path.join(hd, '**', '*'), recursive=True)):
        if os.path.isfile(p) and not p.endswith('HANDOFF_SHA256.txt') and not p.endswith('E6o_REVIEW_input.md'):
            rel = os.path.relpath(p, hd)
            n = phys_rows(p) if p.endswith('.csv') else ''
            lines.append('| `%s` | %s | %s |\n' % (rel, O.sha_file(p)[:16], n))
    return ''.join(lines)


def gate(final=False):
    res = []

    def chk(cid, desc, ok, detail=''):
        res.append(dict(id=cid, desc=desc, status='PASS' if ok else 'FAIL', detail=str(detail)[:400]))
    R = rd('registration/registry_E6o.csv')
    c = R[R.series == 'C_ACCOUNT']
    fam = c[c.execution_profile == 'FEASIBLE_DAILY'].family.value_counts().to_dict()
    want = {'CORE': 540, 'VOLUME20': 72, 'LEVEL_BRIDGE': 96, 'REFERENCE_BRIDGE': 12, 'RECONFIRM': 18, 'SECTOR_RELIEF': 36, 'ENTRY_EXIT': 24, 'FUNDING_NEXT': 24,
            'FUNDING_LAG0': 24, 'FUNDING_REMAIN': 24, 'EDGE_BRIDGE': 96}
    ids = set(R.exec_id)
    ok1 = (len(c) == 1932 and c.logical_id.nunique() == 966 and fam == want and int((c.is_primary72 == 1).sum()) == 72
           and c.groupby('execution_profile').is_main_object.sum().tolist() == [1, 1] and (R.series == 'P_ACCOUNT').sum() >= 48 and (R.series == 'P_SOURCE').sum() >= 24
           and c.parent_exec_id.isin(ids).all() and c.source_parent_exec_id.isin(ids).all() and not R.exec_id.duplicated().any())
    chk('C01', 'registry 行数恒等（1,932 / 966 / 家族 / 72 / 主对象 / 父 / 父引用闭合 / 无重复）', ok1, fam)
    CM = rd('registration/comparisons_E6o.csv')
    chk('C02', 'comparisons 全部 id 在 registry；MAIN_EXIT ≥ 1,932', CM.child_exec_id.isin(ids).all() and CM.parent_exec_id.isin(ids).all() and (CM.kind == 'MAIN_EXIT').sum() >= 1932)
    AS = rd('statistics/account_summary_E6o.csv')
    have = AS.groupby('exec_id').segment.apply(set).to_dict()
    sup = R.set_index('exec_id').support.to_dict()
    miss = [e for e in ids if not ({'2010-2014', '2015-2018', '2019-2023', '2024-2026', 'FULL', 'G4'} | ({'2013-2014', 'FULL_2013', 'G4_2013'} if sup[e] == 'MINUTE_2013' else set())) <= have.get(e, set())]
    comp = AS[AS.status == 'COMPUTED']
    dbad = int(((comp.D_ann_pp - (comp.net_ann_pp - comp.parent_net_ann_pp)).abs() > 1e-9).sum())
    nanc = int(comp[['net_ann_pp', 'parent_net_ann_pp', 'D_ann_pp']].isna().any(axis=1).sum())
    fb = 0
    for e, g in AS.groupby('exec_id'):
        g4 = g[g.segment.isin(['2010-2014', '2015-2018', '2019-2023', '2024-2026'])]
        if len(g4) == 4 and g4.D_ann_pp.notna().all():
            full = (g4.n_days * g4.D_ann_pp).sum() / g4.n_days.sum()
            fr = g[g.segment == 'FULL'].D_ann_pp
            gr = g[g.segment == 'G4'].D_ann_pp
            if len(fr) and abs(float(fr.iloc[0]) - full) > 1e-6:
                fb += 1
            if len(gr) and abs(float(gr.iloc[0]) - float(np.median(g4.D_ann_pp))) > 1e-9:
                fb += 1
    chk('C03', 'account_summary 每对象 × 段齐全；D = net − parent_net；FULL / G4 恒等；COMPUTED 无 NaN', not miss and dbad == 0 and nanc == 0 and fb == 0,
        'missing=%d D_bad=%d nan=%d full_g4_bad=%d' % (len(miss), dbad, nanc, fb))
    ID = rd('verify/identities_E6o.csv')
    req = ['SOURCE_REPLICATION', 'SOURCE_ANCHOR_FRONTIER', 'SOURCE_HOLDINGS_SHA', 'NOEXIT_EQ_PARENT', 'ACCOUNTING_BRIDGE', 'CASH_EQUATION', 'NAV_TELESCOPE', 'TICKET_CONSERVATION',
           'FEE_NET_ORDER', 'FIRSTDAY_ALLEXIT_VS_H1', 'REENTRY_EPISODE_CASES', 'TICKET_DOUBLE_SPEND', 'TICKET_MATURITY_REUSE', 'JOURNAL_REPLAY', 'WRONG_MOTHER_MERGE', 'FUTURE_DATA_PLANT',
           'UNIT_PLANT', 'E7_GUARD']
    att = ['REENTRY_EPISODE_CASES', 'TICKET_DOUBLE_SPEND', 'TICKET_MATURITY_REUSE', 'JOURNAL_REPLAY', 'WRONG_MOTHER_MERGE', 'FUTURE_DATA_PLANT', 'UNIT_PLANT']
    tol_ok = all((ID[ID.check_id == k].status == 'PASS').all() for k in ('NOEXIT_EQ_PARENT', 'CASH_EQUATION', 'NAV_TELESCOPE', 'TICKET_CONSERVATION'))
    chk('C04', 'identities 必含项全在；NOEXIT / CASH / NAV / TICKET ≤ 容差；攻击样例全 BLOCKED',
        all(k in set(ID.check_id) for k in req) and tol_ok and all((ID[ID.check_id == k].status == 'BLOCKED').all() for k in att))
    RT = rd('statistics/randoms_E6o.csv')
    full = AS[AS.segment == 'FULL'].set_index('exec_id')
    need = [e for e in c[c.execution_profile == 'FEASIBLE_DAILY'].exec_id if float(full.loc[e, 'n_exit_intents'] or 0) > 0]
    am = RT[(RT.mechanism == 'AMOUNT_MATCH') & (RT.segment == 'FULL')].set_index('owner_exec_id')
    lack = [e for e in need if e not in am.index or am.loc[e, 'paths'] < 128]
    mm = RT[RT.paths > 0]
    mcbad = int(((mm.rand_sd_D_ann_pp / np.sqrt(mm.paths) - mm.mcse).abs() > 1e-6).sum())
    lw = RT[RT.mechanism == 'LEVEL_WORST_1D'].owner_exec_id.nunique()
    chk('C05', 'randoms 覆盖（brief §6）、mcse 恒等、LEVEL_WORST owner 72', not lack and mcbad == 0 and lw == 72, 'lack=%d mcse_bad=%d lw=%d' % (len(lack), mcbad, lw))
    PO = rd('statistics/policy_E6o.csv')
    pp = set(zip(PO.exec_id, PO.execution_profile))
    chk('C06', 'policy 每 C_ACCOUNT 一行、verdict 词表', all((e, p) in pp for e, p in zip(c.exec_id, c.execution_profile)) and PO.verdict.isin(['通过', '不通过', '不可判']).all())
    CL = rd('reports/claims_E6o.csv')
    QR = rd('reports/query_registry_E6o.csv')
    need_c = ['Q%02d' % i for i in range(1, 19)] + ['E%02d' % i for i in range(1, 8)] + ['CC-%02d' % i for i in range(1, 13)] + ['G-F2-01', 'G-F2-02', 'G-F2-03']
    chk('C07', 'claims 必含 id 全在且 query_id 全在 query_registry', all(x in set(CL.claim_id) for x in need_c) and CL.query_id.isin(set(QR.query_id)).all())
    S0 = rd('diagnostics/stage0_E6o.csv')
    k00 = set(S0[S0.probe_id == 'S0-0'].key)
    chk('C08', 'stage0 S0-0…S0-13 全有行、S0-0 必含键全在', all(('S0-%d' % i) in set(S0.probe_id) for i in range(14)) and all(k in k00 for k in (
        'VETO_MEASURE', 'VETO_CUT_FORM', 'B2_TRIGGER_KIND', 'B2_TRIGGER_MEASURE', 'B2_LEVEL_CONTROL_MEASURE', 'SOURCE_B2_TRIGGER_BINDING', 'SOURCE_B2_TRIGGER_FN_SHA256',
        'SOURCE_CASH_MODEL', 'FEE_CHARGED_TURN_UNIT')))
    EV = rd('events/event_counts_E6o.csv')
    chk('C09', 'events 恒等', ((EV.n_intents - EV.n_realized_early - EV.n_late_fill - EV.n_unfilled - EV.n_censored) == 0).all())
    IX = rd('accounts/daily/INDEX.csv')
    bad_nav = 0
    for r in IX.itertuples():
        d = pd.read_csv(O.P('accounts', 'daily', r.file), usecols=['nav_pre', 'fee', 'nav_post'])
        bad_nav += int(((d.nav_pre - d.fee - d.nav_post).abs() > 1e-6).sum())
    m0 = c[c.is_main_object == 1].exec_id.iloc[0].split('|')
    mains = [e for e in c.exec_id if [e.split('|')[i] for i in (0, 2, 3, 4)] == [m0[i] for i in (0, 2, 3, 4)]]
    chk('C10', 'accounts/daily 范围（72 + P_ACCOUNT + P_SOURCE + 主对象变体）与 NAV 恒等', set(c[c.is_primary72 == 1].exec_id) <= set(IX.exec_id) and set(mains) <= set(IX.exec_id)
        and bad_nav == 0, 'files=%d nav_bad=%d' % (len(IX), bad_nav))
    sc = open(O.P('reports', 'SCHEMA.md'), encoding='utf-8').read()
    rbad = []
    for ln in sc.splitlines():
        cells = [x.strip() for x in ln.strip().strip('|').split('|')]
        if len(cells) >= 3 and cells[0].endswith('.csv') and os.path.exists(O.P(cells[0])):
            if phys_rows(O.P(cells[0])) != int(cells[2]):
                rbad.append(cells[0])
    chk('C11', 'SCHEMA.md 行数 = 实际；合同表全在', not rbad and all(os.path.exists(O.P(t)) for t in CONTRACT), rbad[:5])
    FZ = json.load(open(O.P('registration', 'freeze_E6o.json')))
    a2 = json.load(open(O.P('registration', 'seal_A2.json')))
    fullfiles = glob.glob(O.P('accounts_run', 'full', '*', '*.npz'))
    first = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(min(os.path.getmtime(p) for p in fullfiles)))
    chk('C12', 'freeze 全键；seal_A2.written_at < 任何后段账户首次写入', all(k in FZ for k in ('plan_sha256', 'spec_sha256', 'brief_sha256', 'appendix_sha256', 'd_script_sha256',
        'schema_contract_sha256', 'policy_file_sha256', 'source_fn_sha256', 'data_cutoff', 'protocol', 'mode', 'authorized_by', 'authorized_at', 'written_at')) and a2['written_at'] < first,
        'seal_A2 %s < first_post %s' % (a2['written_at'], first))
    nanhits = []
    for p in glob.glob(O.P('reports', '*.md')):
        txt = open(p, encoding='utf-8').read()
        if re.search(r'(?<![A-Za-z_])(nan|None)(?![A-Za-z_])', txt):
            nanhits.append(os.path.basename(p))
    chk('C13', '报告正文无字面 nan / None', not nanhits, nanhits)
    chk('C14', '全部文件最大日期 ≤ 2026-03-27', str(ID[ID.check_id == 'E7_GUARD'].value.iloc[0])[:10] <= O.CUTOFF)
    cdn = os.path.basename(O.cache_dir())
    chk('C15', '缓存目录名含 E6o-v1.1 与 ce9e98c2', 'E6o-v1.1' in cdn and 'ce9e98c2' in cdn, cdn)
    hdr_bad = [os.path.basename(p) for p in glob.glob(O.P('reports', '*.md')) if os.path.basename(p) not in ('SCHEMA.md', 'SCHEMA_DEVIATIONS.md')
               and not all(s in open(p, encoding='utf-8').read()[:600] for s in ('协议 v1.6', '方式 B', 'E7', 'deployment_authorized = false'))]
    chk('C16', '页首写明无 E7 / 部署授权、协议 v1.6、方式 B', not hdr_bad, hdr_bad)
    spec = open(O.P('verify', 'spec', 'SHA256.txt')).read()
    chk('C17', 'verify/spec 四表 sha 与 plan 附录 C 一致', all(h in spec for h in ('8bdbeedf16cf8e026bcc8c6a00aa91055e12962e6fda887083164ed617458aa5',
        'a6d5e54d7bf19880dd0a88cca71d53bfed372be8fd6d178eeaed16d1d902f987', 'cb8299d905f5029f6ce66bdebd0faa437f530b0496550eaf02f61fd55b2dcbf3',
        'e7299a0103c02dab5f2232fe69e129577eb573d9a144146f61450b8431491044')))
    fzb = frozen_diff()
    chk('C19', 'A1 冻结件：副本 sha = freeze；当前件除 registry.status 与账本结果栏外逐格不变', not fzb, fzb[:6])
    if os.path.exists(O.P('verify', 'replay_A2_vs_B_E6o.csv')):
        rp_ = rd('verify/replay_A2_vs_B_E6o.csv')
        chk('C20', '推导段重放：B 随机路径 / 账户 / 影子在推导段与 A2 逐位相同', (rp_.status == 'PASS').all(), rp_[['check', 'n_diff']].values.tolist())
    else:
        chk('C20', '推导段重放：B 随机路径 / 账户 / 影子在推导段与 A2 逐位相同', False, 'verify/replay_A2_vs_B_E6o.csv 不在')
    if final:
        chk('C18', 'verify/decision/out_E6o_stage2/ 存在且含探针 CSV（结果不作门）', os.path.exists(O.P('verify', 'decision', 'out_E6o_stage2', 'E6o_D_probes_stage2.csv')))
    # ---- E6n 27 项适配
    running = subprocess.run(['pgrep', '-fc', 'python3 e6o_run'], capture_output=True, text=True).stdout.strip()
    chk('S01', '本轮运行中进程 0（e6o_run）', running in ('0', ''), running)
    try:
        gs = subprocess.run(['git', '-C', os.path.dirname(O.__file__), 'status', '--porcelain'], capture_output=True, text=True).stdout.splitlines()
        tracked = [l for l in gs if not l.startswith('??')]
        chk('S02', 'git：tracked 改动 0（e6o_ 新文件未跟踪；白名单提交前）', not tracked, tracked[:5])
    except Exception as e:
        chk('S02', 'git：tracked 改动 0', False, e)
    rc = [json.load(open(p)) for p in glob.glob(O.P('task_status', '*.receipt.json'))]
    rbad = [r.get('task_id') for r in rc if r.get('status') != 'SUCCEEDED' or int(r.get('failed', 0) or 0) != 0]
    chk('S03', '回执（每任务最新一份）：status = SUCCEEDED 且 failed = 0', not rbad, '%d receipts; bad=%s' % (len(rc), rbad[:5]))
    chk('S04', 'seal_A2 / seal_final 在且固定键齐', os.path.exists(O.P('registration', 'seal_A2.json')) and os.path.exists(O.P('registration', 'seal_final.json'))
        and all(k in a2 for k in ('written_at', 'n_files', 'sha256_manifest')))
    st_ok = ID.status.isin(['PASS', 'BLOCKED', 'INFO']).all()
    chk('S05', 'Stage 0 与恒等全过（PASS / BLOCKED / INFO）', st_ok)
    bad_st = []
    for rel in CONTRACT:
        if rel == 'code_register/deploy_log.csv':
            continue                                       # 代码登记的 status = NEW / MODIFIED，不是 B.0 结果状态词
        if not os.path.exists(O.P(rel)):
            bad_st.append('%s:MISSING' % rel)
            continue
        d = rd(rel)
        if 'status' in d.columns:
            vv = set(d.status.astype(str)) - STATUS - {'技术PASS', '技术FAIL'}
            if vv and rel not in ('registration/ledger_G_E6o.csv',):
                bad_st.append('%s:%s' % (rel, sorted(vv)[:3]))
    chk('S06', '状态词扫描（交付 CSV 状态列 ∈ B.0 词表）', not bad_st, bad_st)
    sens = []
    pat = sens_pattern()
    scan = glob.glob(O.P('reports', '*.md')) + [O.P(t) for t in CONTRACT + EXTRA_TABLES if t.endswith('.csv')] + [O.P(j) for j in JSONS]
    scan += [p for p in glob.glob(os.path.join(os.path.dirname(O.__file__), 'e6o_*')) if os.path.isfile(p)]
    for p in scan:
        if os.path.exists(p) and pat.search(open(p, encoding='utf-8', errors='replace').read()):
            sens.append(os.path.basename(p))
    chk('S07', '敏感信息扫描（交付文本 + 本轮代码；IP / 凭据词 / 用户目录名，名单运行时取）', not sens, sens)
    if final:
        lat = O.P('handoff', 'LATEST.txt')
        hd_ = O.P(open(lat).read().strip()) if os.path.exists(lat) else ''
        hits = []
        dsha = '0988d2e5873ed823fb89a697d271e47d3deb0af03dab02087b4289a447e0fc93'      # 决策端脚本原件（其 S22 扫描正则含凭据类词，是模式不是信息；sha 固定、不改）
        for p in (glob.glob(os.path.join(hd_, '**', '*'), recursive=True) if hd_ else []):
            if os.path.isfile(p) and not (os.path.basename(p) == 'E6o_D_stage2.py' and O.sha_file(p) == dsha):
                with open(p, 'rb') as fh:
                    if pat.search(fh.read().decode('utf-8', errors='ignore')):
                        hits.append(os.path.relpath(p, hd_))
        chk('S07b', '交接目录全部文件（含二进制、决策端脚本输出）敏感串扫描', bool(hd_) and not hits, hits[:8] if hd_ else 'no LATEST')
    qbad = [r.query_id for r in QR.itertuples() if not all(os.path.exists(O.P(t.strip().split('（')[0].split(' ')[0])) for t in str(r.table).split('+') if t.strip())]
    chk('S08', 'query：唯一、表存在、≥ 1 行', not QR.query_id.duplicated().any() and (QR.n_rows >= 1).all() and not qbad, qbad[:5])
    chk('N01', '无"全部 NOT_RUN"的 query', not (CL.claim_status == 'NOT_RUN').any())
    chk('S09', '固定表全在且 ≥ 1 行', all(os.path.exists(O.P(t)) and phys_rows(O.P(t)) >= 1 for t in CONTRACT))
    chk('S10', '覆盖：每个登记对象在 account_summary 有四段行', not miss)
    notes = open(O.P('reports', 'E6o_REVIEW_input_notes.md'), encoding='utf-8').read()
    lr = re.findall(r'^\| (L\d\d) \|', open(O.P('reports', 'E6o_limit_register.md'), encoding='utf-8').read(), re.M)
    chk('S11', '限制登记每条在读法注被引用', all(l in notes for l in lr), [l for l in lr if l not in notes][:5])
    chk('S12', '报告齐全', all(os.path.exists(O.P('reports', r)) for r in REPORTS if r != 'E6o_REVIEW_input.md'))
    rp = sorted(glob.glob(O.P('replica', 'E6o', '*', 'MANIFEST_SHA256.txt')))
    rep_ok = False
    if rp:
        base = os.path.dirname(rp[-1])
        rep_ok = all(O.sha_file(os.path.join(base, l.split('  ', 1)[1].strip())) == l.split('  ', 1)[0] for l in open(rp[-1]) if l.strip())
    chk('S13', '副本包 manifest 在且复制后 sha 0 不符', rep_ok)
    chk('S14', 'deployment_authorized 全 false', FZ.get('deployment_authorized') is False)
    chk('S15', 'E7 截止：守卫攻击 BLOCKED、产物日期 ≤ 2026-03-27', (ID[ID.check_id == 'FUTURE_DATA_PLANT'].status == 'BLOCKED').all() and str(ID[ID.check_id == 'E7_GUARD'].value.iloc[0])[:10] <= O.CUTOFF)
    chk('N02', '报告正文字面 nan / None（同 C13）', not nanhits)
    nm = pd.to_numeric(ID[ID.check_id.isin(['NOEXIT_EQ_PARENT', 'NAV_TELESCOPE', 'SOURCE_REPLICATION'])].max_abs_diff, errors='coerce')
    chk('N03', '闭合类 max_abs_diff 全有限且 ≤ 1e−9', nm.notna().all() and (nm <= 1e-9).all(), nm.tolist())
    chk('N04', '限制登记 L 条目机器计数已刷新（含 L08 / L15 / L21 数字）', all(s in open(O.P('reports', 'E6o_limit_register.md'), encoding='utf-8').read() for s in ('未匹配份额中位', '差异格')))
    chk('N05', 'SCHEMA.md 行数 = 实际（同 C11）', not rbad)
    LG = rd('registration/ledger_G_E6o.csv')
    LE = rd('registration/ledger_E_E6o.csv')
    chk('N06', 'G / E 账本非空；E01–E07 有账本行；每卡在 claims', len(LG) > 0 and all(('E%02d' % i) in set(LE.e_id) for i in range(1, 8)) and all(('Q%02d' % i) in set(CL.claim_id) for i in range(1, 19)))
    chk('N07', 'seal_A2.written_at < 任何后段账户首次写入（同 C12）', a2['written_at'] < first)
    chk('N08', 'Stage 0 数据事实在（S0-1 覆盖、S0-9 字段）', ((S0.probe_id == 'S0-1').sum() > 0) and ((S0.probe_id == 'S0-9').sum() > 0))
    mn = S0[S0.key.str.startswith('COVERAGE_minute_bars')]
    chk('N09', '分钟成员的覆盖有 年 × 交易所 行', len(mn) >= 2 * 2 * 13, len(mn))
    chk('N10', '缓存目录名（同 C15）', 'E6o-v1.1' in cdn and 'ce9e98c2' in cdn)
    chk('N11', '守卫攻击矩阵全拦截（同 C04 攻击部分）', all((ID[ID.check_id == k].status == 'BLOCKED').all() for k in att))
    chk('N12', '页首（同 C16）', not hdr_bad)
    D = pd.DataFrame(res)
    O.atomic_write_csv(O.P('verify', 'closure_E6o.csv'), D)
    O.atomic_write_json(O.P('verify', 'closure_E6o.json'), dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n=len(D), n_pass=int((D.status == 'PASS').sum()),
                                                                  fails=D[D.status != 'PASS'].id.tolist(), final=final))
    print(D[D.status != 'PASS'].to_string() if (D.status != 'PASS').any() else 'ALL PASS %d' % len(D), flush=True)
    return int((D.status != 'PASS').sum())


def handoff():
    ts = time.strftime('%Y%m%d_%H%M')
    rep = O.P('replica', 'E6o', ts)
    os.makedirs(rep, exist_ok=True)
    code_dir = os.path.dirname(O.__file__)
    items = [os.path.join(code_dir, os.path.basename(p)) for p in glob.glob(os.path.join(code_dir, 'e6o_*'))]
    items += glob.glob(O.P('registration', '*')) + [O.P('inputs', x) for x in os.listdir(O.P('inputs'))]
    man = []
    for p in items:
        if not os.path.isfile(p):
            continue
        rel = os.path.join('code' if p.startswith(code_dir) else os.path.basename(os.path.dirname(p)), os.path.basename(p))
        dst = os.path.join(rep, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(p, dst)
        man.append('%s  %s' % (O.sha_file(dst), rel))
    O.atomic_write_text(os.path.join(rep, 'MANIFEST_SHA256.txt'), '\n'.join(sorted(man)) + '\n')
    hd = O.P('handoff', 'E6o_%s' % ts)
    for d in ('reports', 'registration', 'statistics', 'events', 'diagnostics', 'verify', 'accounts/daily', 'code_register'):
        src = O.P(d)
        if not os.path.isdir(src):
            continue
        for p in glob.glob(os.path.join(src, '**', '*'), recursive=True):
            if os.path.isfile(p) and '/out_E6o_stage2/' not in p and not p.endswith('.tmp') and '/__pycache__/' not in p and not p.endswith('.pyc'):
                rel = os.path.relpath(p, O.work())
                dst = os.path.join(hd, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(p, dst)
    n = rehash(hd)
    O.atomic_write_text(O.P('handoff', 'LATEST.txt'), O.rel(hd) + '\n')
    print(json.dumps(dict(handoff=O.rel(hd), files=n, replica=O.rel(rep), replica_files=len(man)), ensure_ascii=False), flush=True)


def scrub(s):
    """运行输出脱敏：结果根 / 家目录 / 解释器环境前缀换成占位（不写字面量，运行时取）。"""
    s = O.san(s)
    for pre, tag in ((O.work(), '<W>'), (sys.prefix, '<env>'), (os.path.expanduser('~'), '<home>'), (os.path.dirname(os.path.abspath(O.RES_ROOT)), '<base>')):
        if pre and len(pre) > 4:
            s = s.replace(pre, tag)
    return s


def rehash(hd):
    O.atomic_write_text(O.P('reports', 'E6o_REVIEW_input.md'), review_index(hd))
    shutil.copy2(O.P('reports', 'E6o_REVIEW_input.md'), os.path.join(hd, 'reports', 'E6o_REVIEW_input.md'))
    lines = []
    for p in sorted(glob.glob(os.path.join(hd, '**', '*'), recursive=True)):
        if os.path.isfile(p) and not p.endswith('HANDOFF_SHA256.txt'):
            lines.append('%s  %s' % (O.sha_file(p), os.path.relpath(p, hd)))
    O.atomic_write_text(os.path.join(hd, 'HANDOFF_SHA256.txt'), '\n'.join(lines) + '\n')
    return len(lines)


def dscript(hd):
    want = '0988d2e5873ed823fb89a697d271e47d3deb0af03dab02087b4289a447e0fc93'
    p = O.P('verify', 'decision', 'E6o_D_stage2.py')
    if O.sha_file(p) != want:
        raise RuntimeError('D 脚本 sha 不符')
    # 编译检查写到 tmp（不在 verify/decision 旁生成 __pycache__：其内嵌源文件绝对路径）
    cfile = O.P('tmp', 'py_compile_E6o_D_stage2.pyc')
    r = subprocess.run(['python3', '-c', 'import py_compile, sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)', p, cfile],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('py_compile 失败：%s' % scrub(r.stderr[-400:]))
    out = O.P('verify', 'decision', 'out_E6o_stage2')
    # 在结果目录内以相对路径运行（D 脚本把输出目录印进 stdout_tail.txt；相对路径使交付文本不含用户目录）；-B 不写字节码
    r = subprocess.run(['python3', '-B', os.path.relpath(p, O.work()), '--root', '.', '--handoff', os.path.relpath(hd, O.work()),
                        '--out', os.path.relpath(out, O.work())], capture_output=True, text=True, cwd=O.work())
    O.atomic_write_text(os.path.join(out, 'run_stdout_full.txt'), scrub(r.stdout + '\n' + r.stderr))
    dst = os.path.join(hd, 'verify', 'decision', 'out_E6o_stage2')
    os.makedirs(dst, exist_ok=True)
    for fn in sorted(os.listdir(out)):
        shutil.copy2(os.path.join(out, fn), os.path.join(dst, fn))
    n = rehash(hd)
    print(scrub(r.stdout[-3000:]), flush=True)
    print('exit', r.returncode, 'handoff files', n)


RESULT_COLS = {'registry_E6o.csv': {'status'}, 'ledger_E_E6o.csv': {'result', 'evidence_strength', 'first_stage_evidence', 'miss_root', 'next_change'},
               'ledger_G_E6o.csv': {'probe_result', 'result_at', 'probe_code_hash'}}


def frozen():
    """A1 冻结件副本 registration/A1_frozen/（sha 须 = freeze_E6o.json.frozen_registration_sha256）；之后只有 claims 填账本结果栏、closure 改 registry.status。"""
    FZ = json.load(open(O.P('registration', 'freeze_E6o.json')))
    out = {}
    for fn, sha in FZ['frozen_registration_sha256'].items():
        dst = O.P('registration', 'A1_frozen', fn)
        if not os.path.exists(dst):
            if O.sha_file(O.P('registration', fn)) != sha:
                raise RuntimeError('A1 冻结件已变：%s' % fn)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(O.P('registration', fn), dst)
        out[fn] = O.sha_file(dst) == sha
    print(json.dumps(out), flush=True)
    if not all(out.values()):
        sys.exit(1)


def frozen_diff():
    FZ = json.load(open(O.P('registration', 'freeze_E6o.json')))
    bad = []
    for fn, sha in FZ['frozen_registration_sha256'].items():
        a1 = O.P('registration', 'A1_frozen', fn)
        cur = O.P('registration', fn)
        if not os.path.exists(a1) or O.sha_file(a1) != sha:
            bad.append('copy:' + fn)
            continue
        if O.sha_file(cur) == sha:
            continue
        if fn not in RESULT_COLS:
            bad.append('changed:' + fn)
            continue
        A_ = pd.read_csv(a1, keep_default_na=False, dtype=str)
        B_ = pd.read_csv(cur, keep_default_na=False, dtype=str)
        if len(A_) != len(B_) or list(A_.columns) != list(B_.columns):
            bad.append('shape:' + fn)
            continue
        for col in A_.columns:
            if col not in RESULT_COLS[fn] and not A_[col].equals(B_[col]):
                bad.append('%s:%s' % (fn, col))
    return bad


def registry_status():
    """registry.status：NOT_RUN（A1 冻结时）→ 有产物的执行对象 COMPUTED；以 A1 冻结副本为底，核除 status 外逐格不变。"""
    src = O.P('registration', 'registry_E6o.csv')
    frz = O.P('registration', 'A1_frozen', 'registry_E6o.csv')
    F = pd.read_csv(frz, keep_default_na=False, dtype=str)
    AS = pd.read_csv(O.P('statistics', 'account_summary_E6o.csv'), keep_default_na=False, dtype=str)
    done = set(AS[(AS.segment == 'FULL') & (AS.status == 'COMPUTED')].exec_id)
    G = F.copy()
    G['status'] = np.where(G.exec_id.isin(done), 'COMPUTED', G.status)
    other = [c for c in F.columns if c != 'status']
    if not F[other].equals(G[other]):
        raise RuntimeError('registry 除 status 外有变动')
    O.atomic_write_csv(src, G)
    print(json.dumps(dict(rows=len(G), status=G.status.value_counts().to_dict()), ensure_ascii=False), flush=True)


def precheck():
    """B 前预检（只读登记 / 面板 / Stage 0 表，不读任何账户结果）：claims / diag / reports 用到的变体名在 registry 中是否存在、
    闭包门要求的 Stage 0 check_id 是否在、registry 取值词表、分钟面板日期 / 代码格式、日成交额量级。"""
    R = rd('registration/registry_E6o.csv')
    ids = set(R.exec_id)
    out = {}
    for c in ('funding', 'recycle_lag', 'recycle_maturity', 'reentry', 'entry_guard', 'exit_enabled', 'support', 'family'):
        out['vocab_' + c] = sorted(R[c].astype(str).unique().tolist())

    def fid(form=O.MAIN_FORM, mem='HG10', H='H5', trig='T1b', fund='ENGINE_NATIVE', lag='lag1', mat='RESET_H', re_='ALLOW', eg='OFF', ex='ON', prof='FEASIBLE_DAILY'):
        return '|'.join([form, 'a0.25', mem, H, trig, fund, lag if fund != 'CASH' else 'NA', mat if fund != 'CASH' else 'NA', re_, eg, ex, prof, 'ACCOUNT',
                         'MINUTE_2013' if trig in ('T4a', 'T4b', 'T5') else 'FULLHIST', 'CASH_V0', 'POLICY_E6O_PARENT_Q'])
    probes = {'main': fid(), 'E02_level': fid(trig='T1b_LEVEL'), 'E02_edge': fid(trig='T1b_EDGE'), 'E06_reconfirm': fid(re_='RECONFIRM'), 'E06_block': fid(re_='BLOCK'),
              'E06L_reconfirm': fid(trig='T1b_LEVEL', re_='RECONFIRM'), 'E06L_block': fid(trig='T1b_LEVEL', re_='BLOCK'), 'Q12_cash': fid(fund='CASH'),
              'Q12_next': fid(fund='NEXT_RANK'), 'Q12_lag0': fid(lag='lag0'), 'Q12_remain': fid(mat='ORIGINAL_DUE'), 'Q04_own': fid(trig='T1b_OWNCHANGE'),
              'Q05_T2': fid(trig='T2'), 'Q05_T2p': fid(trig='T2prime'), 'Q09_T4a': fid(trig='T4a'), 'Q09_T4b': fid(trig='T4b'), 'Q09_T5': fid(trig='T5'),
              'CC08_T6a': fid(trig='T6a'), 'CC08_T6b': fid(trig='T6b'), 'CC06_T3b15': fid(trig='T3b15'), 'CC04_A4b_T1b': fid(form='A4b')}
    for mem in O.MEMS:
        for fund in ('ENGINE_NATIVE', 'CASH'):
            probes['E03_y11_%s_%s' % (mem, fund)] = fid(mem=mem, trig='T1b_LEVEL', fund=fund, eg='ON', ex='ON')
            probes['E03_y10_%s_%s' % (mem, fund)] = fid(mem=mem, trig='T1b_LEVEL', fund=fund, eg='ON', ex='OFF')
        for trig in ('T1a', 'T1b', 'T3c15_X', 'T4a'):
            for re_ in ('ALLOW', 'BLOCK'):
                probes['E07_next_%s_%s_%s' % (mem, trig, re_)] = fid(mem=mem, trig=trig, fund='NEXT_RANK', re_=re_)
    for s in ('a', 'b', 'c'):
        probes['CC07_T3%s15_X' % s] = fid(trig='T3%s15_X' % s)
        probes['CC07_T3%s15' % s] = fid(trig='T3%s15' % s)
    out['missing_variant_names'] = sorted(k for k, v in probes.items() if v not in ids)
    out['n_variant_probes'] = len(probes)
    RS = rd('registration/random_scope_E6o.csv')
    am = set(RS[RS.mechanism == 'AMOUNT_MATCH'].owner_exec_id)
    fe_on = R[(R.series == 'C_ACCOUNT') & (R.execution_profile == 'FEASIBLE_DAILY') & (R.exit_enabled == 'ON')]
    out['feasible_exit_on'] = len(fe_on)
    out['feasible_exit_on_without_amount_match'] = int((~fe_on.exec_id.isin(am)).sum())
    out['amount_match_owner_profiles'] = {'|'.join(k): int(v) for k, v in R[R.exec_id.isin(am)].groupby(['execution_profile', 'exit_enabled']).size().items()}
    out['mechanism_owner_counts'] = RS.groupby('mechanism').owner_exec_id.nunique().to_dict()
    st0 = rd('verify/identities_E6o_stage0.csv')
    out['stage0_check_ids'] = sorted(set(st0.check_id))
    req = ['SOURCE_REPLICATION', 'SOURCE_ANCHOR_FRONTIER', 'SOURCE_HOLDINGS_SHA', 'NOEXIT_EQ_PARENT', 'ACCOUNTING_BRIDGE', 'REENTRY_EPISODE_CASES', 'TICKET_DOUBLE_SPEND',
           'TICKET_MATURITY_REUSE', 'JOURNAL_REPLAY', 'WRONG_MOTHER_MERGE', 'FUTURE_DATA_PLANT', 'UNIT_PLANT']
    out['stage0_missing_required'] = [k for k in req if k not in out['stage0_check_ids']]
    S0 = rd('diagnostics/stage0_E6o.csv')
    out['s0_age_keys'] = sorted(k for k in S0.key if str(k).startswith('AGE_REMAINING_BP|HG10'))
    cd = O.cache_dir()
    amt = np.load(os.path.join(cd, 'panels', 'amt.npy'), mmap_mode='r')
    codes = np.load(os.path.join(cd, 'panels', 'codes.npy'))
    dates = np.load(os.path.join(cd, 'panels', 'dates.npy'))
    d0 = int(np.searchsorted(dates, '2018-06-01'))
    row = np.asarray(amt[d0])
    out['amt_median_2018_06_01'] = float(np.nanmedian(row))
    out['amt_max_2018_06_01'] = float(np.nanmax(row))
    out['codes_sample'] = [str(c) for c in codes[:3]]
    md_ = O.E6N('minute_panel')
    pdir = os.path.join(md_, sorted(x for x in os.listdir(md_) if x.startswith('cache_'))[0])
    yd = sorted(x for x in os.listdir(pdir) if x.startswith('Y'))
    out['minute_years'] = yd[:2] + yd[-1:]
    out['minute_dates_sample'] = [str(x) for x in np.load(os.path.join(pdir, yd[-1], 'dates.npy'))[:2]]
    out['minute_codes_sample'] = [str(x) for x in np.load(os.path.join(pdir, yd[-1], 'codes.npy'))[:2]]
    out['minute_files'] = sorted(os.listdir(os.path.join(pdir, yd[-1])))[:20]
    a = np.load(O.E6N('accounts', '2010-2014', '%s.npz' % O.MAIN_FORM), allow_pickle=False)
    out['e6n_account_keys'] = sorted(a.files)[:30]
    print(json.dumps(out, ensure_ascii=False, indent=0), flush=True)


def finalize(hd):
    for fn in ('closure_E6o.csv', 'closure_E6o.json'):
        dst = os.path.join(hd, 'verify', fn)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(O.P('verify', fn), dst)
    print('handoff files', rehash(hd))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'identities':
        identities(deriv=len(sys.argv) > 2 and sys.argv[2] == 'deriv')
    elif cmd == 'schema':
        schema()
    elif cmd == 'gate':
        sys.exit(1 if gate(final=len(sys.argv) > 2 and sys.argv[2] == 'final') else 0)
    elif cmd == 'handoff':
        handoff()
    elif cmd == 'dscript':
        dscript(sys.argv[2] if len(sys.argv) > 2 else O.P(open(O.P('handoff', 'LATEST.txt')).read().strip()))
    elif cmd == 'registry':
        registry_status()
    elif cmd == 'frozen':
        frozen()
    elif cmd == 'precheck':
        precheck()
    elif cmd == 'finalize':
        finalize(sys.argv[2] if len(sys.argv) > 2 else O.P(open(O.P('handoff', 'LATEST.txt')).read().strip()))
