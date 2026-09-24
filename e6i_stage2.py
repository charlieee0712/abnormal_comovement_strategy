#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 2 主账户 (推导段; brief §6 / plan §5-§6)。

每个 A0 描述符 (去掉 H 的"配置") 只建一次掩码 / DEV, 再对其 H 网格各跑一次源同式引擎。
每条账户同时产出 (plan §6.3 确定性对照 + §6.5 归因):
  parent           同 H 母体
  core_matchN      同日同人数核心 (母体冻结 continuation ordering; n=|B| 时逐位 = B, 锚 R5)
  reverse_matchN   同日同人数反向 (取母体核分最差)
  parent_common    母体限制在子账户有名单的日期 (覆盖桥)
  same_capital     逐形成日把子 / 父目标权重都向下缩到共同资本后完整重跑 (只缩不放)
  归因              Δgross_t = Σ_i (act_child - act_parent)[t-2,i] · (r0[t,i] - bench_t)
                   拆进入 / 退出 / 共同成员权重变化三项, 逐日精确相加 (残差 = 0 是锚)
随机对照 (Z-MAP) 在 e6i_randoms.py; 本脚本不产生任何 2019+ 数值 (守卫在每个配置上检查)。

逐日序列存 accounts/<seg>/<route>_<shard>.npz (float64), 汇总存 .csv。
用法: python3 e6i_stage2.py --segment 2015-2018 --route RT --shard 0 --nshard 4
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import io
import sys
import time
import argparse
import collections
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_s1base as SB
import e6i_ops as OP
import e6i_engine as E
import e6f_core as F

ROLE_RULE = {'SLOT': 'SLOT', 'COMMON_SUPPORT': 'COMMON_SUPPORT', 'ADD_SCORE': 'ADD_SCORE',
             'VETO_NEW': 'VETO_NEW', 'SOFT': 'SOFT', 'SOFT_HARD': 'SOFT', 'SWAP': 'SWAP',
             'FOCAL_NEW': 'FOCAL_NEW', 'RL': 'RL', 'T_PAIR': 'T_PAIR', 'FOURARM': 'FOURARM'}
SLOT_LEG = {'RT': 'T', 'RK': 'K', 'RC': 'C', 'RA': 'K', 'TPAIR': 'T'}


def config_key(r):
    return tuple((k, str(r.get(k, ''))) for k in ('route_id', 'mother_id', 'member_id', 'role',
                                                  'strength', 'policy', 'direction',
                                                  'direction_role', 'state_member', 'state',
                                                  'buffer_b'))


