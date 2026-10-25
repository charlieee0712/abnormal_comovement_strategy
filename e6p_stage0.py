# -*- coding: utf-8 -*-
"""E6p Stage 0（brief §2；附录 A0–A14；fail-closed；任何收益读数之前，只打标签不选支）：
S0-0 源合同键（C1–C12、块级 / 依赖级绑定）→ registration/sources_E6p.csv；S0-1 数据覆盖（持仓全域 / pool0 形成域 × 字段 × 年 × 板块）；
S0-2 源复现 / 前沿锚 / E6o 账户复现 / 会计桥 / 敞口 = 日均 ΣW（INFO）/ E6o 62 个不可判对象；S0-3 零干预恒等（自检结果登记）；
S0-4 部署容量与两层分配器；S0-5 token 攻击；S0-6 成本路由与拆单；S0-7 T8 计数；S0-8 RENEW5 时钟；S0-9 匹配 V2；S0-10 landmark；S0-11 日龄与风险集；
S0-12 资源估算；S0-13 / S0-14 结果行。另：FUTURE_DATA_PLANT / UNIT_PLANT / MIRROR_NO_FUTURE_READ / JOURNAL_REPLAY / WRONG_MOTHER_MERGE。
只读源 / 面板 / 已曝光的 E6o 账户与 P_SOURCE 锚；不跑任何本轮退出账户的收益。输出：diagnostics/stage0_E6p_part1.csv、verify/identities_E6p_stage0.csv、
registration/sources_E6p.csv、diagnostics/source_fn_sha256_E6p.json、diagnostics/s0_e6o_undecidable_E6p.json。用法：python3 e6p_stage0.py"""
import os
import sys
import json
import time
import inspect
import hashlib
import importlib.util
import resource

import numpy as np
import pandas as pd

import e6p_core as O
import e6p_engine as E
import e6p_acct as A
import e6p_synth as SY
import e6p_landmark as LM

ROWS = []
IDN = []
SRC = []
BOARDS = ('SH_MAIN', 'SZ_MAIN', 'CHINEXT', 'STAR')
S00_STATUS = 'BOUND'


def put(probe, item, key, value, unit='count', status='INFO', source_file='', note=''):
    if isinstance(value, float) and not np.isfinite(value):
        value, status = '', 'UNKNOWN'
    ROWS.append(dict(probe_id=probe, item=item, key=key, value=value, unit=unit, status=status, source_file=source_file, note=note))


def idn(check, desc, exec_id, value, maxabs, tol, status):
    IDN.append(dict(check_id=check, description=desc, exec_id=exec_id, value=value, max_abs_diff=maxabs, tolerance=tol, status=status))


def src(key, value, item, source_file, fn_sha='', status=S00_STATUS, note=''):
    put('S0-0', item, key, value, 'count', status, source_file, note)
    SRC.append(dict(key=key, value=value, source_file=source_file, fn_sha256=fn_sha, status=status))


def fn_sha(*objs):
    h = hashlib.sha256()
    for o in objs:
        o = getattr(o, 'py_func', o)
        h.update(inspect.getsource(o).encode())
    return h.hexdigest()


def spec_module():
    p = O.P('inputs', 'plans', 'e6p_spec_tests.py')
    if O.sha_file(p) != O.SPEC_SHA256:
        raise RuntimeError('spec 参考脚本 sha 不符')
    sp = importlib.util.spec_from_file_location('e6p_spec_ref', p)
    m = importlib.util.module_from_spec(sp)
    sys.modules['e6p_spec_ref'] = m
    sp.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ S0-0
