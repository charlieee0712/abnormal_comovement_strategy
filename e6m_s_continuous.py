# -*- coding: utf-8 -*-
"""E6m 阶段 S · 附属第 7 项源理论连续链（plan §10.3 第 7 项 / §13.3；移植 e6l_continuous；STAGE_S_IMPL_PLAN §5 第 25 项；limit register L-S2）。
对象：附属清单 item 7 · CONTINUOUS_ALLOWED_HISTORY|SOURCE_THEORY 的 owner（= 描述符 desc_id；主 72 H5 + 同算子 C1 + 六形态原父）。
两种初始化（plan：分段初始化与允许历史内连续初始化分别运行；子、父、C1、HG / LAG 参照同样连续初始化）：
  reset = 各段冷启动（= 主账户分段口径）；
  carry = 段 k+1 第一个门日 d_f 以段 k carry 链末状态起步（按 ticker 重映射；跨过段首 19 日预热，上一段末日对应 d_f − 1）：
    - 源 HG10 / LAG1_10（SOURCE / TWO_DAY）：源 e6l_ops.mem_gate 状态（HG 存实际 G、LAG1 存无记忆 U、last 平移；next_day / next_date / 列哈希）；
    - 新算子 PROTECTED_LAG10（BAND_Q / BAND_BLEND）、RULE_LAG10（PRIORITY_PASS）：e6m_s_ops.run_days 状态（同算子昨日无记忆自然 U + 绝对交易日位置）；
    - 无记忆 owner：门只依当日分值，carry ≡ reset；连续性只在账户层（上一段末批次自然到期、不清仓）。
任务：
  masks     名单层（不读收益；mock / real）：四段按时间顺序在一个进程里递推 → <根>/finals_<段>.npz（每 owner reset / carry 最终名单位图 + 列名 + 日期）、
            boundary_facts_E6m.csv（每段首接续：带入名数、因新段无该 ticker 丢失的名数、新段无前状态列数、carry − reset 门 / 名单差格数）、
            anchor_masks_E6m.csv（锚 i：reset 门 / 名单 = 名单阶段 masks/<段>/<形态>.npz 同配置位图；冷启动续跑接口 = 派发门；均 0 格差）。
  ledger    账户层（只 real；seal_deriv / seal_post 核对 + 两后段 post_gate）：各段 DEV（= e6k_acct.Acct.target 的 SE.dev）按 ticker 拼到全日历，
            e6l_fast.pnl_nb（H5、8e−4、Wd (H5 + 2, 并集列)，与 e6l_continuous 同式）算连续子 / 连续父账本 → continuous_panel_E6m.csv（owner × 段）、
            spill_facts_E6m.csv（跨段持有进入不含该 ticker 的段的批次格数与权重；该段收益按 0 计，记数披露）、
            anchor_ledger_E6m.csv（锚 ii：各形态原父单段 pnl_nb = accounts/<段>/<形态>.npz 父 net8，NaN 位置一致 + 有限格 ≤ 1e−9；不过即停、不写面板）。
  selftest  mock：断点测试（plan §13.3：连续全程 vs 分片恢复的自然 U / 实际 G / bonus / 最终名单 / 末状态；源路径转录与 AST 抽取源函数各一遍）
            + 回归（冷启动续跑 = 派发门 = 现存 stageS_dev/masks 门位图；一个 (段, 形态) 全部配置派发 = 现存门位图）。
根：mock → stageS_dev/continuous/；real → results/full/continuous/（aux_status 读 continuous_panel_E6m.csv）。
B2：ledger 在 mock 上拒绝运行（红线：不跑 Acct / SparseEngine / pnl 路径）；masks / selftest 只到名单层。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import hashlib
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_s_ops as S
import e6m_s_run_masks as RM

H5 = 5
COST = 8e-4                     # = SparseEngine.pnl(…, cost_bp = 8.0)（e6l_continuous 同值）；锚 ii 在真实段上核
MECH = 'CONTINUOUS_ALLOWED_HISTORY|SOURCE_THEORY'
SRC_MEM = ('HG10', 'LAG1_10')
B40 = 40
TOL_LEDGER = 1e-9
SRC_FUNCS = ('parse_op', 'ids_hash', 'cold_state', '_date_at', '_check_resume', 'select_rows', 'mem_gate', 'permute_marks_day')


def out_dir(struct):
    return M.P('stageS_dev', 'continuous') if struct == 'mock' else M.P('results', 'full', 'continuous')


def path_of(cfg):
    """记忆通道：NONE（carry ≡ reset）/ SOURCE（源 mem_gate 状态）/ RUN_DAYS（新算子 run_days 状态）。"""
    mem, blk, op = cfg['memory'], cfg['block'], cfg['operator']
    if mem == 'NONE':
        return 'NONE'
    if blk in ('SOURCE', 'TWO_DAY') and mem in SRC_MEM:
        return 'SOURCE'
    if blk in ('BAND_Q', 'BAND_BLEND') and mem == 'PROTECTED_LAG10':
        return 'RUN_DAYS'
    if blk == 'FILTER' and op == 'PRIORITY_PASS' and mem == 'RULE_LAG10':
        return 'RUN_DAYS'
    raise ValueError('item 7 未登记的记忆通道：%s' % cfg['desc_id'])


def owners():
    """附属 item 7 · SOURCE_THEORY 的 owner → 描述符行 + aux_id + config_id + 记忆通道。"""
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str)
    A = A[(A.item == '7') & (A.mechanism == MECH)]
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str).set_index('desc_id', drop=False)
    miss = sorted(set(A.owner_id) - set(D.index))
    if miss:
        raise RuntimeError('item 7 owner 不在描述符表：%s' % miss[:3])
    O = D.loc[A.owner_id.tolist()].reset_index(drop=True)
    O['aux_id'] = A.aux_id.values
    O['config_id'] = O.desc_id.map(RM.config_id)
    if set(O.H) != {str(H5)}:
        raise RuntimeError('item 7 owner 的 H 不全是 5：%s' % sorted(set(O.H)))
    par = O[O.block == 'PARENT']
    if par.parent.duplicated().any() or set(par.parent) != set(O.parent):
        raise RuntimeError('每个形态须恰有一个原父 owner')
    O['path'] = [path_of(r) for r in O.to_dict('records')]
    return O


def gate_s(R, cfg, state=None, d0=0, d1=None):
    """记忆 owner 的断点续跑门 → (实际 G, 同算子无记忆自然 U, 末状态)。派发与 Runner.gate 同（锚 i 核冷启动 = 名单阶段门位图）。"""
    p, a = RM.fnum(cfg['param']), RM.fnum(cfg['alpha'])
    c = R.ctx(cfg['measurement'])
    if path_of(cfg) == 'SOURCE':
        return S.source_gate_s(c, a, cfg['memory'], state=state, d0=d0, d1=d1)
    if cfg['block'] == 'BAND_Q':
        gn, gm, f = S.band_gates(c, p, None, cfg['memory'], state=state, d0=d0, d1=d1)
    elif cfg['block'] == 'BAND_BLEND':
        gn, gm, f = S.band_gates(c, p, a, cfg['memory'], state=state, d0=d0, d1=d1)
    else:
        gn, gm, f = S.priority_gates(c, p, cfg['memory'], state=state, d0=d0, d1=d1)
    return gm, gn, f['state']


def remap(prev_cols, new_cols, arr, fill):
    """(…, Nc_prev) → (…, Nc_new) 按 ticker（plan §5.6 按显式 ID 重映射）。返回 (新数组, 新段中上一段没有的列数)。"""
    pi = pd.Index(prev_cols).get_indexer(new_cols)
    ok = pi >= 0
    out = np.full(arr.shape[:-1] + (len(new_cols),), fill, dtype=arr.dtype)
    out[..., ok] = arr[..., pi[ok]]
    return out, int((~ok).sum())


def lost_names(prev_cols, new_cols, marks):
    """上一段末状态里有标记、但新段列集没有该 ticker 的名字数（续跑时丢失）。"""
    gone = ~pd.Index(prev_cols).isin(new_cols)
    return int(np.asarray(marks, bool)[..., gone].sum())


def carry_state(pth, prev, cols, tick, seg, d_f):
    """段 k carry 链末状态 → 段 k+1 在 d_f 的续跑状态。返回 (state, 接续事实)。"""
    stt = prev['state']
    if stt['next_day'] != prev['T']:
        raise RuntimeError('上一段末状态未跑到段尾（next_day %s ≠ T %s）' % (stt['next_day'], prev['T']))
    nd = S.date_at(seg, d_f)
    if pth == 'SOURCE':
        Gc, newc = remap(prev['cols'], cols, stt['G'], False)
        Uc, _ = remap(prev['cols'], cols, stt['U'], False)
        lp = np.where(np.isfinite(stt['last']), stt['last'] + (d_f - prev['T']), -np.inf)     # 上一段末日 → d_f − 1（e6l_continuous 同式）
        lc, _ = remap(prev['cols'], cols, lp, -np.inf)
        f = dict(state_G_prev=int(stt['G'].sum()), state_U_prev=int(stt['U'].sum()), carried_G=int(Gc.sum()), carried_U=int(Uc.sum()),
                 lost_G=lost_names(prev['cols'], cols, stt['G']), lost_U=lost_names(prev['cols'], cols, stt['U']), new_cols_without_state=newc)
        return dict(next_day=d_f, next_date=nd, ids=tick, G=Gc, U=Uc, last=lc), f
    Uc, newc = remap(prev['cols'], cols, np.asarray(stt['U'], bool)[None, :], False)
    f = dict(state_U_prev=int(np.asarray(stt['U']).sum()), carried_U=int(Uc.sum()), lost_U=lost_names(prev['cols'], cols, stt['U']),
             new_cols_without_state=newc)
    return dict(next_day=d_f, next_date=nd, ids=tick, U=Uc[0]), f


def main_masks(struct, pname, form):
    import e6m_s_real as RL
    p = RL.root(struct, 'masks', pname, '%s.npz' % form)
    if not os.path.exists(p):
        return None
    z = np.load(p, allow_pickle=False)
    return dict(ix={str(c): j for j, c in enumerate(z['config_ids'])}, gate=z['gate_bits'], final=z['final_bits'], n=int(z['n_cells'][0]),
                n_dom=int(z['n_dom'][0]), path=M.rel(p))


def anchor_i(zm, cid, G, F):
    """锚 i：reset 门 / 最终名单 = 名单阶段文件同配置位图。"""
    if zm is None:
        return dict(status='SOURCE_WAIT', note='名单阶段文件缺')
    j = zm['ix'].get(cid)
    if j is None:
        return dict(status='FAIL', note='配置不在名单阶段文件')
    g = np.unpackbits(zm['gate'][j])[:zm['n_dom']].astype(bool)
    f = np.unpackbits(zm['final'][j])[:zm['n']].astype(bool)
    gd, fd = int((g != G).sum()), int((f != F).sum())
    return dict(gate_diff=gd, final_diff=fd, status='PASS' if gd == 0 and fd == 0 else 'FAIL')


# ====================================================================== masks（名单层）
def task_masks(struct, segs=None):
    import e6m_s_real as RL
    segs = list(segs or M.SEGMENTS)
    O = owners()
    od = out_dir(struct)
    os.makedirs(od, exist_ok=True)
    chain = {}                                   # desc_id → dict(cols, T, state)：carry 链末状态
    rows_b, rows_a, outs = [], [], []
    t0 = time.time()
    for k, pname in enumerate(segs):
        seg = RL.seg_of(pname, struct)
        cols = np.asarray([str(x) for x in S.colnames(seg)])
        tick = S.ids_hash(S.colnames(seg))
        keys, bits = [], []
        for form in sorted(set(O.parent)):
            Of = O[O.parent == form]
            if form in RL.out_parents(struct):
                rows_b += [dict(segment=pname, desc_id=r.desc_id, aux_id=r.aux_id, family=form, status='OUT_OF_SCOPE_MOCK') for r in Of.itertuples()]
                continue
            R = RM.Runner(pname, form, struct, seg=seg)
            d_f = R.ctx0.days[0][0] if R.ctx0.days else None
            zm = main_masks(struct, pname, form)
            for cfg in Of.to_dict('records'):
                did = cfg['desc_id']
                base = dict(segment=pname, desc_id=did, aux_id=cfg['aux_id'], family=form, block=cfg['block'], measurement=cfg['measurement'],
                            operator=cfg['operator'], memory=cfg['memory'], path=cfg['path'])
                if cfg['measurement'] in R.wait:
                    rows_b.append(dict(base, status='SOURCE_WAIT'))
                    chain.pop(did, None)
                    continue
                G0, _ = R.gate(cfg)
                F0 = R.down(G0)
                rows_a.append(dict(base, check='reset 门 / 名单 = 名单阶段位图（%s）' % (zm['path'] if zm else '缺'), **anchor_i(zm, cfg['config_id'], G0, F0)))
                bf = dict(init='MEMORYLESS')
                Gc, Fc = G0, F0
                if cfg['path'] != 'NONE':
                    prev = chain.get(did)
                    if prev is None or d_f is None:
                        Gc, _, end = gate_s(R, cfg)                       # 首段 / 链断：冷启动（carry ≡ reset），只为取末状态
                        nd = int((Gc != G0).sum())
                        rows_a.append(dict(base, check='冷启动续跑接口 = 派发门', gate_diff=nd, status='PASS' if nd == 0 else 'FAIL'))
                        bf = dict(init='COLD_FIRST_SEGMENT' if k == 0 else 'COLD_CHAIN_BROKEN')
                    else:
                        st2, bf = carry_state(cfg['path'], prev, cols, tick, seg, d_f)
                        Gc, _, end = gate_s(R, cfg, st2, d_f)
                        bf['init'] = 'CARRY'
                    Fc = R.down(Gc)
                    chain[did] = dict(cols=cols, T=seg.T, state=end)
                dd = np.unique(seg.ci.t[Fc != F0])
                rows_b.append(dict(base, status='COMPUTED', d_first_gate=d_f, **bf, gate_carry_minus_reset_cells=int((Gc != G0).sum()),
                                   final_carry_minus_reset_cells=int((Fc != F0).sum()), final_added=int((Fc & ~F0).sum()),
                                   final_removed=int((F0 & ~Fc).sum()), days_with_final_diff=int(dd.size),
                                   last_day_with_final_diff=int(dd.max()) if dd.size else -1, final_members_reset=int(F0.sum())))
                keys += [(did, 'reset'), (did, 'carry')]
                bits += [np.packbits(F0), np.packbits(Fc)]
            del R
        p = os.path.join(od, 'finals_%s.npz' % pname)
        M.atomic_write_npz(p, desc=np.array([x[0] for x in keys]), mode=np.array([x[1] for x in keys]), bits=np.array(bits),
                           n_cells=np.array([seg.n]), ccolnames=cols, dates=np.array([str(x)[:10] for x in seg.dates]),
                           status=np.array(['MOCK_STRUCT' if struct == 'mock' else 'REAL_STRUCT']))
        outs.append(p)
        print('%s 完成（%.0fs）' % (pname, time.time() - t0), flush=True)
        del seg
    p1 = os.path.join(od, 'boundary_facts_E6m.csv')
    p2 = os.path.join(od, 'anchor_masks_E6m.csv')
    M.atomic_write_csv(p1, pd.DataFrame(rows_b))
    A = pd.DataFrame(rows_a)
    M.atomic_write_csv(p2, A)
    return outs + [p1, p2], A


# ====================================================================== ledger（账户层；只 real）
def read_main_net8(pname, O):
    """主账户 net8（H5）：accounts/<段>/<形态>.npz 的 d_net8，按 owner desc_id。"""
    out = {}
    for form in sorted(set(O.parent)):
        p = M.P('accounts', pname, '%s.npz' % form)
        z = np.load(p, allow_pickle=False)
        ix = {str(d): j for j, d in enumerate(z['desc'])}
        d8 = z['d_net8']                                   # npz 每次取键都重读，只取一次
        for did in O[O.parent == form].desc_id:
            if did not in ix:
                raise RuntimeError('主账户缺 owner %s（%s）' % (did, M.rel(p)))
            out[(did, pname)] = np.asarray(d8[ix[did]], float)
    return out


def pnl_net(FA, t, c, w, T, r0T, bench, Nc):
    o = np.lexsort((c, t))
    out = np.empty((1, 4, T))
    FA.pnl_nb(np.ascontiguousarray(t[o], np.int64), np.ascontiguousarray(c[o], np.int64), np.ascontiguousarray(w[o], np.float64),
              np.array([H5], np.int64), T, r0T, bench, COST, np.zeros((H5 + 2, Nc)), out)
    return out[0]


LEDGER_RULE = 'NaN 位置一致 + 有限格 max|Δ| ≤ 1e−9'


def ledger_cmp(a, b, tol=TOL_LEDGER):
    """锚 ii 比较（10-12 补丁十五）：长度相同、NaN 位置一致、有限格 max|Δ| ≤ tol 才 PASS；全 NaN 或长度不同 = FAIL。
    两边的 NaN 都来自 bench 预热日（四段各前 19 日）；原写法 np.max(|a − b|) 遇 NaN 得 NaN，恒 FAIL。"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape:
        return dict(max_abs=float('nan'), nan_led=-1, nan_main=-1, same_nan_pos=False, criterion=LEDGER_RULE, status='FAIL')
    na, nb = ~np.isfinite(a), ~np.isfinite(b)
    same = bool((na == nb).all())
    f = ~na & ~nb
    mx = float(np.max(np.abs(a[f] - b[f]))) if f.any() else float('nan')
    ok = same and bool(f.any()) and mx <= tol
    return dict(max_abs=mx, nan_led=int(na.sum()), nan_main=int(nb.sum()), same_nan_pos=same, criterion=LEDGER_RULE,
                status='PASS' if ok else 'FAIL')


