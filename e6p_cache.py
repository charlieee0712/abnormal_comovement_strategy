# -*- coding: utf-8 -*-
"""E6p 缓存命名空间（brief §7：复用 E6o 日期索引 / 内存映射 / 源形成名单 / 触发机器；目录名含 E6p-v1.1 与 efd382ee）。
1. E6o 缓存 panels / triggers / source 逐文件硬链到 E6p 缓存（只读复用，sha 清单 cache_reuse_manifest.json）；
2. 新面板：nclean（当日 clean 只数，RELATIVE_UPPER 单股基准 1 / N_clean）、board（代码前缀板块）、limit_up_raw / open_raw / high_raw；
3. 新触发：T8_LIMIT_CLOSE（raw 收盘在 raw 有效涨停价半 tick 内；无涨跌幅限制日 = 0 非事件；限制价未知 = −1）与 t8_kind（一字 / 盘中收板 / 触板未收 / 无限制 / 未知）；
   UNION = T1a ∨ T3b15 三值或（任一真即真；两假才假；否则 UNKNOWN）。
不读策略收益。用法：python3 e6p_cache.py"""
import os
import json
import time
import resource

import numpy as np
import pandas as pd

import e6p_core as O

TICK = 0.01
BOARDS = ('SH_MAIN', 'SZ_MAIN', 'CHINEXT', 'STAR', 'BSE', 'OTHER')
T8K = ('ORDINARY', 'ONE_TICK', 'INTRADAY_CLOSE_AT_LIMIT', 'TOUCH_NOT_CLOSE', 'NO_LIMIT_DAY', 'UNKNOWN', 'NOT_OPEN')


def board_of(code):
    c = ''.join(ch for ch in str(code) if ch.isdigit())[:6]
    if c.startswith(('600', '601', '603', '605')):
        return 0
    if c.startswith(('000', '001', '002', '003', '004')):
        return 1
    if c.startswith(('300', '301', '302')):
        return 2
    if c.startswith(('688', '689')):
        return 3
    if c.startswith(('8', '43', '92')):
        return 4
    return 5


def link_e6o(cd):
    src_root = O.e6o_cache()
    man = {}
    for sub in ('panels', 'triggers', 'source'):
        sd = os.path.join(src_root, sub)
        dd = os.path.join(cd, sub)
        os.makedirs(dd, exist_ok=True)
        for fn in sorted(os.listdir(sd)):
            sp = os.path.join(sd, fn)
            if not os.path.isfile(sp) or '.tmp' in fn:
                continue
            dp = os.path.join(dd, fn)
            if not os.path.exists(dp):
                os.link(sp, dp)
            man['%s/%s' % (sub, fn)] = dict(bytes=os.path.getsize(dp), sha256=O.sha_file(dp), source='E6o cache（硬链，只读复用）')
    return man


