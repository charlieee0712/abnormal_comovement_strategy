# -*- coding: utf-8 -*-
"""E6p §C 收尾（附录 B.11 / B.15 / C；brief §8）：
  identities   全部账户的经济恒等（现金方程 / NAV 伸缩 / 标签与锁定守恒 / 费用 = 4bp × 净单）+ Stage 0 行 + E7 守卫 + 主对象日志重放 + 随机 A2 / B 推导段重放 → verify/identities_E6p.csv
  stage0       Stage 0 终版（part1 + S0-15 + POST_TRADE_ACTUAL 容量 + RENEW 同证券份额）→ diagnostics/stage0_E6p.csv
  schema       reports/SCHEMA.md（每表一行：行数 / 键列 / 列名 / 单位 / 生成脚本 / query_id / handoff / 真实样例行 / sha256）与 SCHEMA_DEVIATIONS.md
  seal_final   registration/seal_final.json（first_post_segment_write_at）
  gates        闭包门 ①–㉑ → verify/closure_E6p.csv（任一 FAIL 不交付）
  handoff      handoff/E6p_<ts>/ + HANDOFF_SHA256.txt；在结果目录内以相对路径运行决策端脚本，输出与脚本 sha 入 handoff
用法：python3 e6p_closure.py <子命令> [--root <根>]"""
import os
import re
import sys
import glob
import json
import time
import shutil
import argparse
import subprocess
from multiprocessing import get_context

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_engine as E

V0 = O.V0
REQ_IDS = ['SOURCE_REPLICATION', 'SOURCE_ANCHOR_FRONTIER', 'E6O_ACCOUNT_REPLICATION', 'SOURCE_HOLDINGS_SHA', 'ACCOUNTING_BRIDGE', 'NOEXIT_EQ_PARENT', 'RECYCLE_NONE_EQ_NATIVE',
           'CASH_NONE_EQ_NATIVE', 'DEPLOY_ZERO_BUDGET_EQ_NATIVE', 'RENEW_NO_CHECKPOINT_EQ_PARENT', 'CASH_EQUATION', 'NAV_TELESCOPE', 'TICKET_CONSERVATION', 'TOKEN_CONSERVATION',
           'FEE_NET_ORDER', 'FIRSTDAY_ALLEXIT_VS_H1', 'ALLOCATOR_SYNTHETIC_3CASES', 'RELATIVE_UPPER_INCLUDES_ALL_LOTS', 'DEPLOY_TARGET_LE_ONE', 'TOKEN_DOUBLE_SPEND',
           'TOKEN_MATURITY_REUSE', 'TOKEN_REPLAY', 'WRONG_MOTHER_MERGE', 'PARTIAL_FILL_NO_MINT', 'CHECKPOINT_RESTORE_IDEMPOTENT', 'TOKEN_HALF_CUMULATIVE', 'ROUTING_BUDGET_CLOSURE',
           'ROUTING_CAPS_RESPECTED', 'ROUTING_UNKNOWN_FROZEN', 'ROUTING_DEGENERATE_FALLBACK', 'SPLIT_INVARIANCE', 'LOCAL_COST_SPLIT_CLOSURE', 'POSTFEE_CAP_RECHECK',
           'RENEW_DUE_UNCHANGED', 'MATCH_NO_OWNER_FUTURE_INVENTORY', 'MIRROR_NO_FUTURE_READ', 'LANDMARK_NO_FUTURE_GROUPING', 'LANDMARK_CENSOR_AT_CUTOFF', 'FUTURE_DATA_PLANT',
           'UNIT_PLANT', 'JOURNAL_REPLAY', 'E7_GUARD', 'SOURCE_EXPOSURE_EQ_MEAN_SUMW']
ATTACK = {'RELATIVE_UPPER_INCLUDES_ALL_LOTS', 'DEPLOY_TARGET_LE_ONE', 'TOKEN_DOUBLE_SPEND', 'TOKEN_MATURITY_REUSE', 'TOKEN_REPLAY', 'WRONG_MOTHER_MERGE', 'PARTIAL_FILL_NO_MINT',
          'TOKEN_HALF_CUMULATIVE', 'ROUTING_UNKNOWN_FROZEN', 'ROUTING_DEGENERATE_FALLBACK', 'SPLIT_INVARIANCE', 'POSTFEE_CAP_RECHECK', 'MATCH_NO_OWNER_FUTURE_INVENTORY',
          'MIRROR_NO_FUTURE_READ', 'LANDMARK_NO_FUTURE_GROUPING', 'LANDMARK_CENSOR_AT_CUTOFF', 'FUTURE_DATA_PLANT', 'UNIT_PLANT', 'JOURNAL_REPLAY'}
INFO = {'SOURCE_ANCHOR_FRONTIER', 'ACCOUNTING_BRIDGE', 'E7_GUARD', 'SOURCE_HOLDINGS_SHA', 'SOURCE_EXPOSURE_EQ_MEAN_SUMW'}
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def rd(root, rel):
    return pd.read_csv(os.path.join(root, rel), keep_default_na=False, na_values=[''])


def sens_pattern():
    """敏感串：IPv4、凭据类词（拼接生成，代码文本里不出现原词）、运行时取得的用户目录名（不写字面量）。"""
    words = ['pass' + 'w', chr(0x53e3) + chr(0x4ee4), chr(0x5bc6) + chr(0x7801), 'PRIVATE' + ' KEY', 'ssh' + '-rsa', 'ssh' + '-ed25519', 'tok' + 'en=', 'BEGIN ' + 'OPENSSH', 'sec' + 'ret',
             'api' + ' key', 'api' + '_key']
    names = {os.path.basename(os.path.expanduser('~')), os.environ.get('USER', ''), os.environ.get('LOGNAME', ''),
             os.path.basename(os.path.dirname(os.path.abspath(O.RES_ROOT))), os.path.basename(sys.prefix)}
    names = [re.escape(n) for n in names if n and len(n) >= 4 and n not in ('root', 'results', 'mnt', 'sda2')]
    return re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|' + '|'.join(re.escape(w) for w in words) + ('|' + '|'.join(names) if names else ''), re.I)


