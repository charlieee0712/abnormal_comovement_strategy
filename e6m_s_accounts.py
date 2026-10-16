# -*- coding: utf-8 -*-
"""E6m 阶段 S · 确定性账户阶段（brief §1.4；plan §9.1–§9.4）。名单 → 源 DEV → 稀疏账本（与 e6l_run_det accounts 阶段同构、同输出格式）。
**B2 开发期不运行**：读 Acct / SparseEngine 会碰收益（STAGE_S_IMPL_PLAN §0）。阶段 S 在真实 Seg 上运行，
Stage 0 S 用 A2-3 / A2-4 锚（E6j 母体账本、E6k / E6l policy 1e−9）核本模块。

输入：masks/<段>/<形态>.npz（e6m_s_run_masks：config_ids / final_bits）+ registry/descriptors_E6m.csv（配置 → 各 H 描述符）。
输出：accounts/<段>/<形态>.npz：
- desc / desc_target / desc_H / targets / dates / n_cells / bits；
- d_<DESC_KEYS>（描述符 × 日）、t_<TGT_KEYS>（目标 × 日）；DESC_KEYS / TGT_KEYS 同 e6k_acct。
MATCH_CAP（sc_child / sc_parent）相对本形态实际父（K0 PARENT）；父本身不缩放。"""
import os
import time

import numpy as np

import e6m_core as M


def config_id(desc_id):
    p = desc_id.split('|')
    return '|'.join(p[:6] + p[7:])


def run(seg, form, masks_dir, out_dir, descriptors, acct_cls=None):
    """seg：真实 e6k_env.Seg（或 e6l_env.SegL）；descriptors：DataFrame（registry/descriptors_E6m.csv）。返回输出路径。"""
    import e6k_acct as AC
    acct = (acct_cls or AC.Acct)(seg)
    z = np.load(os.path.join(masks_dir, '%s.npz' % form), allow_pickle=False)
    cids = [str(x) for x in z['config_ids']]
    n = int(z['n_cells'][0])
    if n != seg.n:
        raise RuntimeError('名单单元数与段不一致')
    D = descriptors[descriptors.parent == form]
    by_cfg = {}
    for r in D.itertuples():
        by_cfg.setdefault(config_id(r.desc_id), []).append((r.desc_id, int(r.H)))
    parent_cfg = [c for c in cids if c.split('|')[2] == 'PARENT']
    if len(parent_cfg) != 1:
        raise RuntimeError('父配置不唯一')
    pj = cids.index(parent_cfg[0])
    unpack = lambda j: np.unpackbits(z['final_bits'][j])[:n].astype(bool)
    F0 = unpack(pj)
    tp = acct.target(F0)
    DESC = {k: [] for k in AC.DESC_KEYS}
    TS = {k: [] for k in AC.TGT_KEYS}
    desc_ids, desc_tgt, desc_H, prof = [], [], [], []
    for j, cid in enumerate(cids):
        t0 = time.time()
        kept = unpack(j)
        tg = acct.target(kept)
        is_par = j == pj
        stt = acct.target_stats(tg, kept, None if is_par else F0, None if is_par else tp)
        for k in AC.TGT_KEYS:
            TS[k].append(stt[k])
        rows = by_cfg.get(cid, [])
        Hs = tuple(sorted({h for _, h in rows}))
        if Hs:
            led = acct.ledgers(tg, Hs, par=None if is_par else tp, impact=True, roll=True)
            for did, H in rows:
                desc_ids.append(did)
                desc_tgt.append(j)
                desc_H.append(H)
                for k in AC.DESC_KEYS:
                    DESC[k].append(led[H][k])
        prof.append((cid, round(time.time() - t0, 3), len(Hs)))
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, '%s.npz' % form)
    M.atomic_write_npz(p, desc=np.array(desc_ids), desc_target=np.array(desc_tgt), desc_H=np.array(desc_H), targets=np.array(cids),
                       dates=np.array([str(d)[:10] for d in seg.dates]), n_cells=np.array([n]), bits=z['final_bits'],
                       **{'d_' + k: np.vstack(DESC[k]) for k in AC.DESC_KEYS}, **{'t_' + k: np.vstack(TS[k]) for k in AC.TGT_KEYS})
    return p, prof


