# -*- coding: utf-8 -*-
"""E6m 随机层驱动（plan §9.3；auxiliary_manifest_E6m item 2–4；e6l_run_rand 同构）。
一个任务 = (段, 机制, 测量, 路径区间)。对该测量在该机制下的全部登记 owner，逐路径生成最终名单（e6m_s_rand），然后：
- 阶段 S（--mode accounts）：逐路径源 DEV + 多 H 账本（e6l_fast.AcctFast），e6l_run_rand.accum_nb 同构累加；
  输出 randoms/<机制>/<段>/<测量>__p<起>_<数>.npz，格式同 E6l（s_net / n_net / … / dsum / dsq / dcnt / samp / fp）。
- B2 开发（--mode masks）：只在 mock 上生成名单，记录每路径人数、相对真实的编辑数与名单指纹。不读收益。
内容随机在 B2 用 PROFILE_STANDIN 替身；阶段 S 换 e6k_random（Legacy / NewCond，E6k 键）。"""
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
import e6m_s_ops as S
import e6m_s_rand as RN

POLICY = ('LEGACY_POLICY_RANDOM', 'CONTENT_ISK_P5')
TRENDC = {'UP': 2, 'DOWN': 0, 'MIXED': 1}


_SUP = []


def sup_table():
    if not _SUP:
        _SUP.append(M.read_csv_keep(M.P('registry', 'supplemental_E6m.csv'), dtype=str))
    return _SUP[0]


def parse_owner(o):
    """标准 owner（9 段描述符）或补充 owner（SUPP:<16 位>，按 supplemental_E6m 展开；cfg 不含 H，同配置不同 H 共用一次名单）。"""
    if o.startswith('SUPP:'):
        S_ = sup_table()
        r = S_[S_.supp_id.str.startswith(o[5:])]
        if len(r) != 1:
            return None
        r = r.iloc[0]
        num = lambda s: None if s in ('NOT_APPLICABLE', '-', '') else float(s)
        return dict(measurement=r.measurement, parent=r.parent, operator=r.operator, param=num(r.param), alpha=num(r.alpha), memory=r.memory,
                    H=int(r.H), adapter=r.adapter, condition=r.condition, diag=r.diagnostic,
                    cfg='SUPP|%s|%s|%s|%s|%s|%s|%s' % (r.diagnostic, r.measurement, r.parent, r.operator, r.param, r.alpha, r.condition))
    p = o.split('|')
    if len(p) < 9:
        return None
    num = lambda s: float(s[1:]) if s not in ('-', '') else None
    return dict(measurement=p[0], parent=p[1], operator=p[2], param=num(p[3]), alpha=num(p[4]), memory=p[5], H=int(p[6][1:]), adapter=p[7],
                condition=p[8], cfg='|'.join(p[:6] + p[7:]))


class RT(object):
    """一段 × 形态的运行环境（mock 或真实 Seg / Struct 皆可，只用公共接口）。mem_gate：None = 转录（mock），阶段 S 传源记忆门。"""

    def __init__(self, seg, form, me, cal, ind_c, k0_c, kfs, down=None, mem_gate=None):
        self.seg, self.form, self.me, self.cal, self.ind_c, self.k0_c = seg, form, me, cal, ind_c, k0_c
        self.st = seg.struct(form)
        self.kfs = kfs
        self.mem_gate = mem_gate
        self._ctx = {}
        self.down = down or (lambda G: self.st.down(G))
        self.keys = RN.Keys(seg, cal)
        self.F0 = self.down(self.ctx('Q0').U0[None, :])[0]

    def ctx(self, meas):
        if meas not in self._ctx:
            c = S.Ctx(self.st, self.kfs[meas], mem_gate=self.mem_gate)
            c._cal = self.cal
            self._ctx[meas] = c
        return self._ctx[meas]


def content(rt, mech, meas, owner, paths, draws=None):
    c = rt.ctx(meas)
    if draws is not None:
        return draws(mech, meas, rt.form, paths)[:, c.ids]
    return RN.standin_content(c, paths, mech, owner, rt.form)