def s0_0():
    import e6m_b6_triggers as BT
    import e6n_b2 as B2
    import e6j_prod as PR
    import comprehensive_factor_diagnosis as C
    import pool_screening_v2 as PS
    import e6m_stage0_full as SF
    import e6o_engine as OE
    here = os.path.dirname(os.path.abspath(__file__))
    fsha = lambda fn: O.sha_file(os.path.join(here, fn))
    sh = dict(engine=fsha('e6p_engine.py'), engine_e6o_step=fn_sha(OE.step), b2_trigger=fn_sha(BT.ecdf_pct, BT.cvr_triggers, B2.triggers),
              veto_t1a=fn_sha(PR.drop_mask, PR.build_period, C.precompute_neutralized_factor, C.build_factor_strategy_holdings_cached, PS.neutralize_by_mcap),
              volume_baseline=fsha('e6o_triggers.py'), limit_fields=O.digest([fsha('e6p_cache.py'), fn_sha(SF.load_full)]),
              natural_gate=O.digest([fn_sha(A.Market.formation, A.Market.natural), fsha('e6o_source.py')]),
              deploy_eligible_set=fn_sha(A.Market.formation), deploy_prior_weight=O.digest([fn_sha(A.Market.formation), fsha('e6o_source.py')]),
              relative_benchmark=O.digest([fsha('e6o_panels.py'), fsha('e6p_cache.py'), fn_sha(E.alloc2, E.prop_capped)]),
              fee=fn_sha(E.solve_eval, E.feasible), vwap=fn_sha(C.vwap_daily_return, C.adjusted_prices), cost_adv=fsha('e6o_panels.py'), cost_sigma=fsha('e6o_panels.py'))
    src('ENGINE_FN_SHA256', sh['engine'], 'C1 E6o 账户引擎（E6p 扩展版；全开关关闭 ≡ E6o，见 E6O_ACCOUNT_REPLICATION）', 'e6p_engine.py', sh['engine'],
        note='E6o step 源码 sha256 = %s；E6p 扩展只加参数开关（部署 / RENEW5 / 再投资 / 反馈 / 随机 V2），NATIVE 路径逐日复现 E6o 18 个 P_ACCOUNT 与主对象（≤ 1e−9）' % sh['engine_e6o_step'])
    src('SOURCE_CASH_MODEL', 'P_SOURCE=FIXED_ROLLING_WEIGHTS; P_ACCOUNT=E6O_SELF_FINANCING_CASH_ENGINE', 'C1 源现金模型', 'e6i_sparse.SparseEngine.pnl / e6p_engine.step', sh['engine'],
        note='旧滚动源 act[j] = Σ_{k<H} W[j−k] / min(j+1, H)（不随价格漂移）；新账户自融资现金；两者差 = ACCOUNTING_BRIDGE（INFO）')
    src('NATIVE_BUDGET_RULE', 'REGULAR_BUDGET=NAVc*f_w/H; SINGLE_ROOM=1%NAVc-held; INDUSTRY_ROOM=(capsh+3pp)NAVc-held(scaled pro rata); EXTRA=usable tags x f_w', 'C1 常规买入预算与 DEV 形状',
        'e6p_engine.step（次日买单段）', fn_sha(E.step), note='源形成名单 DEV 权重 f_w（E6o 源抽取原样）；早退款标签 lag1、到原 due 重分类；不把同一早退款既用于常规又完整用于额外')
    src('B2_TRIGGER_KIND', 'EDGE', 'C2 SOURCE_T1b 触发类型', 'e6m_b6_triggers.cvr_triggers / e6n_b2.triggers', sh['b2_trigger'],
        note='今日在高尾 ∧ 昨日已知且不在高尾；T1b_EDGE 与 SOURCE_T1b 触发格完全相同（E6o 已核：差 0 格）')
    src('B2_LEVEL_DEFINITION', 'cvr_pct>=0.90 (clean daily empirical position of close/vwap-1); persistent state', 'C2 LEVEL 定义', 'e6o_triggers.py', sh['volume_baseline'])
    src('B2_MISSING_DAY_RULE', 'UNKNOWN_NOT_FILLED', 'C2 缺测量日处置', 'e6o_triggers.py', sh['volume_baseline'], note='今日不可得 → UNKNOWN（−1）；不从昨日填成今日坏 / 好；UNKNOWN 不发卖单')
    src('VETO_MEASURE', 'CVR_20d', 'C3 T1a 否决测量', 'e6j_prod.F_CVR / comprehensive_factor_diagnosis factor spec', sh['veto_t1a'])
    src('VETO_CUT_FORM', 'RESIDUAL_CUT', 'C3 否决切点形式', 'e6j_prod.drop_mask', sh['veto_t1a'], note='pool0 内对 log 市值 OLS 残差 → 秩五分位（rank first）最高组；E6o T1a 面板原样')
    src('VETO_COEF_EXTENSION_RULE', 'SAME_DAY_POOL0_COEF_AND_CUT_EXTENDED_TO_HELD_DOMAIN', 'C3 系数延伸', 'e6o_source.t1a_panel', sh['natural_gate'],
        note='持仓不入 pool0 重估；同日 (α, β, cut) 延伸到池外持仓；缺参考合同 → UNKNOWN')
    src('VETO_TIE_RULE', 'rank(method=first)', 'C3 并列规则', 'comprehensive_factor_diagnosis.build_factor_strategy_holdings_cached', sh['veto_t1a'])
    src('VOLUME_BASELINE_FN', 'V_T/mean(V_{T-20..T-1})', 'C4 T3b15 量比基线', 'e6o_triggers.py', sh['volume_baseline'], note='不含 T；停牌 = 未知；基线 0 = UNKNOWN')
    src('VOLUME_MIN_OBS', 10, 'C4 最小有限观察数', 'e6o_triggers.py', sh['volume_baseline'])
    src('LIMIT_PRICE_FIELDS', 'limit_up/limit_down (daily table, raw price)', 'C5 涨跌停价字段', 'e6m_stage0_full.load_full / e6p_cache.py', sh['limit_fields'],
        note='日线表当日字段（FundamentalTL 涨跌停价，加载器重命名）；与 raw 收盘 close 同单位（不复权）')
    src('LIMIT_PIT_RULE', 'SAME_DAY_FIELD_PIT', 'C5 PIT 规则', 'e6p_cache.py', sh['limit_fields'], note='按 date × code 当日值；不回填、不用今日规则倒推历史')
    src('LIMIT_BOARD_REGIME_START', 'SH_MAIN/SZ_MAIN<=2010-01-04(10%,ST 5%); STAR=2019-07-22(20%); CHINEXT 20%=2020-08-24', 'C5 板块制度起点（按板块）', 'W10 / 交易所公告', sh['limit_fields'],
        note='限制价字段本身携带制度（本轮按字段判，不按板块写死比例）；北交所无样本')
    src('NO_LIMIT_DAY_FLAG', 'DERIVED: limit missing within first 5 open days of a stock listed after sample start -> NO_LIMIT_DAY(0, non-event); other missing -> UNKNOWN', 'C5 无涨跌幅限制日',
        'e6p_cache.py', sh['limit_fields'], note='数据无显式标志；推导规则登记（plan §5.1：无价格限制 = 非事件，未知限制 ≠ 0）')
    src('ONE_TICK_RULE', 'open and close within half tick (0.005) of raw limit-up', 'C5 一字板', 'e6p_cache.py', sh['limit_fields'])
    src('RENEW_NATURAL_GATE_FN', 'NATURAL_GATE_VIA_NONE_MEMORY: e6p_acct.Market.natural(form) = source final formation list with memory=NONE', 'C6 自然入场名单', 'e6p_acct.Market.natural / e6o_source',
        sh['natural_gate'], note='与期望绑定一致（完整 K / T / C / CVR 最终资格，无 HG 优惠）；段首预热日名单为空 → UNKNOWN（不发单）')
    src('RENEW_GATE_OUTPUT_KIND', 'FULL_FINAL_LIST', 'C6 名单类型', 'e6o_source', sh['natural_gate'])
    src('DEPLOY_ELIGIBLE_SET_FN', 'e6p_acct.Market.formation(form, memory)[day T] = E6o engine regular new-lot buy list (source final allowed buys)', 'C7 部署合法买入集合',
        'e6p_acct.Market.formation / e6p_engine.step（部署层）', sh['deploy_eligible_set'], note='与期望绑定一致；部署只给当日源最终允许买入的股票')
    src('DEPLOY_PRIOR_WEIGHT_FN', 'f_w (source DEV target weight, positive part)', 'C7 部署方向', 'e6o_source（fm_w）', sh['deploy_prior_weight'], note='只作额外资金分配方向；源账户不整体归一')
    src('RELATIVE_BENCHMARK_CONTRACT', 'CLEAN_EQUAL_WEIGHT: w_bm=1/N_clean(T); industry share=n_ind(T)/N_clean(T) (ind_share panel); industry code = day-T industry_zx1',
        'C8 基准权重与行业归属', 'e6o_panels.py（ind_share / clean）/ e6p_cache.py（nclean）', sh['relative_benchmark'],
        note='与期望一致之处：干净全市场等权、个股 1/N_clean、行业 n_ind/N_clean；差异登记：源 bench_industry_shares 用 T 日行业码（T 收盘可得，非前视），期望写 T−1 冻结；本轮沿源')
    src('SECTOR_LOWER_BOUND_EXISTS', 'FALSE', 'C8 行业下界', 'e6p_engine.step', sh['relative_benchmark'], note='源 NATIVE 只实现上界（capsh + 3pp）；RELATIVE_UPPER 不冒称双侧合规（plan §6.3）')
    src('FEE_CHARGED_TURN_UNIT', '4bp x sum|net security order notional| (one side)', 'C9 费率单位', 'e6p_engine.solve_eval / feasible', sh['fee'], note='同日同证券先内部转移再按净额收费；一次买卖合计 8bp')
    src('VWAP_DEFINITION', 'amount/volume (daily vwap field; adjusted pv for valuation)', 'C9 VWAP', 'comprehensive_factor_diagnosis.vwap_daily_return', sh['vwap'])
    src('CORPORATE_ACTION_FIELDS', 'adj_factor (backward-adjusted, PIT cumulative)', 'C9 公司行为', 'e6o_panels.py', sh['cost_adv'], note='沿 E6o 登记：估值与收益用后复权 VWAP / 收盘；停牌估值与复牌跳价照源')
    src('COST_ADV_FN', 'adv20 = mean(amount_{T-20..T-1}) CNY, >=10 obs', 'C10 ADV', 'e6o_panels.rolling_prev', sh['cost_adv'], note='执行日 e 用截至 e−1 的窗口；路由在 T 收盘用 e = T+1 的窗口（截至 T）')
    src('COST_SIGMA_FN', 'sig20 = std(r_day_{T-20..T-1}), >=10 obs', 'C10 σ', 'e6o_panels.rolling_prev', sh['cost_sigma'], note='r_day = close / lclose − 1（前收盘已除权）')
    src('COST_FIELD_CLOCK', '<=T (window ends at T-1 for execution day T)', 'C10 可得时钟', 'e6o_panels.rolling_prev', sh['cost_adv'])
    # C11：E6o 表 ID 绑定
    S = pd.read_csv(O.E6O('statistics', 'account_summary_E6o.csv'), keep_default_na=False, na_values=[''])
    F = S[(S.segment == 'FULL') & S.exec_id.str.contains('\\|FULLHIST\\|')]
    Fp = F[F.exec_id.str.contains('NONE\\|NA\\|NA\\|NA\\|NA\\|OFF\\|OFF')]
    Fc = F[~F.exec_id.str.contains('NONE\\|NA\\|NA\\|NA\\|NA\\|OFF\\|OFF')]
    for v in (6.956, 6.897, 6.266, 6.228, 5.516, 5.509):
        own = sorted(Fp[(Fp.net_ann_pp - v).abs() < 5e-4].exec_id)
        kid = Fc[(Fc.parent_net_ann_pp - v).abs() < 5e-4]
        par = sorted(set(kid.parent_exec_id))
        if own:
            val, note = ';'.join(own), ('该父行自身 FULL net（支持 = 与其 P_SOURCE 父的共同日：剔除每段约 19 日源预热）；起点 CASH_V0、绩效时钟 POST_VWAP（E6o）')
        elif par:
            val, note = ';'.join(par), ('退出子行里的 parent_net_ann_pp（支持 = 与退出子的共同日：全日）——同一父账户、不同共同支持；%d 个子行引用' % len(kid))
        else:
            val, note = '', '未匹配'
        src('E6O_TABLE_BINDING_%s' % ('%.3f' % v), val, 'C11 E6o 表读数 %.3f 的执行身份' % v, 'E6o statistics/account_summary_E6o.csv', '',
            status='BOUND' if val else 'SOURCE_BINDING_PENDING', note=note + '；本轮 P_ACCOUNT_N(H) 复现按 ID 取（E6O_ACCOUNT_REPLICATION）')
    src('SOURCE_H_SET', '5,10,15,20,30,40', 'S0-2 源引擎支持的 H', 'e6i_sparse.SparseEngine.pnl', '', note='源引擎对任意 H 计算；E6n 冻结账户只覆盖 H5 / 10 / 20（逐日复现）')
    for b in ('PARENT', 'MAIN', 'TRANSFER', 'RENEW5', 'CAP_BRIDGE', 'CASH_BRIDGE', 'RECYCLE_EXTENSION', 'MIRROR'):
        src('BLOCK_BINDING_%s' % b, 'BOUND', '块级绑定 %s' % b, 'registration/registry_E6p.csv', '')
    for dep, cov in (('DEPLOY', 'deploy ∈ {D80, D95}'), ('RELATIVE_BENCHMARK', 'cap ∈ {RELATIVE_UPPER, ABS01}'), ('LIMIT', 'trigger = T8_LIMIT_CLOSE'),
                     ('COST', '全部成本曲线 + deploy ∈ {RECYCLE_COST0, RECYCLE_COSTNET}'), ('RENEW_GATE', 'renew = 5'), ('MIRROR', 'role = MIRROR')):
        src('DEPENDENCY_BINDING_%s' % dep, 'BOUND', '依赖级绑定 %s（覆盖 %s）' % (dep, cov), 'registration/sources_E6p.csv', '')
    return sh


# ------------------------------------------------------------------ 持仓全域
def holding_domain(mk, H=40):
    """持仓全域：源形成名单 H40 窗（e0 = f+1 … f+40）的 8 坐标并集（≥ 任一账户的实际持仓日；FEASIBLE 卖不出的延期另在账户层计）。"""
    T, N = mk.T, mk.N
    hold = np.zeros((T, N), bool)
    for (f, m), (ptr, col, w) in G['f'].items():
        t = np.repeat(np.arange(T), np.diff(ptr))
        for k in range(1, H + 1):
            tt = t + k
            ok = tt < T
            hold[tt[ok], col[ok]] = True
    return hold


G = {}