def aux_rows(form):
    """附属对象（item 5 / 6 名单层 + 补充 384）→ {aux_key: [(账户 ID, H)]}；aux_key 与 e6m_s_aux 输出同名。"""
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str)
    SUP = M.read_csv_keep(M.P('registry', 'supplemental_E6m.csv'), dtype=str)
    own_form = lambda o: o.split('|')[1] if '|' in o else (SUP[SUP.supp_id.str.startswith(o[5:])].parent.iloc[0] if o.startswith('SUPP:') else '')
    X = A[A.item.isin(['5', '6'])].copy()
    X = X[X.owner_id.map(lambda o: own_form(o.split('@')[0]) == form)]
    out = {}
    for r in X.itertuples():
        out.setdefault('%s|%s' % (r.aux_id, r.mechanism), []).append((r.aux_id, int(r.H)))
    for s in SUP[SUP.parent == form].itertuples():
        out.setdefault('SUPP|%s|%s' % (s.supp_id[:16], s.diagnostic), []).append(('SUPP:' + s.supp_id[:16], int(s.H)))
    return out, X


def run_aux(seg, form, masks_dir, aux_dir, out_dir, acct_cls=None, only_keys=None, skip_fpwd=False):
    """附属名单（masks_aux/<段>/<形态>.npz）→ 账户（同主账户格式；MATCH_CAP 相对本形态实际父）；
    另算 FROZEN_PARENT_WEIGHT_DELETE（plan §4.2 / §9.1）：父目标权重冻结、删去不在子最终名单的名字（删去的权重留作现金，不重新 DEV），
    与"幸存者重新 DEV"（= 子对象本身的主账户）构成两端；只在子最终名单逐日是父的子集时有两端含义，否则记 NOT_SUBSET 日数作适用性限制。"""
    import e6k_acct as AC
    acct = (acct_cls or AC.Acct)(seg)
    zm = np.load(os.path.join(masks_dir, '%s.npz' % form), allow_pickle=False)
    n = int(zm['n_cells'][0])
    if n != seg.n:
        raise RuntimeError('名单单元数与段不一致')
    un = lambda bits: np.unpackbits(bits)[:n].astype(bool)
    F0 = un(zm['parent_final_bits'])
    tp = acct.target(F0)
    finals = {str(c): j for j, c in enumerate(zm['config_ids'])}
    keys, H_of = aux_rows(form)
    DESC = {k: [] for k in AC.DESC_KEYS}
    TS = {k: [] for k in AC.TGT_KEYS}
    desc_ids, desc_tgt, desc_H, tkeys, tbits, facts = [], [], [], [], [], []

    def emit(tkey, kept, tg, rows):
        j = len(tkeys)
        tkeys.append(tkey)
        tbits.append(np.packbits(kept))
        stt = acct.target_stats(tg, kept, F0, tp)
        for k in AC.TGT_KEYS:
            TS[k].append(stt[k])
        Hs = tuple(sorted({h for _, h in rows}))
        led = acct.ledgers(tg, Hs, par=tp, impact=True, roll=True)
        for did, H in rows:
            desc_ids.append(did)
            desc_tgt.append(j)
            desc_H.append(H)
            for k in AC.DESC_KEYS:
                DESC[k].append(led[H][k])
    za = os.path.join(aux_dir, '%s.npz' % form)
    auxbits = {}
    if os.path.exists(za):
        A = np.load(za, allow_pickle=False)
        for j, k in enumerate([str(x) for x in A['aux_keys']]):
            auxbits[k] = j
            if only_keys is not None and k not in only_keys:          # 补丁十九：补充件只算指定键（缺省 None = 全算）
                continue
            if k not in keys:
                facts.append(dict(aux_key=k, status='NOT_IN_MANIFEST'))
                continue
            kept = un(A['final_bits'][j])
            emit(k, kept, acct.target(kept), keys[k])
            facts.append(dict(aux_key=k, status='COMPUTED', members=int(kept.sum())))
    fr = H_of[H_of.mechanism == 'FROZEN_PARENT_WEIGHT_DELETE']
    if skip_fpwd:                                                     # 补丁十九：补充件不重算冻结父权重删除（主路径已算）
        fr = fr.iloc[:0]
    wp = np.bincount(tp['t'], weights=tp['w'], minlength=seg.T)
    live = wp > 0
    for r in fr.itertuples():
        own = r.owner_id.split('@')[0]
        key = '%s|FROZEN_PARENT_WEIGHT_DELETE' % r.aux_id
        if own.startswith('SUPP:'):                                 # 补充 V_ALL_KNOWN 的最终名单在附属名单里
            sk = 'SUPP|%s|V_ALL_KNOWN' % own[5:21]
            Fc = un(A['final_bits'][auxbits[sk]]) if sk in auxbits else None
            cfg = sk
        else:
            cfg = config_id(own)
            Fc = un(zm['final_bits'][finals[cfg]]) if cfg in finals else None
        if Fc is None:
            facts.append(dict(aux_key=key, status='OWNER_NOT_COMPUTED', owner_config=cfg))
            continue
        not_subset_days = int(np.unique(seg.ci.t[Fc & ~F0]).size)
        m = Fc[tp['ids']]
        tf = dict(ids=tp['ids'][m], t=tp['t'][m], c=tp['c'][m], w=tp['w'][m])
        wf = np.bincount(tf['t'], weights=tf['w'], minlength=seg.T)
        emit(key, Fc & F0, tf, [(r.aux_id, int(r.H))])
        facts.append(dict(aux_key=key, status='COMPUTED', owner_config=cfg, not_subset_days=not_subset_days,
                          applicability='TWO_ENDS' if not_subset_days == 0 else 'NOT_SUBSET_SEE_ADDED_REMOVED_COMMON（plan §9.1 三项账本）',
                          frozen_cash_share_mean=float(np.mean(1.0 - wf[live] / wp[live])) if live.any() else float('nan')))
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, '%s.npz' % form)
    if desc_ids:
        M.atomic_write_npz(p, desc=np.array(desc_ids), desc_target=np.array(desc_tgt), desc_H=np.array(desc_H), targets=np.array(tkeys),
                           dates=np.array([str(d)[:10] for d in seg.dates]), n_cells=np.array([n]), bits=np.array(tbits),
                           **{'d_' + k: np.vstack(DESC[k]) for k in AC.DESC_KEYS}, **{'t_' + k: np.vstack(TS[k]) for k in AC.TGT_KEYS})
    import pandas as pd
    pf = os.path.join(out_dir, 'facts_aux_accounts_%s.csv' % form)
    M.atomic_write_csv(pf, pd.DataFrame(facts))
    return p, pf