def main():
    t0 = time.time()
    cd = O.cache_dir()
    man = link_e6o(cd)
    O.atomic_write_json(os.path.join(cd, 'cache_reuse_manifest.json'), man)
    pdir = os.path.join(cd, 'panels')
    tdir = os.path.join(cd, 'triggers')
    L = lambda k, d=pdir: np.load(os.path.join(d, k + '.npy'), mmap_mode='r')
    dates = np.load(os.path.join(pdir, 'dates.npy'))
    codes = np.load(os.path.join(pdir, 'codes.npy'))
    T, N = len(dates), len(codes)
    clean = np.asarray(L('clean'))
    O.atomic_save_npy(os.path.join(pdir, 'nclean.npy'), clean.sum(1).astype(np.float64))
    board = np.array([board_of(c) for c in codes], np.int8)
    O.atomic_save_npy(os.path.join(pdir, 'board.npy'), board)
    import e6m_stage0_full as SF
    data, before, dcd = SF.load_full()
    close = data['close']
    if [str(d)[:10] for d in close.index] != list(dates) or [str(c) for c in close.columns] != list(codes):
        raise RuntimeError('日线轴与 E6o 面板轴不一致')
    g = lambda k: data[k].reindex(index=close.index, columns=close.columns).astype(float).to_numpy()
    is_open = np.asarray(L('is_open'))
    op, hi, cl, lu = g('open'), g('high'), g('close'), g('limit_up')
    for k, a in (('limit_up_raw', lu), ('open_raw', op), ('high_raw', hi)):
        O.atomic_save_npy(os.path.join(pdir, k + '.npy'), np.where(is_open, a, np.nan))
    # 上市窗：首个开盘日在样本首日之后者，其前 5 个开盘日为"无涨跌幅限制可能"窗（限制价缺 → NO_LIMIT_DAY）；其余缺 → UNKNOWN
    first_open = np.full(N, -1, np.int64)
    anyo = is_open.any(0)
    first_open[anyo] = np.argmax(is_open[:, anyo], axis=0)
    open_rank = np.cumsum(is_open, axis=0)                      # 截至当日（含）开盘日序号
    ipo_win = np.zeros((T, N), bool)
    late = first_open > 0
    ipo_win[:, late] = is_open[:, late] & (open_rank[:, late] <= 5)
    h = TICK / 2 + 1e-9
    with np.errstate(invalid='ignore'):
        known = is_open & np.isfinite(lu) & (lu > 0) & np.isfinite(cl) & (cl > 0)
        at = known & (np.abs(cl - lu) <= h)
        one = at & np.isfinite(op) & (np.abs(op - lu) <= h)
        touch = known & ~at & np.isfinite(hi) & (hi >= lu - h)
    nolim = is_open & ~np.isfinite(lu) & ipo_win
    unk = is_open & ~known & ~nolim
    t8 = np.full((T, N), -1, np.int8)
    t8[known] = 0
    t8[at] = 1
    t8[nolim] = 0
    kind = np.full((T, N), 6, np.int8)
    kind[known] = 0
    kind[at & ~one] = 2
    kind[one] = 1
    kind[touch] = 3
    kind[nolim] = 4
    kind[unk] = 5
    O.atomic_save_npy(os.path.join(tdir, 'T8_LIMIT_CLOSE.npy'), t8)
    O.atomic_save_npy(os.path.join(pdir, 't8_kind.npy'), kind)
    a = np.asarray(L('T1a', tdir))
    b = np.asarray(L('T3b15', tdir))
    un = np.full((T, N), -1, np.int8)
    un[(a == 0) & (b == 0)] = 0
    un[(a == 1) | (b == 1)] = 1
    O.atomic_save_npy(os.path.join(tdir, 'UNION.npy'), un)
    years = np.array([int(d[:4]) for d in dates])
    rows = []
    for y in sorted(set(years)):
        m = years == y
        for bi, bn in enumerate(BOARDS):
            cb = board == bi
            if not cb.any():
                continue
            op_ = is_open[m][:, cb]
            n_open = int(op_.sum())
            if n_open == 0:
                continue
            kk = kind[m][:, cb]
            rows.append(dict(year=int(y), board=bn, n_open_cells=n_open, limit_known_share=float(known[m][:, cb].sum() / n_open),
                             **{'n_' + T8K[k]: int((kk == k).sum()) for k in range(6)}))
    facts = dict(T=int(T), N=int(N), reused_files=len(man), board_counts={BOARDS[i]: int((board == i).sum()) for i in range(len(BOARDS))},
                 t8_cells=dict(one_tick=int(one.sum()), at_limit=int(at.sum()), touch_not_close=int(touch.sum()), no_limit=int(nolim.sum()), unknown=int(unk.sum())),
                 union_true=int((un == 1).sum()), union_unknown=int((un < 0).sum()), wall_s=round(time.time() - t0, 1),
                 rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    O.atomic_write_csv(os.path.join(cd, 't8_counts_by_year_board.csv'), pd.DataFrame(rows))
    O.atomic_write_json(os.path.join(cd, 'cache_facts.json'), facts)
    O.write_receipt('E6p_cache', [os.path.join(cd, 'cache_facts.json'), os.path.join(cd, 't8_counts_by_year_board.csv')], code=[__file__, O.__file__], **facts)
    print(json.dumps(facts, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