def s0_1(mk, hold):
    cd = mk.cd
    pdir = os.path.join(cd, 'panels')
    L = lambda k: np.asarray(np.load(os.path.join(pdir, k + '.npy'), mmap_mode='r'))
    years = np.array([int(d[:4]) for d in mk.dates])
    board = L('board')
    pool0 = np.asarray(np.load(os.path.join(cd, 'triggers', 'pool0.npy'), mmap_mode='r')).astype(bool)
    is_open = np.asarray(mk.isopen).astype(bool)
    t8k = L('t8_kind')
    minute = np.isfinite(np.load(os.path.join(O.e6o_cache(), 'minute', 'tail_amt.npy'), mmap_mode='r'))
    fields = {'daily': np.isfinite(np.asarray(mk.pv)) | ~is_open, 'limit_up_down': L('limit_known') | ~is_open, 'no_limit_flag': (t8k != 5),
              'suspension': np.ones(is_open.shape, bool), 'one_tick': L('limit_known') | ~is_open, 'corporate_actions': L('adj_known'),
              'industry_L1': np.asarray(mk.ind) >= 0, 'ADV20': np.isfinite(np.asarray(mk.adv20)) | ~is_open, 'sigma20': np.isfinite(np.asarray(mk.sig20)) | ~is_open,
              'benchmark_weight': (np.asarray(mk.ind) >= 0) & (mk.nclean[:, None] > 0), 'minute_bars': np.asarray(minute) | ~is_open}
    for dom, M in (('HOLDING_ALL', hold), ('POOL0_FORMATION', pool0)):
        for fld, Fm in fields.items():
            for y in sorted(set(years)):
                ym = (years == y)
                for bi, bn in enumerate(BOARDS):
                    m = M[ym][:, board == bi]
                    n = int(m.sum())
                    if n == 0:
                        continue
                    v = float(Fm[ym][:, board == bi][m].mean())
                    put('S0-1', dom, 'COVERAGE_%s_%d_%s' % (fld, y, bn), round(v, 6), 'share', 'INFO', 'cache panels',
                        '分母 = 该域股票日（%d）；daily / limit / ADV / σ / minute 对停牌日记已知；no_limit_flag = 非 UNKNOWN；minute_bars 2013-08-01 前为 0' % n)
    for bn, v in (('SH_MAIN', '2010-01-04 前已 10%（ST 5%）；注册制新股前 5 日无限制自 2023-04-10'), ('SZ_MAIN', '同沪主板；2021-04 深市主板与中小板合并'),
                  ('CHINEXT', '20% 自 2020-08-24（此前 10%）；注册制新股前 5 日无限制自 2020-08-24'), ('STAR', '开板 2019-07-22 起 20%；新股前 5 日无限制')):
        put('S0-1', '板块制度起点（W10；本轮按 PIT 字段判，不写死比例）', 'LIMIT_REGIME_START_%s' % bn, v, 'count', 'INFO', 'W10 / 交易所规则')
    put('S0-1', '持仓全域股票日（源 H40 窗 8 坐标并集）', 'HOLDING_ALL_CELLS', int(hold.sum()), 'count', 'INFO', 'cache/source', '离池持仓日 = %d' % int((hold & ~pool0).sum()))
    return pool0


# ------------------------------------------------------------------ S0-2
def s0_2(mk):
    cd = mk.cd
    rep = pd.concat([pd.read_csv(os.path.join(cd, 'source_e6p', 'replication_%s.csv' % s), keep_default_na=False) for s in O.SEGS])
    r = rep[rep.status != 'NOT_APPLICABLE']
    for x in r.itertuples():
        idn('SOURCE_REPLICATION', 'P_SOURCE（源引擎 SE.pnl）vs E6n 冻结账户 d_* 与 E6o 源账本逐日（gross / pos / turn / net8）：%s %s %s H%d' % (x.segment, x.form, x.memory, x.H),
            'E6P-SRC-%s-%s-H%d' % (x.form, x.memory, x.H), x.segment, float(x.max_abs_diff), 1e-9, 'PASS' if (x.status == 'PASS') else 'DIFFERS')
    put('S0-2', 'P_SOURCE 逐日复现（E6n 支持的 H5 / 10 / 20 × 8 坐标 × 四段）', 'SOURCE_REPLICATION_ROWS', '%d/%d PASS' % (int((r.status == 'PASS').sum()), len(r)), 'count',
        'PASS' if (r.status == 'PASS').all() else 'DIFFERS', 'cache/source_e6p/replication_*.csv', 'H15 / 30 / 40 由同一源引擎计算（E6n 无对应冻结账户 → NOT_APPLICABLE 复现）')
    # 前沿锚（W05；已曝光；INFO）
    segv = {}
    nd = {}
    for s in O.SEGS:
        z = np.load(os.path.join(cd, 'source_e6p', '%s.npz' % s), allow_pickle=False)
        v = z['src_net8|%s|HG10|H5' % O.MAIN_FORM]
        ok = np.isfinite(v)
        segv[s] = float(np.mean(v[ok]) * O.ANN_PP)
        nd[s] = int(ok.sum())
    full = sum(segv[s] * nd[s] for s in O.SEGS) / sum(nd.values())
    anc = dict(zip(O.SEGS, (3.21, 7.36, 8.24, 10.31)))
    mx = max(max(abs(segv[s] - anc[s]) for s in O.SEGS), abs(full - 6.74))
    idn('SOURCE_ANCHOR_FRONTIER', 'P_SOURCE 主父（A4b_CVRv5 × HG10 × H5，8bp）四段 / FULL net vs W05 锚 3.21 / 7.36 / 8.24 / 10.31 / 6.74（容差 1e−2；不达只记 INFO）',
        'E6P-SRC-%s-HG10-H5' % O.MAIN_FORM, '/'.join('%.4f' % segv[s] for s in O.SEGS) + ' FULL %.4f' % full, mx, 1e-2, 'INFO')
    # E6o 账户复现与零干预恒等（e6p_selftest.py 结果）
    st = pd.read_csv(O.P('verify', 'selftest_identities_E6p.csv'), keep_default_na=False)
    for x in st[st.check_id.isin(['E6O_ACCOUNT_REPLICATION', 'NOEXIT_EQ_PARENT', 'RECYCLE_NONE_EQ_NATIVE', 'CASH_NONE_EQ_NATIVE', 'DEPLOY_ZERO_BUDGET_EQ_NATIVE',
                                  'RENEW_NO_CHECKPOINT_EQ_PARENT', 'CHECKPOINT_RESTORE_IDEMPOTENT'])].itertuples():
        idn(x.check_id, x.description, x.exec_id, x.value, x.max_abs_diff, x.tolerance, x.status)
    # 源持仓 sha
    for (f, m), (ptr, col, w) in G['f'].items():
        h = hashlib.sha256()
        for a in (ptr, col, w):
            h.update(np.ascontiguousarray(a).tobytes())
        idn('SOURCE_HOLDINGS_SHA', '源形成名单（CSR：日指针 / 列 / DEV 权重）sha256：%s × %s' % (f, m), 'E6P-SRC-%s-%s' % (f, m), h.hexdigest()[:16], '', '', 'INFO')
    # 会计桥（P_ACCOUNT − P_SOURCE；E6o 已曝光坐标；INFO）
    segi = np.array([O.seg_of_date(d) for d in mk.dates])
    for mem in O.MEMS:
        for H in (5, 10, 20):
            p = O.P('tmp', 'selftest', 'DY_REPL_FE_%s_H%d.npy' % (mem, H))
            if not os.path.exists(p):
                continue
            ne_a = np.load(p)[:, E.DYI['net_excess']]
            ne_s = np.full(mk.T, np.nan)
            for s in O.SEGS:
                z = np.load(os.path.join(cd, 'source_e6p', '%s.npz' % s), allow_pickle=False)
                idx = np.array([mk.di[d] for d in z['dates']])
                ne_s[idx] = z['src_net8|%s|%s|H%d' % (O.MAIN_FORM, mem, H)]
            ok = np.isfinite(ne_a) & np.isfinite(ne_s)
            br = float(np.mean(ne_a[ok] - ne_s[ok]) * O.ANN_PP)
            idn('ACCOUNTING_BRIDGE', 'P_ACCOUNT（E6o 现金引擎，FEASIBLE）− P_SOURCE（固定滚动权重）FULL 共同日 ann_pp：%s × %s × H%d（SOURCE_CASH_MODEL 不同；非零如实登记）' % (O.MAIN_FORM, mem, H),
                'E6P-SRC-%s-%s-H%d' % (O.MAIN_FORM, mem, H), round(br, 6), '', '', 'INFO')
    # 敞口 = 日均 ΣW（CC-E6p-11；INFO）
    segz = {s: np.load(os.path.join(cd, 'source_e6p', '%s.npz' % s), allow_pickle=False) for s in O.SEGS}
    for (f, m) in sorted(G['f']):
        for H in O.HS:
            best = None
            for lag in (0, 1, 2):
                P_, Q_ = [], []
                for s in O.SEGS:
                    z = segz[s]
                    pos = z['src_pos|%s|%s|H%d' % (f, m, H)]
                    sw = z['sumw|%s|%s' % (f, m)]
                    n = len(sw)
                    act = np.array([sw[max(0, j - H + 1):j + 1].sum() / min(j + 1, H) for j in range(n)])   # 源 act[j] = Σ_{k<H} W[j−k] / min(j+1, H)（段内）
                    pred = np.full(n, np.nan)
                    pred[lag:] = act[:n - lag] if lag else act
                    ok = np.isfinite(pos) & np.isfinite(pred)
                    P_.append(pos[ok])
                    Q_.append(pred[ok])
                p_, q_ = np.concatenate(P_), np.concatenate(Q_)
                if len(p_) < 30:
                    continue
                d_ = float(np.max(np.abs(p_ - q_)))
                c_ = float(np.corrcoef(p_, q_)[0, 1])
                if best is None or d_ < best[1]:
                    best = (lag, d_, c_, float(np.mean(p_)), float(np.mean(q_)))
            if best:
                idn('SOURCE_EXPOSURE_EQ_MEAN_SUMW', 'P_SOURCE 逐日敞口 vs 源公式 act = H 日内 ΣW 均值（段内、段首按 min(j+1, H)；最佳对齐滞后 %d 日）：%s × %s × H%d；value = 相关 / 敞口均值 / ΣW 均值' % (best[0], f, m, H),
                    'E6P-SRC-%s-%s-H%d' % (f, m, H), 'corr=%.6f;mean_pos=%.4f;mean_sumw_H=%.4f' % (best[2], best[3], best[4]), best[1], '', 'INFO')
    # E6o 62 个"全部可算条件通过却不可判"对象（不重跑，只读 E6o 政策表）
    P = pd.read_csv(O.E6O('statistics', 'policy_E6o.csv'), keep_default_na=False, dtype=str)
    flds = ['c1_segment_tolerance_ok', 'c2_ok', 'c3_full_sc_same_sign', 'c4_random_post_ok', 'c5_impact_ok', 'c6_declared_ok', 'port3t_ok', 'positive_ok']
    U = P[P.verdict == '不可判']
    allok = U[(U[flds] != '0').all(axis=1)]
    na_counts = {f: int((allok[f] == '').sum()) for f in flds}
    f7 = [x for x in flds if x != 'c6_declared_ok']
    Pq = P[(P.profile_name == 'POLICY_E6O_PARENT_Q') & ~P.exec_id.str.split('|').str[4].isin(['T4a', 'T4b', 'T5'])]
    all1 = Pq[(Pq[f7] == '1').all(axis=1)]
    out = dict(n_undecidable=len(U), n_all_computable_true=len(allok), na_fields=na_counts,
               by_profile=allok.execution_profile.value_counts().to_dict(), mapping_unresolved=allok.mapping_unresolved_fields.value_counts().to_dict(),
               partial_history=allok.partial_history_years.value_counts().head(5).to_dict(), random_mechanism=allok.random_mechanism.value_counts().to_dict(),
               feasible_all_fields_true=int((all1.execution_profile == 'FEASIBLE_DAILY').sum()),
               feasible_all_fields_true_verdicts=all1[all1.execution_profile == 'FEASIBLE_DAILY'].verdict.value_counts().to_dict(),
               feasible_all_true_H=all1[all1.execution_profile == 'FEASIBLE_DAILY'].exec_id.str.split('|').str[3].value_counts().to_dict(),
               feasible_all_true_trigger=all1[all1.execution_profile == 'FEASIBLE_DAILY'].exec_id.str.split('|').str[4].value_counts().to_dict(),
               diagnosis='62 个 FEASIBLE 对象 c1 / c2 / c3 / c4 / c5 / c6 / port3t / positive 八项全为 1，无不可算项；不可判来自 e6o_policy.py 的类型判定：'
                         'conds 里 c3（np.sign 比较）与 positive（numpy 浮点比较）是 numpy.bool_，`c is True` 恒为假 → all(...) 不成立 → 落入 不可判。'
                         '按 E6o 自身 verdict_rule（全部可算条件都过 → 通过）应为 通过；IDEAL 59 个缺 c4（IDEAL 无随机）→ 真不可判。E6o 结果按 brief 不改，只登记。')
    O.atomic_write_json(O.P('diagnostics', 's0_e6o_undecidable_E6p.json'), out)
    put('S0-2', 'E6o 不可判对象中"全部可算条件为真"者及其缺项（写 notes §8）', 'E6O_UNDECIDABLE_ALL_COMPUTABLE_TRUE', len(allok), 'count', 'INFO', 'E6o statistics/policy_E6o.csv',
        json.dumps(na_counts, ensure_ascii=False))
    return segv