def gate_with_content(rt, o, KQ, paths):
    """owner 算子在逐路径坏度 KQ（门域坐标）下的门 (P, len(ids))。"""
    c = rt.ctx(o['measurement'])
    op, mem = o['operator'], o['memory']
    if o.get('diag') in ('NATIVE_METRIC_LAG', 'COPY_NATIVE_METRIC_LAG'):     # 补充对象：向量化带算子无 metric 版，逐路径走标量算子
        out = []
        for i in range(KQ.shape[0]):
            ci = S.Ctx.__new__(S.Ctx)
            ci.__dict__.update(c.__dict__)
            ci.kq = KQ[i]
            ci.kf = RN._cells(c, KQ[i])
            ci._ns = {}
            out.append(S.band_gates(ci, o['param'], o['alpha'], 'PROTECTED_LAG10', copy=o['diag'].startswith('COPY'), metric=True)[1])
        return np.vstack(out)
    if o.get('diag'):
        raise ValueError('补充对象 %s 的内容随机未登记' % o['diag'])
    if op == 'LINEAR':
        return RN.source_paths(c, KQ, o['alpha'], mem)
    if op in ('BAND_Q', 'BAND_BLEND'):
        gn, gm = RN.band_paths(c, KQ, o['param'], o['alpha'] if op == 'BAND_BLEND' else None, 'PROTECTED_LAG10' if mem != 'NONE' else 'NONE')
        return gn if mem == 'NONE' else gm
    if op == 'PRIORITY_PASS':
        return RN.priority_paths(c, KQ, o['param'], mem)
    if op == 'HARD_CONJ':
        return RN.hard_paths(c, KQ, o['param'], mem)
    if op.startswith('EDIT_'):
        out = []
        for i in range(KQ.shape[0]):
            ci = S.Ctx.__new__(S.Ctx)
            ci.__dict__.update(c.__dict__)
            ci.kq = KQ[i]
            ci.kf = RN._cells(c, KQ[i])
            ci._ns = {}
            out.append(S.edit_gates(ci, o['alpha'], o['param'])[0][op.replace('EDIT_', '')])
        return np.vstack(out)
    if op in ('SLOT_Q', 'SLOT_BLEND25'):
        out = []
        for i in range(KQ.shape[0]):
            ci = S.Ctx.__new__(S.Ctx)
            ci.__dict__.update(c.__dict__)
            ci.kf = RN._cells(c, KQ[i])
            out.append(S.slot_bridge_gate(ci, o['param'], op)[0])
        return np.vstack(out)
    raise ValueError('内容随机不支持的算子：%s' % op)


def path_finals(rt, mech, owner, paths, draws=None):
    """→ (F (P, n) 最终名单, 事实)。"""
    o = parse_owner(owner)
    if o is None:
        raise ValueError('非标准 owner（补充对象由调用方展开）：%s' % owner)
    c = rt.ctx(o['measurement']) if o['measurement'] in rt.kfs else None
    if mech in POLICY:
        if o['operator'] in ('DELETE_HIGH', 'DELETE_LOW'):
            raise ValueError('V 的内容随机未登记')
        KQ = content(rt, mech, o['measurement'], o['cfg'], paths, draws)
        return rt.down(gate_with_content(rt, o, KQ, paths)), {}
    if mech == 'R-BAND':
        KQ = RN.r_band_content(c, paths, o['cfg'], rt.form, o['param'])
        return rt.down(gate_with_content(rt, o, KQ, paths)), {}
    if mech == 'R-FILTER_LABEL':
        KQ = RN.r_filter_content(c, paths, o['cfg'], rt.form)
        return rt.down(gate_with_content(rt, o, KQ, paths)), {}
    if mech in ('R-EDIT_FIXED_OUT', 'R-EDIT_BOTH_RANDOM'):
        G, f = RN.r_edit(c, paths, o['cfg'], rt.form, o['alpha'], o['param'], o['operator'].replace('EDIT_', ''),
                         'FIXED_OUT' if mech.endswith('FIXED_OUT') else 'BOTH_RANDOM', rt.ind_c, rt.k0_c)
        return rt.down(G), f
    if mech == 'DELETE_BUDGET_COND':
        return delete_budget_finals(rt, o, paths)
    if mech in ('R-MEMORY-HG', 'R-MEMORY-LAG'):
        return rt.down(memory_gate(rt, o, mech, paths)), {}
    raise ValueError(mech)


