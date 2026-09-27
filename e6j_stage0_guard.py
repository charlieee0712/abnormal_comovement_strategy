# -*- coding: utf-8 -*-
"""E6j Stage 0 第 5 项（brief v1.2 §2；plan §10.4）：E7 守卫攻击测试 —— 覆盖矩阵 = E6j 代码实际触及行情 / 特征的全部入口。
攻击一律用合成未来数据或伪造 sidecar（写在 stage0/guard_attack/ 下），不读 2026-03-27 之后的任何真实行情。
入口（覆盖矩阵行）：
  G1 e6j_prod.build_period      段截止日 > 2026-03-27 → 在调用 load_all_daily_data 之前抛错（加载函数被替身记录，须 0 次调用）
  G2 e6i_core.seg_i / e6f_core.guarded_load（研究母体、预热数据）→ end > 冻结末日抛错
  G3 e6j_slot.e6i_member_raw（E6i 成员缓存）→ sidecar max_feature_date 越界抛错
  G4 e6j_slot.j_member_raw（E6j J 成员缓存）→ 同上
  G5 e6j_core.assert_index_ok（任何已载帧的日期索引）→ 含 2026-03-30 抛错
  G6 e6j_random.Grid / day_index（随机抽样坐标）→ 日历外日期抛错；trade_calendar 末日 ≤ 2026-03-27
  G7 母体账本 / J 缓存 / 交易日历的实际末日 ≤ 2026-03-27（已落盘产物的静态核查）"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import glob

import numpy as np
import pandas as pd

import e6j_core as J

TASK = 'stage0_item5_guard'
OUT = os.path.join(J.RES, 'stage0', 'guard_attack')


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def chk(gid, entry, attack, ok, detail=''):
        rows.append(dict(entry_id=gid, entry=entry, attack=attack, status='PASS' if ok else 'FAIL', detail=detail))

    def raises(fn):
        try:
            fn()
        except (RuntimeError, ValueError) as e:
            return True, repr(e)[:160]
        return False, 'no exception'

    # G1
    import e6j_prod as P
    calls = []
    orig = P.load_all_daily_data
    P.load_all_daily_data = lambda *a, **k: calls.append((a, k))
    P.PERIODS['__ATTACK__'] = ('20260301', '20260410')
    ok, why = raises(lambda: P.build_period('__ATTACK__'))
    chk('G1', 'e6j_prod.build_period', "段 ('20260301','20260410')", ok and not calls, '%s; load calls=%d' % (why, len(calls)))
    del P.PERIODS['__ATTACK__']; P.load_all_daily_data = orig
    # G2
    import e6f_core as F
    ok, why = raises(lambda: F.guarded_load('20260301', '20260401'))
    chk('G2', 'e6f_core.guarded_load（seg_i 唯一取数口）', "guarded_load('20260301','20260401')", ok, why)
    # G3 / G4：伪造缓存
    import e6j_slot as SL
    fake = os.path.join(OUT, 'fake_cache', '2024-2026')
    os.makedirs(fake, exist_ok=True)
    arr = np.zeros((3, 2))
    for nm in ('FAKE__OBS', 'FAKE_J'):
        pth = os.path.join(fake, nm + '.npy'); np.save(pth, arr)
        meta = dict(shape=[3, 2], sha256=J.sha_file(pth), max_feature_date='2026-04-01', segment='2024-2026')
        json.dump(meta, open(pth.replace('.npy', '.json'), 'w'))
    o3, o4 = SL.E6I_CACHE, SL.J_CACHE
    SL.E6I_CACHE = SL.J_CACHE = os.path.join(OUT, 'fake_cache')
    ok, why = raises(lambda: SL.e6i_member_raw('2024-2026', 'FAKE'))
    chk('G3', 'e6j_slot.e6i_member_raw', 'sidecar max_feature_date=2026-04-01', ok, why)
    ok, why = raises(lambda: SL.j_member_raw('2024-2026', 'FAKE_J'))
    chk('G4', 'e6j_slot.j_member_raw', 'sidecar max_feature_date=2026-04-01', ok, why)
    SL.E6I_CACHE, SL.J_CACHE = o3, o4
    # G5
    ok, why = raises(lambda: J.assert_index_ok(pd.Index([20260325, 20260327, 20260330]), 'attack'))
    chk('G5', 'e6j_core.assert_index_ok', '索引含 20260330', ok, why)
    ok2, _ = raises(lambda: J.assert_index_ok(pd.Index([20260325, 20260327]), 'ok'))
    chk('G5b', 'e6j_core.assert_index_ok', '合法索引（止于 20260327）不应误报', not ok2)
    # G6
    import e6j_random as R
    cal = pd.Index(pd.to_datetime(pd.read_csv(os.path.join(J.RES, 'registry', 'trade_calendar.csv')).date))
    ok, why = raises(lambda: R.Grid(pd.to_datetime(['2026-03-27', '2026-03-30']), ['000001.SZ'], cal))
    chk('G6', 'e6j_random.Grid / day_index', '日期 2026-03-30 不在日历', ok, why)
    chk('G6b', 'registry/trade_calendar.csv', '日历末日', str(cal.max().date()) <= J.MARKET_DATA_END_MAX, str(cal.max().date()))
    # G7 已落盘产物静态核查
    led = pd.read_parquet(os.path.join(J.RES, 'anchors', 'mother_ledger_prod_v2.parquet'), columns=['date'])
    chk('G7a', 'anchors/mother_ledger_prod_v2.parquet', '账本末日', led.date.max() <= J.MARKET_DATA_END_MAX, led.date.max())
    mx = max(json.load(open(p))['max_feature_date'] for p in glob.glob(os.path.join(J.RES, 'cache', '*', '*.json')))
    chk('G7b', 'cache/<段>/J_*.json', 'J 成员 max_feature_date 最大值', mx <= J.MARKET_DATA_END_MAX, mx)
    df = pd.DataFrame(rows)
    p = os.path.join(OUT, 'guard_attack_results.csv'); J.atomic_write_csv(p, df)
    cov = pd.DataFrame([dict(entry_id=g, covered=bool((df.entry_id.str.startswith(g)).any())) for g in ('G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7')])
    pc = os.path.join(OUT, 'coverage_matrix.csv'); J.atomic_write_csv(pc, cov)
    ok = bool((df.status == 'PASS').all() and cov.covered.all())
    J.write_receipt(TASK, [p, pc], 'SUCCEEDED' if ok else 'FAILED', n_tests=len(df), entries=len(cov), blocker=not ok)
    print(df.to_string(), flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