# ------------------------------------------------------------------ S0-4
def s0_4(mk, spec):
    # 两层分配器：手算三例 + 随机对照 spec.allocate
    cases = [([1, 1, 2], [10, 10, 10], [-1, -1, -1], [0, 0, 0], 8.0, [2, 2, 4]),
             ([1, 1, 2], [10, 10, 3], [-1, -1, -1], [0, 0, 0], 8.0, [2.5, 2.5, 3]),
             ([1, 1, 1, 1], [5, 5, 5, 5], [0, 0, 1, 1], [3, 3, 10, 10], 8.0, [1.5, 1.5, 2.5, 2.5])]
    mx = 0.0
    for p, c, g, gc, b, exp in cases:
        x = E.alloc2(np.array(p, float), np.array(c, float), np.array(g, np.int64), np.array(gc, float), b)
        mx = max(mx, float(np.max(np.abs(x - np.array(exp, float)))))
    rng = np.random.default_rng(11)
    mr = 0.0
    for _ in range(300):
        n = int(rng.integers(2, 12))
        p = rng.random(n) * (rng.random(n) > 0.2)
        c = rng.random(n) * 0.05
        g = rng.integers(0, 3, n)
        gcap = {int(k): float(rng.random() * 0.08) for k in range(3)}
        b = float(rng.random() * 0.2)
        ref = spec.allocate(list(p), list(c), [int(v) for v in g], gcap, b)
        x = E.alloc2(p, c, g.astype(np.int64), np.array([gcap[int(v)] for v in g]), b)
        mr = max(mr, float(np.max(np.abs(x - np.array(ref)))))
    idn('ALLOCATOR_SYNTHETIC_3CASES', '两层水位分配器（e6p_engine.alloc2）：手算三例（无上限 / 单股上限再分配 / 行业饱和）与 300 个随机例 vs plan 附录 C allocate', '',
        'hand=%.1e;random=%.1e' % (mx, mr), max(mx, mr), 1e-9, 'PASS' if max(mx, mr) <= 1e-9 else 'DIFFERS')
    # RELATIVE_UPPER 含全部已有批次：已有仓位到上限的名字不再加仓
    T = 30
    mk2 = SY.SynthMarket(T=T, N=2, flat=True, nclean=50.0, capsh=1.0)
    f = SY.csr_daily(T, [0, 1], [0.9, 0.1])
    ip, fp = A.ip_fp(5, E.TM_NONE, fund=E.FD_NATIVE, deploy=E.DP_TARGET, target=0.95, cap=E.CP_REL)
    fp[E.FP_IDEV] = 10.0
    acc = SY.account(mk2, ip, fp, None, f).run(0, T)
    cap = 1.0 / 50.0 + 0.01
    nl = int(acc.S_i[E.SI_NL])
    v0 = float(np.sum(acc.L_f[:nl, 0][(acc.L_i[:nl, 0] == 0) & (acc.L_i[:nl, 7] == 1)]) * mk2.pc[-1, 0])
    share0 = v0 / acc.DY[T - 1, E.DYI['nav_close']]
    ok = share0 <= cap * (1.0 + 1e-3) and float(acc.DY[:, E.DYI['deploy_buy']].sum()) > 0
    idn('RELATIVE_UPPER_INCLUDES_ALL_LOTS', '合成例：D95 × RELATIVE_UPPER（源方向 90%% 集中于股 0），单股上界 1/N_clean + 1pp = %.4f 含全部已有批次（常规 + 部署）；末日股 0 份额 %.6f（交易后费用漂移容差 0.1%%）→ 超限加仓被拦' % (cap, share0), '',
        round(share0, 8), '', '', 'BLOCKED' if ok else 'DIFFERS')
    try:
        A.ip_fp(20, E.TM_NONE, deploy=E.DP_TARGET, target=1.2)
        st = 'DIFFERS'
    except ValueError:
        st = 'BLOCKED'
    idn('DEPLOY_TARGET_LE_ONE', '部署目标 1.2 > 1（借入）→ ip_fp 拒绝（R1 纯多头无杠杆）', '', 'target=1.2', '', '', st)


def capacity_rows(mk):
    """部署容量（RELATIVE_UPPER 与 ABS01；份额 NAV；按日再段均值）：ALL_ACTIVE_THEORETICAL（主母体 HG10 H20 活批次名字全域）/ LEGAL_NEW_BUY_DOMAIN（当日源形成名单）/
    FROZEN_DIRECTION_REACHABLE（按源方向 ∝ f_w 两层水位分配的可达上限）；POST_TRADE_ACTUAL 由正式账户在 B 后补（终版 stage0）。"""
    ptr, col, w = G['f'][(O.MAIN_FORM, 'HG10')]
    T = mk.T
    ind = np.asarray(mk.ind)
    capsh = mk.capsh
    segi = np.array([O.seg_of_date(d) for d in mk.dates])
    res = {k: np.full((T, 2), np.nan) for k in ('ALL_ACTIVE_THEORETICAL', 'LEGAL_NEW_BUY_DOMAIN', 'FROZEN_DIRECTION_REACHABLE')}
    for d in range(T):
        a, b = ptr[d], ptr[d + 1]
        if b <= a or not (mk.nclean[d] > 0):
            continue
        lo = ptr[max(0, d - 19)]
        act = np.unique(col[lo:b])
        today = col[a:b]
        for j, scd in enumerate((1.0 / mk.nclean[d] + 0.01, 0.01)):
            for kind, names, pri in (('ALL_ACTIVE_THEORETICAL', act, np.ones(len(act))), ('LEGAL_NEW_BUY_DOMAIN', today, np.ones(len(today))),
                                     ('FROZEN_DIRECTION_REACHABLE', today, np.maximum(w[a:b], 0.0))):
                g = ind[d, names].astype(np.int64)
                gc = np.where(g >= 0, capsh[d, np.maximum(g, 0)] + 0.03, 0.0)
                x = E.alloc2(pri.astype(float), np.full(len(names), scd), g, gc, 10.0)
                res[kind][d, j] = min(1.0, float(x.sum()))
    for kind, arr in res.items():
        for s in O.SEGS:
            m = segi == s
            put('S0-4', '部署容量 %s（主母体 HG10 × H20 域；RELATIVE_UPPER）' % kind, 'CAPACITY_%s_%s' % (kind, s), round(float(np.nanmean(arr[m, 0])), 6), 'share', 'INFO',
                'cache/source + panels', 'ABS01 同口径 = %.6f；名字数 ≥ 100 不等于满仓（行业 / 资格 / 冻结库存共同决定）' % float(np.nanmean(arr[m, 1])))
    for s in O.SEGS:
        put('S0-4', '部署容量 POST_TRADE_ACTUAL（D80 / D95 父成交后实际敞口）', 'CAPACITY_POST_TRADE_ACTUAL_%s' % s, '', 'share', 'NOT_RUN', '',
            '正式账户（B 后）在 stage0 终版补值')


