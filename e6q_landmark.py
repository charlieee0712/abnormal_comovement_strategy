# -*- coding: utf-8 -*-
"""E6q landmark 存活剖面机器（plan §10；附录 B.0 / B.23；brief S0-D / D4）：在投资批次年龄 a 的 T 收盘，只用截至 T 已知的记录给批次定状态；
前向窗口从 T+1 VWAP 起 q 个交易间隔，超出授权数据终点 → RIGHT_CENSORED（不取 E7 价格）。按未来事件分组（"到 H 末一直未触发"）一律拒绝。
状态（8）：NOT_TRIGGERED / BAD_STATE / REQUEST_PENDING / HALF_PENDING / HALF_DONE_RESIDUAL / REARMED / DEADLINE_OVERRIDDEN / QUARANTINED_CASH。"""
LANDMARK_AGES = (1, 2, 3, 5, 10, 15, 20, 30)
QS = (1, 5, 10, 20)
STATES = ('NOT_TRIGGERED', 'BAD_STATE', 'REQUEST_PENDING', 'HALF_PENDING', 'HALF_DONE_RESIDUAL', 'REARMED', 'DEADLINE_OVERRIDDEN', 'QUARANTINED_CASH')


def state_at(T, intent_day, half_state=0, half_done=False, forced=False, quarantined=False):
    """批次在 T 收盘的状态（只读 T 及之前的记录）：intent_day > T 的记录是未来信息，按"无意向"处理。
    half_state：0 无 / 1 首次半量 / 2 REARM 升级；half_done：首次半量已在 T 及之前完成（余半回持有）；forced：截至 T 已到 deadline 强制完成；
    quarantined：该批次关闭款项对应标签在 T 已处隔离（只用于现金类 landmark）。"""
    if quarantined:
        return 'QUARANTINED_CASH'
    if intent_day is None or intent_day < 0 or intent_day > T:
        return 'NOT_TRIGGERED'
    if forced:
        return 'DEADLINE_OVERRIDDEN'
    if half_state == 2:
        return 'REARMED'
    if half_state == 1:
        return 'HALF_DONE_RESIDUAL' if half_done else 'HALF_PENDING'
    if intent_day < T:
        return 'REQUEST_PENDING'
    return 'BAD_STATE'


def group_by_outcome(*args, **kw):
    """按未来事件（批次此后是否触发 / 是否跑满 H）分组：永生时间偏差的来源，拒绝。"""
    raise ValueError('landmark：按未来事件分组被拒（只能用截至 T 已知的记录）')


def fwd_window(T, q, last_day):
    """前向窗口 [T+1, T+1+q]（VWAP 到 VWAP）；终点超出授权数据最后一日 → RIGHT_CENSORED。"""
    a, b = T + 1, T + 1 + q
    if b > last_day:
        return None, 'RIGHT_CENSORED'
    return (a, b), 'COMPUTED'