class Runner(object):
    def __init__(self, S):
        self.S = S
        self.M = {}
        self.parent_W = {}
        self.parent_pnl = {}

    def mother(self, mn):
        if mn not in self.M:
            self.M[mn] = OP.Mother(self.S, mn)
            self.parent_W[mn] = E.dev_weights(self.S, self.M[mn].B)
        return self.M[mn]

    def ppnl(self, mn, H):
        k = (mn, H)
        if k not in self.parent_pnl:
            self.mother(mn)
            self.parent_pnl[k] = E.pnl_W(self.S, self.parent_W[mn], H, I.COST)
        return self.parent_pnl[k]

    # ------------------------------------------------------------ 建子账户掩码
    def build(self, r):
        """返回 (mask, wmul, info)。NOT_APPLICABLE 抛 ValueError。"""
        S = self.S
        M = self.mother(r['mother_id'])
        route, role, mid = r['route_id'], r['role'], r['member_id']
        s, pol, dirn = r['strength'], str(r.get('policy') or ''), r['direction']
        if role in ('SLOT', 'COMMON_SUPPORT'):
            leg = SLOT_LEG[route]
            a = float(s)
            policy = 'COMMON_SUPPORT' if role == 'COMMON_SUPPORT' else pol
            if M.kind == 'dep' and leg == 'T':
                raw = SB.raw_member(S, mid)
                B2, info = M.slot_dep_T(raw, dirn, a, 'FALLBACK' if policy == 'FALLBACK' else policy)
            else:
                B2, info = M.slot(leg, lambda: OP._dirpct(S, mid, dirn), a, policy)
            return B2, None, info
        if role == 'T_PAIR':
            lv, cv = mid.split('+')
            b = float(s)
            if M.kind == 'dep':                           # R1: T 位是第二阶段, 两分量都在 S1 内重中性化
                zl = OP._ns_pct_within(S, SB.raw_member(S, lv), M.s1, 'hi')
                zc = OP._ns_pct_within(S, SB.raw_member(S, cv), M.s1, 'hi')
                comp = np.where(np.isfinite(zl) & np.isfinite(zc), (1 - b) * zl + b * zc, np.nan)
                keep, _, _ = M._keep_dep(stage2=comp, s1=M.s1)
                return keep & ~M.veto_drop(), None, dict(note='tpair_dep_b%s' % b)
            zl = OP._dirpct(S, lv, 'high_bad')
            zc = OP._dirpct(S, cv, 'high_bad')
            comp = np.where(np.isfinite(zl) & np.isfinite(zc), (1 - b) * zl + b * zc, np.nan)
            B2, info = M.slot('T', lambda: comp, 1.0, 'FULL_REPLACE')
            return B2, None, info
        # 焦点状态行 (RO 的 O_o1 / RS 的 S 成员) 方向记为 'state': 成员只定义状态, 不产生新分数
        z = OP._dirpct(S, mid, dirn) if (mid in FE.CATALOG_IDS and dirn in ('high_bad', 'low_bad')) \
            else None
        if role == 'ADD_SCORE':
            if M.kind == 'dep':
                raw = SB.raw_member(S, mid)
                z = OP._ns_pct_within(S, raw, M.s1, 'hi' if dirn == 'high_bad' else 'lo')
            B2, info = M.add_score(z, float(s))
            return B2, None, info
        if role == 'VETO_NEW':
            B2, info = M.veto_new(z, int(float(s)))
            return B2, None, info
        if role == 'SOFT':
            B2, info = M.soft(z, float(s))
            return B2, info['wmul'], info
        if role == 'SOFT_HARD':
            B2, info = M.veto_new(z, int(float(s)))
            return B2, None, info
        if role == 'SWAP':
            state = None
            if r.get('state_member') and str(r.get('state_member')) != 'nan':
                state = state_mask(S, str(r['state_member']), str(r['state']))
            out_score = None
            if 'out=max_K' in pol:
                out_score = M.legs[M.leg_roles.index('K')] if M.kind != 'dep' else M.Px
            B2, info = M.swap(z, float(s), out_score=out_score, state=state)
            bb = r.get('buffer_b')
            if bb is not None and str(bb) != 'nan' and float(bb) > 0:
                B2 = buffered_child(S, M, B2, int(float(bb)))
                info['note'] = info.get('note', '') + '|buffer_b%d' % int(float(bb))
            return B2, None, info
        if role == 'RL':
            return M.edge_replace(OP._dirpct(S, mid, 'high_bad'))[0], None, dict(note='rl')
        if role == 'FOCAL_NEW':
            focal = pol.split('@')[0]
            arm = str(s)
            if arm.startswith('replace_'):            # RR 收益焦点替换 (plan §5.1/§5.3): 关原焦点, 新成员同 k
                arm = 'new'
            elif arm.startswith('both_'):             # A0 v1.2: 原焦点 + 新成员同 k 两者都删
                arm = 'both'
            if arm in ('new', 'both'):
                return M.focal(focal, arm, znew=z)[0], None, dict(note='focal_%s' % arm)
            if arm in ('old', 'none', 'all_on', 'all_off'):
                return M.focal(focal, arm)[0], None, dict(note='focal_%s' % arm)
            st_name = pol.split('@')[1] if '@' in pol else r.get('direction_role')
            state = focal_state(S, mid, st_name)
            if arm == 'real_state':
                return M.focal(focal, 'real_state', state=state)[0], None, dict(note='focal_state')
            rng = np.random.default_rng(abs(hash(r['descriptor_id'])) % (2 ** 32))
            return M.focal(focal, 'random_state', state=state, rng=rng)[0], None, \
                dict(note='focal_random_state')
        if role == 'FOURARM':
            return self.fourarm(r, M)
        raise ValueError('role 未实现: %s' % role)

    def fourarm(self, r, M):
        """plan §5.6/§5.7 四臂中心 (固定, 不看单项结果): 臂 A / B / AB, 母体臂 = parent。"""
        S = self.S
        name, arm, pv = r['policy'], r['direction_role'], r['strength']
        if name == 'T_level_x_CV':
            if arm in ('A', 'B'):
                mid = 'T_mean20' if arm == 'A' else 'T_cv20'
                if M.kind == 'dep':
                    return M.slot_dep_T(SB.raw_member(S, mid), 'high_bad', 1.0, 'FULL_REPLACE')[0], \
                        None, dict(note='fourarm_T_%s' % arm)
                return M.slot('T', lambda: OP._dirpct(S, mid, 'high_bad'), 1.0,
                              'FULL_REPLACE')[0], None, dict(note='fourarm_T_%s' % arm)
            rr = dict(r, role='T_PAIR', member_id='T_mean20+T_cv20', strength=0.5,
                      route_id='TPAIR')
            return self.build(rr)
        if name == 'K_resid_x_A_event':
            a = float(pv)
            zA = lambda: OP._dirpct(S, 'K_res_log', 'high_bad')
            zB = lambda: OP._dirpct(S, 'T_evlevel', 'high_bad')
            if arm == 'A':
                fn = zA
            elif arm == 'B':
                fn = zB
            else:
                def fn():
                    x, y = zA(), zB()
                    return np.where(np.isfinite(x) & np.isfinite(y), 0.5 * x + 0.5 * y,
                                    np.where(np.isfinite(x), x, y))
            return M.slot('K', fn, a, 'FALLBACK')[0], None, dict(note='fourarm_KA_%s_a%s' % (arm, a))
        if name == 'R_peer_x_S_state':
            st = state_mask(S, 'S_peerR20', str(pv))
            zR = OP._dirpct(S, 'R_peer20', 'high_bad')
            if arm == 'A':
                return M.swap(zR, 0.10)[0], None, dict(note='fourarm_RS_A')
            if arm == 'B':                                  # 状态内按源核排序
                zc = M.score if M.kind != 'dep' else np.where(np.isfinite(M.Px), M.Px, np.nan)
                return M.swap(zc, 0.10, state=st)[0], None, dict(note='fourarm_RS_B_%s' % pv)
            return M.swap(zR, 0.10, state=st)[0], None, dict(note='fourarm_RS_AB_%s' % pv)
        if name == 'V_rs_x_O_on':
            zV = OP._dirpct(S, 'V_rs20_obs', 'high_bad')
            zO = OP._dirpct(S, 'O_onmean5', 'low_bad')          # 正隔夜方向 (高 = 好)
            g = float(pv)
            if arm == 'A':
                return M.add_score(zV, g)[0], None, dict(note='fourarm_VO_A')
            if arm == 'B':
                return M.add_score(zO, g)[0], None, dict(note='fourarm_VO_B')
            base = M.score
            zV2 = np.where(np.isfinite(zV), zV, base)
            zO2 = np.where(np.isfinite(zO), zO, base)
            z = (1 - 2 * g) * base + g * zV2 + g * zO2
            if M.kind in ('mean', 'single'):
                keep = OP.G.keep_SRC(z, M.p0, M.core['s']).astype(bool)
            else:
                keep = OP.G.keep_SRC(z, M.s1, M.core['b']).astype(bool)
            return keep & ~M.veto_drop(), None, dict(note='fourarm_VO_AB')
        raise ValueError('未知四臂 %s' % name)