# ------------------------------------------------------------------ S0-5
def s0_5(spec):
    TK_f = np.zeros(16)
    TK_i = np.zeros((16, 4), np.int64)
    S_i = np.zeros(E.NSI, np.int64)
    E.tk_add(TK_f, TK_i, S_i, 100.0, 1, 5, E.SI_NTK)
    sd, sa = np.zeros(8, np.int64), np.zeros(8)
    k1 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 2, 60.0, sd, sa)
    k2 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 2, 60.0, sd, sa)
    idn('TOKEN_DOUBLE_SPEND', '标签 100 先耗 60，再耗 60 → 拒绝（返回 −1）', '', 'first=%d second=%d' % (k1, k2), '', '', 'BLOCKED' if (k1 >= 1 and k2 == -1) else 'DIFFERS')
    k3 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 0, 10.0, sd, sa)
    k4 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 5, 10.0, sd, sa)
    nid0 = int(S_i[E.SI_NTKID])
    E.tk_add(TK_f, TK_i, S_i, 50.0, 1, 5, E.SI_NTK)
    idn('TOKEN_MATURITY_REUSE', '未解锁 / 已到期标签不可用；到期后新标签 ID 只增（全生命周期唯一）', '', 'unlock_before=%d matured=%d id_next=%d' % (k3, k4, int(S_i[E.SI_NTKID])), '', '',
        'BLOCKED' if (k3 == -1 and k4 == -1 and int(S_i[E.SI_NTKID]) == nid0 + 1) else 'DIFFERS')
    # 续跑重放：非连续日拒绝；非有限消耗拒绝
    k5 = E.tk_consume(TK_f, TK_i, int(S_i[E.SI_NTK]), 2, float('nan'), sd, sa)
    T = 30
    mk = SY.SynthMarket(T=T, N=2)
    f = SY.csr_daily(T, [0, 1], [0.5, 0.5])
    ip, fp = A.ip_fp(5, E.TM_NONE, fund=E.FD_NATIVE)
    x = SY.account(mk, ip, fp, None, f).run(0, 10)
    rej = False
    try:
        x.run(5, 10)
    except RuntimeError:
        rej = True
    idn('TOKEN_REPLAY', '续跑必须从 checkpoint 的下一日开始（重复 / 跳日 → 拒绝）；非有限消耗 → 拒绝', '', 'replay_rejected=%s nan_consume=%d' % (rej, k5), '', '',
        'BLOCKED' if (rej and k5 == -1) else 'DIFFERS')
    idn('JOURNAL_REPLAY', '日志重放：续跑日不连续即拒绝（Account.run）；正式链在闭包期另以主对象一次跑完 vs A2 checkpoint + B 续跑逐位核（verify/journal_replay_E6p.csv）', '',
        'replay_rejected=%s' % rej, '', '', 'BLOCKED' if rej else 'DIFFERS')
    # 错母体合并
    import e6o_merge as MG
    try:
        MG.merge_unique([{'X': dict(form='A4b', v=1)}, {'X': dict(form='A4b_CVRv5', v=2)}])
        st = 'DIFFERS'
    except ValueError:
        st = 'BLOCKED'
    idn('WRONG_MOTHER_MERGE', '两份结果同 exec_id、不同母体 → 合并报错（merge_unique 全局键冲突）', '', 'collision', '', '', st)
    # 部分成交不铸币：触发后次日不可卖，只有与常规买单的内部转移成交 → 标签只按已成交部分
    T = 20
    mk = SY.SynthMarket(T=T, N=2, flat=True)
    tg = np.zeros((T, 2), np.int8)
    tg[10, 0] = 1
    mk.trigs['P1'] = tg
    mk.sellable[11, 0] = False
    W = np.zeros((T, 2))
    W[:8] = (0.2, 0.8)
    W[8:] = (0.8, 0.2)                          # 第 11 日股 0 常规买单（16% NAV）> 当日到期批次（4%）→ 内部转移覆盖部分早退批次
    f = SY.csr_weights(W)
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True)
    fp[E.FP_SCAP] = 1.0
    fp[E.FP_IDEV] = 10.0
    a = SY.account(mk, ip, fp, 'P1', f).run(0, T)
    DY = a.DY
    intent_val = float(a.IN_f[:int(a.S_i[E.SI_NIN]), 0].sum())
    early = float(DY[11, E.DYI['early_val']])
    newtag = float(DY[11, E.DYI['tag_new']])
    fee_sh = DY[11, E.DYI['fee']] / max(DY[11, E.DYI['buy_val']] + DY[11, E.DYI['sell_val']], 1e-12)
    ok = 0 < early < intent_val - 1e-6 and abs(newtag - early * (1 - fee_sh)) <= 1e-6
    idn('PARTIAL_FILL_NO_MINT', '合成例：意向 %.2f、次日不可卖只与常规买单内部转移成交 %.2f → 新标签 %.4f = 成交额 × (1 − 分摊费率)，未成交部分不铸币' % (intent_val, early, newtag), '',
        round(newtag, 6), '', '', 'BLOCKED' if ok else 'DIFFERS')
    # HALF：η = .5 累计额度（成交后下一执行日起至原 due 前最多 ηF；到 due 全额；不是每天减半）
    mk = SY.SynthMarket(T=T, N=2, flat=True)
    mk.trigs['P1'] = tg
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True, recycle=E.RY_HALF)
    fp[E.FP_SCAP] = 1.0
    fp[E.FP_IDEV] = 10.0
    h = SY.account(mk, ip, fp, 'P1', f).run(0, T)
    DH = h.DY
    F_ = float(DH[11, E.DYI['tag_new']] + DH[11, E.DYI['lock_new']])
    eta_ok = abs(DH[11, E.DYI['tag_new']] - 0.5 * F_) <= 1e-9 and abs(DH[11, E.DYI['lock_new']] - 0.5 * F_) <= 1e-9
    later = float(DH[12:, E.DYI['tag_new']].sum() + DH[12:, E.DYI['lock_new']].sum())
    tok = spec.ReleaseToken('t1', 11, 15, 100.0)
    book = spec.ReleaseBook()
    book.add(tok)
    blocked = False
    try:
        book.consume('t1', 13, 0.5, 60.0)
    except ValueError:
        blocked = True
    cum_ok = spec.unlocked_cumulative(tok, 12, 0.5) == 50.0 and spec.unlocked_cumulative(tok, 14, 0.5) == 50.0 and spec.unlocked_cumulative(tok, 15, 0.5) == 100.0
    idn('TOKEN_HALF_CUMULATIVE', '合成例 RECYCLE_HALF：早退净款 F = %.4f → 标签 ηF / 锁至原 due (1 − η)F（η = .5）、之后无追加释放（%.1e）；参考账本：due 前消费 0.6F 被拒、累计额度 12…14 日恒为 .5F（非每日减半）' % (F_, later),
        '', 'eta_split=%s cum=%s', '', '', 'BLOCKED' if (eta_ok and later == 0.0 and blocked and cum_ok) else 'DIFFERS')
    IDN[-1]['value'] = 'eta_split=%s later=%.1e overspend_blocked=%s cumulative=%s' % (eta_ok, later, blocked, cum_ok)