def ann(x):
    x = np.asarray(x, float)
    f = np.isfinite(x)
    return float(np.mean(x[f])) * M.ANN if f.any() else float('nan')


def task_ledger(segs=None):
    import e6m_s_real as RL
    import e6m_s_seal as SEAL
    import e6m_s_gate as GT
    SEAL.require('deriv')
    SEAL.require('post')
    for s in M.POST_SEGS:
        GT.post_gate(s, 'continuous ledger')
    import e6l_fast as FA
    segs = list(segs or M.SEGMENTS)
    O = owners()
    od = out_dir('real')
    par_of = {r.parent: r.desc_id for r in O[O.block == 'PARENT'].itertuples()}
    Z = {s: dict(np.load(os.path.join(od, 'finals_%s.npz' % s), allow_pickle=False)) for s in segs}     # 一次读入（npz 取键会重读）
    cols_all = {s: np.asarray([str(x) for x in Z[s]['ccolnames']]) for s in segs}
    union = pd.Index(sorted(set().union(*[set(c) for c in cols_all.values()])))
    seg_meta, r0_parts, bench_parts = [], [], []
    WC = {}                                      # (段, 名单位图 sha1) → (全日历 t, 并集列 c, w)：carry ≡ reset 的名单只算一次 DEV
    refs = {}                                    # (desc, mode) → [WC 键]（按段）
    anchors, spill = [], []
    main_net = {}
    goff = 0
    t0 = time.time()
    for k, pname in enumerate(segs):
        seg = RL.seg_of(pname, 'real')
        z = Z[pname]
        cols = cols_all[pname]
        if list(cols) != [str(x) for x in S.colnames(seg)] or int(z['n_cells'][0]) != seg.n or str(z['status'][0]) != 'REAL_STRUCT':
            raise RuntimeError('finals_%s 与段结构不一致' % pname)
        T, SE = seg.T, seg.SE
        seg_meta.append((pname, goff, T))
        r0_parts.append((goff, union.get_indexer(cols), SE.r0))
        bench_parts.append(np.asarray(SE.bench, float))
        uc = union.get_indexer(cols)
        miss_next = (~pd.Index(cols).isin(cols_all[segs[k + 1]])) if k + 1 < len(segs) else None
        un = lambda b: np.unpackbits(b)[:seg.n].astype(bool)
        main_net.update(read_main_net8(pname, O))
        for j, (did, mode) in enumerate(zip(z['desc'], z['mode'])):
            did, mode = str(did), str(mode)
            key = (pname, hashlib.sha1(z['bits'][j].tobytes()).hexdigest())
            if key not in WC:
                ids = np.flatnonzero(un(z['bits'][j]))
                t, c = seg.ci.t[ids], seg.ci.c[ids]
                w = np.asarray(SE.dev(t, c), float)
                WC[key] = (t.astype(np.int64) + goff, uc[c].astype(np.int64), w)
                if miss_next is not None:
                    tail = t >= T - (H5 + 1)                              # 持有窗 [f + 2, f + H + 1] 伸进下一段
                    mm = tail & miss_next[c]
                    spill.append(dict(key=key, segment_from=pname, segment_to=segs[k + 1], spill_cells=int(tail.sum()),
                                      spill_weight=float(w[tail].sum()), missing_ticker_cells=int(mm.sum()), missing_ticker_weight=float(w[mm].sum())))
            refs.setdefault((did, mode), []).append(key)
        pos = {(str(d_), str(m_)): j for j, (d_, m_) in enumerate(zip(z['desc'], z['mode']))}
        for form, pdid in sorted(par_of.items()):                         # 锚 ii：原父单段 pnl_nb = 主账户 net8（不经 DEV 去重缓存）
            ids = np.flatnonzero(un(z['bits'][pos[(pdid, 'reset')]]))
            t, c = seg.ci.t[ids].astype(np.int64), seg.ci.c[ids].astype(np.int64)
            led = pnl_net(FA, t, c, np.asarray(SE.dev(t, c), float), T, SE.r0T, np.asarray(SE.bench, float), seg.Nc)
            cmp_ = ledger_cmp(led[3], main_net[(pdid, pname)])          # 补丁十五：NaN 位置一致 + 有限格 ≤ TOL_LEDGER
            anchors.append(dict(segment=pname, family=form, desc_id=pdid, check='单段 pnl_nb（H5、8e−4）= 主账户原父 net8', **cmp_))
        goff += T
        print('%s DEV 完成（%.0fs）' % (pname, time.time() - t0), flush=True)
        del seg, SE
    A = pd.DataFrame(anchors)
    pa = os.path.join(od, 'anchor_ledger_E6m.csv')
    M.atomic_write_csv(pa, A)
    if A.empty or (A.status != 'PASS').any():
        raise RuntimeError('锚 ii 未过（%s）：不写连续面板' % M.rel(pa))
    Tf = goff
    r0f = np.zeros((Tf, len(union)))
    for go, ix, r0 in r0_parts:
        r0f[go:go + r0.shape[0], ix] = r0
    benchf = np.concatenate(bench_parts)
    r0T = np.ascontiguousarray(r0f.T).ravel()
    del r0f, r0_parts
    cache, led = {}, {}
    for key, ks in refs.items():
        sig = tuple(ks)
        if sig not in cache:
            t = np.concatenate([WC[x][0] for x in sig])
            c = np.concatenate([WC[x][1] for x in sig])
            w = np.concatenate([WC[x][2] for x in sig])
            cache[sig] = pnl_net(FA, t, c, w, Tf, r0T, benchf, len(union))
        led[key] = cache[sig]
    rows = []
    for r in O.itertuples():
        pdid = par_of[r.parent]
        par = led[(pdid, 'reset')][3]
        for (pname, go, T) in seg_meta:
            sl = slice(go, go + T)
            cc, rr, pp = led[(r.desc_id, 'carry')][3][sl], led[(r.desc_id, 'reset')][3][sl], par[sl]
            mn, mp = main_net[(r.desc_id, pname)], main_net[(pdid, pname)]
            b = slice(0, min(T, B40))
            rows.append(dict(aux_id=r.aux_id, desc_id=r.desc_id, family=r.parent, block=r.block, measurement=r.measurement, operator=r.operator,
                             memory=r.memory, memory_reference=r.memory_reference, is_primary72=r.is_primary72, path=r.path, segment=pname, days=T,
                             D_cont_carry_minus_cont_parent_ann_pp=ann(cc - pp), D_cont_reset_minus_cont_parent_ann_pp=ann(rr - pp),
                             carry_minus_reset_ann_pp=ann(cc - rr), boundary40_carry_minus_parent_ann_pp=ann((cc - pp)[b]),
                             boundary40_carry_minus_reset_ann_pp=ann((cc - rr)[b]), D_seg_main_ann_pp=ann(mn - mp),
                             cont_carry_minus_seg_self_ann_pp=ann(cc - mn), cont_parent_minus_seg_parent_ann_pp=ann(pp - mp),
                             net8_cont_carry_ann_pp=ann(cc), status='COMPUTED'))
    P = pd.DataFrame(rows)
    p1 = os.path.join(od, 'continuous_panel_E6m.csv')
    M.atomic_write_csv(p1, P)
    sp = pd.DataFrame(spill)
    if not sp.empty:
        k2o = {}
        for (did, mode), ks in refs.items():
            for x in ks:
                k2o.setdefault(x, []).append('%s@%s' % (did, mode))
        sp['owners'] = sp.key.map(lambda x: ';'.join(sorted(k2o.get(x, []))))
        sp['n_owner_modes'] = sp.key.map(lambda x: len(k2o.get(x, [])))
        sp['bits_sha1'] = sp.key.map(lambda x: x[1][:16])
        sp = sp.drop(columns=['key'])
    p2 = os.path.join(od, 'spill_facts_E6m.csv')
    M.atomic_write_csv(p2, sp)
    return [p1, p2, pa], dict(rows=len(P), union_tickers=len(union), days=Tf, unique_dev=len(WC), unique_ledgers=len(cache))