def main():
    """阶段 S：一个 (段, 形态) 的主账户 + 附属账户。后段先过 e6m_s_gate.post_gate（方式 A 批准 / 方式 B 事前授权 + 条件回执 + 冻结清单 sha）。"""
    import sys
    import json
    import argparse
    import resource
    import e6m_s_real as RL
    import e6m_s_gate as GT
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--form', required=True)
    a = ap.parse_args()
    t0 = time.time()
    GT.post_gate(a.seg, 'accounts %s %s' % (a.seg, a.form))
    seg = RL.seg_of(a.seg, 'real')
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    p1, prof = run(seg, a.form, M.P('masks', a.seg), M.P('accounts', a.seg), D)
    p2, pf = run_aux(seg, a.form, M.P('masks', a.seg), M.P('masks_aux', a.seg), M.P('accounts_aux', a.seg))
    outs = [p1, pf] + ([p2] if os.path.exists(p2) else [])
    M.write_receipt(os.environ.get('E6M_TASK', 'S_accounts_%s_%s' % (a.seg, a.form)), outs, status='SUCCEEDED', code=[__file__, M.__file__],
                    configs=len(prof), wall_s=round(time.time() - t0, 1), rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    print(json.dumps(dict(seg=a.seg, form=a.form, configs=len(prof), wall_s=round(time.time() - t0, 1)), ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