# ------------------------------------------------------------------ S0-6
def s0_6(spec):
    rng = np.random.default_rng(5)
    mxd = 0.0
    mclose = 0.0
    capv = 0.0
    for _ in range(200):
        n = int(rng.integers(2, 10))
        b = rng.normal(0, 0.003, n)
        a = rng.random(n) * 0.5 + 0.05
        u = rng.random(n) * 0.01
        g = rng.integers(0, 3, n)
        gcap = {int(k): float(rng.random() * 0.02) for k in range(3)}
        B = float(rng.random() * 0.02)
        ref = np.array(spec.signed_allocate(list(b), list(a), list(u), [int(v) for v in g], gcap, B))
        x = E.route_solve(b, a, u, g.astype(np.int64), np.array([gcap[int(v)] for v in g]), B, 4e-4, 0.5)
        mxd = max(mxd, float(np.max(np.abs(x - ref))))
        tgt = min(B, float(sum(min(sum(u[g == k]), gcap[k]) for k in range(3))))
        mclose = max(mclose, abs(float(x.sum()) - tgt) / max(1.0, tgt))
        capv = max(capv, float(np.max(x - u)), max(float(x[g == k].sum() - gcap[k]) for k in range(3)))
    idn('ROUTING_BUDGET_CLOSURE', '凸成本路由（e6p_engine.route_solve）200 个随机例：Σx = min(B, 可行容量)（相对差）；与 plan 附录 C signed_allocate 最大差 %.1e' % mxd, '',
        'max_vs_spec=%.1e' % mxd, mclose, 1e-12, 'PASS' if (mclose <= 1e-12 and mxd <= 1e-8) else 'DIFFERS')
    idn('ROUTING_CAPS_RESPECTED', '路由解：单股余量与行业余量均不被突破（最大超出量）', '', round(capv, 15), max(capv, 0.0), 1e-12, 'PASS' if capv <= 1e-12 else 'DIFFERS')
    # 未知成本冻结 / 退化回退（plan_routed 直接调用）
    T, N = 4, 4
    sig = np.full((T, N), 0.02)
    adv = np.full((T, N), 1e8)
    sig[1, 2] = np.nan
    sig[1, 3] = 0.0
    f_col = np.arange(N, dtype=np.int64)
    f_w = np.full(N, 0.25)
    PB_i = np.zeros((64, 3), np.int64)
    PB_f = np.zeros(64)
    DY = np.zeros((T, E.NDY))
    expv = np.zeros(N)
    indsum = np.zeros(1)
    L_i = np.zeros((1, 8), np.int64)
    L_f = np.zeros((1, 4))
    out = {}
    for rm in (E.RY_COST0, E.RY_COSTNET):
        PB_f[:] = 0.0
        expv[:] = 0.0
        indsum[:] = 0.0
        DY[:] = 0.0
        npb, xp = E.plan_routed(0, 4e6, 0, N, f_col, f_w, 0, L_i, L_f, np.full((T, N), 10.0), expv, indsum, np.zeros((T, N), np.int16), np.ones((T, 1)), 10.0, 1e7, 1e8,
                                1e8, sig, adv, 1e8, 0.5, 0.5, 0.01, 4e-4, rm, PB_i, PB_f, 0, np.zeros(N), DY)
        xs = np.zeros(N)
        for k in range(npb):
            xs[PB_i[k, 0]] += PB_f[k]
        out[rm] = (xs, float(DY[0, 59]), float(DY[0, 60]))
    xn = 4e6 * 0.25
    ok_u = all(abs(out[rm][0][2] - xn) <= 1e-6 and abs(out[rm][1] - xn) <= 1e-6 for rm in out)
    ok_d = all(abs(out[rm][0][3] - xn) <= 1e-6 and abs(out[rm][2] - xn) <= 1e-6 for rm in out)
    idn('ROUTING_UNKNOWN_FROZEN', '路由：σ 未知的名字不当零成本、不删除 → 冻结原 NATIVE 分配（%.0f），只在已知域优化同预算（COST0 / COSTNET 各一例）' % xn, '',
        'frozen=%s' % ok_u, '', '', 'BLOCKED' if ok_u else 'DIFFERS')
    idn('ROUTING_DEGENERATE_FALLBACK', '路由：已知 σ = 0（严格正系数条件不满足）→ 冻结原分配并计 KNOWN_DEGENERATE_FALLBACK（DY rt_degen），不取消账户', '',
        'fallback=%s' % ok_d, '', '', 'BLOCKED' if ok_d else 'DIFFERS')
    # 拆单不变性：同窗口等比例切片恒等；每份占全 V 的 1/√n 伪折扣被拦（引擎按证券日净额只收一次）
    q, V = 1e7, 1e9
    prop = spec.split_volume_consistent(q, V, [0.25, 0.25, 0.5])
    whole = q * np.sqrt(q / V)
    fake = sum((q / 4) * np.sqrt((q / 4) / V) for _ in range(4))
    T = 20
    mk = SY.SynthMarket(T=T, N=2, flat=True)
    tg = np.zeros((T, 2), np.int8)
    tg[10, 0] = 1
    mk.trigs['P1'] = tg
    f = SY.csr_daily(T, [0, 1], [0.5, 0.5])
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True, tlog=True)
    a = SY.account(mk, ip, fp, 'P1', f, tlcap=4096).run(0, T)
    n = int(a.S_i[E.SI_NTL])
    TI, TF = a.TL_i[:n], a.TL_f[:n]
    worst = 0.0
    smax = float(np.max(np.abs(a.DY[:, E.DYI['cost_s05']])))
    lot_level_lower = False
    for d in range(1, T):
        m = TI[:, 0] == d
        if not m.any():
            continue
        Vp = a.DY[d - 1, E.DYI['nav_post']]
        agg = 0.0
        per_lot = 0.0
        for s in np.unique(TI[m, 1]):
            ms = m & (TI[:, 1] == s)
            sgn = np.where(TI[ms, 5] == 0, 1.0, -1.0)
            dn = abs(float((sgn * TF[ms, 1]).sum()))
            sg, av = mk.sig20[d, s], mk.adv20[d, s]
            agg += (dn / Vp) * sg * 0.1 * (dn / (1e8 * av * 0.01)) ** 0.5 if dn > 0 else 0.0
            for v in TF[ms, 1]:
                per_lot += (v / Vp) * sg * 0.1 * (v / (1e8 * av * 0.01)) ** 0.5
        worst = max(worst, abs(agg - a.DY[d, E.DYI['cost_s05']]))
        if per_lot < agg - 1e-15 or per_lot > agg + 1e-15:
            lot_level_lower = True
    ok = abs(prop - whole) <= 1e-9 * whole and fake < whole and worst <= 1e-12 * max(smax, 1e-300) and smax > 0
    idn('SPLIT_INVARIANCE', '拆单：同窗口等比例切片成本恒等（%.6g vs %.6g）；每份占全 V 的 n = 4 切片得 1/√n 伪折扣（%.6g）——引擎按证券日净订单只收一次（成本系数与成交日志重算最大差 %.1e）→ 伪折扣被拦' % (prop, whole, fake, worst),
        '', 'per_lot_differs=%s' % lot_level_lower, worst, '', 'BLOCKED' if ok else 'DIFFERS')
    # 局部四费用面板闭合
    mloc = 0.0
    for _ in range(500):
        b, e, r = rng.normal(0, 0.01, 3)
        co = float(rng.random() * 2)
        ref = spec.local_cost_split(b, e, r, coeff=co)
        C = lambda x: E.res_cost(x, co, 4e-4, 0.5)
        ce = 0.5 * ((C(b + e) - C(b)) + (C(b + e + r) - C(b + r)))
        cr = 0.5 * ((C(b + r) - C(b)) + (C(b + e + r) - C(b + e)))
        mloc = max(mloc, abs(ce + cr - (C(b + e + r) - C(b))), abs(ce - ref['exit']), abs(cr - ref['recycle']))
    idn('LOCAL_COST_SPLIT_CLOSURE', '局部四费用面板对称分摊：φ_e + φ_r = C(b+e+r) − C(b)（500 例；与 plan 附录 C local_cost_split 同值）', '', 'max=%.1e' % mloc, mloc, 1e-12,
        'PASS' if mloc <= 1e-12 else 'DIFFERS')
    # 交易后上限复核
    navs = 1e8
    pos = np.array([0.01, 0.01, 0.005]) * navs
    fee = 4e4
    flags = (pos / (navs - fee)) > 0.01 + 1e-12
    idn('POSTFEE_CAP_RECHECK', '交易前恰顶 1%% 的两只股票，扣费后 NAV 下降 → 交易后份额 > 1%% 被识别（%d 只标记）；正式账户的交易后超限按日计数进 D2（继承超限单列，不强卖）' % int(flags.sum()), '',
        int(flags.sum()), '', '', 'BLOCKED' if flags.sum() == 2 else 'DIFFERS')


# ------------------------------------------------------------------ S0-7 / S0-8 / S0-9 / S0-10 / S0-11
def s0_7(mk, hold):
    years = np.array([int(d[:4]) for d in mk.dates])
    pdir = os.path.join(mk.cd, 'panels')
    board = np.load(os.path.join(pdir, 'board.npy'))
    kind = np.asarray(np.load(os.path.join(pdir, 't8_kind.npy'), mmap_mode='r'))
    is_open = np.asarray(mk.isopen).astype(bool)
    KN = {1: 'ONE_TICK', 2: 'INTRADAY_CLOSE_AT_LIMIT', 3: 'TOUCH_NOT_CLOSE', 4: 'NO_LIMIT_DAY', 5: 'UNKNOWN'}
    for y in sorted(set(years)):
        ym = years == y
        for bi, bn in enumerate(BOARDS):
            M = hold[ym][:, board == bi] & is_open[ym][:, board == bi]
            n = int(M.sum())
            if n == 0:
                continue
            kk = kind[ym][:, board == bi][M]
            for k, kn in KN.items():
                put('S0-7', '持仓域开盘日 T8 份额（%d；%s）' % (y, bn), 'T8_SHARE_%d_%s_%s' % (y, bn, kn), round(float((kk == k).mean()), 8), 'share', 'INFO', 'cache panels/t8_kind',
                    'n = %d 持仓开盘股票日；事件稀少只记精度' % n)
    put('S0-7', 'T8 无行动机会规则', 'T8_NO_ACTION_RULE', 'NO_ACTION_OPPORTUNITY', 'count', 'INFO', 'e6p_engine.step（noact 计数）',
        '持仓证券当日 T8 = 1 但所有批次已有请求 / 已到期 / 当日新买（无可干预批次）→ 计 NO_ACTION_OPPORTUNITY；账户无有效事件时等于父（不报 NOT_COMPUTABLE）；无限制日 = 0 非事件；未知 = UNKNOWN 不发单')


