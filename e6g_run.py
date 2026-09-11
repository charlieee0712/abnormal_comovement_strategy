#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 通用块执行器: 按【冻结的 H manifest】跑一个 (块, 段, 分片)。

  python3 e6g_run.py --block H1 --segment 2010-2014 [--shard 0 --nshard 4]

描述符由 e6g_expand.<block>() 现场重新生成 (纯组合、确定性), 并与 checks/H_manifest_frozen.json
的 sha256 对账 —— 保证跑的就是冻结的那一份。

每个描述符出: 逐日 gross/pos/turn (net 由 turn 推) + 逐日冲击括号 + 汇总标量 + 逐日原因码;
外加两个对照: 同人数 (母核分数上取相同人数) 与共同有效域重拟。
"""
import os, sys, json, time, argparse, hashlib, collections
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import e6g_desc as GD
import e6g_expand as EX
import e6g_c as CC

REASONS = ('pool_empty', 'feature_missing', 'insufficient_valid', 'three_g_threshold',
           'veto_removed_all', 'ok')


def reason_codes(S, score, cand, core_mask, final_mask, g):
    """逐形成日的原因码 (brief §2)。返回 (逐日码数组, 计数字典)。"""
    T = S.T
    out = np.empty(T, dtype=object)
    for t in range(T):
        if not cand[t].any():
            out[t] = 'pool_empty'
            continue
        nv = int((cand[t] & ~np.isnan(score[t])).sum())
        if nv == 0:
            out[t] = 'feature_missing'
        elif final_mask[t].any():
            out[t] = 'ok'
        elif nv < 6:
            out[t] = 'insufficient_valid'
        elif g is not None and nv < 3 * g:
            out[t] = 'three_g_threshold'
        elif core_mask[t].any():
            out[t] = 'veto_removed_all'
        else:
            out[t] = 'three_g_threshold'
    return out, collections.Counter(out)


def summarize(S, M, cid, row, pnl, iv, mask, score, cand, core_mask, g, extra=None,
              full_profile=True):
    gross, pos, turn, net8 = pnl
    net12 = gross - turn * 12.0 / 1e4
    br, prof, tw, qmiss, live_n, live_w = CC.profile_and_impact(
        M, iv[0], iv[1], K.HOLD, full_profile=full_profile)
    tn = mask.sum(axis=1).astype(float)                    # 形成日目标只数
    rc, cnt = reason_codes(S, score, cand, core_mask, mask, g)
    inp, lead = GD.interior_nopos(pos)
    d = dict(row)
    d.update(
        config_id=cid, segment=S.name, support=S.support,
        gross_ann=G.ann(gross), net8_ann=G.ann(net8), net12_ann=G.ann(net12),
        turn_mean=float(np.nanmean(turn)), pos_mean=float(np.nanmean(pos)),
        target_n_calendar=float(tn.mean()), target_n_active=(float(tn[tn > 0].mean())
                                                             if (tn > 0).any() else np.nan),
        live_n_calendar=prof.get('live_n_calendar'), live_n_active=prof.get('live_n_active'),
        days_no_target=int((tn == 0).sum()), days_no_position=int(prof.get('days_live_zero', 0)),
        interior_nopos=inp, warmup_lead=lead,
        bracket_sqrt_mean=float(np.nanmean(br['sqrt'])),
        bracket_lin_mean=float(np.nanmean(br['lin'])),
        bracket_cal_mean=float(np.nanmean(br['cal'])),
        bracket_s60_mean=float(np.nanmean(br['s60'])),
        turn_abs_mean=float(np.mean(tw)), q_missing_adv_mean=float(np.mean(qmiss)),
    )
    for r in REASONS:
        d['reason_' + r] = int(cnt.get(r, 0))
    for k2 in ('tw_adv_pct', 'tw_mc_pct', 'tw_lowadv', 'tw_nobuy', 'tw_nosell', 'tw_st',
               'hhi', 'wmax', 'invested', 'ind_max', 'ind_n'):
        d[k2] = prof.get(k2, np.nan)
    if extra:
        d.update(extra)
    return d, (gross, pos, turn), (br['sqrt'], br['lin'])


def run_one(S, ctx, M, row, cache):
    """跑一个经济描述符 + 两个对照。返回 (summary rows, daily dict)。"""
    cid = row['descriptor_id']
    core, veto = row['_core'], row['_veto']
    sel = core.get('sel', 'SRC')
    g = None
    if core['kind'] in ('single', 'mean') and sel != 'RANKBUDGET':
        try:
            g = F.P2G[int(core['s'])]
        except (KeyError, TypeError, ValueError):
            g = None
    cfg = dict(config_id=cid, core=core, veto=veto, H=K.HOLD)
    mask, score, cand, core_mask = ctx.full_mask_g(cfg)
    G.guard(ctx.lineage(cfg), 'trade', segment=S.name, where=cid)
    idx, val = F.dev_from_dense(S, mask)
    pnl = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
    base = dict(row)
    base.pop('_core', None)
    base.pop('_veto', None)
    rows, daily, brs = [], {}, {}
    s, dl, br = summarize(S, M, cid, base, pnl, (idx, val), mask, score, cand, core_mask, g,
                          extra=dict(role='economic'))
    rows.append(s); daily[cid] = dl; brs[cid] = br

    # ---- 对照 1: 同人数 (在母核分数上按当日相同人数取股) ----
    pcid = row.get('parent_cfg')
    if pcid:
        pk = ('parent', pcid)
        if pk not in cache:
            pcfg = GD.parse_cfg(pcid)
            pm, ps, pc, pcm = ctx.full_mask_g(pcfg)
            pidx, pval = F.dev_from_dense(S, pm)
            cache[pk] = (pm, ps, pc, pcm,
                         F.sparse_pnl_H(S, pidx, pval, K.HOLD, F.COST))
        pm, ps, pc, pcm, ppnl = cache[pk]
        tn = mask.sum(axis=1).astype(int)
        mm = F.coretrim_matchN(S, ps, pm, tn)
        mi, mv = F.dev_from_dense(S, mm)
        mpnl = F.sparse_pnl_H(S, mi, mv, K.HOLD, F.COST)
        cid2 = cid + '~ctl:matchN'
        s2, dl2, br2 = summarize(S, M, cid2, base, mpnl, (mi, mv), mm, ps, pc, pcm, g,
                                 extra=dict(role='control_matchN', of=cid),
                                 full_profile=False)
        rows.append(s2); daily[cid2] = dl2; brs[cid2] = br2

        # ---- 对照 2: 共同有效域重拟 (母与子都在两者都有分的票上重建) ----
        cd = F.common_domain([ps, score])
        for tag, cfg2 in (('child', cfg), ('parent', GD.parse_cfg(pcid))):
            m3, s3_, c3, cm3 = ctx.full_mask_g(cfg2, pool_override=cd)
            i3, v3 = F.dev_from_dense(S, m3)
            p3 = F.sparse_pnl_H(S, i3, v3, K.HOLD, F.COST)
            cid3 = cid + '~ctl:common_' + tag
            s4, dl4, br4 = summarize(S, M, cid3, base, p3, (i3, v3), m3, s3_, c3, cm3, g,
                                     extra=dict(role='control_common_' + tag, of=cid),
                                     full_profile=False)
            rows.append(s4); daily[cid3] = dl4; brs[cid3] = br4
    return rows, daily, brs


def run_block(A, S, ctx, M, block, t0):
    fn = dict(EX.BLOCKS)[block]
    rows = fn()
    man = json.load(open(os.path.join(G.RES, 'checks', 'H_manifest_frozen.json')))
    assert man['counts'][block] == len(rows), \
        '块 %s 重新生成 %d 个描述符, 冻结表记 %d 个' % (block, len(rows), man['counts'][block])
    if block == 'H2':
        rows = [r for r in rows if r.get('support', 'legacy_all') == A.support]
    elif A.support != 'legacy_all':
        return None                       # 只有 H2 有 history_warmed 支
    rows = [r for i, r in enumerate(rows) if i % A.nshard == A.shard]
    if A.limit:
        rows = rows[:A.limit]
    print('[%s/%s shard %d/%d sup=%s] %d 个描述符'
          % (block, A.segment, A.shard, A.nshard, A.support, len(rows)), flush=True)

    # 描述符行里只带 id/元数据; 核与否决要重建
    allrows, daily, brs = [], {}, {}
    cache = {}
    n = 0
    for r in rows:
        r = dict(r)
        # 重新造核/否决: expand 里已经有, 这里用同一函数再取一次 (确定性)
        core, veto = r.pop('_core', None), r.pop('_veto', None)
        if core is None:
            raise RuntimeError('描述符缺 _core: %s' % r.get('descriptor_id'))
        r['_core'], r['_veto'] = core, veto
        try:
            rr, dd, bb = run_one(S, ctx, M, r, cache)
            allrows.extend(rr); daily.update(dd); brs.update(bb)
        except G.GuardViolation:
            raise
        except Exception as e:
            allrows.append(dict(descriptor_id=r['descriptor_id'], segment=A.segment,
                                role='FAILED', error='%s: %s' % (type(e).__name__, str(e)[:200])))
            print('  !! %s %s: %s' % (r['descriptor_id'], type(e).__name__, str(e)[:160]),
                  flush=True)
        n += 1
        if n % 100 == 0:
            print('  %d/%d  %.0fs  (%.2fs/个)' % (n, len(rows), time.time() - t0,
                                                  (time.time() - t0) / n), flush=True)

    out = os.path.join(G.RES, 'H4' if block.startswith('H4') else block)
    os.makedirs(out, exist_ok=True)
    tag = '%s_%s_s%d' % (block, A.segment, A.shard)
    if A.support != 'legacy_all':
        tag += '_' + A.support
    dts = pd.DatetimeIndex(S.dates)
    tmp = []
    for i, fld in enumerate(('gross', 'pos', 'turn')):
        p = os.path.join(out, 'daily_%s_%s.parquet' % (fld, tag))
        pd.DataFrame({c: v[i] for c, v in daily.items()}, index=dts).to_parquet(p + '.tmp')
        tmp.append(p)
    for i, fld in enumerate(('brsqrt', 'brlin')):
        p = os.path.join(out, 'daily_%s_%s.parquet' % (fld, tag))
        pd.DataFrame({c: v[i] for c, v in brs.items()}, index=dts).to_parquet(p + '.tmp')
        tmp.append(p)
    sm = pd.DataFrame(allrows)
    sp_ = os.path.join(out, 'summary_%s.csv' % tag)
    sm.to_csv(sp_ + '.tmp', index=False)
    for p in tmp + [sp_]:                         # 全部写完再原子 rename (协议 §13)
        os.replace(p + '.tmp', p)

    nfail = int((sm.get('role', pd.Series(dtype=object)) == 'FAILED').sum())
    st = dict(block=block, segment=A.segment, shard=A.shard, nshard=A.nshard,
              support=A.support, n_registered=len(rows), n_rows=len(sm), n_failed=nfail,
              n_daily_cols=len(daily), elapsed_s=round(time.time() - t0, 1),
              manifest_sha=man['descriptor_id_sha256'],
              summary_sha=hashlib.sha256(open(sp_, 'rb').read()).hexdigest()[:16])
    os.makedirs(os.path.join(G.RES, 'task_status'), exist_ok=True)
    json.dump(st, open(os.path.join(G.RES, 'task_status', 'DONE_%s.json' % tag), 'w'),
              indent=1, ensure_ascii=False)
    print('DONE %s: %d 行 (%d 失败), %d 列日账本, %.0fs'
          % (tag, len(sm), nfail, len(daily), st['elapsed_s']), flush=True)
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--blocks', default='H0,H1,H2,H4a,H4b,H5,B2',
                    help='逗号分隔; 一个进程跑多块 = 共用同一份腿 pct 缓存')
    ap.add_argument('--segment', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    ap.add_argument('--support', default='legacy_all')
    ap.add_argument('--limit', type=int, default=0)
    A = ap.parse_args()
    t0 = time.time()
    S = G.seg(A.segment, A.support, verbose=False)
    ctx = GD.GCtx(S)
    M = CC.MarketCtx(S)
    print('段就绪 %.0fs  T=%d Nc=%d  支持集=%s' % (time.time() - t0, S.T, S.Nc, S.support),
          flush=True)
    for b in A.blocks.split(','):
        b = b.strip()
        if not b:
            continue
        run_block(A, S, ctx, M, b, time.time())
    print('全部块完成, 总计 %.0fs' % (time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