def buffered_child(S, M, child, b):
    """E6h 子对象可持有域 (e6h_post_lgrid 的 Bmask(b), b=0 锚 62/62): Bmask(b) = 子名单 ∪ 母体核放宽 b 档
       新开的那一圈; 用 e6g_l.buffered_targets 的 matchN 推进 (跌出子名单但仍在放宽圈内就继续持有)。"""
    import e6g_l as L6
    ctx, cfg = M.ctx, M.cfg
    ring = (L6.relaxed_domain(ctx, cfg['core'], b)[0] & ~L6.relaxed_domain(ctx, cfg['core'], 0)[0])
    Tdrop = L6.veto_drop(ctx, cfg)
    tg, _ = L6.buffered_targets(S, child, child | ring, Tdrop, M.score, 'matchN')
    return tg.astype(bool)


def state_mask(S, state_member, st):
    """S 轴状态 (plan §4.8): 当日行业间 P30 / P70 (对状态成员原值在 pool0 内的截面分位) 与自然零界。"""
    raw = SB.raw_member(S, state_member)
    pr = SB.row_rank(raw, S.p0c)
    if st == 'P30':
        return pr <= 0.30
    if st == 'P70':
        return pr >= 0.70
    if st == 'neg':
        return raw < 0
    if st == 'pos':
        return raw > 0
    raise ValueError(st)


