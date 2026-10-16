# -*- coding: utf-8 -*-
"""E6m Stage A（brief §5 S2；附录 B / C；plan §13.1）：掩码层事实表 + 校准分布。任何收益读取之前落盘；不读任何收益。
不含 MDE80 / 配对 se / IC / 前向收益（附录 B 末句）。
- 名单：名单阶段输出 masks/<段>/<形态>.npz（主配置）与 masks_aux/<段>/<形态>.npz（附属）；门层事实沿 facts*.csv。
- 权重：源 DEV（e6j_prod.weights_of → assign_weights_dev），只算形成日目标权重，不记账。
- size：e6k_env.Seg 同口径，z_T = 形成日 T 收盘 mcap 在当日 clean 域 rank(pct)；z_LAG1 = 前一日 z_T 前向填充；size 五分组。
- 目标级统计：e6k_acct.Acct.target_stats / edit_gap 逐字转录（DEV 权重由源函数给），得到：
  - 组合层 size 紧区间（T / L）、编辑 gap、small30、未知 size 权重、lv5；
  - 换入 / 换出 / 编辑数、编辑权重份额。
- 补充事实：
  - 带内份额 s_w 与可动名额 m（逐日 → 段均）、带内 Q 缺失数、带内 Q 与旧 K 排序不一致对份额（逐日 → 段均）；
  - PASS 率（每 c）、回填资本份额、HARD 最终人数增加日数；
  - 与 NATIVE（同 α .25）/ SOURCE HG10 / LAG1_10 / OLD_RULE 的编辑重叠（逐日 Jaccard 均值）；
  - V 各状态可施加数；STATE_UNKNOWN 日数。
- 校准（附录 C，名单 / 权重层）：PORT3 紧区间中点绝对值的分位（50 / 90 / 95）在 C1 / COPY 上的分布；lv5 在父与子上的分布；
  EDIT_MATCH 的 J 与 J*/J；带内份额随 w 的实际曲线。随机编辑的分布留给随机层，H 剖面要用收益，不在 Stage A。
B2 开发期在 mock 上运行；阶段 S 原样读真实名单。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import hashlib
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_ops as O
import e6m_s_ops as S
import e6m_s_mock as MK
import e6m_s_meas as ME
import e6m_s_real as RL

FORMS = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')


class SizeCtx(object):
    """e6k_env.Seg 的 size 部分（W03）在 mock 坐标上的转录。"""

    def __init__(self, seg):
        ctx = seg.ctx
        pool0 = seg.pool0
        mc = ctx['data']['mcap'].astype(float).reindex(index=pool0.index, columns=pool0.columns)
        cl = ctx['clean'].reindex(index=pool0.index, columns=pool0.columns).fillna(0) == 1
        zfull = mc.where(cl).rank(axis=1, pct=True).values
        self.zc = np.ascontiguousarray(zfull[:, seg.ccols])
        prev = np.full(self.zc.shape, np.nan)
        prev[1:] = self.zc[:-1]
        val, age = ffill_age(prev)
        self.zLc = val
        self.zT = self.zc[seg.ci.t, seg.ci.c]
        self.zL = self.zLc[seg.ci.t, seg.ci.c]
        b5 = size_bins(zfull, 5)
        clv = cl.values
        self.share5 = np.zeros((seg.T, 5))
        for g in range(5):
            self.share5[:, g] = ((b5 == g) & clv).sum(1) / np.maximum(clv.sum(1), 1)
        self.b5 = size_bins(self.zc, 5)


def size_bins(z, G):
    out = np.full(z.shape, -1, np.int64)
    ok = np.isfinite(z)
    out[ok] = np.clip(np.ceil(z[ok] * G - 1e-12).astype(np.int64) - 1, 0, G - 1)
    return out


def ffill_age(A):
    T, N = A.shape
    ok = np.isfinite(A)
    idx = np.where(ok, np.arange(T)[:, None], -1)
    last = np.maximum.accumulate(idx, axis=0)
    val = np.where(last >= 0, A[np.maximum(last, 0), np.arange(N)[None, :]], np.nan)
    age = np.where(last >= 0, np.arange(T)[:, None] - last, -1)
    return val, age


class Targets(object):
    """名单 → 源 DEV 目标权重（按名单内容缓存）→ e6k_acct.target_stats 转录。"""

    def __init__(self, seg):
        self.seg = seg
        self.sz = SizeCtx(seg)
        self._w = {}

    def weights(self, kept):
        h = hashlib.sha1(np.packbits(kept).tobytes()).hexdigest()
        if h not in self._w:
            import e6j_prod as PR
            seg = self.seg
            hold, w = PR.weights_of(seg.ctx, seg.to_tn(kept))
            W = np.asarray(w.reindex_like(seg.pool0).fillna(0.0).values, float)
            wc = seg.cells(W)
            ids = np.flatnonzero(kept)
            self._w[h] = dict(ids=ids, t=seg.ci.t[ids], c=seg.ci.c[ids], w=wc[ids])
        return self._w[h]

    def wcell(self, tg):
        out = np.zeros(self.seg.n)
        out[tg['ids']] = tg['w']
        return out

    def stats(self, kept, par_kept=None):
        seg, T, sz = self.seg, self.seg.T, self.sz
        ci = seg.ci
        tg = self.weights(kept)
        t, c, w, ids = tg['t'], tg['c'], tg['w'], tg['ids']
        o = {}
        o['nnames'] = np.bincount(t, minlength=T).astype(float)
        P_ = np.bincount(t, weights=w, minlength=T)
        o['wsum'] = P_
        zT, zL = sz.zT[ids], sz.zL[ids]
        with np.errstate(divide='ignore', invalid='ignore'):
            for nm, z in (('T', zT), ('L', zL)):
                kn = np.isfinite(z)
                num = np.bincount(t[kn], weights=w[kn] * z[kn], minlength=T)
                unk = np.bincount(t[~kn], weights=w[~kn], minlength=T)
                o['z%s_mean' % nm] = np.where(P_ - unk > 0, num / (P_ - unk), np.nan)
                o['unk%s' % nm] = np.where(P_ > 0, unk / P_, np.nan)
            s30 = np.isfinite(zT) & (zT <= 0.3)
            o['small30'] = np.where(P_ > 0, np.bincount(t[s30], weights=w[s30], minlength=T) / P_, np.nan)
        b = sz.b5[t, c]
        dev = np.full((T, 5), 0.0)
        kb = b >= 0
        np.add.at(dev, (t[kb], b[kb]), w[kb])
        lv = dev - sz.share5
        o['lv5'] = np.where(P_ > 0, lv.max(axis=1), np.nan)
        if par_kept is not None:
            ptg = self.weights(par_kept)
            wc = self.wcell(tg)
            wb = self.wcell(ptg)
            Pb = np.bincount(ptg['t'], weights=ptg['w'], minlength=T)
            both = (P_ > 0) & (Pb > 0)
            with np.errstate(divide='ignore', invalid='ignore'):
                a = np.where(both[ci.t], wc / np.where(P_ > 0, P_, 1)[ci.t] - wb / np.where(Pb > 0, Pb, 1)[ci.t], 0.0)
            for nm, z in (('T', sz.zT), ('L', sz.zL)):
                kn = np.isfinite(z)
                k_ = np.bincount(ci.t, weights=np.where(kn, a * np.where(kn, z, 0.0), 0.0), minlength=T)
                lo = k_ + np.bincount(ci.t, weights=np.where(~kn, np.minimum(a, 0.0), 0.0), minlength=T)
                hi = k_ + np.bincount(ci.t, weights=np.where(~kn, np.maximum(a, 0.0), 0.0), minlength=T)
                o['sz%s_lo' % nm] = np.where(both, 100.0 * lo, np.nan)
                o['sz%s_hi' % nm] = np.where(both, 100.0 * hi, np.nan)
            ent = kept & ~par_kept
            ext = par_kept & ~kept
            o['n_in'] = np.bincount(ci.t[ent], minlength=T).astype(float)
            o['n_out'] = np.bincount(ci.t[ext], minlength=T).astype(float)
            o['n_edits'] = o['n_in'] + o['n_out']
            with np.errstate(divide='ignore', invalid='ignore'):
                o['edit_w_in'] = np.where(P_ > 0, np.bincount(ci.t, weights=np.where(ent, wc, 0.0), minlength=T) / P_, np.nan)
            for nm, z in (('T', sz.zT), ('L', sz.zL)):
                o['gap%s' % nm] = edit_gap(seg, ent, ext, z)
        return o


def edit_gap(seg, ent, ext, z):
    T = seg.T
    out = np.full(T, np.nan)
    ci = seg.ci
    for d in np.unique(ci.t[ent | ext]):
        a0, a1 = seg.off[d], seg.off[d + 1]
        e = z[a0:a1][ent[a0:a1]]
        x = z[a0:a1][ext[a0:a1]]
        e = e[np.isfinite(e)]
        x = x[np.isfinite(x)]
        if len(e) and len(x):
            out[d] = np.median(e) - np.median(x)
    return out


def summarize(o, par=None):
    """目标级日数组 → 段事实（均值 / 份额 / 计数）。"""
    m = lambda x: float(np.nanmean(x)) if np.isfinite(x).any() else np.nan
    r = dict(nnames_mean=m(o['nnames']), wsum_mean=m(o['wsum']), lv5_mean=m(o['lv5']), small30_mean=m(o['small30']), unkT_mean=m(o['unkT']),
             unkL_mean=m(o['unkL']))
    if 'n_in' in o:
        mid = np.abs(0.5 * (o['szT_lo'] + o['szT_hi']))
        fin = np.isfinite(mid)
        r.update(n_in=int(np.nansum(o['n_in'])), n_out=int(np.nansum(o['n_out'])), n_edits=int(np.nansum(o['n_edits'])), edit_w_in_mean=m(o['edit_w_in']),
                 port_size_lo_T=m(o['szT_lo']), port_size_hi_T=m(o['szT_hi']), port_size_lo_L=m(o['szL_lo']), port_size_hi_L=m(o['szL_hi']),
                 port3_mid_abs_p50=float(np.percentile(mid[fin], 50)) if fin.any() else np.nan,
                 port3_mid_abs_p90=float(np.percentile(mid[fin], 90)) if fin.any() else np.nan,
                 port3_mid_abs_p95=float(np.percentile(mid[fin], 95)) if fin.any() else np.nan,
                 port3_days_outside=int(np.nansum((o['szT_lo'] < -3.0) | (o['szT_hi'] > 3.0))),
                 edit_gap_mean_T=m(o['gapT']) * 100.0 if np.isfinite(o['gapT']).any() else np.nan,
                 edit_gap_absmean_T=abs(m(o['gapT']) * 100.0) if np.isfinite(o['gapT']).any() else np.nan,
                 edit_gap_days_T=int(np.isfinite(o['gapT']).sum()))
        if par is not None:
            r['small30_delta'] = r['small30_mean'] - par['small30_mean']
            r['n_increase_days'] = int((o['nnames'] > par['_nnames']).sum())
    return r


def band_geometry(ctx, w):
    """带内份额 s_w = 2m/N、可动名额 m、带内 Q 缺失数、带内 Q 与旧 K 排序不一致对份额（逐日 → 段均 / 合计）。"""
    sw, mm, miss, disc = [], 0, 0, []
    for d, a, e, K in ctx.days:
        o = ctx.orders[d]
        N = e - a
        A, B, C, j = O.band_parts(o, K, w)
        sw.append(2.0 * j / N if N else np.nan)
        mm += j
        kq = ctx.kq[a:e][B]
        miss += int((~np.isfinite(kq)).sum())
        fin = np.isfinite(kq)
        if fin.sum() >= 2:
            q = kq[fin]
            r0 = np.arange(len(B))[fin]                       # B 内旧 K 次序（已按 (s0, ticker) 排）
            dq = np.sign(q[:, None] - q[None, :])
            dk = np.sign(r0[:, None] - r0[None, :])
            iu = np.triu_indices(len(q), 1)
            disc.append(float(np.mean(dq[iu] * dk[iu] < 0)))
    return dict(band_share_mean=float(np.nanmean(sw)) if sw else np.nan, movable_slots_total=int(mm), band_q_missing_total=int(miss),
                band_q_k0_discordant_pair_share=float(np.mean(disc)) if disc else np.nan)


def jaccard_days(seg, A, B, F0):
    """两目标相对父的编辑集合逐日 Jaccard（两边都有编辑的日子）均值。"""
    ea, eb = A != F0, B != F0
    vals = []
    for d in range(seg.T):
        a0, a1 = int(seg.off[d]), int(seg.off[d + 1])
        x, y = ea[a0:a1], eb[a0:a1]
        u = int((x | y).sum())
        if x.any() and y.any() and u:
            vals.append(int((x & y).sum()) / u)
    return float(np.mean(vals)) if vals else np.nan


def run(seg_name, form, struct='mock'):
    t0 = time.time()
    seg = RL.seg_of(seg_name, struct)
    st = seg.struct(form)
    me = ME.load(seg_name)
    TG = Targets(seg)
    mz = np.load(RL.root(struct, 'masks', seg_name, '%s.npz' % form), allow_pickle=False)
    n = int(mz['n_cells'][0])
    cids = [str(x) for x in mz['config_ids']]
    un = lambda bits: np.unpackbits(bits)[:n].astype(bool)
    finals = {c: un(mz['final_bits'][j]) for j, c in enumerate(cids)}
    F0 = un(mz['parent_final_bits'])
    facts = pd.read_csv(RL.root(struct, 'masks', seg_name, 'facts_%s.csv' % form), keep_default_na=False, na_values=[''], dtype={'param': str, 'alpha': str})
    po = TG.stats(F0)
    par = summarize(po)
    par['_nnames'] = po['nnames']
    ctx = S.Ctx(st, RL.kfs_of(seg, struct, me)['Q0'], mem_gate=RL.mem_gate_of(struct))
    refs = {}
    for c in cids:
        p = c.split('|')
        if p[0] == 'Q0' and p[2] == 'LINEAR' and p[4] == 'a0.25' and p[5] in ('NONE', 'HG10', 'LAG1_10'):
            refs['Q0_' + p[5]] = finals[c]
        if p[2] == 'OLD_RULE':
            refs['OLDRULE_' + p[5]] = finals[c]
    rows = []
    geo = {}
    for r in facts.itertuples():
        base = dict(segment=seg_name, form=form, target=r.config_id, kind='MAIN', block=r.block, measurement=r.measurement, operator=r.operator,
                    param=r.param, alpha=r.alpha, memory=r.memory, status=r.status)
        if r.status != 'COMPUTED':
            rows.append(base)
            continue
        F = finals[r.config_id]
        o = TG.stats(F, F0)
        x = summarize(o, par)
        x.update({k: getattr(r, k) for k in facts.columns if k.startswith('f_') and pd.notna(getattr(r, k))})
        if r.block in ('BAND_Q', 'BAND_BLEND', 'LEAK_BRIDGE') and r.measurement == 'Q0':
            w = float(r.param)
            if w not in geo:
                geo[w] = band_geometry(ctx, w)
            x.update(geo[w])
        if r.block == 'FILTER' and r.measurement == 'Q0':
            c_ = float(r.param)
            rates = [float(np.mean(ctx.kq[a:e][np.isfinite(ctx.kq[a:e])] <= c_)) for d, a, e, K in ctx.days if np.isfinite(ctx.kq[a:e]).any()]
            x['pass_rate_mean'] = float(np.mean(rates)) if rates else np.nan
        if r.block == 'EDIT_MATCH':
            J, Js = getattr(r, 'f_J', np.nan), getattr(r, 'f_J_star', np.nan)
            x['edit_truncated_share'] = 1.0 - Js / J if (pd.notna(J) and J) else np.nan
        for k, R_ in refs.items():
            if r.config_id.split('|')[2] != 'PARENT':
                x['edit_overlap_' + k] = jaccard_days(seg, F, R_, F0)
        rows.append(dict(base, **x))
    az = RL.root(struct, 'masks_aux', seg_name, '%s.npz' % form)
    if os.path.exists(az):
        A = np.load(az, allow_pickle=False)
        for j, k in enumerate([str(x) for x in A['aux_keys']]):
            F = un(A['final_bits'][j])
            x = summarize(TG.stats(F, F0), par)
            rows.append(dict(segment=seg_name, form=form, target=k, kind='AUX', block=k.split('|')[-1], status='COMPUTED', **x))
    df = pd.DataFrame(rows)
    zs = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)
    dts = [str(d)[:10] for d in seg.dates]
    di = {s: i for i, s in enumerate(zs['dates'])}
    vs = zs['vol_state'][[di[s] for s in dts]]
    head = dict(segment=seg_name, form=form, parent_nnames_mean=par['nnames_mean'], parent_lv5_mean=par['lv5_mean'],
                parent_small30_mean=par['small30_mean'], state_unknown_days_vol=int((vs < 0).sum()), days=seg.T,
                trend_unknown_share_parent=float(np.mean(me['trend'][F0] < 0)) if F0.any() else np.nan)
    od = RL.root(struct, 'stage_a', seg_name)
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'mask_facts_%s.csv' % form)
    p2 = os.path.join(od, 'mask_facts_head_%s.json' % form)
    M.atomic_write_csv(p1, df)
    M.atomic_write_json(p2, head)
    import resource
    T = dict(rows=len(df), dev_weight_sets=len(TG._w), wall_s=round(time.time() - t0, 1), struct=struct,
             rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    M.write_receipt(os.environ.get('E6M_TASK', ('S_dev_stage_a_%s_%s' if struct == 'mock' else 'S_stage_a_%s_%s') % (seg_name, form)), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__],
                    note='Stage A 名单层事实（不读收益）', **T)
    print(json.dumps(dict(seg=seg_name, form=form, **T), ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--form', required=True)
    ap.add_argument('--struct', default='mock', choices=['mock', 'real'])
    a = ap.parse_args()
    sys.exit(run(a.seg, a.form, a.struct))
