# -*- coding: utf-8 -*-
"""E6q 读法规则的单一实现（plan §7.1 / §12.2 / §13.2；附录 C 参考函数同语义）：政策字段 → verdict（显式 Python bool，numpy.bool_ / 数字 / 空 profile 拒绝）、
两个密度（分母退化 → NOT_POSITIVE_DENOMINATOR）、E 带评分（不交换端点）。Stage 0 夹具、政策与统计共用。"""
import math

VERDICT = {'PASS': '通过', 'FAIL': '不通过', 'UNDECIDABLE': '不可判'}


def policy_verdict(fields):
    """fields: {字段: True / False / None}；值必须是 Python bool 或 None（numpy.bool_、0 / 1、字符串一律 TypeError）。
    任一 False → 不通过（附 NA 字段）；无 False 有 None → 不可判；全 True → 通过；空 → 不可判（EMPTY_PROFILE）。"""
    if not fields:
        return VERDICT['UNDECIDABLE'], ['EMPTY_PROFILE']
    for k, v in fields.items():
        if type(v) not in (bool, type(None)):
            raise TypeError('policy field %s must be explicit bool / None, got %s' % (k, type(v).__name__))
    na = [k for k, v in fields.items() if v is None]
    if any(v is False for v in fields.values()):
        return VERDICT['FAIL'], na
    return (VERDICT['UNDECIDABLE'], na) if na else (VERDICT['PASS'], [])


def to_bool(x):
    """统计量比较结果 → Python bool（入表前显式转换；NaN / None → None）。"""
    if x is None:
        return None
    if isinstance(x, float) and math.isnan(x):
        return None
    return bool(x)


def density(d_net, d_impact, d_turn, eps=1e-12):
    """plan §7.1：v = Δnet8 / Δturn、c = Δimpact / Δturn；Δturn ≤ eps → NOT_POSITIVE_DENOMINATOR（不报无穷效率）。"""
    if d_turn is None or d_net is None or not (isinstance(d_turn, (int, float)) and math.isfinite(d_turn)):
        return None, None, 'NOT_POSITIVE_DENOMINATOR'
    if d_turn <= eps:
        return None, None, 'NOT_POSITIVE_DENOMINATOR'
    v = d_net / d_turn
    c = (d_impact / d_turn) if (d_impact is not None and math.isfinite(d_impact)) else None
    return v, c, 'OK'


def score_band(value, lo, hi):
    """带内 = 支持；带外 = 不支持；无值 = NOT_EVALUABLE；lo > hi（参照顺序假设不支持）不交换端点 → INSTRUMENT_LIMITED 由调用方标。"""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 'NOT_EVALUABLE'
    if lo > hi:
        return 'BAND_ORDER_NOT_SUPPORTED'
    return '支持' if lo <= value <= hi else '不支持'