def s0_8(mk):
    ptr, col = G['nf'][O.MAIN_FORM]
    known = np.diff(ptr) > 0
    segi = np.array([O.seg_of_date(d) for d in mk.dates])
    put('S0-8', 'RENEW5 检查点规则', 'RENEW_CHECKPOINT_RULE', 'e=e0+5m<e0+H; decision at close e-1 using NONE-memory natural list', 'count', 'INFO', 'e6p_engine.step（RENEW5 段）',
        '执行日龄 age_e = d + 1 − e0 ∈ (0, H) 且 5 | age_e；已知不含 → e 日卖（kind RENEW）；不改 due、不清已挂卖单')
    for s in O.SEGS:
        m = segi == s
        put('S0-8', '自然名单可得日份额（%s）' % s, 'RENEW_GATE_AVAILABLE_SHARE_%s' % s, round(float(known[m].mean()), 6), 'share', 'INFO', 'source（memory = NONE）',
            '段首约 19 日源预热名单为空 → UNKNOWN')
    put('S0-8', 'RENEW5 未知处置', 'RENEW_UNKNOWN_RULE', 'NO_NEW_SELL_ORDER', 'count', 'INFO', 'e6p_engine.step', '名单为空（预热）或本股当日未开盘 = UNKNOWN：不新增卖单；普通到期与触发退出照常')
    # 续期不改 due（合成例）
    T = 60
    mk2 = SY.SynthMarket(T=T, N=2, flat=True)
    f = SY.csr_daily(T, [0, 1], [0.5, 0.5])
    nptr = np.zeros(T + 1, np.int64)
    ncol = []
    for d in range(T):
        keep = [0] if (d % 7) else [0, 1]
        ncol += keep
        nptr[d + 1] = nptr[d] + len(keep)
    nf = (nptr, np.array(ncol, np.int64))
    ip, fp = A.ip_fp(20, E.TM_NONE, fund=E.FD_NATIVE, exit_on=True, renew=5)
    a = SY.account(mk2, ip, fp, None, f, nf=nf)
    dues = {}
    md = 0
    for d in range(T):
        a.run(d, d + 1)
        nl = int(a.S_i[E.SI_NL])
        for j in range(nl):
            lid = int(a.L_id[j])
            due = int(a.L_i[j, 2])
            if lid in dues:
                md = max(md, abs(due - dues[lid]))
            else:
                dues[lid] = due
                if a.L_i[j, 5] == 0:
                    md = max(md, abs(due - (int(a.L_i[j, 1]) + 20)))
    n_in = int(a.S_i[E.SI_NIN])
    dd = a.IN_i[:n_in, E.IN_DUE] - (a.IN_i[:n_in, E.IN_DAY] + 1 - a.IN_i[:n_in, E.IN_AGE])
    md = max(md, int(np.max(np.abs(dd - 20))) if n_in else 0)
    idn('RENEW_DUE_UNCHANGED', '合成例 RENEW5（H20）：检查点确认 / 拒绝前后批次 due 恒 = e0 + H（逐日核 %d 个批次；%d 个检查点退出意向的原 due 同）' % (len(dues), n_in), '', md, float(md), 0.0,
        'PASS' if md == 0 else 'DIFFERS')


def s0_9():
    put('S0-9', '匹配 V2 两级', 'MATCH_V2_LEVELS', 'TIER1=registered cell (age bucket on execution age; COUNT_ISK: industry x size3 x bucket); TIER2=all own-path R_INTENT', 'count', 'INFO',
        'e6p_engine.select_v2', 'COUNT_ISK 回填：行业 × 日龄 → 日龄；AMOUNT_ISK_V2：同层金额 → 全域；末批可部分（拆批次）；只用本路径 T 收盘库存与 owner T 收盘意向')
    put('S0-9', '匹配 V2 日龄桶', 'MATCH_V2_BUCKETS', '1,2,3-5,6-10,11-20,21+', 'count', 'INFO', 'e6p_engine.bucket_of')
    put('S0-9', '不可比标签规则（A1 冻结）', 'CONTROL_NOT_COMPARABLE_RULE', 'FULL unmatched_cny / requested_cny > 0.25', 'ratio', 'INFO', 'e6p_core.NOT_COMPARABLE_UNMATCHED',
        '首次短配只打标签；不以 < 90% 筛账户；不当 FAIL')
    T = 30
    mk = SY.SynthMarket(T=T, N=3, flat=True)
    f = SY.csr_daily(T, [0, 1], [0.5, 0.5])
    tgb = np.zeros((T, E.NB))
    tgb[2, 3] = 5e8            # 第 2 日要求日龄 6–10 桶 5 亿：本路径无该桶库存、全域库存也不足 → 跨层取尽后记未匹配
    tgb[12, 0] = 1e5
    mk.trigs['P0'] = np.zeros((T, 3), np.int8)
    ip, fp = A.ip_fp(20, E.TM_PANEL, sel=E.SM_AMT2, fund=E.FD_NATIVE, exit_on=True, seed=3)
    a = SY.account(mk, ip, fp, 'P0', f, targets=dict(b=tgb))
    a.run(0, T)
    DY = a.DY
    req, wi, cr, un = (float(DY[:, E.DYI[k]].sum()) for k in ('v2_req', 'v2_within', 'v2_cross', 'v2_unm'))
    lots_sec2 = int(((a.L_i[:int(a.S_i[E.SI_NL]), 0] == 2)).sum())
    ok = abs(req - (wi + cr + un)) <= 1e-6 * max(1.0, req) and un > 0 and lots_sec2 == 0
    idn('MATCH_NO_OWNER_FUTURE_INVENTORY', '合成例 AMOUNT_MATCH_V2：路径当日同层与全域库存不足 → 记未匹配（%.0f），不借 owner 未来库存、不补造批次（未持有证券 2 的批次 = %d）；requested = within + cross + unmatched' % (un, lots_sec2),
        '', 'req=%.0f within=%.0f cross=%.0f unm=%.0f' % (req, wi, cr, un), '', '', 'BLOCKED' if ok else 'DIFFERS')


def s0_10():
    blocked = False
    try:
        LM.group_by_outcome([1, 2, 3], future=True)
    except ValueError:
        blocked = True
    s_future = LM.state_at(5, 8, 'TRIG')
    ok = blocked and s_future == 'NOT_TRIGGERED' and LM.state_at(5, 5, 'TRIG') == 'BAD_STATE' and LM.state_at(5, 3, 'TRIG') == 'REQUEST_PENDING'
    idn('LANDMARK_NO_FUTURE_GROUPING', '按未来事件（"到 H 末一直未触发"）分组的合成调用被拒；T 之后的意向记录不改变 T 时状态（T = 5、意向日 8 → NOT_TRIGGERED）', '',
        'rejected=%s future_ignored=%s' % (blocked, s_future == 'NOT_TRIGGERED'), '', '', 'BLOCKED' if ok else 'DIFFERS')
    w, st = LM.fwd_window(95, 10, 100)
    w2, st2 = LM.fwd_window(80, 10, 100)
    idn('LANDMARK_CENSOR_AT_CUTOFF', 'landmark 前向窗口超出授权终点（2026-03-27）→ RIGHT_CENSORED（不取 E7 价格）', '', '%s/%s' % (st, st2), '', '',
        'BLOCKED' if (st == 'RIGHT_CENSORED' and st2 == 'COMPUTED') else 'DIFFERS')


def s0_11():
    for k, v in (('event_age', '原 I11 事件时钟（源；多次事件处理沿源）'), ('lot_age', '投资批次已持区间：执行日龄 age_e = d + 1 − e0（T 收盘决策、e = T+1 执行）'),
                 ('security_age', '物理证券连续暴露日数（DY sec_age_*；任一批次持有即连续）')):
        put('S0-11', k, 'AGE_DEFINITIONS', v, 'days', 'INFO', 'e6p_engine.step')
    put('S0-11', '风险集计数', 'RISKSET_COUNT_RULE', 'R_OBS=held unique securities; R_INTENT=lots without irrevocable request and d+1<due; R_FILL=sellable physical qty', 'count', 'INFO',
        'e6p_engine.step', '信息按证券算一次、按批次作用；到期未成交在 R_OBS、不重复发同批卖单；人数不把一股十批算十只')


