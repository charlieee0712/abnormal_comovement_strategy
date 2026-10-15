# -*- coding: utf-8 -*-
"""E6n 确定性账户层（brief §1.3-8；plan §6.5、§7.3；E6m e6m_s_accounts 同构、同输出格式）。读收益：后段先过 post_gate。
一个进程 = (段, 母体)：masks/<段>/<母体>.npz 的每个名单键 → 源 DEV 目标（e6k_acct.Acct.target）→ 目标级统计（相对本形态实际父）→
引用该键的全部对象（主 / 附属 / 分量）按 H 并集出多 H 账本（e6i 稀疏引擎；gross / pos / turn / net8 / MATCH_CAP sc_child·sc_parent 相对实际父 /
平方根冲击括号 / 滚动 size 暴露）。输出 accounts/<段>/<母体>.npz：desc / desc_table / desc_target / desc_H / targets / dates / n_cells / bits /
d_<DESC_KEYS> / t_<TGT_KEYS> / feature_version / contract_version / holdings_sha。"""
import os
import sys
import json
import time
import hashlib
import argparse
import resource

import numpy as np

import e6n_core as N
import e6n_masks as MK


def post_gate(seg, what):
    """推导段：Stage B 冻结 + seal_B1_0 已写（B1-0 封存先于任何推导段账户）；两后段（brief W10）：方式 B 事前授权文件 + 生效条件回执 +
    seal_deriv 在且冻结清单 sha 未变；方式 A 批准文件。不满足即拒绝。"""
    import e6n_gate as GT
    GT.deriv_ready(seg, what)


def run(seg_name, parent, segobj=None):
    import e6k_acct as AC
    import e6l_env as V
    t0 = time.time()
    seg = segobj or V.SegL(seg_name, state=False)
    acct = AC.Acct(seg)
    z = np.load(N.P('masks', seg_name, '%s.npz' % parent), allow_pickle=False)
    keys = [str(x) for x in z['mask_keys']]
    n = int(z['n_cells'][0])
    if n != seg.n:
        raise RuntimeError('名单单元数与段不一致')
    R = MK.registry_rows()
    R = R[R.parent == parent]
    missing = sorted(set(R.mask_key) - set(keys))
    if missing:
        raise RuntimeError('名单缺键 %d 个，例：%s' % (len(missing), missing[:3]))
    by_key = {}
    for r in R.itertuples():
        by_key.setdefault(r.mask_key, []).append((r.obj, r.table, int(r.H)))
    nat = [k for k in keys if k.split('|', 2)[2].startswith('NATIVE') and k.startswith('NONE|')]
    if len(nat) != 1:
        raise RuntimeError('本形态实际父名单键不唯一：%s' % nat)
    pj = keys.index(nat[0])
    un = lambda j: np.unpackbits(z['final_bits'][j])[:n].astype(bool)
    F0 = un(pj)
    tp = acct.target(F0)
    DESC = {k: [] for k in AC.DESC_KEYS}
    TS = {k: [] for k in AC.TGT_KEYS}
    desc_ids, desc_tab, desc_tgt, desc_H, hsha, prof = [], [], [], [], [], []
    for j, mk in enumerate(keys):
        t1 = time.time()
        kept = un(j)
        tg = acct.target(kept)
        is_par = j == pj
        stt = acct.target_stats(tg, kept, None if is_par else F0, None if is_par else tp)
        for k in AC.TGT_KEYS:
            TS[k].append(stt[k])
        hsha.append(hashlib.sha256(np.ascontiguousarray(tg['ids']).tobytes() + np.ascontiguousarray(tg['w']).tobytes()).hexdigest()[:16])
        rows = by_key.get(mk, [])
        Hs = tuple(sorted({h for _, _, h in rows}))
        if Hs:
            led = acct.ledgers(tg, Hs, par=None if is_par else tp, impact=True, roll=True)
            for obj, tab, H in rows:
                desc_ids.append(obj)
                desc_tab.append(tab)
                desc_tgt.append(j)
                desc_H.append(H)
                for k in AC.DESC_KEYS:
                    DESC[k].append(led[H][k])
        prof.append((mk, round(time.time() - t1, 3), len(Hs)))
    od = N.P('accounts', seg_name)
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, '%s.npz' % parent)
    N.atomic_write_npz(p, desc=np.array(desc_ids), desc_table=np.array(desc_tab), desc_target=np.array(desc_tgt), desc_H=np.array(desc_H),
                       targets=np.array(keys), dates=np.array([str(d)[:10] for d in seg.dates]), n_cells=np.array([n]), bits=z['final_bits'],
                       holdings_sha=np.array(hsha), feature_version=np.array(['E6n-minute-v1']), contract_version=np.array([N.CONTRACT_VERSION]),
                       **{'d_' + k: np.vstack(DESC[k]) for k in AC.DESC_KEYS}, **{'t_' + k: np.vstack(TS[k]) for k in AC.TGT_KEYS})
    return p, prof, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--parent', required=True)
    a = ap.parse_args()
    t0 = time.time()
    post_gate(a.seg, 'accounts %s %s' % (a.seg, a.parent))
    p, prof, wall = run(a.seg, a.parent)
    N.write_receipt('E6n_accounts_%s_%s' % (a.seg, a.parent), [p], code=[__file__, MK.__file__], keys=len(prof), wall_s=round(wall, 1),
                    rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    print(json.dumps(dict(seg=a.seg, parent=a.parent, keys=len(prof), wall_s=round(wall, 1)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