def delete_budget_finals(rt, o, paths):
    seg = rt.seg
    ind = rt.ind_c[seg.ci.t, seg.ci.c]
    size3 = size_terciles(seg)
    if o['operator'] == 'HARD_CONJ':
        c = rt.ctx(o['measurement'])
        Gh, f = S.hard_gates(c, o['param'], o['memory'])
        pre_dom = c.U0 if o['memory'] == 'NONE' else S.source_gate(S._OldCtx(c), 0.0, 'LAG1_10')[0]
        pre = np.zeros(seg.n, bool)
        pre[c.ids] = pre_dom
        dele = np.zeros(seg.n, bool)
        dele[c.ids] = pre_dom & ~Gh
        fin = np.zeros(seg.n, bool)
        fin[c.ids] = np.isfinite(c.kq)
        grp = (ind + 1) * 4 + size3
        Gc = RN.delete_budget(seg, rt.keys, pre, dele, grp, fin, o['cfg'], rt.form, paths)
        return rt.down(Gc[:, c.ids]), {}
    # V_STATE：父最终名单上同层同数随机删（层 = Trend × 行业 × size3；候选 = V 有限且满足条件）
    import e6m_s_aux  # noqa: F401（口径同 e6m_s_run_masks.Runner.v_state）
    tr = rt.me['trend']
    cond = o['condition']
    elig = {'ALL': np.ones(seg.n, bool), 'ALL_KNOWN': tr >= 0, 'DOWN_MIXED': (tr == TRENDC['DOWN']) | (tr == TRENDC['MIXED']),
            'UP': tr == TRENDC['UP']}[cond] & np.isfinite(rt.me['vol'])
    real = rt.v_final(o)
    dele = rt.F0 & ~real
    grp = ((tr.astype(np.int64) + 1) * 1000 + (ind + 1)) * 4 + size3
    return RN.delete_budget(seg, rt.keys, rt.F0, dele, grp, elig, o['cfg'], rt.form, paths), {}


def size_terciles(seg):
    """当日 pool0 单元内 log 市值三分（e6m_b3_build.terc_ref 同式；缺失 = 3）。"""
    import e6m_b3_build as BB
    lm = seg.cells(seg.ctx['log_mcap'].reindex_like(seg.pool0).to_numpy(float))
    out = np.full(seg.n, 3, np.int64)
    for d in range(seg.T):
        a0, a1 = int(seg.off[d]), int(seg.off[d + 1])
        v = BB.terc_ref(lm[a0:a1], np.ones(a1 - a0, bool)).astype(np.int64)
        out[a0:a1] = np.where(v < 0, 3, v)
    return out