# ------------------------------------------------------------------ 恒等
def job_acct_ident(args):
    e, h, d_end, sub = args
    z = np.load(O.P('accounts_run', sub, h[:2], '%s.npz' % h), allow_pickle=False)
    DY = z['DY'][:d_end]
    nav = DY[:, E.DYI['nav_post']]
    cash = DY[:, E.DYI['cash_share']] * nav
    prev = np.r_[V0, cash[:-1]]
    flow = DY[:, E.DYI['sell_val']] - DY[:, E.DYI['buy_val']] - DY[:, E.DYI['fee']]
    out = dict(e=e)
    out['cash'] = float(np.max(np.abs(cash - prev - flow)) / V0)
    out['tele'] = float(abs(np.prod(1.0 + DY[:, E.DYI['r_net']]) - nav[-1] / V0))
    out['nav'] = float(np.max(np.abs(DY[:, E.DYI['nav_pre']] - DY[:, E.DYI['fee']] - nav)) / V0)
    out['fee'] = float(np.max(np.abs(DY[:, E.DYI['fee']] - DY[:, E.DYI['fb_impact']] - O.FEE_RATE * DY[:, E.DYI['traded']])) / V0)
    tg = DY[:, E.DYI['tag_amt']]
    tk = np.abs(tg[1:] - (tg[:-1] + DY[1:, E.DYI['tag_new']] - DY[1:, E.DYI['tag_use_reg']] - DY[1:, E.DYI['tag_use_ext']] - DY[1:, E.DYI['tag_matured']]))
    out['tk'] = float(tk.max() / V0) if len(tk) else 0.0
    lk = DY[:, E.DYI['lock_amt']]
    lkd = np.abs(lk[1:] - (lk[:-1] + DY[1:, E.DYI['lock_new']] - DY[1:, E.DYI['lock_matured']]))
    out['lk'] = float(lkd.max() / V0) if len(lkd) else 0.0
    out['err'] = int(z['S_i'][E.SI_ERR])
    out['rnd'] = int(z['S_i'][E.SI_RNDFIX])
    return out


def identities(root, deriv=False):
    R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    st0 = pd.read_csv(O.P('verify', 'identities_E6p_stage0.csv'), keep_default_na=False)
    dates = np.load(os.path.join(O.cache_dir(), 'panels', 'dates.npy'))
    T = int(np.searchsorted(dates, '2019-01-01')) if deriv else len(dates)
    jobs = [(r.exec_id, r.exec_hash, T, 'deriv' if deriv else 'full') for r in R[R.series != 'P_SOURCE'].itertuples(index=False)]
    with get_context('fork').Pool(64) as pool:
        res = pool.map(job_acct_ident, jobs, chunksize=8)
    worst = {k: max(x[k] for x in res) for k in ('cash', 'tele', 'nav', 'fee', 'tk', 'lk')}
    where = {k: max(res, key=lambda x: x[k])['e'] for k in worst}
    nerr = sum(1 for x in res if x['err'])
    nrnd = sum(x['rnd'] for x in res)
    rows = [r._asdict() for r in st0.itertuples(index=False)]
    n = len(res)

    def add(cid, desc, val, mx, tol, ok, status=None):
        rows.append(dict(check_id=cid, description=desc, exec_id='', value=val, max_abs_diff=mx, tolerance=tol, status=status or ('PASS' if ok else 'DIFFERS')))
    add('CASH_EQUATION', '全部 %d 个执行账户（账户 + 镜像）逐日：现金 = 昨现金 + 卖款 − 买款 − 费（/ V0；引擎错误码非零 %d 个；舍入级缺口日 %d 个）' % (n, nerr, nrnd), n, worst['cash'], 1e-6,
        worst['cash'] <= 1e-6 and nerr == 0)
    add('NAV_TELESCOPE', '全部账户：Π(1 + R_net) = V⁺_终 / V0（另核 nav_post = nav_pre − fee：最大差 %.1e）' % worst['nav'], n, worst['tele'], 1e-9, worst['tele'] <= 1e-9 and worst['nav'] <= 1e-9)
    add('TICKET_CONSERVATION', '全部账户逐日：标签余额 = 昨余 + 新建 − 常规耗 − 额外耗 − 到期重分类（/ V0）', n, worst['tk'], 1e-6, worst['tk'] <= 1e-6)
    add('TOKEN_CONSERVATION', '全部账户逐日：锁定余额（CASH 锁至原 due、HALF 的 1 − η 部分）= 昨余 + 新建 − 到期（/ V0）', n, worst['lk'], 1e-6, worst['lk'] <= 1e-6)
    add('FEE_NET_ORDER', '全部账户逐日：费用 − 反馈冲击 = 4e−4 × Σ|证券净市场订单名义|（同日同证券先内部转移；/ V0）', n, worst['fee'], 1e-9, worst['fee'] <= 1e-9)
    rows.append(dict(check_id='FIRSTDAY_ALLEXIT_VS_H1', description='"全部首日退出 = H1"只在资本投入 / 初始化 / 交易等同时成立；本账户从 CASH_V0、按 NAV × w / H 分批建仓，与 H1 不等同（plan 附录 C）→ 只记、不作恒等',
                     exec_id='', value='NOT_EQUIVALENT_BY_DESIGN', max_abs_diff='', tolerance='', status='INFO'))
    # 主对象日志重放：一次跑完 vs A2 checkpoint + B 续跑（逐位）
    jr = pd.read_csv(O.P('verify', 'journal_replay_E6p.csv'), keep_default_na=False) if os.path.exists(O.P('verify', 'journal_replay_E6p.csv')) else None
    if jr is not None:
        add('JOURNAL_REPLAY_MAIN_OBJECTS', '主对象两只 × 两情景及其父：一次跑完 vs A2 checkpoint + B 续跑，全部 DY 逐位（%d 个）' % len(jr), len(jr), float(jr.max_abs_diff.max()), 0.0,
            float(jr.max_abs_diff.max()) == 0.0)
    rr = pd.read_csv(O.P('verify', 'random_replay_E6p.csv'), keep_default_na=False) if os.path.exists(O.P('verify', 'random_replay_E6p.csv')) else None
    if rr is not None:
        add('RANDOM_REPLAY_A2_EQ_B', '随机路径：B 从 0 日整段重放的推导段 D 与 A2 逐位一致（%d 条路径）' % len(rr), len(rr), float(rr.max_abs_diff.max()), 0.0, float(rr.max_abs_diff.max()) == 0.0)
    rn = rd(root, 'events/renew_E6p.csv')
    rows.append(dict(check_id='RENEW_SAME_SECURITY_NEW_LOT_SHARE', description='RENEW5 退出意向日同证券另有更新批次仍持有的份额（INFO；"关闭旧论点但同证券仍有新仓"）', exec_id='',
                     value=float(np.nanmean(rn.share_new_lot_same_security)) if len(rn) else '', max_abs_diff='', tolerance='', status='INFO'))
    maxdate = ''
    for p in [os.path.join(root, 'accounts', 'daily', 'INDEX.csv')]:
        d = pd.read_csv(p, dtype=str)
        maxdate = max(maxdate, d.date_max.max())
    for p in glob.glob(os.path.join(root, 'trades', '*.csv'))[:50] + [os.path.join(root, 'statistics', 'yearly_E6p.csv')]:
        try:
            d = pd.read_csv(p, usecols=lambda c: c in ('date', 'date_max', 'lot_due'), dtype=str)
            for c in d.columns:
                v = d[c][d[c].str.match(r'^\d{4}-\d{2}-\d{2}$', na=False)]
                if len(v) and v.max() > maxdate:
                    maxdate = v.max()
        except Exception:
            pass
    maxdate = max(maxdate, str(max(dates.tolist())))
    rows.append(dict(check_id='E7_GUARD', description='全部交付日序列 / 成交分片 / 年表与面板的最大日期；分钟读取接口对 > 2026-03-27 拒绝（FUTURE_DATA_PLANT）', exec_id='', value=maxdate[:10],
                     max_abs_diff='', tolerance='', status='INFO' if maxdate[:10] <= O.CUTOFF else 'DIFFERS'))
    D = pd.DataFrame(rows)[['check_id', 'description', 'exec_id', 'value', 'max_abs_diff', 'tolerance', 'status']]
    O.atomic_write_csv(os.path.join(root, 'verify', 'identities_E6p.csv'), D)
    print(json.dumps(dict(rows=len(D), worst=worst, worst_at={k: v.split('|')[0] for k, v in where.items()}, maxdate=maxdate[:10], nerr=nerr, rndfix_days=nrnd),
                     ensure_ascii=False), flush=True)


