#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 共用核心: 键集合与血缘守卫 / 描述符 ID 与真实路径去重 / 缓存键 /
   三个具名 selector / H2 输入变换 / 固定展示组。

设计约定 (brief §2 §3 §13):
  * 新代码一律 e6g_*.py; 四地基 + 七 e6e + 十九 e6f 只读不改。
  * 描述符 ID 在【全部默认】时与 E6f cfg_id 逐字相同 -> OLD 域可逐位对表。
  * 方向统一 bad_pct (越高越该剔); 反向走【真实反序】而不是 1-pct (奇偶/并列另测)。
  * 40 键血缘守卫: 表达式 DAG 标签 + 段/label_end/用途三重检查; 祖父豁免只认
    "上一轮已显式登记过的键" (intraday_cvr_1d), 同公式的【新】登记一律继承 NEW40 血缘。
"""
import os, re, sys, math, json, hashlib, warnings
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import comprehensive_factor_diagnosis as C

VERSION = 'E6g-v1'
RES = '/mnt/sda2/lichenchen/results/20260911_1140_E6g_structure_layer'
E6F_DIR = '/mnt/sda2/lichenchen/results/20260910_0814_E6f_construction_selection_implementation'
E6E_DIR = F.E6E_DIR
E6C_DIR = F.E6C_DIR
FROZEN_END = F.FROZEN_END                      # 20260327
SEGMENTS = ['2010-2014', '2015-2018', '2019-2023', '2024-2026']
DERIV_SEGS = ('2010-2014', '2015-2018')        # 40 键唯一允许段
NEW40_LABEL_END = '2018-12-31'                 # 40 键任何标签/估值端点上界

# ============================================================
# 1. 键集合 (全部由源码生成, 不手抄)
# ============================================================
CONFIRMED30 = list(C.CONFIRMED_FEATURE_NAMES)                     # 30
SPEC34 = [s['name'] for s in C.get_default_factor_specs()]        # 34 = 4 自定义 + 30
CUSTOM4 = [n for n in SPEC34 if n not in CONFIRMED30]             # 4
U34 = list(SPEC34)
U35 = U34 + [K.FCVR1]                                             # + intraday_cvr_1d (E6e 研究 spec)

# NEW40 = proposal 附录 A 的 40 个名字。阶段 0 已核: 恰等于
#   set(calc_all_daily_features) - set(CONFIRMED_FEATURE_NAMES), 无重叠、无遗漏。
NEW40 = [
    'CLV', 'CVR', 'CVR_5d', 'shadow_asymmetry', 'tug_of_war', 'intraday_ret', 'overnight_ret',
    'gap_zscore_20d', 'gap_abs_zscore_20d', 'gap_percentile_60d', 'gap_vs_sector',
    'gap_rank_in_sector', 'consecutive_gap_same_direction', 'gap_direction_consistency_5d',
    'gap_trend_5d', 'gap_volume_ratio', 'daynight_divergence', 'agreement_count_5d',
    'overnight_ret_cross_sectional_rank', 'overnight_ret_trend', 'intraday_ret_consistency_5d',
    'positive_day_ratio_5d', 'volume_ratio_1d', 'volume_ratio_3d', 'volume_ratio_5d',
    'volume_zscore_60d', 'volume_accel_3d', 'volume_trend_10d', 'volume_momentum_divergence',
    'volume_regime_break', 'turnover_5d', 'turnover_rank_market', 'amount_ratio_1d',
    'amount_concentration_5d', 'amihud_daily', 'amihud_ratio_5d_20d', 'inside_bar_freq_20d',
    'volume_rank_market', 'CMF_20d', 'mcap_rank',
]
DIAGNOSTIC_ONLY = {'mcap_rank'}                        # 中性化目标, 只作诊断行
MARKET_WIDE_PLACEHOLDER = {'gap_vs_sector', 'gap_rank_in_sector',
                           'overnight_ret_cross_sectional_rank',
                           'turnover_rank_market', 'volume_rank_market', 'mcap_rank'}
SIGNAL_TRUNCATED = {'CMF_20d', 'cum_return_5d', 'intraday_ret'}   # I11 三成分

# H1 的第四腿/换腿候选集 (由注册表生成, 不手数)
J_KTC = [k for k in U35 if k not in (K.FK, K.FT, K.FC)]           # 期望 32
J_KT = [k for k in U35 if k not in (K.FK, K.FT)]                  # 期望 33 (含 C)

# ---- 公式别名 (同一数学式的不同登记名) ----
CANON_FORMULA = {
    'CVR': 'close_over_vwap_minus_1',
    K.FCVR1: 'close_over_vwap_minus_1',        # intraday_cvr_1d, 数学恒等、浮点不必逐位
}
# 祖父豁免: 上一轮 (E6e/E6f) 已显式登记并全段产出过收益的键。
# 只豁免这【一个登记名】; 同公式的新登记名不继承豁免 (见 guard 攻击测试 a)。
GRANDFATHERED = {K.FCVR1}

_NEW40_SET = set(NEW40)

# 显示别名 -> 真实源键。任何新登记名必须在这里落一条 (或 spec 直接带 key),
# 否则 build_raw_g 因 feats 里没有该名字而 KeyError -> 无法静默绕过血缘。
ALIAS_OF = {}


def register_alias(new_name, source_key):
    """登记一个显示别名。血缘一律按 source_key 解析 (攻击测试 a: 重命名新键)。"""
    if source_key not in _NEW40_SET and source_key not in U35:
        raise ValueError('别名源键 %r 未注册' % (source_key,))
    ALIAS_OF[new_name] = source_key
    return new_name


def resolve_key(k):
    """把任意登记名解析到源键 (跟随别名链, 防环)。"""
    seen = set()
    while k in ALIAS_OF and k not in seen:
        seen.add(k)
        k = ALIAS_OF[k]
    return k


def key_class(k):
    if k in GRANDFATHERED:
        return 'U35_grandfathered'
    if k in _NEW40_SET:
        return 'NEW40'
    if k in U34:
        return 'U34'
    return 'UNREGISTERED'


def has_new40_blood(k):
    """登记名 k 是否带 NEW40 血缘。祖父豁免只对 GRANDFATHERED 里的登记名生效;
       任何【新】名字若解析到 NEW40 的公式, 一律带血缘 (防重命名绕过)。"""
    if k in GRANDFATHERED:
        return False
    r = resolve_key(k)
    if r in _NEW40_SET:
        return True
    cf = CANON_FORMULA.get(r)
    if cf is not None and any(CANON_FORMULA.get(n) == cf for n in _NEW40_SET):
        return True
    return False


KNOWN_ROLES = ('T', 'C', 'Cf', 'B', 'K', 'F')


def assert_registered_spec(sp, where=''):
    """任何进入计算的规格必须是已知角色; F 角色的 key 必须是已登记名。
       挡住"自己写公式重造一个新键、绕开 F 角色"的路径。"""
    r = sp.get('role')
    if r not in KNOWN_ROLES:
        raise GuardViolation('[40 键守卫] 未登记角色 %r @ %s' % (r, where))
    if r == 'F':
        k = resolve_key(sp['key'])
        if k not in _NEW40_SET and k not in U35:
            raise GuardViolation('[40 键守卫] 未登记键 %r @ %s' % (sp['key'], where))
    return True


# ============================================================
# 2. 血缘 DAG 与守卫 (硬约束 2)
# ============================================================
class Lin(object):
    """表达式 DAG 节点上的血缘标签: 用到的【登记键名】集合。"""
    __slots__ = ('keys',)

    def __init__(self, keys=()):
        self.keys = frozenset(keys)

    @staticmethod
    def of(*keys):
        return Lin(keys)

    def __or__(self, other):
        return Lin(self.keys | other.keys)

    def merge(self, *others):
        s = set(self.keys)
        for o in others:
            s |= o.keys
        return Lin(s)

    @property
    def new40_keys(self):
        return sorted(k for k in self.keys if has_new40_blood(k))

    @property
    def new40(self):
        return len(self.new40_keys) > 0

    def __repr__(self):
        return 'Lin(%s)' % ','.join(sorted(self.keys))

    def tag(self):
        return '|'.join(sorted(self.keys))


class GuardViolation(RuntimeError):
    pass


# 带 NEW40 血缘时受限的用途 (T0-74 / K 只允许推导段, 产物不进 H/B)
USE_TYPES = ('label', 'shape', 'holding', 'trade', 'cost', 'outcome_cluster', 'selection')
_GUARD_LOG = []


def guard(lin, use_type, segment=None, label_end=None, where='', strict=True):
    """40 键守卫。任何带 NEW40 血缘的收益/持仓/交易/成本/标签/学习产物:
         - 只允许 2010-2014 / 2015-2018
         - label_end 与任何估值端点 <= 2018-12-31
       不带血缘的一律放行。strict=True 违规即抛; strict=False 返回 (ok, reason)。"""
    if use_type not in USE_TYPES:
        raise ValueError('未知 use_type %r' % (use_type,))
    reason = None
    if lin.new40:
        if segment is None or segment not in DERIV_SEGS:
            reason = ('NEW40 血缘 %s 用于 use_type=%s, 段=%r 不在推导段 %s'
                      % (lin.new40_keys, use_type, segment, list(DERIV_SEGS)))
        elif label_end is not None and str(label_end)[:10] > NEW40_LABEL_END:
            reason = ('NEW40 血缘 %s 的 label_end=%s > %s'
                      % (lin.new40_keys, label_end, NEW40_LABEL_END))
    rec = dict(where=where, use_type=use_type, segment=segment, label_end=str(label_end),
               new40=lin.new40_keys, passed=reason is None, reason=reason)
    _GUARD_LOG.append(rec)
    if reason is not None and strict:
        raise GuardViolation('[40 键守卫] %s @ %s' % (reason, where))
    return True if strict else (reason is None, reason)


def guard_log():
    return list(_GUARD_LOG)


def learned_lineage(*lins):
    """学习产物 (树 / kmeans / 拟合权重) 的血缘 = 所有输入坐标血缘之并。"""
    out = Lin()
    for l in lins:
        out = out | l
    return out


# ============================================================
# 3. 规格扩展: role 'F' = 直接取 feats[key]
# ============================================================
SPEC_FUNCS = {s['name']: s for s in C.get_default_factor_specs()}
# 源 spec 声明的方向 (只有四个自定义 spec 有实义; 30 个 CONFIRMED 走 make_feature_func,
# 源码注释写明"不预设方向"). 本轮两个方向都跑, 这一列只作解读标注。
SPEC_DIRECTION = {n: s.get('direction') for n, s in SPEC_FUNCS.items()}


def specF(key, w=1):
    """任意注册键的规格。w>1 = 因果 MA(w) (B2 的 MA3/MA5 用)。"""
    return dict(role='F', key=key, w=int(w), est='MA', eps=0.0, base='diff', adj=False)


def fidg(sp):
    """规格 ID; 非 F 角色逐字回落到 e6f_core.fid (保持 E6f cfg_id 不变)。"""
    if sp.get('role') != 'F':
        return F.fid(sp)
    w = int(sp['w'])
    return 'F:%s' % sp['key'] if w == 1 else 'F:%s@MA%d' % (sp['key'], w)


def lin_of_spec(sp):
    """血缘来自【规格】而不是显示名: 换个名字挂同一个 key, 血缘不变。"""
    if sp.get('role') == 'F':
        return Lin.of(resolve_key(sp['key']))
    return Lin.of(F.ROLE_CANON[sp['role']])


def build_raw_g(S, sp):
    """原始因子帧 (全市场宽度, 未入池)。F 角色取 feats; 其余走 e6f build_raw(S.wdata)。"""
    if sp.get('role') != 'F':
        return F.build_raw(S.wdata, sp)
    key = resolve_key(sp['key'])
    src = S.wfeats if getattr(S, 'wfeats', None) is not None else S.feats
    if key == K.FCVR1:                                # E6e 研究 spec, feats 里没有
        raw = (S.wdata['close'] / S.wdata['vwap']).replace([np.inf, -np.inf], np.nan) - 1
    elif key in src:
        raw = src[key]
    elif key in SPEC_FUNCS:
        # U34 的四个自定义 spec (reversal_skip1 / parkinson_vol / abn_turnover / cmf_change_neg)
        # 不在 calc_all_daily_features 的 70 键里, 按源 spec 的 func(data, features, industry)
        # 现算 —— 与 e6e_core 走同一条路径。
        ind = getattr(S, 'industry', None)
        cl = S.wdata['close']
        if ind is not None and not ind.index.equals(cl.index):
            ind = ind.reindex(index=cl.index, columns=cl.columns)
        raw = SPEC_FUNCS[key]['func'](S.wdata, src, ind)
    else:
        raise KeyError('注册键 %r 既不在 feats (%d 键) 也不是自定义 spec' % (key, len(src)))
    w = int(sp['w'])
    if w > 1:
        raw = raw.rolling(w, min_periods=F.mp(w)).mean()
    return raw.astype(float)


# ============================================================
# 4. H2 输入变换 (在【个股完整已允许历史】上做, 不在池内截断后 rolling)
# ============================================================
TRANSFORMS = ('identity', 'delta5', 'delta20', 'zprior60')


def tf_apply(raw, kind, zwin=60, zmin=30):
    if kind == 'identity':
        return raw
    if kind == 'delta5':
        return raw - raw.shift(5)
    if kind == 'delta20':
        return raw - raw.shift(20)
    if kind == 'zprior60':
        prior = raw.shift(1)
        m = prior.rolling(zwin, min_periods=zmin).mean()
        s = prior.rolling(zwin, min_periods=zmin).std(ddof=1)
        s = s.where(s > 0)                               # std=0 -> NaN (历史常数无定义)
        return (raw - m) / s
    raise ValueError(kind)


# ============================================================
# 5. pct 表 (方向走真实反序)
# ============================================================
def agg_dense(Ps, how):
    """多腿聚合 (bad_pct 语义: 越大越该剔)。

    mean / median / worst(max) 与 m-of-n 自然投票都是同一族的序统计量:
      vote_m  = 升序第 m 个 -> "至少 m 条腿说它好" 的单调代理
      worst   = 升序最后一个 = n-of-n
      median  = 中间两个的均值 (偶数腿); 四腿时与 trimmed_mean 同 (已对锚)
    域规则与 combine_dense(complete=True) 一致: 任一腿当日无值即整格无值。"""
    A = np.stack(Ps, axis=0)
    n = A.shape[0]
    bad = np.isnan(A).any(axis=0)
    with np.errstate(invalid='ignore'), warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        if how == 'mean':
            out = np.nanmean(A, axis=0)
        elif how == 'median':
            out = np.nanmedian(A, axis=0)
        elif how in ('worst', 'max'):
            out = np.nanmax(A, axis=0)
        elif how.startswith('vote'):
            m = int(how[4])
            if not 1 <= m <= n:
                raise ValueError('vote%d 与 %d 条腿不匹配' % (m, n))
            out = np.sort(A, axis=0)[m - 1]
        else:
            raise ValueError(how)
    # _day_ok_g 是 (T,), out 是 (T, Nc): np.where 按【最后一个轴】对齐, 必须显式加轴。
    # (与 e6f combine_dense 的 _day_ok(A)[:, None] 同一处置; E6f 块 D 曾在这里出过错)
    out = np.where(_day_ok_g(A)[:, None], out, np.nan)
    return np.where(bad, np.nan, out)


def _day_ok_g(A):
    """沿 e6f combine 的日期交集语义: 任一腿当日整行无值 -> 当日整体无值。"""
    return (~np.isnan(A)).any(axis=2).all(axis=0)


def pct_dense_dir(cache, dates, colpos, Nc, direction='hi'):
    """direction='hi': 高值 = 坏 (bad_pct = 原序 pct);
       direction='lo': 低值 = 坏 -> 【真实反序】 (-s).rank(pct=True), 不用 1-pct。"""
    out = np.full((len(dates), Nc), np.nan)
    for i, d in enumerate(dates):
        s = cache.get(d)
        if s is None:
            continue
        p = s.rank(pct=True) if direction == 'hi' else (-s).rank(pct=True)
        idx = np.asarray(s.index)
        pos = np.fromiter((colpos.get(x, -1) for x in idx), int, len(idx))
        v = pos >= 0
        out[i, pos[v]] = p.to_numpy()[v]
    return out


# 一张 (T, Nc) float64 pct 表约 1214 x 5000 x 8B ~ 48 MB。机器 2 TB, 内存不是约束;
# 真正的约束是 B2 那种 32 个 J x 2 方向 x {raw, MA3, MA5} = 192 张表的访问模式,
# FIFO 会把 K/T/C 挤出去反复重算 -> 用 LRU (命中即移到末尾)。
_PCT_CACHE_LIMIT = 256


def get_pct_g(S, sp, mode='NS', direction='hi', transform='identity'):
    """(T, Nc) bad_pct 表, 按 (规格, 中性化, 方向, 变换) LRU 缓存在 S 上。"""
    key = (fidg(sp), mode, direction, transform)
    st = getattr(S, '_g', None)
    if st is None:
        st = S._g = {}
    if key in st:
        st[key] = st.pop(key)                 # LRU: 命中移到末尾
        return st[key][0]
    raw = build_raw_g(S, sp)
    raw = tf_apply(raw, transform)
    if raw.shape != S.pool0.shape or not raw.index.equals(S.pool0.index):
        raw = raw.reindex(index=S.pool0.index, columns=S.pool0.columns)
    cache, info = F.neu_cache(raw, S.pool0, S.log_mcap, S.icodes_neu, mode)
    P = pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, direction)
    info.update(fid=key[0], mode=mode, direction=direction, transform=transform,
                support=S.support, period=S.name, lineage=lin_of_spec(sp).tag())
    if len(st) >= _PCT_CACHE_LIMIT:
        st.pop(next(iter(st)))
    st[key] = (P, info)
    return P


def get_info_g(S, sp, mode='NS', direction='hi', transform='identity'):
    get_pct_g(S, sp, mode, direction, transform)
    return S._g[(fidg(sp), mode, direction, transform)][1]


# ============================================================
# 6. 三个具名 selector (brief §3)
# ============================================================
def keep_SRC(P, p0c, pctkeep, g=None):
    """源语义, 逐字复用 e6f_core.keep_mask_dense (含池内有值票 < 3g 当日空仓)。"""
    return F.keep_mask_dense(P, p0c, pctkeep, g)


def keep_QEDGE(P, p0c, pctkeep, g=None, report=None):
    """只去掉 '需表达成 g 组' 造成的 3g 空仓, 其余一律沿源:
         有效票 n < 6      -> 不形成目标 (源中性化在 <6 已跳过)
         6 <= n < g        -> 分箱数降到 n (每箱 1 只), keep 数 = max(1, round(n*pct/100)), 打标
         n >= g            -> 与 SRC 逐位相同 (同一 pd.qcut 记忆化调用)
       共同可运行日 (n >= 3g) 上与 SRC 必须逐位一致 -- 由 e6g_selftests 阻断验收。"""
    T, Nc = P.shape
    if pctkeep >= 100:
        return p0c.copy()
    if g is None:
        g = F.P2G[int(pctkeep)]
    out = np.zeros((T, Nc), bool)
    nred = nsmall = nfb = 0
    for t in range(T):
        v = np.where(p0c[t] & ~np.isnan(P[t]))[0]
        n = len(v)
        if n < 6:
            nsmall += 1
            continue
        if n < 10:
            nfb += 1          # 6-9: 源 neutralize_by_mcap 在 len<10 时原样返回未中性化值
        gg = int(min(g, n))
        if gg < g:
            nred += 1
        keep_g = int(round(gg * pctkeep / 100.0))
        if keep_g < 1:
            keep_g = 1
        order = np.lexsort((v, P[t, v]))
        gid_ = F.qcut_group(n, gg)
        out[t, v[order[gid_ <= keep_g]]] = True
    if report is not None:
        report.update(qedge_g_reduced_days=nred, qedge_too_small_days=nsmall,
                      qedge_ns_fallback_days=nfb)
    return out


def keep_RANKBUDGET(P, p0c, d, report=None):
    """active 有效域内稳定排序保留 floor(n*d/100); d 连续; 不足 1 则当日空仓。"""
    T, Nc = P.shape
    out = np.zeros((T, Nc), bool)
    nz = 0
    for t in range(T):
        v = np.where(p0c[t] & ~np.isnan(P[t]))[0]
        n = len(v)
        if n == 0:
            continue
        r = int(math.floor(n * float(d) / 100.0))
        if r < 1:
            nz += 1
            continue
        order = np.lexsort((v, P[t, v]))
        out[t, v[order[:r]]] = True
    if report is not None:
        report.update(rankbudget_empty_days=nz)
    return out


def drop_SRC(P, p0c, k):
    return F.drop_mask_dense(P, p0c, k)


def drop_QEDGE(P, p0c, k, report=None):
    """否决侧的同一处置: 只去掉 n < 3k 的【全池皆剔】, 其余沿源。"""
    T, Nc = P.shape
    kept = np.zeros((T, Nc), bool)
    nred = nsmall = nfb = 0
    for t in range(T):
        v = np.where(p0c[t] & ~np.isnan(P[t]))[0]
        n = len(v)
        if n < 6:
            nsmall += 1
            continue
        if n < 10:
            nfb += 1
        kk = int(min(k, n))
        if kk < k:
            nred += 1
        order = np.lexsort((v, P[t, v]))
        gid_ = F.qcut_group(n, kk)
        kept[t, v[order[gid_ <= kk - 1]]] = True
    if report is not None:
        report.update(qedge_veto_g_reduced_days=nred, qedge_veto_too_small_days=nsmall,
                      qedge_veto_ns_fallback_days=nfb)
    return p0c & ~kept


SELECTORS = {'SRC': keep_SRC, 'QEDGE': keep_QEDGE, 'RANKBUDGET': keep_RANKBUDGET}
VETO_SELECTORS = {'SRC': drop_SRC, 'QEDGE': drop_QEDGE}


# ============================================================
# 7. 描述符 ID 与真实路径去重
# ============================================================
_DEF_SUF = dict(sel='SRC', tf='identity', dr='hi', tie='src', buf=None, alpha=None, state=None)


def _frac(x):
    from fractions import Fraction
    f = Fraction(x).limit_denominator(64)
    return '%d/%d' % (f.numerator, f.denominator) if f.denominator != 1 else str(f.numerator)


def gid(base_cfg_id, sel='SRC', tf='identity', dr='hi', alpha=None,
        buf=None, tie='src', state=None, extra=None):
    """E6g 描述符 ID = E6f cfg_id + 非默认后缀块。
       全部默认时与 E6f cfg_id 逐字相同 (OLD 域可逐位对表)。"""
    s = base_cfg_id
    if sel != _DEF_SUF['sel']:
        s += '~sel:%s' % sel
    if tf != _DEF_SUF['tf']:
        s += '~tf:%s' % tf
    if dr != _DEF_SUF['dr']:
        s += '~dir:%s' % dr
    if alpha is not None:
        s += '~a:%s' % _frac(alpha)
    if buf is not None:
        s += '~buf:%s' % buf
    if tie != _DEF_SUF['tie']:
        s += '~tie:%s' % tie
    if state is not None:
        s += '~st:%s' % state
    if extra:
        s += '~x:%s' % extra
    return s


PATH_FIELDS = ('core', 'veto', 'H', 'support', 'sel', 'tf', 'dr', 'alpha', 'buf',
               'tie', 'state', 'neu', 'seed', 'selector_veto')


def canon_veto(v):
    """否决腿是【或】的关系 -> 顺序无关。'cr5:k10+cvr_1d:k10' 与 'cvr_1d:k10+cr5:k10'
       是同一条真实路径; 不规范化就会漏去重。复合否决 (cmp_*) 内部顺序也排序。"""
    if not v:
        return None
    s = str(v)
    m = re.match(r'^(cmp_\w+)\(([^)]*)\)(.*)$', s)
    if m:
        return '%s(%s)%s' % (m.group(1), ','.join(sorted(x.strip() for x in m.group(2).split(','))),
                             m.group(3))
    return '+'.join(sorted(s.split('+')))


def canon_legs(legs, weights=None):
    """腿集合 -> 规范串。均值/中位等对称聚合下腿序无关; 带权重时按 (腿, 权重) 对排序。"""
    if legs is None:
        return None
    if weights is None:
        return '|'.join(sorted(str(x) for x in legs))
    return '|'.join(sorted('%s@%s' % (a, b) for a, b in zip(legs, weights)))


def path_key(d):
    """真实计算路径键: 只含影响数值的字段。不同描述符名共享同一 path_key = 可复用计算,
       映射全部保留 (registry/descriptor_path_map.csv)。"""
    dd = {k: d.get(k) for k in PATH_FIELDS}
    dd['veto'] = canon_veto(dd.get('veto'))
    payload = json.dumps(dd, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]


# ============================================================
# 8. 缓存键 (brief §13 逐项)
# ============================================================
_DATA_FP = {}


def data_fingerprint(S):
    """段数据指纹: 形状 + 首末日 + 收益阵抽样校验和。"""
    k = (S.name, S.support)
    if k in _DATA_FP:
        return _DATA_FP[k]
    a = np.nan_to_num(S.dr.values, nan=0.0)
    h = hashlib.sha1()
    h.update(('%s|%s|%d|%d|%s|%s' % (S.name, S.support, S.T, S.Nfull,
                                     S.dates[0], S.dates[-1])).encode())
    h.update(np.ascontiguousarray(a[::17, ::13]).tobytes())
    _DATA_FP[k] = h.hexdigest()[:16]
    return _DATA_FP[k]


def cache_key(S, desc, lineage, **kw):
    """brief §13: 数据指纹 / allowed-end / 表达式血缘 / active legs 与权重 /
       raw-rank-NS 域 / tie / selector / pool 哈希 / veto / H / 状态初值 / seed / 费用版本。"""
    pool_h = hashlib.sha1(np.packbits(S.p0).tobytes()).hexdigest()[:12]
    payload = dict(v=VERSION, data=data_fingerprint(S), allowed_end=FROZEN_END,
                   lineage=lineage.tag(), pool=pool_h, desc=desc)
    payload.update({k: kw[k] for k in sorted(kw)})
    return hashlib.sha1(json.dumps(payload, sort_keys=True, ensure_ascii=False,
                                   default=str).encode('utf-8')).hexdigest()[:20]


# ============================================================
# 9. 固定展示组 (plan 1.3; 只是展示, 不是准入名单)
# ============================================================
DISPLAY = [
    ('R1',  'KT_dep(50,50)|C:k5',                      '生产 v2 主参照 = A4b_CVRv5'),
    ('R2',  'KT_mean@30|C:k5+cr5:k10',                 'E6b 样本内研究参照, 不是 v2 交付'),
    ('A03', 'KT_dep(50,50)|C:k5+cr5:k10',              '最小改动'),
    ('A04', 'KTC_mean@25',                             '裸核消融'),
    ('A05', 'KTC_mean@25|cvr_1d:k10',                  '单否决父'),
    ('A06', 'KTC_mean@25|cvr_1d:k10+cr5:k10',          '结构母体 1'),
    ('A07', 'KTC_mean@30|cvr_1d:k10+cr5:k10',          '结构母体 2'),
    ('A08', 'T@30|C:k5+cr5:k10',                       '简单 / 低换手母体'),
    ('T25', 'T@25|C:k5+cr5:k10',                       '低换手端'),
    ('A09', 'KTC_mean@25|cmp_mean(cvr_1d,cr5):k10',    '复合否决参照'),
    ('A10', 'TC_mean@35|cvr_1d:k10+cr5:k10',           '无 K 核参照'),
]
DISPLAY_ID = dict((a, b) for a, b, _ in DISPLAY)
BLEND3_MEMBERS = ('A03', 'A06', 'A08')


def blend3_weights(idxvals):
    """Blend3_t = (W_A03 + W_A06 + W_A08)/3。成员 DEV 各自先算, 【不】对合并名单再 DEV、
       【不】归一。返回 (idx, val) 稀疏对。"""
    T = len(idxvals[0][0])
    oi, ov = [], []
    for t in range(T):
        acc = {}
        for idx, val in idxvals:
            for c, w in zip(idx[t], val[t]):
                acc[c] = acc.get(c, 0.0) + w / 3.0
        cs = np.fromiter(sorted(acc), int, len(acc))
        oi.append(cs)
        ov.append(np.fromiter((acc[c] for c in cs), float, len(cs)))
    return oi, ov


# ============================================================
# 10. 段构建 (薄包装; history_warmed 下另算 wfeats)
# ============================================================
def seg(pname, support='legacy_all', verbose=True):
    S = F.build_segment(pname, support=support, verbose=verbose)
    S.wfeats = None
    if support == 'history_warmed' and S.wdata is not S.data:
        S.wfeats = C.calc_all_daily_features(S.wdata)
    S._g = {}
    return S


def eval_mask(S, mask_c, H=K.HOLD, cost_bp=F.COST):
    return F.eval_dense(S, mask_c, H=H, cost_bp=cost_bp)


def ann(x):
    """日序列 -> 年化百分点 (nanmean x 252 x 100), 与 E6e/E6f 口径一致。"""
    return float(np.nanmean(x)) * 252 * 100.0