def memory_gate(rt, o, mech, paths):
    c = rt.ctx(o['measurement'])
    st = rt.st
    op = o['operator']
    kind = 'HG' if mech == 'R-MEMORY-HG' else 'LAG'
    if op == 'LINEAR':
        sc = st.gate_scores(S.native_q(c.q0, c.kf, o['alpha'])[None, :])[0]
        U = st.gate_keep(sc[None, :])[0]
        be = 10.0 * st.bunit
        return RN.r_memory(c, paths, o['cfg'], rt.form, kind, lambda d, a, e, K, oo: U[a:e],
                           lambda d, a, e, K, oo, mark: S.select_rows((sc[a:e] - be * mark)[None, :], K)[0],
                           lambda d, a, e, K, oo: np.zeros(e - a, np.int64))
    if op in ('BAND_Q', 'BAND_BLEND'):
        import e6m_ops as O
        w = o['param']
        ins = c.kq if op == 'BAND_Q' else c.native_s(o['alpha'])

        def nomem(d, a, e, K, oo):
            return O.band(oo, c.sc0[a:e], c.kq[a:e], K, w, inside=ins[a:e], ids=c.tk[a:e])

        def sel(d, a, e, K, oo, mark):
            return O.band(oo, c.sc0[a:e], c.kq[a:e], K, w, inside=ins[a:e], prev_natural=mark, b=S.B_MEM, loading=c.load[a:e], ids=c.tk[a:e])

        def scope(d, a, e, K, oo):
            A, B, C, j = O.band_parts(oo, K, w)
            g = np.full(e - a, -1, np.int64)
            g[B[np.isfinite(c.kq[a + B])]] = 0
            return g
        return RN.r_memory(c, paths, o['cfg'], rt.form, kind, nomem, sel, scope)
    if op == 'PRIORITY_PASS':
        import e6m_ops as O
        cc = o['param']

        def nomem(d, a, e, K, oo):
            return O.priority_pass(oo, c.sc0[a:e], c.kq[a:e], K, cc, ids=c.tk[a:e])[0]

        def sel(d, a, e, K, oo, mark):
            return O.priority_pass(oo, c.sc0[a:e], c.kq[a:e], K, cc, prev_natural=mark, b=S.B_MEM, loading=c.load[a:e], ids=c.tk[a:e])[0]

        def scope(d, a, e, K, oo):
            kq = c.kq[a:e]
            return np.where(np.isfinite(kq), (kq <= cc).astype(np.int64), 2)
        return RN.r_memory(c, paths, o['cfg'], rt.form, kind, nomem, sel, scope)
    raise ValueError('R-MEMORY 不支持：%s' % op)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--form', required=True)
    ap.add_argument('--mode', default='masks', choices=['masks', 'accounts'])
    ap.add_argument('--paths', type=int, default=4)
    ap.add_argument('--per-mech', type=int, default=3, help='masks 模式：每机制抽前 N 个 owner 做冒烟')
    ap.add_argument('--mech', default='', help='accounts 模式：机制')
    ap.add_argument('--path0', type=int, default=0)
    ap.add_argument('--npaths', type=int, default=1024)
    ap.add_argument('--batch', type=int, default=16)
    ap.add_argument('--group', default='', help='accounts 模式 MC 增补：只跑这个共享路径组的"测量"键')
    a = ap.parse_args()
    if a.mode == 'accounts':
        return main_accounts(a)
    t0 = time.time()
    import e6m_s_mock as MK
    import e6m_s_meas as ME
    import e6m_s_run_masks as RM
    seg = MK.MockSeg(a.seg)
    me = ME.load(a.seg)
    cal = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)['dates']
    ind = seg.ctx['industry'].reindex_like(seg.pool0).to_numpy(float)[:, seg.ccols]
    ind_c = np.where(np.isfinite(ind), ind, -1).astype(np.int64)
    k0_c = MK.dict_dense(seg.ctx['pcond'], seg.pool0)[:, seg.ccols]
    kfs = {'Q0': me['kQ0'], **{k: me['k' + k] for k in ('Q_MAX2', 'Q_MIN2', 'Q_LAGRAW1', 'Q_MEAN2')}}
    rt = RT(seg, a.form, me, cal, ind_c, k0_c, kfs)
    runner = RM.Runner(a.seg, a.form)
    rt.v_final = lambda o: runner.v_state(dict(operator=o['operator'], param=str(o['param']), condition=o['condition']))[0]
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str)
    A = A[A.item.isin(['2', '3', '4']) & A.owner_id.str.contains('|%s|' % a.form, regex=False)]
    paths = list(range(a.paths))
    rows = []
    for mech, g in A.groupby('mechanism'):
        seen = set()
        for r in g.itertuples():
            o = parse_owner(r.owner_id)
            if o is None or o['cfg'] in seen or len(seen) >= a.per_mech:
                continue
            if mech == 'NO_NEW_CONTENT_TO_PERMUTE':
                rows.append(dict(mechanism=mech, owner=o['cfg'], status='NO_NEW_CONTENT_TO_PERMUTE'))
                seen.add(o['cfg'])
                continue
            if o['measurement'] in ('C1', 'M', 'S'):
                rows.append(dict(mechanism=mech, owner=o['cfg'], status='SOURCE_WAIT'))
                seen.add(o['cfg'])
                continue
            seen.add(o['cfg'])
            t1 = time.time()
            F, f = path_finals(rt, mech, r.owner_id, paths)
            real = runner.down(runner.gate(dict(config_id=o['cfg'], block=_block_of(o), operator=o['operator'], measurement=o['measurement'],
                                                memory=o['memory'], param=str(o['param']) if o['param'] is not None else 'NOT_APPLICABLE',
                                                alpha=str(o['alpha']) if o['alpha'] is not None else 'NOT_APPLICABLE'))[0]) \
                if o['operator'] not in ('DELETE_HIGH', 'DELETE_LOW') else rt.v_final(o)
            fps = [hashlib.blake2b(np.packbits(F[i]).tobytes(), digest_size=8).hexdigest() for i in range(len(paths))]
            rows.append(dict(mechanism=mech, owner=o['cfg'], status='MASKS_OK', paths=len(paths), members=int(F.sum(1).mean()),
                             real_members=int(real.sum()), diff_vs_real_mean=int((F != real[None, :]).sum(1).mean()),
                             distinct_paths=len(set(fps)), seconds=round(time.time() - t1, 1), **{('f_' + k): v for k, v in f.items()}))
    df = pd.DataFrame(rows)
    p = M.P('stageS_dev', 'rand_masks_%s_%s.csv' % (a.seg, a.form))
    M.atomic_write_csv(p, df)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_rand_masks_%s_%s' % (a.seg, a.form)), [p], status='SUCCEEDED', code=[__file__, RN.__file__, M.__file__],
                    wall_s=round(time.time() - t0, 1), note='B2：随机名单冒烟（不读收益）')
    print(df.to_string(index=False), flush=True)
    return 0