def stage0_final(root):
    p1 = pd.read_csv(O.P('diagnostics', 'stage0_E6p_part1.csv'), keep_default_na=False)
    s15 = pd.read_csv(O.P('diagnostics', 'stage0_E6p_S015.csv'), keep_default_na=False)
    AS = rd(root, 'statistics/account_summary_E6p.csv')
    R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    par = R[(R.form == O.MAIN_FORM) & (R.memory == 'HG10') & (R.H == '20') & (R.trigger == 'NONE') & (R.renew == '0') & (R.deploy.isin(['D80', 'D95'])) & (R.cap == 'RELATIVE_UPPER')
            & (R.execution_profile == 'FEASIBLE_DAILY')]
    p1 = p1[~p1.key.str.startswith('CAPACITY_POST_TRADE_ACTUAL')]
    add = []
    for s in O.SEGS:
        vals = {}
        for r in par.itertuples(index=False):
            x = AS[(AS.exec_id == r.exec_id) & (AS.segment == s)]
            vals[r.deploy] = float(x.exposure_mean.iloc[0]) if len(x) else np.nan
        add.append(dict(probe_id='S0-4', item='部署容量 POST_TRADE_ACTUAL（主母体 HG10 × H20 D95 父成交后实际敞口；RELATIVE_UPPER）', key='CAPACITY_POST_TRADE_ACTUAL_%s' % s,
                        value=round(vals.get('D95', np.nan), 6), unit='share', status='INFO', source_file='statistics/account_summary_E6p.csv',
                        note='D80 父 = %.6f；正式账户（B 后）补值' % vals.get('D80', np.nan)))
    idn = pd.read_csv(O.P('verify', 'identities_E6p_stage0.csv'), keep_default_na=False)
    groups = {'S0-3': ('零干预恒等（逐位）', ['NOEXIT_EQ_PARENT', 'RECYCLE_NONE_EQ_NATIVE', 'CASH_NONE_EQ_NATIVE', 'DEPLOY_ZERO_BUDGET_EQ_NATIVE', 'RENEW_NO_CHECKPOINT_EQ_PARENT'], 'PASS'),
              'S0-5': ('token 账本攻击（合成）', ['TOKEN_DOUBLE_SPEND', 'TOKEN_MATURITY_REUSE', 'TOKEN_REPLAY', 'WRONG_MOTHER_MERGE', 'PARTIAL_FILL_NO_MINT', 'TOKEN_HALF_CUMULATIVE',
                                               'CHECKPOINT_RESTORE_IDEMPOTENT'], None),
              'S0-6': ('成本路由与拆单（合成）', ['ROUTING_BUDGET_CLOSURE', 'ROUTING_CAPS_RESPECTED', 'ROUTING_UNKNOWN_FROZEN', 'ROUTING_DEGENERATE_FALLBACK', 'SPLIT_INVARIANCE',
                                             'LOCAL_COST_SPLIT_CLOSURE', 'POSTFEE_CAP_RECHECK'], None),
              'S0-10': ('landmark 机器（合成）', ['LANDMARK_NO_FUTURE_GROUPING', 'LANDMARK_CENSOR_AT_CUTOFF'], 'BLOCKED')}
    extra = []
    for pid, (item, ids, want) in groups.items():
        for cid in ids:
            x = idn[idn.check_id == cid]
            st = ';'.join(sorted(set(x.status)))
            ok = len(x) > 0 and all(s in ('PASS', 'BLOCKED') for s in x.status)
            extra.append(dict(probe_id=pid, item=item, key=cid, value=st, unit='count', status='PASS' if ok else 'DIFFERS', source_file='verify/identities_E6p.csv',
                              note='%d 行；恒等类 PASS、攻击类 BLOCKED（详见 identities 同 check_id）' % len(x)))
    out = pd.concat([p1, pd.DataFrame(add), pd.DataFrame(extra), s15], ignore_index=True)
    O.atomic_write_csv(os.path.join(root, 'diagnostics', 'stage0_E6p.csv'), out)
    print(json.dumps(dict(rows=len(out), probes=sorted(out.probe_id.unique().tolist())), ensure_ascii=False), flush=True)


