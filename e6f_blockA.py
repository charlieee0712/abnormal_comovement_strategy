#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 A: 构造改进地图 (§4)。一个进程 = 一个 (段, 支持集)。
   用法: python e6f_blockA.py --out DIR --period P --support legacy_all|history_warmed
"""
import os, sys, json, time, copy, argparse, traceback
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--period', required=True)
ap.add_argument('--support', default='legacy_all')
ap.add_argument('--limit', type=int, default=0)
A = ap.parse_args()
PN, SUP = A.period, A.support
TAG = '%s__%s' % (PN, SUP)
for d in ('A_oat', 'A_interactions', 'A_weights', 'A_neutralization', 'A_horizon',
          'neighborhoods', 'daily', 'task_status', 'logs', 'checks'):
    os.makedirs(os.path.join(A.out, d), exist_ok=True)
LOGP = os.path.join(A.out, 'logs', 'blockA_%s.log' % TAG)
_lf = open(LOGP, 'w', encoding='utf-8', buffering=1)


def P(s=''):
    print(s, flush=True)
    _lf.write(s + '\n')


T0 = time.time()
P('=== 块 A [%s] === %s' % (TAG, time.strftime('%Y-%m-%d %H:%M:%S')))
S = F.build_segment(PN, SUP)
if SUP == 'history_warmed':
    P('  预热: %s 起 (%s)' % (S.warm_start, S.warm_tag))
    if S.warm_tag == 'no_prior_data':
        P('  !! 本段源数据没有更早日期, history_warmed 与 legacy_all 恒等; 如实保留标签后退出')
        json.dump(dict(period=PN, support=SUP, status='LIMIT',
                       reason='no_prior_data: 源 kline 最早日 = 段首日, 无法预热'),
                  open(os.path.join(A.out, 'checks', 'warm_%s.json' % TAG), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        sys.exit(0)

CFGS = D.gen_all()
if A.limit:
    CFGS = CFGS[:A.limit]
P('  配置 %d 个' % len(CFGS))

RES, DAILY = {}, {}
TASK = F.TaskTable(os.path.join(A.out, 'task_status', 'blockA_%s.csv' % TAG))
_corecache = {}
_domcache = {}


def comps_of(core):
    out = list(core.get('comps', []))
    if core.get('x'):
        out.append(core['x'])
    out += list(core.get('ys', []))
    return out


def veto_specs(veto):
    return [dict(sp) for sp, _ in veto['legs']] if veto else []


def core_key(core):
    return D.core_id(core)


CORE_LRU = 8


def build_core(core, pool_override=None):
    """-> (mask_c, score, cand_pool). score = 末级排序分 (低=好), 供 coretrim/邻域用。
       只对 pool_override=None 缓存, 且 LRU 上限 8 —— 一个 score 表 (T,Nc) float64 约 50 MB,
       995 个核全缓存要 48 GB。配置按 (parent_id, core_id) 排序, 8 个足够覆盖父+子的复用。"""
    key = core_key(core)
    if pool_override is None and key in _corecache:
        _corecache[key] = _corecache.pop(key)          # move to end
        return _corecache[key]
    md = core.get('neu', 'NS') or 'NS'
    p0 = S.p0c if pool_override is None else (S.p0c & pool_override)
    if core['kind'] in ('single', 'mean'):
        Ps = [F.get_pct(S, sp, md) for sp in core['comps']]
        ws = core.get('ws')
        if ws is not None:
            wf = [float(x) for x in ws]
            score = F.wcombine_dense(Ps, wf)
            used = [Pi for Pi, w in zip(Ps, wf) if w > 0]
            if core['fam'] == 'KTC_mean' and len(used) > 1:      # KTC_mean 是 complete 口径
                score = np.where(F.common_domain(used), score, np.nan)
        elif len(Ps) == 1:
            score = Ps[0]
        else:
            score = F.combine_dense(Ps, 'mean', complete=(core['fam'] == 'KTC_mean'))
        m = F.keep_mask_dense(score, p0, core['s'])
        out = (m, score, p0)
    else:
        Px = F.get_pct(S, core['x'], md)
        s1 = F.keep_mask_dense(Px, p0, core['a'])
        S1full = np.zeros((S.T, S.Nfull))
        S1full[:, S.ccols] = s1.astype(float)
        S1df = pd.DataFrame(S1full, index=S.pool0.index, columns=S.pool0.columns)
        parts = []
        for y in core['ys']:
            raw = F.build_raw(S.wdata, y)
            if raw.shape != S.pool0.shape or not raw.index.equals(S.pool0.index):
                raw = raw.reindex(index=S.pool0.index, columns=S.pool0.columns)
            cch, _ = F.neu_cache(raw, S1df, S.log_mcap, S.icodes_neu, md)
            parts.append(F.pct_dense(cch, S.dates, S.ccolpos, S.Nc, None, hb=F.high_bad(y)))
        score = parts[0] if len(parts) == 1 else F.combine_dense(parts, 'mean')
        m = F.keep_mask_dense(score, s1, core['b'])
        out = (m, score, s1)
    if pool_override is None:
        _corecache[key] = out
        while len(_corecache) > CORE_LRU:
            _corecache.pop(next(iter(_corecache)))
    return out


def build_veto_drop(veto, core, pool_override=None):
    if not veto:
        return None
    md = core.get('neu_veto') or core.get('neu', 'NS') or 'NS'
    p0 = S.p0c if pool_override is None else (S.p0c & pool_override)
    if veto['kind'] == 'composite':
        Ps = [F.get_pct(S, sp, md) for sp, _ in veto['legs']]
        comp = F.combine_dense(Ps, veto['how'], complete=True)
        return F.drop_mask_dense(comp, p0, veto['k'])
    dr = np.zeros_like(p0)
    for sp, k in veto['legs']:
        dr |= F.drop_mask_dense(F.get_pct(S, sp, md), p0, k)
    return dr


def full_mask(cfg, pool_override=None):
    m, sc, cand = build_core(cfg['core'], pool_override)
    dr = build_veto_drop(cfg['veto'], cfg['core'], pool_override)
    return ((m & ~dr) if dr is not None else m), sc, cand, m


def record(cid, pnl, meta):
    g, p, u, n8 = pnl
    DAILY[cid] = (g, p, u)
    m = ~np.isnan(g)
    d = dict(config_id=cid, period=PN, support=SUP,
             net8=F.ann(g - u * (F.COST / 1e4)), net12=F.ann(g - u * (F.COST_HI / 1e4)),
             gross=F.ann(g), turn=252 * float(np.mean(u[m])) if m.any() else np.nan,
             pos=float(np.mean(p[m])) if m.any() else np.nan,
             days_valid=int(m.sum()))
    d['cost'] = d['gross'] - d['net8']
    d.update(meta)
    RES[cid] = d
    return d


def run_one(cfg):
    cid = cfg['config_id']
    mk, sc, cand, coremask = full_mask(cfg)
    (g, p, u, n8), (idx, val) = F.eval_dense(S, mk, H=cfg['H'])
    nh = mk.sum(axis=1)
    meta = dict(layer=cfg['layer'], core_id=cfg['core_id'], veto_id=cfg['veto_id'],
                family=cfg['family'], parent_id=cfg['parent_id'], H=cfg['H'],
                neu=cfg.get('neu', 'NS'), neu_veto=cfg['core'].get('neu_veto') or '',
                anchor=cfg.get('anchor', ''), role='primary',
                avg_nh=float(nh[nh > 0].mean()) if (nh > 0).any() else np.nan,
                days_nohold=int((nh == 0).sum()),
                n_zero_weight=cfg.get('n_zero_weight', 0))
    record(cid, (g, p, u, n8), meta)
    return cfg, mk, sc, cand, coremask, (idx, val), nh


def run_controls(cfg, mk, sc, cand, coremask, iv, nh):
    cid, pid = cfg['config_id'], cfg['parent_id']
    if pid == cid or pid not in RES:
        return
    pc = PARENT_OBJ.get(pid)
    if pc is None:
        return
    ctr = cfg['controls']
    if 'coretrim_matchN' in ctr:
        pmk, psc, pcand, pcore = full_mask(pc)
        tm = F.coretrim_matchN(S, psc, pcore, nh)     # 按父的【核】排序剔深, 不是核减否决
        (g, p, u, _), _ = F.eval_dense(S, tm, H=cfg['H'])
        record(cid + '#trim', (g, p, u, None),
               dict(layer=cfg['layer'] + '_ctrl', role='coretrim_matchN', parent_id=pid,
                    child_id=cid, core_id=pc['core_id'], veto_id='', family=cfg['family'],
                    H=cfg['H'], neu=cfg.get('neu', 'NS'), neu_veto='', anchor=cfg.get('anchor', ''),
                    avg_nh=np.nan, days_nohold=0, n_zero_weight=0))
    if 'eqpos' in ctr:
        pmk, _, _, _ = full_mask(pc)
        _, piv = F.eval_dense(S, pmk, H=cfg['H'])
        a, b = F.eqpos_pair(S, piv, iv, H=cfg['H'])
        for suf, r, rr in ((cid + '||eqpos_par', a, 'eqpos_parent'),
                           (cid + '||eqpos_chd', b, 'eqpos_child')):
            record(suf, (r[0], r[1], r[2], None),
                   dict(layer=cfg['layer'] + '_ctrl', role=rr, parent_id=pid, child_id=cid,
                        core_id=cfg['core_id'], veto_id=cfg['veto_id'], family=cfg['family'],
                        H=cfg['H'], neu=cfg.get('neu', 'NS'), neu_veto='',
                        anchor=cfg.get('anchor', ''), avg_nh=np.nan, days_nohold=0,
                        n_zero_weight=0))
    if 'paired_common_domain' in ctr:
        sps = comps_of(cfg['core']) + comps_of(pc['core']) + \
              veto_specs(cfg['veto']) + veto_specs(pc['veto'])
        md_c = cfg['core'].get('neu', 'NS') or 'NS'
        md_p = pc['core'].get('neu', 'NS') or 'NS'
        Ps = [F.get_pct(S, sp, md_c) for sp in comps_of(cfg['core'])] + \
             [F.get_pct(S, sp, md_p) for sp in comps_of(pc['core'])]
        dom = F.common_domain(Ps)
        for who, cc, sufx in ((cid, cfg, '#cdom'), (pid, pc, '#cdom_par@' + cid)):
            mk2, _, _, _ = full_mask(cc, pool_override=dom)
            (g, p, u, _), _ = F.eval_dense(S, mk2, H=cc['H'])
            record(who + sufx, (g, p, u, None),
                   dict(layer=cfg['layer'] + '_ctrl', role='paired_common_domain',
                        parent_id=pid, child_id=cid, core_id=cc['core_id'],
                        veto_id=cc['veto_id'], family=cc['family'], H=cc['H'],
                        neu=cc['core'].get('neu', 'NS'), neu_veto='',
                        anchor=cfg.get('anchor', ''), avg_nh=np.nan,
                        days_nohold=0, n_zero_weight=0))


BYID = {c['config_id']: c for c in CFGS}
PARENT_OBJ = BYID
for c in CFGS:
    TASK.reg(c['config_id'], 'blockA_primary', layer=c['layer'])

order = sorted(range(len(CFGS)),
               key=lambda i: (CFGS[i]['parent_id'],
                              0 if CFGS[i]['config_id'] == CFGS[i]['parent_id'] else 1,
                              CFGS[i]['core_id'], CFGS[i]['H']))
nerr = 0
t1 = time.time()
for j, i in enumerate(order):
    cfg = CFGS[i]
    cid = cfg['config_id']
    try:
        TASK.set(cid, 'RUNNING')
        out = run_one(cfg)
        run_controls(cfg, *out[1:])
        TASK.set(cid, 'SUCCEEDED')
    except Exception as e:
        nerr += 1
        TASK.set(cid, 'FAILED', note=('%s: %s' % (type(e).__name__, e))[:180])
        if nerr <= 5:
            P('  !! %s -> %s' % (cid, traceback.format_exc().splitlines()[-1]))
    if (j + 1) % 250 == 0:
        el = time.time() - t1
        P('  %5d/%d  %.0fs  (%.3fs/配置, 已产 %d 条评估, 估计剩 %.0f 分)'
          % (j + 1, len(order), el, el / (j + 1), len(RES),
             el / (j + 1) * (len(order) - j - 1) / 60.0))
        TASK.flush()

P('  主循环 %.0fs, 评估 %d 条, 失败 %d' % (time.time() - t1, len(RES), nerr))

# ---------------- 写盘 ----------------
cols = sorted(DAILY)
idx = pd.DatetimeIndex(S.dates)
for nm, k in (('gross', 0), ('pos', 1), ('turn', 2)):
    df = pd.DataFrame({c: DAILY[c][k] for c in cols}, index=idx)
    p = os.path.join(A.out, 'daily', 'A_%s_%s.parquet' % (nm, TAG))
    df.to_parquet(p + '.tmp')
    os.replace(p + '.tmp', p)
SUM = pd.DataFrame([RES[c] for c in cols])
p = os.path.join(A.out, 'A_oat', 'A_summary_%s.csv' % TAG)
SUM.to_csv(p + '.tmp', index=False)
os.replace(p + '.tmp', p)
TASK.flush()
au = TASK.audit()

# ---------------- 段内锚 ----------------
P('')
P('=== 段内锚: P54 默认与 A12 对 E6e 账本 ===')
GG = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % PN))
TT = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % PN))
PPz = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_pos_%s.parquet' % PN))
anch, worst = [], 0.0
for c in CFGS:
    if c['layer'] not in ('P54_default', 'A12_anchor'):
        continue
    cid = c['config_id']
    if cid not in DAILY or cid not in GG.columns:
        continue
    g, p_, u = DAILY[cid]
    m = ~np.isnan(g) & ~np.isnan(GG[cid].values)
    dg = float(np.max(np.abs(g[m] - GG[cid].values[m])))
    du = float(np.max(np.abs(u - TT[cid].values)))
    dp = float(np.max(np.abs(p_ - PPz[cid].values)))
    worst = max(worst, dg, du, dp)
    anch.append(dict(config_id=cid, layer=c['layer'], d_gross=dg, d_turn=du, d_pos=dp,
                     ok=bool(max(dg, du, dp) < 1e-12)))
AN = pd.DataFrame(anch)
AN.to_csv(os.path.join(A.out, 'checks', 'anchors_%s.csv' % TAG), index=False)
nok = int(AN.ok.sum()) if len(AN) else 0
P('  对上的锚 %d/%d, 全体 max|d| = %.3e (阈 1e-12) %s'
  % (nok, len(AN), worst, 'OK' if (len(AN) and nok == len(AN)) else ('无锚可对' if not len(AN) else 'FAIL')))
if SUP != 'legacy_all':
    P('  (history_warmed 支持集下因子提前预热, 与 E6e 账本本就不应逐位相同 —— 上表仅供参考)')

json.dump(dict(period=PN, support=SUP, n_configs=len(CFGS), n_evals=len(RES),
               n_failed=nerr, task_audit=au, anchor_worst=worst, anchor_ok=nok,
               anchor_total=len(AN), seconds=time.time() - T0,
               warm_tag=S.warm_tag, warm_start=S.warm_start, T=S.T, Nc=S.Nc),
          open(os.path.join(A.out, 'checks', 'blockA_%s.json' % TAG), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
P('')
P('块 A [%s] 完成 %.0fs; 登记 %d, 状态计数和 %s; 评估 %d 条'
  % (TAG, time.time() - T0, au['total'], au['by_state'], len(RES)))
_lf.close()
open(os.path.join(A.out, 'task_status', '_DONE_A_%s' % TAG), 'w').write(
    '%s n_eval=%d failed=%d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), len(RES), nerr))