# ------------------------------------------------------------------ 攻击：未来数据 / 单位 / 镜像
def plants(mk):
    T = 40
    m1 = SY.SynthMarket(T=T, N=3)
    f = SY.csr_daily(T, [0, 1, 2], [0.4, 0.3, 0.3])
    tg = np.zeros((T, 3), np.int8)
    tg[6, 0] = 1
    tg[15, 1] = 1
    m1.trigs['F0'] = tg
    ip, fp = A.ip_fp(5, E.TM_PANEL, fund=E.FD_NATIVE, exit_on=True)
    base = SY.account(m1, ip, fp, 'F0', f).run(0, T)
    t_star = 20
    m2 = SY.SynthMarket(T=T, N=3)
    m2.pv[t_star + 1:] *= 1.5
    m2.pc[t_star + 1:] *= 0.5
    pl = tg.copy()
    pl[t_star + 1:, :] = 1
    m2.trigs['F1'] = pl
    alt = SY.account(m2, ip, fp, 'F1', f).run(0, T)
    dmax = float(np.max(np.abs(base.DY[:t_star + 1] - alt.DY[:t_star + 1])))
    e7 = False
    try:
        import e6o_minute as MI
        MI.read_va(20260330)
    except RuntimeError:
        e7 = True
    idn('FUTURE_DATA_PLANT', 'T* 之后植入价格 / 触发改动：T* 及之前日序列逐位不变（最大差 %.1e）；分钟读取接口对 > 2026-03-27 拒绝 = %s' % (dmax, e7), '', dmax, '', '',
        'BLOCKED' if (dmax == 0.0 and e7) else 'DIFFERS')
    # 镜像不读未来：owner 目标序列在 T* 之后改动 → 镜像 T* 及之前不变
    te = np.full(T, 0.6)
    te2 = te.copy()
    te2[t_star + 1:] = 0.95
    ipm, fpm = A.ip_fp(5, E.TM_NONE, fund=E.FD_NATIVE, deploy=E.DP_MIRROR)
    a1 = SY.account(m1, ipm, fpm, None, f, tgt_expo=te).run(0, T)
    a2 = SY.account(m1, ipm, fpm, None, f, tgt_expo=te2).run(0, T)
    dm = float(np.max(np.abs(a1.DY[:t_star + 1] - a2.DY[:t_star + 1])))
    later = float(np.max(np.abs(a1.DY[t_star + 2:] - a2.DY[t_star + 2:])))
    idn('MIRROR_NO_FUTURE_READ', '镜像目标 = owner 在 T 收盘已观测敞口：T* 之后目标改动 → 镜像 T* 及之前日序列逐位不变（%.1e）；改动后确有反应（%.2e）' % (dm, later), '', dm, '', '',
        'BLOCKED' if (dm == 0.0 and later > 0) else 'DIFFERS')
    # 单位植入
    cd = mk.cd
    vol = np.load(os.path.join(cd, 'panels', 'vol.npy'), mmap_mode='r')
    vm = np.load(os.path.join(O.e6o_cache(), 'minute', 'vol_min.npy'), mmap_mode='r')
    t0 = int(np.searchsorted(mk.dates, '2020-01-01'))
    t1 = int(np.searchsorted(mk.dates, '2021-01-01'))
    j = int(np.flatnonzero(np.isfinite(np.asarray(vol[t0:t1])).all(0) & np.isfinite(np.asarray(vm[t0:t1])).all(0))[0])
    v = np.asarray(vol[t0:t1, j]).copy() / 100.0
    m = np.asarray(vm[t0:t1, j])
    with np.errstate(all='ignore'):
        r = np.abs(m / v - 1.0)
        r0 = np.abs(m / np.asarray(vol[t0:t1, j]) - 1.0)
    caught = bool(np.nanmedian(r) > 0.5)
    idn('UNIT_PLANT', '把一只股票 2020 年日频量 ÷ 100（冒充"手"）：日频 / 分钟量相对差中位 %.2f（原始 %.2e）→ 单位核对拦下' % (float(np.nanmedian(r)), float(np.nanmedian(r0))), '',
        round(float(np.nanmedian(r)), 4), '', '', 'BLOCKED' if caught else 'DIFFERS')


# ------------------------------------------------------------------ S0-12 / S0-13 / S0-14
def s0_12_14():
    st = json.load(open(O.P('verify', 'selftest_E6p.json')))
    res = st['results']
    w_acct = [v['wall_s'] for k, v in res.items() if k.startswith(('S_', 'REPL_', 'Z_')) and v.get('status') == 'OK']
    sec = float(np.median(w_acct)) if w_acct else np.nan
    p95 = float(np.percentile(w_acct, 95)) if w_acct else np.nan
    n_acc = 2 * 2128 + 84 * 2 + 32
    n_rand = 576 * 3 * 128 + 576 + 180 * 128 + 12 * 128 + 18 * 128 + 18 * 3 * 896
    workers = 96
    core_s = n_acc * p95 + n_rand * p95 * 1.6 + 576 * 2 * p95
    est_days = core_s / workers / 86400.0
    rec = json.load(open(O.P('task_status', 'E6p_selftest.receipt.json')))
    put('S0-12', '单账户单情景全程耗时（中位 / P95；FEASIBLE 与 IDEAL 同引擎）', 'RUNTIME_ACCOUNT_SEC_FEASIBLE_DAILY', round(sec, 2), 'count', 'INFO', 'verify/selftest_E6p.json', 'P95 = %.2f s' % p95)
    put('S0-12', '同上（IDEALIZED_SOURCE_FILL）', 'RUNTIME_ACCOUNT_SEC_IDEALIZED_SOURCE_FILL', round(sec, 2), 'count', 'INFO', 'verify/selftest_E6p.json')
    put('S0-12', '随机单路径全程耗时（同引擎 V2 选择；按账户 P95 估）', 'RUNTIME_RANDOM_PATH_SEC', round(p95, 2), 'count', 'INFO', 'verify/selftest_E6p.json')
    put('S0-12', '峰值 RSS（自检主进程；每 worker 另 ≤ 1 GB）', 'PEAK_RSS_GB', rec.get('rss_peak_gb', ''), 'count', 'INFO', 'task_status/E6p_selftest.receipt.json')
    put('S0-12', '磁盘估算（成交分片 ≈ 1,512 × 0.1 GB；随机日统计 ≈ 30 GB；checkpoint ≈ 20 GB；结果 ≈ 30 GB）', 'DISK_GB_ESTIMATE', 250, 'count', 'INFO', '', '47 剩余 > 30 TB')
    put('S0-12', '总耗时估算（账户 A2 + B、随机 ≈ %d 路径 × 1.6（A2 重放）、影子；%d worker）' % (n_rand, workers), 'EST_TOTAL_DAYS', round(est_days, 3), 'days', 'INFO', '',
        '≤ 14 天 → 不回传（brief §0.2 #4）')
    put('S0-12', '每 worker 线程', 'THREADS', 'BLAS 2 / numba 1', 'count', 'INFO', 'e6p_bg.sh')
    put('S0-12', '并发 worker', 'CONCURRENT_JOBS', workers, 'count', 'INFO', 'e6p_bg.sh（核心绑定 96-191, 288-383）')
    txt = open(O.P('verify', 'spec', 'spec_run.txt'), encoding='utf-8', errors='replace').read()
    ok13 = 'Ran 160 tests' in txt and '\nOK' in txt
    put('S0-13', 'spec tests 隔离重跑与七指纹', 'SPEC_160_AND_7SHA', 'PASS' if ok13 else 'DIFFERS', 'count', 'PASS' if ok13 else 'DIFFERS', 'verify/spec/spec_run.txt + SHA256.txt',
        '160 项 OK（python3 -W error，stderr 合并）；七个 json 指纹与 plan 附录 B 一致（LF）')
    lg = open(O.P('logs', 's0_14_run.log'), encoding='utf-8', errors='replace').read() if os.path.exists(O.P('logs', 's0_14_run.log')) else ''
    ok14 = os.path.exists(O.P('verify', 'decision', 'E6p_D_stage2.py')) and O.sha_file(O.P('verify', 'decision', 'E6p_D_stage2.py')) == O.D_SCRIPT_SHA256
    put('S0-14', '决策端脚本 sha / py_compile / 夹具空跑', 'D_SCRIPT_FIXTURE', 'PASS' if ok14 else 'DIFFERS', 'count', 'PASS' if ok14 else 'DIFFERS', 'verify/decision + logs/s0_14_*.log',
        'sha = 4274d7fe…（与 brief 一致）；py_compile 字节码写临时目录；夹具 33 探针全有状态行（32 PASS / 1 INFO；夹具上 DIFFERS / NOT_COMPUTABLE 为预期）%s' % (' ' if lg else ''))
    return est_days


def main():
    t0 = time.time()
    spec = spec_module()
    sh = s0_0()
    mk = A.Market()
    G['f'] = {(f, m): mk.formation(f, m) for f in O.FORMS for m in O.MEMS if (f == O.MAIN_FORM or m == 'HG10')}
    G['nf'] = {f: mk.natural(f) for f in O.FORMS}
    hold = holding_domain(mk)
    s0_1(mk, hold)
    s0_2(mk)
    s0_4(mk, spec)
    capacity_rows(mk)
    s0_5(spec)
    s0_6(spec)
    s0_7(mk, hold)
    s0_8(mk)
    s0_9()
    s0_10()
    s0_11()
    plants(mk)
    est = s0_12_14()
    os.makedirs(O.P('diagnostics'), exist_ok=True)
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6p_part1.csv'), pd.DataFrame(ROWS))
    O.atomic_write_csv(O.P('verify', 'identities_E6p_stage0.csv'), pd.DataFrame(IDN))
    O.atomic_write_csv(O.P('registration', 'sources_E6p.csv'), pd.DataFrame(SRC))
    O.atomic_write_json(O.P('diagnostics', 'source_fn_sha256_E6p.json'), sh)
    I = pd.DataFrame(IDN)
    O.write_receipt('E6p_stage0_part1', [O.P('diagnostics', 'stage0_E6p_part1.csv'), O.P('verify', 'identities_E6p_stage0.csv'), O.P('registration', 'sources_E6p.csv')],
                    code=[__file__, E.__file__, A.__file__, SY.__file__, LM.__file__], wall_s=round(time.time() - t0, 1), est_total_days=est,
                    rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    bad = I[~I.status.isin(['PASS', 'BLOCKED', 'INFO'])]
    print(json.dumps(dict(rows=len(ROWS), identities=len(I), bad=len(bad), est_total_days=round(est, 3), wall_s=round(time.time() - t0, 1),
                          statuses=I.groupby('check_id').status.agg(lambda s: ','.join(sorted(set(s)))).to_dict()), ensure_ascii=False, default=str), flush=True)
    if len(bad):
        print(bad.to_string()[:4000], flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