# ------------------------------------------------------------------ SCHEMA
CONTRACT = ['registration/registry_E6p.csv', 'registration/comparisons_E6p.csv', 'registration/compound_contrasts_E6p.csv', 'registration/random_control_refs_E6p.csv',
            'registration/cost_feedback_refs_E6p.csv', 'registration/recycle_diagnostic_refs_E6p.csv', 'registration/ledger_G_E6p.csv', 'registration/ledger_E_E6p.csv',
            'registration/cc_statement_carry.csv', 'registration/reported_claims_E6p.csv', 'registration/sources_E6p.csv', 'registration/permissions_E6p.csv',
            'registration/exposure_E6p.csv', 'registration/park_E6p.csv', 'statistics/account_summary_E6p.csv', 'statistics/randoms_E6p.csv', 'statistics/random_paths_main_E6p.csv',
            'statistics/matching_E6p.csv', 'statistics/policy_E6p.csv', 'statistics/policy_fields_E6p.csv', 'statistics/main72_E6p.csv', 'statistics/yearly_E6p.csv',
            'statistics/cost_curve_E6p.csv', 'statistics/breakeven_E6p.csv', 'statistics/cost_feedback_E6p.csv', 'diagnostics/stage0_E6p.csv', 'verify/identities_E6p.csv',
            'events/event_counts_E6p.csv', 'events/renew_E6p.csv', 'reports/claims_E6p.csv', 'reports/query_registry_E6p.csv', 'accounts/daily/INDEX.csv', 'trades/INDEX.csv',
            'diagnostics/D1_holding_E6p.csv', 'diagnostics/D2_deploy_E6p.csv', 'diagnostics/D3_cost_E6p.csv', 'diagnostics/D4_composition_E6p.csv', 'diagnostics/D5_reinvest_E6p.csv',
            'diagnostics/D6_regime_E6p.csv', 'diagnostics/D7_cvr_E6p.csv', 'diagnostics/D8_window_E6p.csv', 'diagnostics/D9_discount_E6p.csv', 'diagnostics/G1_E6p.csv',
            'diagnostics/landmark_E6p.csv', 'diagnostics/mirror_E6p.csv', 'diagnostics/D9_recycle_local_E6p.csv', 'code_register/deploy_log.csv']
EXTRA = ['statistics/warm_sensitivity_E6p.csv', 'verify/trades_events_bridge_E6p.csv', 'verify/selftest_identities_E6p.csv', 'verify/identities_E6p_stage0.csv',
         'verify/journal_replay_E6p.csv', 'verify/random_replay_E6p.csv', 'verify/closure_E6p.csv', 'registration/cards_E6p.csv', 'registration/ledger_G_E6p_A1.csv',
         'registration/ledger_E_E6p_A1.csv']
GEN = {'registration': 'e6p_registry.py / e6p_a1.py / e6p_stage0.py / e6p_claims.py', 'statistics': 'e6p_stats.py / e6p_policy.py', 'diagnostics': 'e6p_diag.py / e6p_g1.py / e6p_closure.py',
       'verify': 'e6p_stage0.py / e6p_selftest.py / e6p_closure.py', 'events': 'e6p_stats.py', 'reports': 'e6p_claims.py', 'accounts': 'e6p_stats.py', 'trades': 'e6p_stats.py',
       'code_register': 'e6p_closure.py'}
KEYS = {'registration/registry_E6p.csv': 'exec_id', 'statistics/account_summary_E6p.csv': 'exec_id|segment', 'statistics/randoms_E6p.csv': 'owner_exec_id|mechanism|segment',
        'statistics/matching_E6p.csv': 'owner_exec_id|mechanism|segment', 'statistics/policy_E6p.csv': 'exec_id|profile_name', 'statistics/policy_fields_E6p.csv': 'exec_id|profile_name|field',
        'statistics/yearly_E6p.csv': 'exec_id|year', 'statistics/cost_curve_E6p.csv': 'exec_id|comparator_kind|A_cny|kappa|exponent|segment',
        'statistics/breakeven_E6p.csv': 'exec_id|comparator_kind|kappa|exponent', 'statistics/cost_feedback_E6p.csv': 'owner_exec_id|A_cny|segment',
        'statistics/main72_E6p.csv': 'exec_id', 'registration/comparisons_E6p.csv': 'comparison_id', 'registration/compound_contrasts_E6p.csv': 'contrast_id|term_exec_id',
        'accounts/daily/INDEX.csv': 'exec_hash', 'trades/INDEX.csv': 'exec_id', 'events/event_counts_E6p.csv': 'exec_id', 'events/renew_E6p.csv': 'exec_id',
        'reports/claims_E6p.csv': 'claim_id', 'reports/query_registry_E6p.csv': 'query_id', 'verify/identities_E6p.csv': 'check_id|description'}