def focal_state(S, mid, st_name):
    """焦点状态: gap_pos / gap_neg = 当日隔夜 o 的正 / 负 (O_o1 原值); weak_or_dispersed = 同行 R20 处
       P30 以下或 同行 IQR 处 P70 以上 (S 成员原值)。未知状态 -> False (不执行新增操作, plan §5.3)。"""
    if st_name in ('gap_pos', 'gap_neg'):
        o = SB.raw_member(S, 'O_o1')
        return (o > 0) if st_name == 'gap_pos' else (o < 0)
    if st_name == 'weak_or_dispersed':
        pr = SB.row_rank(SB.raw_member(S, mid), S.p0c)
        if mid == 'S_peeriqr20':
            return pr >= 0.70
        return pr <= 0.30
    raise ValueError(st_name)


def attrib(S, Wc, Wp, H):
    """plan §6.5: 持有权重 (源引擎实际计收益时点) 的差拆三项; 返回每日三项与总差 (T,) x 4。"""
    ac, ap = E._act(Wc, H), E._act(Wp, H)
    T = S.T
    ex = S.r0 - S.bench[:, None]
    ex = np.where(np.isfinite(ex), ex, 0.0)
    out = {k: np.zeros(T) for k in ('added', 'removed', 'common', 'total')}
    if T > 2:
        c, p = ac[:-2], ap[:-2]
        d = (c - p) * ex[2:]
        a_ = (c > 0) & (p == 0)
        r_ = (p > 0) & (c == 0)
        m_ = (c > 0) & (p > 0)
        out['added'][2:] = np.where(a_, d, 0.0).sum(1)
        out['removed'][2:] = np.where(r_, d, 0.0).sum(1)
        out['common'][2:] = np.where(m_, d, 0.0).sum(1)
        out['total'][2:] = d.sum(1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--route', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    ap.add_argument('--limit', type=int, default=0, help='计时样本: 只跑前 n 个配置')
    ap.add_argument('--rerun-failed', action='store_true',
                    help='只重跑本分片 csv 里 FAILED_TECH 的描述符, 结果写 <tag>_rerun.* (合并时 SUCCEEDED 优先)')
    ap.add_argument('--missing', action='store_true',
                    help='只跑 merged_<route>.csv 里还没有 SUCCEEDED 的描述符 (A0 增补), 结果写 <tag>_add.*')
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS or I.post_allowed(a.segment)   # Stage 3 技术修复: 后段需 E6i 记录 B
    t0 = time.time()
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    dd = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    dd = dd[dd.route_id == a.route]
    groups = collections.OrderedDict()
    for r in dd.to_dict('records'):
        groups.setdefault(config_key(r), []).append(r)
    keys = list(groups)[a.shard::a.nshard]
    if a.limit:
        keys = keys[:a.limit]
    if a.rerun_failed:
        prev = pd.read_csv(os.path.join(I.RES, 'accounts', a.segment, '%s_%02d.csv' % (a.route, a.shard)))
        bad = set(prev.loc[prev.status == 'FAILED_TECH', 'descriptor_id'])
        keys = [k for k in keys if any(r['descriptor_id'] in bad for r in groups[k])]
    if a.missing:
        mp = os.path.join(I.RES, 'accounts', a.segment, 'merged_%s.csv' % a.route)
        have = set()
        if os.path.exists(mp):
            m_ = pd.read_csv(mp, low_memory=False)
            have = set(m_.loc[m_.status == 'SUCCEEDED', 'descriptor_id'])
        keys = [k for k in keys if any(r['descriptor_id'] not in have for r in groups[k])]
    S = I.seg_i(a.segment, warm=False)
    RN = Runner(S)
    print('段就绪 %.0fs; %s shard %d/%d: %d 配置 (%d 描述符)'
          % (time.time() - t0, a.route, a.shard, a.nshard, len(keys),
             sum(len(groups[k]) for k in keys)), flush=True)
    rows, series = [], collections.defaultdict(list)
    n_fail = n_na = 0
    for gi, k in enumerate(keys):
        rs = groups[k]
        r0 = rs[0]
        mid = r0['member_id']
        members = [x for x in str(mid).replace('+', '|').split('|') if x in FE.CATALOG_IDS]
        ts = time.time()
        try:
            I.guard_i(members, [ROLE_RULE.get(r0['role'], r0['role'])], segment=a.segment,
                      label_end=str(S.dates[-1].date()), use='trade', where=r0['descriptor_id'])
            mask, wmul, info = RN.build(r0)
        except ValueError as e:
            if 'NOT_APPLICABLE' in str(e):
                n_na += 1
                for r in rs:
                    rows.append(dict(descriptor_id=r['descriptor_id'], status='NOT_APPLICABLE',
                                     note=str(e)[:120]))
                continue
            n_fail += 1
            traceback.print_exc()
            for r in rs:
                rows.append(dict(descriptor_id=r['descriptor_id'], status='FAILED_TECH',
                                 note=str(e)[:150]))
            continue
        except Exception as e:
            n_fail += 1
            traceback.print_exc()
            for r in rs:
                rows.append(dict(descriptor_id=r['descriptor_id'], status='FAILED_TECH',
                                 note='%s: %s' % (type(e).__name__, str(e)[:150])))
            continue
        M = RN.mother(r0['mother_id'])
        Wc = E.dev_weights(S, mask)
        if wmul is not None:
            Wc = Wc * wmul
        Wp = RN.parent_W[r0['mother_id']]
        nC = mask.sum(1)
        cm, restricted = M.core_matchN(nC)
        rv, _ = M.core_matchN(nC, largest=True)
        Wcm, Wrv = E.dev_weights(S, cm), E.dev_weights(S, rv)
        days = nC > 0
        Wpc = Wp * days[:, None]
        W1s, W0s = E.scale_to_common(Wc, Wp)
        changed = int((mask != M.B).sum())
        for r in rs:
            H = int(r['H'])
            g, p, u, n = E.pnl_W(S, Wc, H, I.COST)
            gp_, pp_, up_, np_ = RN.ppnl(r0['mother_id'], H)
            ctl = {'core_matchN': E.pnl_W(S, Wcm, H, I.COST),
                   'reverse_matchN': E.pnl_W(S, Wrv, H, I.COST),
                   'parent_common': E.pnl_W(S, Wpc, H, I.COST)}
            s1_, s0_ = E.pnl_W(S, W1s, H, I.COST), E.pnl_W(S, W0s, H, I.COST)
            at = attrib(S, Wc, Wp, H)
            resid = float(np.max(np.abs(at['total'] - (at['added'] + at['removed'] + at['common']))))
            both = np.isfinite(n) & np.isfinite(np_)
            dn = np.where(both, n - np_, np.nan)
            rec = dict(descriptor_id=r['descriptor_id'], status='SUCCEEDED', route_id=a.route,
                       mother_id=r0['mother_id'], member_id=mid, role=r0['role'],
                       strength=r0['strength'], policy=r0.get('policy'), direction=r0['direction'],
                       direction_role=r0.get('direction_role'), H=H,
                       representative=bool(r0.get('representative')),
                       net8_ann=I.ann(n), gross_ann=I.ann(g), net12_ann=I.ann(g - u * I.COST_HI / 1e4),
                       turn_mean=float(np.nanmean(u)), pos_mean=float(np.nanmean(p)),
                       parent_net8_ann=I.ann(np_), d_net8_ann=I.ann(dn),
                       d_gross_ann=I.ann(np.where(both, g - gp_, np.nan)),
                       d_turn=float(np.nanmean(u - up_)), d_pos=float(np.nanmean(p - pp_)),
                       n_changed_cells=changed, target_n_mean=float(nC.mean()),
                       parent_n_mean=float(M.B.sum(1).mean()),
                       d_vs_core_matchN=I.ann(n - ctl['core_matchN'][3]),
                       d_vs_reverse_matchN=I.ann(n - ctl['reverse_matchN'][3]),
                       d_vs_parent_common=I.ann(n - ctl['parent_common'][3]),
                       d_same_capital=I.ann(s1_[3] - s0_[3]),
                       core_matchN_restricted=bool(restricted),
                       attr_added_ann=float(np.mean(at['added'])) * I.ANN,
                       attr_removed_ann=float(np.mean(at['removed'])) * I.ANN,
                       attr_common_ann=float(np.mean(at['common'])) * I.ANN,
                       attr_identity_resid=resid, note=info.get('note', ''))
            rows.append(rec)
            series['descriptor_id'].append(r['descriptor_id'])
            for nm, arr in (('net8', n), ('gross', g), ('pos', p), ('turn', u), ('dnet8', dn),
                            ('dcore', n - ctl['core_matchN'][3]), ('dsamecap', s1_[3] - s0_[3])):
                series[nm].append(np.asarray(arr, np.float64))
        if (gi + 1) % 25 == 0:
            print('  %d/%d 配置  %.0fs  (末个 %.2fs)' % (gi + 1, len(keys), time.time() - t0,
                                                   time.time() - ts), flush=True)
    od = os.path.join(I.RES, 'accounts', a.segment)
    os.makedirs(od, exist_ok=True)
    tag = '%s_%02d' % (a.route, a.shard) + ('_timing' if a.limit else '') + \
        ('_rerun' if a.rerun_failed else '') + ('_add' if a.missing else '')
    d = pd.DataFrame(rows)
    p_csv = os.path.join(od, tag + '.csv')
    I.atomic_write_csv(p_csv, d)
    outs = [p_csv]
    if series['descriptor_id']:
        buf = io.BytesIO()
        np.savez(buf, descriptor_id=np.asarray(series['descriptor_id']),
                 **{k: np.vstack(v) for k, v in series.items() if k != 'descriptor_id'})
        p_npz = os.path.join(od, tag + '.npz')
        I.atomic_write_bytes(p_npz, buf.getvalue())
        outs.append(p_npz)
    I.write_receipt(os.path.join(I.RES, 'task_status', 'stage2_%s_%s.receipt.json'
                                 % (a.segment, tag)), 'stage2:%s:%s' % (a.segment, tag), outs,
                    status='SUCCEEDED' if n_fail == 0 else 'FAILED', n_fail=n_fail, n_na=n_na,
                    n_configs=len(keys), elapsed_s=round(time.time() - t0, 1))
    ok = d[d.status == 'SUCCEEDED'] if 'status' in d else d
    mx = float(ok.attr_identity_resid.max()) if len(ok) else float('nan')
    print('[%s %s] 配置 %d: 成功行 %d / 失败配置 %d / 不适用 %d; 归因残差 max %.2e; %.0fs'
          % (a.segment, tag, len(keys), len(ok), n_fail, n_na, mx, time.time() - t0))
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == '__main__':
    main()