def rand_rows(form, mech):
    """auxiliary_manifest item 2–4 中 owner 属本形态、机制 = mech 的登记随机行（标准 owner 与补充 owner）。"""
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str)
    A = A[A.item.isin(['2', '3', '4']) & (A.mechanism == mech)]
    S_ = sup_table()
    pf = {('SUPP:' + s[:16]): p for s, p in zip(S_.supp_id, S_.parent)}
    own_form = A.owner_id.map(lambda o: pf.get(o) if o.startswith('SUPP:') else (o.split('|')[1] if o.count('|') >= 8 else ''))
    return A[own_form == form][['aux_id', 'owner_id', 'H']].to_dict('records')


def group_of(owner):
    """共享路径组里的"测量"键（e6m_s_stats.mc_plan：desc_id 第一段；补充 owner 自成一组）。"""
    return owner.split('|')[0]


def out_path(seg, form, mech, path0, npaths, group=''):
    tail = '' if not group else '__%s' % group.replace(':', '_').replace('|', '_')
    return M.P('randoms', mech, seg, '%s__p%d_%d%s.npz' % (form, path0, npaths, tail))


def main_accounts(a):
    """阶段 S：一个 (段, 形态, 机制, 路径区间) 的登记随机行 → 逐路径名单 → 源 DEV + 多 H 账本 → randoms/<机制>/<段>/<形态>__p<path0>_<n>.npz。
    内容随机（LEGACY / ISK）用 E6k 键的源置换器（e6m_stage0_S_engine.make_draws）；记忆门用源 e6l_ops.mem_gate；后段先过 post_gate。"""
    import e6m_s_real as RL
    import e6m_s_gate as GT
    import e6m_s_mock as MK
    import e6m_s_meas as ME
    import e6m_s_run_masks as RM
    import e6m_stage0_S_engine as EN
    import e6l_fast as FA
    t0 = time.time()
    GT.post_gate(a.seg, 'randoms %s %s %s' % (a.seg, a.form, a.mech))
    rows = rand_rows(a.form, a.mech)
    skip_v = [r for r in rows if a.mech in POLICY and (parse_owner(r['owner_id']) or {}).get('operator') in ('DELETE_HIGH', 'DELETE_LOW')]
    rows = [r for r in rows if r not in skip_v]      # V（PARKINSON veto）的内容随机未定义（登记 status = SOURCE_WAIT）：本轮不跑，回执记数（2026-10-11）
    if a.group:                                                     # MC 增补：只跑一个共享路径组（机制 × 测量）
        rows = [r for r in rows if group_of(r['owner_id']) == a.group]
    p = out_path(a.seg, a.form, a.mech, a.path0, a.npaths, a.group)
    task = os.environ.get('E6M_TASK', 'S_rand_%s_%s_%s_p%d_%d%s' % (a.seg, a.form, a.mech, a.path0, a.npaths, ('_' + a.group) if a.group else ''))
    if not rows:
        M.write_receipt(task, [], status='SUCCEEDED', code=[__file__, M.__file__], rows=0, skipped_v_source_wait=len(skip_v),
                        note='本形态无此机制的可跑登记随机行' + ('（V 内容随机未定义，跳过 %d 行，登记 SOURCE_WAIT）' % len(skip_v) if skip_v else ''))
        return 0
    seg = RL.seg_of(a.seg, 'real')
    me = ME.load(a.seg)
    cal = np.load(M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz'), allow_pickle=False)['dates']
    ind = seg.ctx['industry'].reindex_like(seg.pool0).to_numpy(float)[:, seg.ccols]
    ind_c = np.where(np.isfinite(ind), ind, -1).astype(np.int64)
    k0_c = MK.dict_dense(seg.ctx['pcond'], seg.pool0)[:, seg.ccols]
    rt = RT(seg, a.form, me, cal, ind_c, k0_c, RL.kfs_of(seg, 'real', me), mem_gate=RL.mem_gate_of('real'))
    if os.environ.get('E6M_STAGE2_FAST', '1') != '0':     # 随机层换 e6j_fast.stage2_fast（e6k_env 设计接口；与 IR.dep_stage2_keep 逐位相同；2026-10-11）
        import e6j_fast as FJ
        rt.st.stage2 = FJ.stage2_fast
    if a.mech == 'DELETE_BUDGET_COND':
        runner = RM.Runner(a.seg, a.form, 'real', seg=seg)
        rt.v_final = lambda o: runner.v_state(dict(operator=o['operator'], param=str(o['param']), condition=o['condition']))[0]
    AF = FA.AcctFast(seg)
    draws = EN.make_draws(seg, kfs=rt.kfs) if a.mech in POLICY else None      # E6l 不认识的测量用本轮 kfs（2026-10-11）
    os.makedirs(os.path.dirname(p), exist_ok=True)
    run_accounts(rt, AF, rows, a.mech, a.path0, a.npaths, p, batch=a.batch, draws=draws)
    M.write_receipt(task, [p], status='SUCCEEDED', code=[__file__, RN.__file__, M.__file__], rows=len(rows), skipped_v_source_wait=len(skip_v), path0=a.path0, n_paths=a.npaths,
                    wall_s=round(time.time() - t0, 1), rss_peak_gb=round(__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    print(json.dumps(dict(seg=a.seg, form=a.form, mech=a.mech, rows=len(rows), path0=a.path0, npaths=a.npaths, wall_s=round(time.time() - t0, 1)),
                     ensure_ascii=False), flush=True)
    return 0


AUDIT_PATHS = (0, 1)


def run_accounts(rt, AF, rows, mech, path0, npaths, out_path, batch=16, draws=None):
    """阶段 S：一个 (段, 形态, 机制, [测量]) 的登记随机行 rows（auxiliary_manifest 行：owner_id 含 H，H 列）→ 逐路径名单 → 源 DEV + 多 H 账本
    （AF = e6l_fast.AcctFast(seg)）→ e6l_run_rand.accum_nb 同构累加 → E6l 同格式 npz。B2 不调用。"""
    from e6l_run_rand import accum_nb
    seg = rt.seg
    T = seg.T
    R = pd.DataFrame(rows).reset_index(drop=True)
    R['cfg'] = R.owner_id.map(lambda s: parse_owner(s)['cfg'])
    R['Hn'] = R.H.astype(int)
    nr = len(R)
    s_net = np.zeros((nr, npaths))
    n_net = np.zeros((nr, npaths), np.int32)
    s_gross = np.zeros((nr, npaths))
    n_gross = np.zeros((nr, npaths), np.int32)
    s_turn = np.zeros((nr, npaths))
    s_pos = np.zeros((nr, npaths))
    dsum = np.zeros((nr, T))
    dsq = np.zeros((nr, T))
    dcnt = np.zeros((nr, T), np.int32)
    aud = [p for p in AUDIT_PATHS if path0 <= p < path0 + npaths]
    samp = np.full((nr, len(aud), 4, T), np.nan) if aud else np.zeros((nr, 0, 4, T))
    fp = np.zeros((nr, npaths), np.uint64)
    for cfg, g in R.groupby('cfg', sort=True):
        Hs = np.asarray(sorted(set(g.Hn)), np.int64)
        hrow = np.array([int(g.index[g.Hn == h][0]) for h in Hs], np.int64)
        owner = g.owner_id.iloc[0]
        for b0 in range(0, npaths, batch):
            paths = list(range(path0 + b0, path0 + min(npaths, b0 + batch)))
            F, _ = path_finals(rt, mech, owner, paths, draws)
            for i, p in enumerate(paths):
                out, nn = AF.run(F[i], Hs)
                k = p - path0
                accum_nb(out, hrow, k, s_net, n_net, s_gross, n_gross, s_turn, s_pos, dsum, dsq, dcnt)
                h8 = np.frombuffer(hashlib.blake2b(np.packbits(F[i]).tobytes(), digest_size=8).digest(), np.uint64)[0]
                fp[hrow, k] = h8
                if p in aud:
                    j = aud.index(p)
                    for hi, r in enumerate(hrow):
                        samp[r, j] = (out[hi, 3], out[hi, 0], out[hi, 1], out[hi, 2])
    M.atomic_write_npz(out_path, desc=R.owner_id.values.astype(str), H=R.Hn.values.astype(np.int64), aux_id=R.aux_id.values.astype(str),
                       mother=np.array([rt.form] * nr), mechanism=np.array([mech] * nr), path0=np.array([path0]), n_paths=np.array([npaths]),
                       audit_paths=np.array(aud, np.int64), s_net=s_net, n_net=n_net, s_gross=s_gross, n_gross=n_gross, s_turn=s_turn, s_pos=s_pos,
                       dsum=dsum, dsq=dsq, dcnt=dcnt, samp=samp, fp=fp, dates=np.array([str(d)[:10] for d in seg.dates]))
    return out_path


def _block_of(o):
    op = o['operator']
    if op in ('BAND_Q', 'BAND_BLEND'):
        return op
    if op in ('PRIORITY_PASS', 'HARD_CONJ'):
        return 'FILTER'
    if op.startswith('EDIT_'):
        return 'EDIT_MATCH'
    if op in ('SLOT_Q', 'SLOT_BLEND25'):
        return 'MEAN_SLOT_BRIDGE'
    if op == 'LINEAR':
        return 'TWO_DAY' if o['measurement'].startswith('Q_') and o['measurement'] != 'Q0' else 'SOURCE'
    return op


if __name__ == '__main__':
    sys.exit(main())