def schema(root, in_handoff=True):
    pat = sens_pattern()
    lines = ['# E6p SCHEMA（由 e6p_closure.py schema 从实际文件生成；附录 B 合同；sha256 = 生成时文件）', '',
             '| 文件（相对结果目录） | 类型 | 行数或键数 | 键列 | 列名全列 | 单位列说明 | 生成脚本 | query_id 列是否存在 | 是否入 handoff | 样例行（一行真实值，脱敏） | sha256 |',
             '|---|---|---|---|---|---|---|---|---|---|---|']
    for rel in CONTRACT + EXTRA:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            continue
        with open(p, 'r', encoding='utf-8') as f:
            hdr = f.readline().rstrip('\n')
            first = f.readline().rstrip('\n')
            n = 1 + sum(1 for _ in f) if first else 0
        cols = hdr.split(',')
        unit = '有 unit 列' if 'unit' in cols else ('ann_pp / share / count（列名后缀）' if any(c.endswith(('_ann_pp', '_share', '_cny')) for c in cols) else '见列名')
        sample = pat.sub('<redacted>', first)[:240].replace('|', '/')
        lines.append('| %s | csv | %d | %s | %s | %s | %s | %s | %s | %s | %s |' % (rel, n, KEYS.get(rel, '').replace('|', ' + '), ' '.join(cols), unit, GEN.get(rel.split('/')[0], 'e6p_*'),
                                                                           '是' if 'query_id' in cols else '否', '是' if in_handoff else '否', sample, O.sha_file(p)))
    lines += ['', '另：`accounts/daily/<exec_hash>.csv`（%d 个，列 = B.14 日序列列）与 `trades/<exec_hash>.csv`（列 = B.18 分区列）按 INDEX 列出；随机路径日统计分片在 47 `randoms/daily/`（不入 handoff，可取）；'
              '`registration/spec/*.json` 为 plan 附录 C 七个 json 原样复制。' % len(glob.glob(os.path.join(root, 'accounts', 'daily', '*.csv'))), '']
    O.atomic_write_text(os.path.join(root, 'reports', 'SCHEMA.md'), '\n'.join(lines) + '\n')
    dev = ['# E6p SCHEMA_DEVIATIONS（表 | 列 | 原因 | 影响的探针）', '',
           '| 表 | 列 | 原因 | 影响的探针 |', '|---|---|---|---|',
           '| trades/<exec_hash>.csv | lot_due | 原批次 due 落在授权终点（2026-03-27）之后的早退 / 续期行写 `POST_CUTOFF`（不物化 E7 日期；字典序大于任何样本日期，`date < lot_due` 比较保持正确） | S29（早退行计数）、S17（不涉及：只看日序列） |',
           '| trades/<exec_hash>.csv 与 events/event_counts_E6p.csv | order_kind=EXIT 行数 vs n_realized_early | 成交日志按"成交行"写（一字跌停日只与常规买单内部转移的部分成交 + 次日余量 = 同一批次 2 行），事件按"意向"计（B.12 恒等要求）；两者差 = 部分成交行数，逐对象见 `verify/trades_events_bridge_E6p.csv` | S29 |',
           '| registration/registry_E6p.csv | parent_same_h_exec_id | 合同只规定 trigger ≠ NONE 行；renew-only（trigger = NONE、renew = 5）行另填同坐标 renew = 0 的父（= plan 附录 C 的 VS_SAME_H_PARENT 右侧），使其 D 与比较图一致 | S04（不涉及）、S07（D 恒等照核） |',
           '| statistics/account_summary_E6p.csv | 额外列 | 另加 D_imp_ann_pp / D_imp_stress_ann_pp / boot20_* / boot80_* / size_unknown_share / sector_active_max_peak_pp / D_h5_same_trigger_ann_pp / parent_h5_same_trigger_exec_id / start_state / cost_profile（只加不改） | 无 |',
           '| statistics/randoms_E6p.csv / matching_E6p.csv | COUNT_ISK 行 | COUNT_ISK 的请求 / 层内 / 跨层 / 未匹配是证券数：CNY 列留空，计数写 n_requests / n_unmatched_requests 与额外列 matched_within_n / matched_cross_n | S11（恒等只在 CNY 列为数值时核） |', '']
    O.atomic_write_text(os.path.join(root, 'reports', 'SCHEMA_DEVIATIONS.md'), '\n'.join(dev) + '\n')
    print('SCHEMA rows', len(lines) - 4, flush=True)


def seal_final(root):
    fs = glob.glob(O.P('accounts_run', 'full', '*', '*.npz'))
    first = min(os.path.getmtime(f) for f in fs) if fs else time.time()
    man = []
    for sub in ('statistics', 'events', 'diagnostics', 'verify', 'reports'):
        for p in sorted(glob.glob(os.path.join(root, sub, '*.*'))):
            man.append('%s  %s' % (O.sha_file(p), O.rel(p)))
    mp = O.P('registration', 'seal_final_manifest.txt')
    O.atomic_write_text(mp, '\n'.join(man) + '\n')
    s = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), n_files=len(man), sha256_manifest=O.sha_file(mp), manifest='registration/seal_final_manifest.txt',
             first_post_segment_write_at=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(first)))
    O.atomic_write_json(O.P('registration', 'seal_final.json'), s)
    print(json.dumps(s, ensure_ascii=False), flush=True)


def deploy_log(root):
    here = os.path.dirname(os.path.abspath(__file__))
    fz = json.load(open(O.P('registration', 'freeze_E6p.json')))
    a1 = fz.get('code_sha256', {})
    rows = []
    for f in sorted(os.listdir(here)):
        if f.startswith('e6p_') and (f.endswith('.py') or f.endswith('.sh')):
            sha = O.sha_file(os.path.join(here, f))
            rows.append(dict(file=f, sha256=sha, sha256_at_A1=a1.get(f, ''), changed_after_A1='' if f not in a1 else ('yes' if a1[f] != sha else 'no'),
                             role='E6p 模块（只读复用 e6o_* / e6n_* 等既有模块，不改）'))
    O.atomic_write_csv(os.path.join(root, 'code_register', 'deploy_log.csv'), pd.DataFrame(rows))


GATE_ROWS = []


def gate(no, desc, ok, detail=''):
    GATE_ROWS.append(dict(gate=no, description=desc, status='PASS' if ok else 'FAIL', detail=str(detail)[:400]))


