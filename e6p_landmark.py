# -*- coding: utf-8 -*-
"""E6p landmark 存活剖面机器（plan §10.1；brief S0-10）：在投资批次年龄 a 的 T 收盘，只用截至 T 已知的记录给批次定状态；前向窗口从 T+1 VWAP 起 q 个交易间隔，
超出授权数据终点 → RIGHT_CENSORED（不取 E7 价格）。按未来事件分组（"到 H 末一直未触发"）一律拒绝。"""
LANDMARK_AGES = (1, 2, 3, 5, 10, 15, 20, 30)
QS = (1, 5, 10, 20)
STATES = ('NOT_TRIGGERED', 'BAD_STATE', 'REQUEST_PENDING', 'RENEW_CONFIRMED', 'RENEW_REJECTED', 'RENEW_UNKNOWN')


def state_at(T, intent_day, intent_kind, renew_check=None):
    """批次在 T 收盘的状态（只读 T 及之前的记录）：
    intent_day < T → REQUEST_PENDING（已发请求未成交，调用方保证批次在 T 仍持有）；intent_day == T → BAD_STATE（触发）/ RENEW_REJECTED（检查点不认可）；
    无意向：检查点当日 → RENEW_CONFIRMED / RENEW_UNKNOWN；否则 NOT_TRIGGERED。intent_day > T 的记录是未来信息，按"无意向"处理。"""
    if intent_day is not None and intent_day >= 0 and intent_day <= T:
        if intent_day < T:
            return 'REQUEST_PENDING'
        return 'RENEW_REJECTED' if intent_kind == 'RENEW' else 'BAD_STATE'
    if renew_check == 'CONFIRMED':
        return 'RENEW_CONFIRMED'
    if renew_check == 'UNKNOWN':
        return 'RENEW_UNKNOWN'
    return 'NOT_TRIGGERED'


def group_by_outcome(*args, **kw):
    """按未来事件（批次此后是否触发 / 是否跑满 H）分组：永生时间偏差的来源，拒绝。"""
    raise ValueError('landmark：按未来事件分组被拒（只能用截至 T 已知的记录）')


def fwd_window(T, q, last_day):
    """前向窗口 [T+1, T+1+q]（VWAP 到 VWAP）；终点超出授权数据最后一日 → RIGHT_CENSORED。"""
    a, b = T + 1, T + 1 + q
    if b > last_day:
        return None, 'RIGHT_CENSORED'
    return (a, b), 'COMPUTED'