# ====================================================================== selftest（mock；名单层）
def src_inputs(c, a):
    st = c.st
    q = c.q0 if (c.kf is None or float(a) == 0.0) else S.native_q(c.q0, c.kf, a)
    sc = st.gate_scores(q[None, :])
    return st, sc, st.gate_keep(sc)


same_state = S.states_equal


def task_selftest(segs=('2010-2014', '2015-2018'), regress=('2010-2014', 'A4b')):
    from types import SimpleNamespace
    import e6m_s_real as RL
    import e6m_stage0_S_feat as SF
    ns, sh = SF.extract_source_funcs(os.path.join(M.CODE, 'e6l_ops.py'), SRC_FUNCS, consts=('STATE_OPS', 'RMARK_MECHS'))
    O = owners()
    rows = []

    def ok(check, seg, form, did, val, cond, note=''):
        rows.append(dict(check=check, segment=seg, family=form, desc_id=did, value=val, status='PASS' if cond else 'FAIL', note=note))
    for pname in segs:
        seg = RL.seg_of(pname, 'mock')
        seg.S = SimpleNamespace(ccolnames=seg.ccolnames)                     # 源 mem_gate 读 seg.S.ccolnames（续跑列哈希）
        for form in sorted(set(O.parent)):
            R = RM.Runner(pname, form, 'mock', seg=seg)
            days = [d for d, _, _, _ in R.ctx0.days]
            splits = sorted(set([days[0], days[0] + 1, days[len(days) // 2], days[-1], seg.T]))
            zm = main_masks('mock', pname, form)
            for cfg in O[O.parent == form].to_dict('records'):
                did = cfg['desc_id']
                if cfg['measurement'] in R.wait:
                    continue
                G0, _ = R.gate(cfg)
                F0 = R.down(G0)
                a = anchor_i(zm, cfg['config_id'], G0, F0)
                ok('派发门 = 现存 stageS_dev/masks 门 / 名单位图', pname, form, did, '%s/%s' % (a.get('gate_diff'), a.get('final_diff')), a['status'] == 'PASS')
                if cfg['path'] == 'NONE':
                    continue
                Gf, Uf, ef = gate_s(R, cfg)
                ok('冷启动续跑接口 = 派发门', pname, form, did, int((Gf != G0).sum()), np.array_equal(Gf, G0))
                if cfg['path'] == 'SOURCE':
                    st, sc, U = src_inputs(R.ctx(cfg['measurement']), RM.fnum(cfg['alpha']))
                    rule, bday = ns['parse_op'](cfg['memory']), np.full(seg.T, 10.0)
                    gs, ss, _ = ns['mem_gate'](st, sc, U, rule, b_day=bday)
                    ok('转录 = 源 mem_gate（AST 抽取）：全程 G 与末状态', pname, form, did, int((gs[0] != Gf).sum()), np.array_equal(gs[0], Gf) and same_state(ss, ef))
                for dk in splits:
                    G1, U1, e1 = gate_s(R, cfg, None, 0, dk)
                    G2, U2, e2 = gate_s(R, cfg, e1, dk)
                    G = G1 | G2
                    Ux = (U1 | U2) if cfg['path'] == 'RUN_DAYS' else U2         # 新算子 U 只在已跑日给出；源 U 逐日无状态、全程给出
                    lab = 'd%d' % dk
                    ok('断点 %s：实际 G = 全程' % ('末' if dk == seg.T else '中'), pname, form, did, int((G != Gf).sum()), np.array_equal(G, Gf), lab)
                    ok('断点：自然 U = 全程', pname, form, did, int((Ux != Uf).sum()), np.array_equal(Ux, Uf), lab)
                    ok('断点：bonus（G ∧ ¬U）= 全程', pname, form, did, int(((G & ~Ux) != (Gf & ~Uf)).sum()), np.array_equal(G & ~Ux, Gf & ~Uf), lab)
                    ok('断点：最终名单 = 全程', pname, form, did, int((R.down(G) != R.down(Gf)).sum()), np.array_equal(R.down(G), R.down(Gf)), lab)
                    ok('断点：末状态 = 全程末状态', pname, form, did, '', same_state(e2, ef), lab)
                    if cfg['path'] == 'SOURCE':
                        ga, sa, _ = ns['mem_gate'](st, sc, U2[None, :], rule, b_day=bday, d1=dk)
                        gb, sb, _ = ns['mem_gate'](st, sc, U2[None, :], rule, b_day=bday, state=sa, d0=dk)
                        ok('断点：源 mem_gate 分片 = 转录分片（G 与两段末状态）', pname, form, did, int(((ga[0] | gb[0]) != G).sum()),
                           np.array_equal(ga[0], G1) and np.array_equal(gb[0], G2) and same_state(sa, e1) and same_state(sb, e2), lab)
                try:
                    bad = dict(e1, next_day=e1['next_day'] + 1)
                    gate_s(R, cfg, bad, splits[2])
                    ok('身份不符的状态被拒绝', pname, form, did, 'accepted', False)
                except ValueError:
                    ok('身份不符的状态被拒绝', pname, form, did, 'rejected', True)
            del R
    sg, fm = regress
    seg = RL.seg_of(sg, 'mock')
    R = RM.Runner(sg, fm, 'mock', seg=seg)
    zm = main_masks('mock', sg, fm)
    C = RM.configs(fm)
    nd = nc = 0
    for cfg in C.to_dict('records'):
        if cfg['measurement'] in R.wait or cfg['block'] == 'V_STATE' or cfg['config_id'] not in (zm or {}).get('ix', {}):
            continue
        G, _ = R.gate(cfg)
        a = anchor_i(zm, cfg['config_id'], G, R.down(G))
        nd += int(a['status'] != 'PASS')
        nc += 1
    ok('回归：一个 (段, 形态) 全部可算配置派发 = 现存门 / 名单位图', sg, fm, '', '%d/%d 不符' % (nd, nc), nd == 0 and nc > 0)
    rows.append(dict(check='源文件 sha（AST 抽取）', segment='', family='', desc_id='', value=sh, status='INFO', note='e6l_ops.py'))
    return pd.DataFrame(rows)


def main():
    import e6m_s_real as RL
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['masks', 'ledger', 'selftest'])
    ap.add_argument('--struct', default='mock', choices=['mock', 'real'])
    ap.add_argument('--segs', default='')
    a = ap.parse_args()
    t0 = time.time()
    segs = [x for x in a.segs.split(',') if x] or None
    rss = lambda: round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2)
    code = [__file__, S.__file__, RM.__file__, RL.__file__, M.__file__]
    if a.task == 'masks':
        outs, A = task_masks(a.struct, segs)
        st = A.status.value_counts().to_dict()
        good = not (A.status == 'FAIL').any()
        M.write_receipt(os.environ.get('E6M_TASK', ('S_dev_cont_masks' if a.struct == 'mock' else 'S_cont_masks')), outs,
                        status='SUCCEEDED' if good else 'FAILED', code=code, anchors=st, struct=a.struct, wall_s=round(time.time() - t0, 1), rss_peak_gb=rss(),
                        note='名单层（不读收益）：%s' % ('B2 开发 mock' if a.struct == 'mock' else '阶段 S 真实结构'))
        print(json.dumps(dict(task='masks', struct=a.struct, anchors=st, wall_s=round(time.time() - t0, 1), rss_peak_gb=rss()), ensure_ascii=False))
        return 0 if good else 1
    if a.task == 'ledger':
        if a.struct != 'real':
            raise RuntimeError('ledger 只在真实结构上运行（B2 红线：不在 mock 上跑 pnl 路径）')
        outs, T = task_ledger(segs)
        M.write_receipt(os.environ.get('E6M_TASK', 'S_cont_ledger'), outs, status='SUCCEEDED', code=code + [os.path.join(M.CODE, 'e6l_fast.py')],
                        wall_s=round(time.time() - t0, 1), rss_peak_gb=rss(), **T)
        print(json.dumps(dict(task='ledger', **T, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
        return 0
    df = task_selftest()
    p = os.path.join(out_dir('mock'), 'selftest_continuous_E6m.csv')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    M.atomic_write_csv(p, df)
    st = df.status.value_counts().to_dict()
    good = not (df.status == 'FAIL').any()
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_cont_selftest'), [p], status='SUCCEEDED' if good else 'FAILED', code=code, counts=st,
                    wall_s=round(time.time() - t0, 1))
    print(json.dumps(dict(task='selftest', counts=st, fails=df[df.status == 'FAIL'].check.value_counts().to_dict(), wall_s=round(time.time() - t0, 1)),
                     ensure_ascii=False))
    return 0 if good else 1


if __name__ == '__main__':
    sys.exit(main())