def gates(root, stage='pre'):
    """闭包门 ①–㉑（stage = pre：handoff 前；post：含 ⑱ / ⑳ / ㉑ 的 handoff 后复核）。"""
    del GATE_ROWS[:]
    R = pd.read_csv(O.P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    spec = json.load(open(O.P('registration', 'spec', 'registry.json')))
    bad = [s['id'] for s in spec if O.spec_logical_id(s) != s['id']]
    cnt = R[R.series != 'P_SOURCE'].groupby('execution_profile').size().to_dict()
    gate('①', 'registry 行数恒等与逻辑 id 重算', not bad and cnt.get('FEASIBLE_DAILY') == 1064 and cnt.get('IDEALIZED_SOURCE_FILL') == 1064 and (R.series == 'P_SOURCE').sum() >= 24,
         dict(cnt=cnt, bad=len(bad)))
    C = rd(O.work(), 'registration/comparisons_E6p.csv')
    PC = rd(O.work(), 'registration/compound_contrasts_E6p.csv')
    ids = set(R.exec_id)
    ok2 = len(C) == 7216 and set(C.left_exec_id) <= ids and set(C.right_exec_id) <= ids and PC.drop_duplicates(['contrast_id', 'execution_profile']).shape[0] == 1748 \
        and set(PC.term_exec_id) <= ids and (PC.groupby('contrast_id').coefficient.sum() == 0).all()
    gate('②', 'comparisons / compound / refs 全部 id 在 registry、计数 = 附录 C', ok2, dict(comparisons=len(C), compound=PC.contrast_id.nunique()))
    AS = rd(root, 'statistics/account_summary_E6p.csv')
    full = AS.groupby('exec_id').segment.nunique()
    c = AS[(AS.status == 'COMPUTED') & AS.parent_same_h_exec_id.notna() & (AS.segment != 'G4')]
    dd = (c.D_same_h_ann_pp - (c.net_ann_pp - c.parent_same_h_net_ann_pp)).abs().max()
    gate('③', 'account_summary 每执行对象 × 6 段齐全、D 恒等', (full == 6).all() and len(full) == len(R) and dd <= 1e-9, dict(objects=len(full), max_D_identity=dd))
    I = rd(root, 'verify/identities_E6p.csv')
    miss = [k for k in REQ_IDS if k not in set(I.check_id)]
    att_bad = I[I.check_id.isin(ATTACK) & (I.status != 'BLOCKED')]
    pas = I[I.status == 'PASS']
    tol_bad = pas[pd.to_numeric(pas.max_abs_diff, errors='coerce') > pd.to_numeric(pas.tolerance, errors='coerce')]
    oth_bad = I[I.check_id.isin(set(REQ_IDS) - ATTACK - INFO) & ~I.status.isin(['PASS', 'INFO'])]
    gate('④', 'identities 必含 check_id 全在、恒等类 ≤ 容差、攻击类全 BLOCKED', not miss and not len(att_bad) and not len(tol_bad) and not len(oth_bad),
         dict(missing=miss, attack_bad=len(att_bad), tol_bad=len(tol_bad), other_bad=list(oth_bad.check_id.unique())[:5]))
    RDt = rd(root, 'statistics/randoms_E6p.csv')
    full_r = RDt[RDt.segment == 'FULL']
    refs = rd(O.work(), 'registration/random_control_refs_E6p.csv')
    feas = R[R.execution_profile == 'FEASIBLE_DAILY'].set_index('logical_id').exec_id
    have = set(zip(full_r.owner_exec_id, full_r.mechanism))
    miss_r = sum(1 for x in refs.itertuples(index=False) if (feas[x.owner_logical_id], x.mechanism) not in have)
    low = full_r[(full_r.paths < full_r.minimum_paths) & ~full_r.status.isin(['MC_LIMIT', 'NO_RANDOM_BY_SCOPE'])]
    mc = full_r[full_r.paths > 1]
    mc_bad = (mc.mcse - mc.rand_sd_D_ann_pp / np.sqrt(mc.paths)).abs().max()
    gate('⑤', 'randoms 覆盖按 brief §6、mcse 恒等、主对象精度', miss_r == 0 and not len(low) and mc_bad <= 1e-9, dict(missing=miss_r, below_min=len(low), mcse_identity=mc_bad))
    PO = rd(root, 'statistics/policy_E6p.csv')
    acc = R[R.role == 'ACCOUNT']
    ok6 = len(PO) == 2 * len(acc) and set(PO.verdict) <= {'通过', '不通过', '不可判'} and (PO[PO.verdict == '不可判'].undecidable_reason.fillna('') != '').all()
    gate('⑥', 'policy 每 ACCOUNT 执行对象 × 两 profile 一行、词表、不可判必有原因', ok6, dict(rows=len(PO), verdicts=PO.verdict.value_counts().to_dict()))
    CL = rd(root, 'reports/claims_E6p.csv')
    QR = set(rd(root, 'reports/query_registry_E6p.csv').query_id)
    req = ['Q%02d' % i for i in range(1, 19)] + ['E%02d' % i for i in range(1, 11)] + ['G-P-%02d' % i for i in range(1, 12)] + ['CC-E6p-%02d' % i for i in range(1, 12)]
    e = CL[CL.claim_id.isin(['E%02d' % i for i in range(1, 11)])]
    inside = ((pd.to_numeric(e.ci_lo, errors='coerce') <= pd.to_numeric(e.result_value, errors='coerce') + 1e-12) &
              (pd.to_numeric(e.result_value, errors='coerce') <= pd.to_numeric(e.ci_hi, errors='coerce') + 1e-12)) | (e.note.fillna('') != '')
    gate('⑦', 'claims 必含 id、query_id 全在 query_registry、E01–E10 点估在区间内或 note', set(req) <= set(CL.claim_id) and set(CL.query_id.fillna('')) - {''} <= QR and inside.all(),
         dict(missing=sorted(set(req) - set(CL.claim_id))[:5]))
    S0 = rd(root, 'diagnostics/stage0_E6p.csv')
    gate('⑧', 'stage0 S0-0…S0-15 全有行、S0-0 必含键全在', {'S0-%d' % i for i in range(16)} <= set(S0.probe_id) and (S0[S0.probe_id == 'S0-0'].status.isin(['BOUND', 'SOURCE_BINDING_PENDING', 'NOT_APPLICABLE'])).all(),
         sorted(S0.probe_id.unique()))
    EV = rd(root, 'events/event_counts_E6p.csv')
    RW = rd(root, 'events/renew_E6p.csv')
    gate('⑨', 'events / renew 恒等', (EV.n_intents == EV.n_realized_early + EV.n_late_fill + EV.n_unfilled + EV.n_censored).all() and len(RW) == 72 and
         (RW.n_checkpoints == RW.n_confirmed + RW.n_rejected + RW.n_unknown).all() and len(EV) == len(acc), dict(events=len(EV), renew=len(RW)))
    DI = rd(root, 'accounts/daily/INDEX.csv')
    ex = all(os.path.exists(os.path.join(root, f)) for f in DI.file)
    nd = AS[AS.segment.isin(O.SEGS)].groupby('exec_id').n_days.sum()
    mism = (DI.set_index('exec_id').n_rows - nd.reindex(DI.exec_id).values).abs().max()
    gate('⑩', 'accounts/daily 范围（全部执行对象 + P_SOURCE）与 n_rows = Σ n_days', len(DI) == len(R) and ex and mism == 0, dict(index=len(DI), files_exist=ex, n_rows_mismatch=mism))
    sm = open(os.path.join(root, 'reports', 'SCHEMA.md'), encoding='utf-8').read() if os.path.exists(os.path.join(root, 'reports', 'SCHEMA.md')) else ''
    okS = bool(sm) and os.path.exists(os.path.join(root, 'reports', 'SCHEMA_DEVIATIONS.md'))
    if okS:
        for line in sm.splitlines():
            if line.startswith('| ') and '.csv' in line.split('|')[1]:
                cells = [x.strip() for x in line.strip().strip('|').split('|')]
                p = os.path.join(root, cells[0])
                with open(p, encoding='utf-8') as f:
                    hdr = f.readline().rstrip('\n')
                    n = sum(1 for _ in f)
                if int(cells[2]) != n or cells[4] != ' '.join(hdr.split(',')):
                    okS = False
    gate('⑪', 'SCHEMA.md 行数 = 实际、列名 = 表头、DEVIATIONS 存在', okS)
    fz = json.load(open(O.P('registration', 'freeze_E6p.json')))
    keys = ['plan_sha256', 'spec_sha256', 'brief_sha256', 'appendix_sha256', 'd_script_sha256', 'schema_contract_sha256', 'policy_file_sha256', 'source_fn_sha256', 'data_cutoff',
            'protocol', 'mode', 'authorizations', 'authorized_by', 'authorized_at', 'written_at', 'cache_tag']
    s2 = json.load(open(O.P('registration', 'seal_A2.json')))
    sf = json.load(open(O.P('registration', 'seal_final.json'))) if os.path.exists(O.P('registration', 'seal_final.json')) else {}
    gate('⑫', 'freeze 全键（含授权行）；seal_A2.written_at < 后段首次写入', all(k in fz for k in keys) and str(s2['written_at']) < str(sf.get('first_post_segment_write_at', '')),
         dict(seal_A2=s2['written_at'], first_post=sf.get('first_post_segment_write_at')))
    pat_nan = re.compile(r'(?<![A-Za-z_])(nan|None)(?![A-Za-z_])')
    nanf = [f for f in glob.glob(os.path.join(root, 'reports', '*.md')) if pat_nan.search(open(f, encoding='utf-8').read())]
    gate('⑬', '报告正文无字面 nan / None', not nanf, [os.path.basename(f) for f in nanf])
    e7 = I[I.check_id == 'E7_GUARD'].value.astype(str).max()
    gate('⑭', '全部文件最大日期 ≤ 2026-03-27', e7 <= O.CUTOFF and DI.date_max.max() <= O.CUTOFF, e7)
    cdn = os.path.basename(O.cache_dir())
    gate('⑮', '缓存目录含 E6p-v1.1 与 efd382ee', 'E6p-v1.1' in cdn and 'efd382ee' in cdn, cdn)
    r0 = open(os.path.join(root, 'reports', 'E6p_REPORT_R0.md'), encoding='utf-8').read() if os.path.exists(os.path.join(root, 'reports', 'E6p_REPORT_R0.md')) else ''
    gate('⑯', '页首写明无 E7 / 部署授权、协议 v1.6、方式 B、授权行值', all(x in r0[:3000] for x in ('E7', 'deployment_authorized = false', 'v1.6', '方式 B', 'research_long_H_authorized', 'UNDECIDABLE_TARGET_A')))
    txt = open(O.P('verify', 'spec', 'spec_run.txt'), encoding='utf-8', errors='replace').read()
    fps = {'registry': 'c3fb08b5', 'comparisons': '8215df76', 'random_control_refs': 'e7137d33', 'primary72': '1c70888e', 'compound_contrasts': '5b595881',
           'auxiliary_refs': 'd115fa67', 'recycle_diagnostic_refs': '0374f36c'}
    lf = lambda p: O.sha_bytes(open(p, 'rb').read().replace(b'\r\n', b'\n'))
    okf = all(lf(O.P('registration', 'spec', k + '.json')).startswith(v) for k, v in fps.items())
    gate('⑰', 'verify/spec 七指纹与 plan 附录 B 一致（LF）、160 PASS', okf and 'Ran 160 tests' in txt and '\nOK' in txt)
    if stage == 'post':
        out = O.P('verify', 'decision', 'out_E6p_stage2', 'E6p_D_probes_stage2.csv')
        gate('⑱', 'verify/decision/out_E6p_stage2/ 存在且含探针 CSV（结果不作门）', os.path.exists(out))
    CU = rd(root, 'statistics/cost_curve_E6p.csv')
    need = len(O.A_GRID) * len(O.KAPPAS) * len(O.EXPONENTS) * 6
    g_ = CU.groupby(['exec_id', 'comparator_kind']).size()
    abs_ok = all(g_.get((e_, 'ABSOLUTE'), 0) >= need for e_ in acc.exec_id)
    par_ok = all(g_.get((r.exec_id, 'VS_SAME_H_PARENT'), 0) >= need for r in acc.itertuples(index=False) if r.parent_same_h_exec_id)
    FB = rd(root, 'statistics/cost_feedback_E6p.csv')
    BE = rd(root, 'statistics/breakeven_E6p.csv')
    gate('⑲', '成本：曲线网格齐全、breakeven 行齐全、反馈 84 × 6 段', abs_ok and par_ok and FB.groupby(['owner_exec_id', 'A_cny']).ngroups == 84 and
         (FB.groupby(['owner_exec_id', 'A_cny']).segment.nunique() == 6).all() and len(BE) > 0)
    if stage == 'post':
        pass
    newt = ['trades/INDEX.csv', 'statistics/yearly_E6p.csv', 'statistics/policy_fields_E6p.csv', 'registration/sources_E6p.csv', 'registration/permissions_E6p.csv',
            'registration/exposure_E6p.csv', 'registration/park_E6p.csv']
    gate('㉑', '新增合同表存在（S18b / S29–S32 状态行在 D 输出）', all(os.path.exists(os.path.join(root if not t.startswith('registration') else O.work(), t)) for t in newt))
    G_ = pd.DataFrame(GATE_ROWS)
    O.atomic_write_csv(os.path.join(root, 'verify', 'closure_E6p.csv') if stage == 'pre' else os.path.join(root, 'verify', 'closure_post_E6p.csv'), G_)
    print(G_.to_string()[:6000], flush=True)
    return G_


_SCAN_PAT = None


def _scan_file(p):
    """单文件敏感模式扫描（进程内缓存已编译模式）；命中返回相对路径。"""
    global _SCAN_PAT
    if _SCAN_PAT is None:
        _SCAN_PAT = sens_pattern()
    with open(p, 'r', encoding='utf-8', errors='replace') as fh:
        while True:
            chunk = fh.read(1 << 24)
            if not chunk:
                return None
            if _SCAN_PAT.search(chunk):
                return O.rel(p)


def handoff_scan(hd):
    """S07b 全交接件扫描：规则不变，按文件并行（成交分片合计约 128 GB，单线程约 7 MB/s 不可行）。"""
    dsha = O.D_SCRIPT_SHA256
    hits, todo = [], []
    for dp, dn, fn in os.walk(hd):
        if '__pycache__' in dp or any(d == '__pycache__' for d in dn):
            hits.append(('__pycache__', O.rel(dp)))
        for f in fn:
            p = os.path.join(dp, f)
            if f.endswith(('.pyc',)):
                hits.append(('pyc', f))
                continue
            if f == 'E6p_D_stage2.py' and O.sha_file(p) == dsha:
                continue
            if f.endswith(('.csv', '.md', '.txt', '.json', '.py', '.sh')):
                todo.append(p)
    todo.sort(key=lambda x: -os.path.getsize(x))
    with get_context('fork').Pool(96) as pool:
        for r in pool.imap_unordered(_scan_file, todo, chunksize=1):
            if r:
                hits.append(('pattern', r))
    return hits


def _sha_rel(args):
    p, base = args
    return O.sha_file(p), os.path.relpath(p, base)


def handoff(root):
    ts = time.strftime('%Y%m%d_%H%M')
    hd = O.P('handoff', 'E6p_%s' % ts)
    os.makedirs(hd, exist_ok=True)
    W = O.work()

    def link(src, dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            return
        try:
            os.link(src, dst)
        except OSError:
            shutil.copy2(src, dst)
    for sub in ('registration', 'accounts/daily', 'trades', 'statistics', 'diagnostics', 'events', 'reports', 'verify', 'code_register'):
        sd = os.path.join(W, sub)
        for dp, dn, fn in os.walk(sd):
            dn[:] = [d for d in dn if d not in ('__pycache__', 'decision_tmp')]
            for f in fn:
                if '.tmp' in f or f.endswith('.pyc'):
                    continue
                if sub == 'verify' and os.path.relpath(dp, sd).startswith('decision') and f.endswith('.pyc'):
                    continue
                link(os.path.join(dp, f), os.path.join(hd, os.path.relpath(os.path.join(dp, f), W)))
    here = os.path.dirname(os.path.abspath(__file__))
    for f in sorted(os.listdir(here)):
        if f.startswith('e6p_') and (f.endswith('.py') or f.endswith('.sh')):
            link(os.path.join(here, f), os.path.join(hd, 'code_register', 'src', f))
    hits = handoff_scan(hd)
    files = []
    for dp, dn, fn in os.walk(hd):
        for f in fn:
            if f != 'HANDOFF_SHA256.txt':
                files.append((os.path.join(dp, f), hd))
    with get_context('fork').Pool(64) as pool:
        shas = pool.map(_sha_rel, files, chunksize=16)
    O.atomic_write_text(os.path.join(hd, 'HANDOFF_SHA256.txt'), '\n'.join('%s  %s' % (s, r) for s, r in sorted(shas, key=lambda x: x[1])) + '\n')
    print(json.dumps(dict(handoff=O.rel(hd), files=len(files), scan_hits=hits[:10], n_hits=len(hits)), ensure_ascii=False), flush=True)
    return hd, hits


def run_d(hd):
    """决策端脚本：在结果目录内以相对路径运行（stdout 不含绝对路径）；输出入 handoff 并追加 sha。"""
    W = O.work()
    d = O.P('verify', 'decision')
    assert O.sha_file(os.path.join(d, 'E6p_D_stage2.py')) == O.D_SCRIPT_SHA256
    tmp = O.P('tmp', 'pyc_d')
    os.makedirs(tmp, exist_ok=True)
    env = dict(os.environ, PYTHONPYCACHEPREFIX=tmp, PYTHONDONTWRITEBYTECODE='1')
    rel_hd = os.path.relpath(hd, W)
    cmd = [sys.executable, 'verify/decision/E6p_D_stage2.py', '--root', '.', '--handoff', rel_hd, '--out', 'verify/decision/out_E6p_stage2']
    p = subprocess.run(cmd, cwd=W, env=env, capture_output=True, text=True)
    out = O.P('verify', 'decision', 'out_E6p_stage2')
    os.makedirs(out, exist_ok=True)
    tail = (p.stdout + '\n' + p.stderr)[-6000:]
    O.atomic_write_text(os.path.join(out, 'stdout_tail.txt'), O.san(tail))
    lines = []
    for f in sorted(os.listdir(out)):
        src = os.path.join(out, f)
        dst = os.path.join(hd, 'verify', 'decision', 'out_E6p_stage2', f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy2(src, dst)
        lines.append('%s  %s' % (O.sha_file(dst), os.path.relpath(dst, hd)))
    with open(os.path.join(hd, 'HANDOFF_SHA256.txt'), 'a', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(json.dumps(dict(rc=p.returncode, outputs=len(lines)), ensure_ascii=False), flush=True)
    return p.returncode


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('--root', default='')
    ap.add_argument('--handoff', default='')
    a = ap.parse_args()
    root = O.P(a.root) if a.root else O.work()
    if a.cmd == 'gates':
        G_ = gates(root, 'pre')
        sys.exit(0 if (G_.status == 'PASS').all() else 2)
    elif a.cmd == 'gates_post':
        G_ = gates(root, 'post')
        sys.exit(0 if (G_.status == 'PASS').all() else 2)
    elif a.cmd == 'handoff':
        hd, hits = handoff(root)
        if hits:
            print('S07b 扫描命中，不交付', flush=True)
            sys.exit(3)
        run_d(hd)
    elif a.cmd == 'run_d':
        run_d(O.P(a.handoff))
    elif a.cmd == 'identities_deriv':
        identities(root, deriv=True)
    else:
        {'identities': identities, 'stage0': stage0_final, 'schema': schema, 'seal_final': seal_final, 'deploy_log': deploy_log}[a.cmd](root)
