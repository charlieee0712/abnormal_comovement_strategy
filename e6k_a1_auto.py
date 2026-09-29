# -*- coding: utf-8 -*-
"""E6k A1-auto（brief §4 / W15；plan §13.2；附录 B）。任一 FAIL 不得进入 A2。
  --pre     E6j 七项之 1–6 + plan §13.2 七类细目（读数前；不读任何收益）→ registration/a1_auto_E6k.json + reports/E6k_routing_review_A1_auto.md
  --masks   附录 B 掩码事实（推导两段；从确定性账户的目标级位图 / 目标统计机械计算，不读收益）→ registry/mask_facts_deriv_E6k.csv；
            只触发预冻结的数学回退 / 不适用标注（写 flags 列），不生成阈值、不挑臂
  --draft   第 7 项：记录 B 草稿字段齐（part1 之后）
词表（W15 / E6j #65）：direction_role ∈ {main, competitor, both_registered}；每张卡 queries 非空（E6j #73）。"""
import e6k_boot  # noqa: F401
import os
import sys
import json

import numpy as np
import pandas as pd

import e6k_core as K

VOCAB_ROLE = ('main', 'competitor', 'both_registered')
LOCKED = dict(alpha=[0.125, 0.25, 0.5], H=list(range(1, 21)), landmark=[3, 5, 10, 20], b=[5, 10, 15], tau=['0p5', '1', '3', 'INF'],
              gamma=['05', '1'], trefit_g=['0', '0p5'], delta=0.10, MC_Z=2.0, MC_TARGET=0.03, paths_initial=1024, topup=512, cap=8192,
              boot_L=[20, 60], boot_n=2000, hac_lag='H', hac_sens='max(2H, 20)', mean_b_div=3)


def pre():
    reg = K.P('registry')
    rgn = K.P('registration')
    D = pd.read_csv(os.path.join(reg, 'descriptors_E6k.csv'))
    T2O = pd.read_csv(os.path.join(reg, 'task_to_objects_E6k.csv'))
    Q2O = pd.read_csv(os.path.join(reg, 'question_to_objects_E6k.csv'))
    C = pd.read_csv(os.path.join(reg, 'cards_E6k.csv'))
    Qy = pd.read_csv(os.path.join(reg, 'query_registry_E6k.csv'))
    X = pd.read_csv(os.path.join(reg, 'selection_exposure_ledger_E6k.csv'))
    a0 = json.load(open(os.path.join(rgn, 'a0_manifest_E6k.json'), encoding='utf-8'))
    sm = json.load(open(K.P('source_manifest.json'), encoding='utf-8'))
    rows = []

    def chk(item, sub, what, ok, detail=''):
        rows.append(dict(item=item, sub=sub, what=what, status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), detail=str(detail)[:300]))
    # 1 登记对账
    chk(1, '', '描述符 = 39,142 / 段，与 plan §16.3 compile_design 逐元组、块集合相等', a0['compare']['ok'] and len(D) == 39142, json.dumps(a0['compare']))
    chk(1, '', '任务 → 对象：每个描述符恰属一个任务', T2O.desc_id.is_unique and set(T2O.desc_id) == set(D.desc_id), '%d 行' % len(T2O))
    qo = set(Q2O.desc_id) - {'E6J_638_OBJECTS', 'ALL_DESCRIPTORS'}
    chk(1, '', '问题 → 对象：对象全在登记表内；每条 query 至少一个对象', qo <= set(D.desc_id) and Q2O.groupby('query_id').size().min() >= 1,
        '%d 条 query' % Q2O.query_id.nunique())
    chk(1, '', '暴露台账覆盖全部描述符', set(X.desc_id) == set(D.desc_id), json.dumps(X.exposure_type.value_counts().to_dict()))
    # 2 身份与方向（词表）
    import e6k_env as E
    roles = {'S': 'main', 'M': 'main', 'Q': 'main', 'C1': 'main', 'SM': 'main', 'K0': 'main'}
    roles.update({k: 'main' for k in E.MEAS if k.startswith('RARPRE')})
    bad = [f for f in D.meas.unique() if roles.get(f) not in VOCAB_ROLE]
    chk(2, '', '方向角色在词表内（main / competitor / both_registered；E6j #65 补 both_registered）', not bad, bad)
    dirs = {k: v[2] for k, v in E.MEAS.items()}
    chk(2, '', '测量方向：S / M / Q / RARPRE = low_bad（lo），C1 = high_bad（hi）', dirs == {'S': 'lo', 'M': 'lo', 'C1': 'hi', 'Q': 'lo', 'RARPRE20_LT': 'lo',
                                                                             'RARPRE60_LT': 'lo', 'RARPRE20_SE': 'lo', 'RARPRE60_SE': 'lo'}, json.dumps(dirs))
    chk(2, '', '方向论证：engine_contract §3 / source_resolution #5 / 补充 X05（RARPRE 与 S 同向；Q 价稳高 = 好）', os.path.exists(K.P('engine_contract.md')))
    # 3 槽位合法
    P6 = set(E.P6)
    chk(3, '', 'BAND / BAND_COMPARATOR / HG_ONLY 只在生产六形态', set(D[D.blocks.str.contains('BAND|HG_ONLY')].mother) <= P6)
    chk(3, '', 'TREFIT / POST2 只在 A4b 两形态', set(D[D.family.isin(['TREFIT', 'POST2'])].mother) <= {'A4b', 'A4b_CVRv5'})
    chk(3, '', 'RAR 只在 A4b_CVRv5（= R1）/ R2 / A06；R1 不另算', set(D[D.blocks.str.contains('RAR')].mother) <= {'A4b_CVRv5', 'R2', 'A06'}
        and 'R1' not in set(D.mother))
    chk(3, '', 'POST2 测量 ∈ {S, Q, C1}（C1 = 同算子主动控制）', set(D[D.family == 'POST2'].meas) == {'S', 'Q', 'C1'})
    # 4 锁定值
    ok4 = (sorted(D[D.alpha > 0].alpha.unique().tolist()) == LOCKED['alpha'] and sorted(D.H.unique().tolist()) == LOCKED['H'])
    chk(4, '', '锁定值（α / H / b / τ / γ / g / δ / MC / bootstrap / HAC / mean b÷3）', ok4, json.dumps(LOCKED))
    pol = json.load(open(os.path.join(rgn, 'policy_profiles_E6k.json'), encoding='utf-8'))
    chk(4, '', '政策常数与 E6j 口径一致（δ .10、MC_Z 2、MC_TARGET .03、SIGN_TOL 1e−9）', pol['common_conditions']['delta_main'] == 0.10
        and pol['common_conditions']['MC'] == {'MC_Z': 2.0, 'MC_TARGET': 0.03, 'SIGN_TOL': 1e-9, 'topup': pol['common_conditions']['MC']['topup']})
    # 5 源事实表
    facts = ['W02 Q = J_B1_qCC low_bad（c4 A4-4 真实重算逐位）', 'W03 z_T = negMarketValue 当日 clean pct（c4 A4-1）', 'W04 DEV 精确合同（c2 A2-1 / A2-4）',
             'W05 行业逐日快照 PIT（c4 A4-3）', 'W06 E6j flag = 两段 n 加权合并（Q16 复现时按原表）', 'W07 生产路径 / SLOT / 六形态（c2 / c3）']
    chk(5, '', '源事实表（brief §0.1 ★ 项）逐条有 Stage 0 证据', sm['stage0_all_pass'], ' | '.join(facts))
    # 6 Stage 0 全 PASS
    chk(6, '', 'Stage 0 六类全 PASS（source_manifest.stage0_all_pass）', sm['stage0_all_pass'], json.dumps({k: v['ok'] for k, v in sm['stage0'].items()}))
    # plan §13.2 七类细目
    chk('13.2', '①', '参数完整性 / 不存在收益预筛：编译器只读登记规则，网格全枚举（A0 不读账户）', True)
    chk('13.2', '②', '对象 / 方向 / 母体映射：任务 = 母体 × 测量，SM 双分量、K0 = PARENT / HG_ONLY', set(T2O.desc_id) == set(D.desc_id))
    chk('13.2', '③', '支持 / 状态 / 权限：方式 A 文件存在；后段守卫 post_gate；HG 段首空状态（X09）；COMMON_SUPPORT 定义（X16）',
        os.path.exists(os.path.join(rgn, 'record_B_mode_A.json')))
    chk('13.2', '④', '公式与端点：Stage 0 第 3 类恒等锚全 PASS（两推导段）', sm['stage0']['3_new_operators_deriv']['ok'])
    chk('13.2', '⑤', '主对象与政策版本：144 唯一存在；policy_profiles 五列（三登记 + 两 print-only）', int(D.primary144.sum()) == 144
        and len(pol['size_profiles']) == 5)
    plan = open(K.P('PLAN_COPY.md'), encoding='utf-8').read().split('\n')
    chk('13.2', '⑥', 'Q 原文与 query 模板非空：18 卡原文 = PLAN_COPY 对应行；每卡 queries 非空（E6j #73）',
        len(C) == 18 and all(plan[int(r.plan_line)] == r.text for r in C.itertuples()) and all(str(q) != 'nan' and len(str(q)) > 0 for q in C.queries)
        and Qy.query_id.is_unique)
    ok7 = True
    for nm in ('P_package_manifest_E6k.json', 'B_package_manifest_E6k.json'):
        m = json.load(open(os.path.join(rgn, nm), encoding='utf-8'))
        for f, s in m['registry_sha256'].items():
            ok7 &= K.sha_file(os.path.join(reg, f)) == s
    chk('13.2', '⑦', 'P / B 派生闭包与登记 sha 一致（两包清单记录的 registry 文件 sha = 当前）', ok7)
    df = pd.DataFrame(rows)
    ok = not (df.status == 'FAIL').any()
    res = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), stage='pre', all_pass=bool(ok), items=rows,
               note='第 7 项（记录 B 草稿字段）在 part1 之后核；附录 B 掩码事实在推导段目标落盘后机械计算（--masks），不读收益')
    K.atomic_write_json(os.path.join(rgn, 'a1_auto_E6k.json'), res)
    md = ['# E6k routing_review_A1_auto（执行端机械对账；决策端人工 A1 移到 REVIEW）', '', '状态：**%s**（%s）' % ('全 PASS' if ok else '有 FAIL', res['written_at']), '',
          '| 项 | 细目 | 核对 | 结果 | 说明 |', '|---|---|---|---|---|']
    md += ['| %s | %s | %s | %s | %s |' % (r['item'], r['sub'], r['what'], r['status'], r['detail'].replace('|', '/')) for r in rows]
    md += ['', res['note']]
    os.makedirs(K.P('reports'), exist_ok=True)
    K.atomic_write_text(K.P('reports', 'E6k_routing_review_A1_auto.md'), '\n'.join(md) + '\n')
    K.write_receipt('a1_auto_pre', [os.path.join(rgn, 'a1_auto_E6k.json'), K.P('reports', 'E6k_routing_review_A1_auto.md')],
                    'SUCCEEDED' if ok else 'FAILED', all_pass=bool(ok))
    print(df.to_string(max_colwidth=90), flush=True)
    print('ALL PASS' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


def masks(segs):
    """附录 B 掩码事实（每目标 × 段；只用位图与目标级统计，不读收益）。flags 只触发预冻结回退 / 不适用标注。"""
    import glob
    import e6k_env as E
    out = []
    for pname in segs:
        tg, bits, stats = {}, {}, {}
        n = None
        for f in sorted(glob.glob(K.P('accounts', pname, '*.npz'))):
            if os.path.basename(f).startswith('weights_'):
                continue
            z = K.npz(f)
            n = int(z['n_cells'][0])
            for j, tid in enumerate(map(str, z['targets'])):
                bits[tid] = z['bits'][j]
                stats[tid] = {k[2:]: z[k][j] for k in z.files if k.startswith('t_')}
        facts = pd.concat([pd.read_csv(f) for f in glob.glob(K.P('accounts', pname, 'facts_*.csv'))], ignore_index=True).set_index('target_id')
        seg = E.Seg(pname)
        t_of = seg.ci.t
        cache = {}

        def mask(tid):
            if tid not in cache:
                cache[tid] = np.unpackbits(bits[tid])[:n].astype(bool)
            return cache[tid]
        for tid in stats:
            if tid.startswith('CS|') or tid.startswith('CSPARENT|'):
                continue
            parts = tid.split('|')
            f, p, a, op = parts[0], parts[1], parts[2], parts[3]
            par = 'K0|%s|a0|PARENT' % p
            if par not in bits:
                continue
            st = stats[tid]
            m, mp = mask(tid), mask(par)
            ent, ext = m & ~mp, mp & ~m
            r = dict(segment=pname, target_id=tid, meas=f, mother=p, alpha=a, op=op,
                     n_edits_in=float(np.nanmean(st['n_in'])) if 'n_in' in st else np.nan, n_edits_out=float(np.nanmean(st['n_out'])) if 'n_out' in st else np.nan,
                     edit_weight_share=float(np.nanmean(st['edit_w_in'])), size_edit_gap_T=float(np.nanmean(st['gapT']) * 100) if np.isfinite(st['gapT']).any() else np.nan,
                     size_edit_gap_LAG1=float(np.nanmean(st['gapL']) * 100) if np.isfinite(st['gapL']).any() else np.nan,
                     size_port_delta_T=float(np.nanmean(0.5 * (st['szT_lo'] + st['szT_hi']))) if np.isfinite(st['szT_lo']).any() else np.nan,
                     size_port_delta_LAG1=float(np.nanmean(0.5 * (st['szL_lo'] + st['szL_hi']))) if np.isfinite(st['szL_lo']).any() else np.nan,
                     small30_share_delta=float(np.nanmean(st['small30']) - np.nanmean(stats[par]['small30'])),
                     size_unknown_weight=float(np.nanmean(st['unkT'])), total_edit_cells=int(ent.sum() + ext.sum()))
            nat = '%s|%s|%s|NATIVE' % (f, p, a)
            if op != 'NATIVE' and nat in bits:
                en = mask(nat) & ~mp
                r['same_ticker_overlap_with_native'] = float((ent & en).sum() / max(ent.sum(), 1))
            if f in ('S', 'M'):
                other = '%s|%s|%s|%s' % ('M' if f == 'S' else 'S', p, a, op)
                if other in bits:
                    eo = mask(other) & ~mp
                    r['arm_overlap_S_M'] = float((ent & eo).sum() / max((ent | eo).sum(), 1))
            # 编辑 5 日内撤销：换入者在其后 5 个形成日内离开目标名单的比例（按列跨日）
            ii = np.flatnonzero(ent)
            if len(ii):
                T = seg.T
                cols = seg.ci.c
                dense = np.zeros((T, seg.Nc), bool)
                dense[t_of[m], cols[m]] = True
                gone = 0
                for k in ii[:: max(1, len(ii) // 2000)]:
                    t0, c0 = t_of[k], cols[k]
                    win = dense[t0 + 1:min(T, t0 + 6), c0]
                    gone += int(len(win) and not win.all())
                r['edit_persistence_5d_reversal_share'] = gone / len(ii[:: max(1, len(ii) // 2000)])
            fa = facts.loc[tid] if tid in facts.index else None
            if isinstance(fa, pd.DataFrame):
                fa = fa.iloc[0]
            flags = []
            if r['total_edit_cells'] == 0 and op not in ('PARENT',):
                flags.append('NO_EDITS_EQUIV_PARENT')
            if fa is not None:
                for k in ('rp_pairs', 'rp_unknown_edits', 'rp_unpaired_structural', 'coef_interp_unavailable_days', 'no_dose_match_days', 'solver_limit_days'):
                    if k in fa.index and pd.notna(fa[k]):
                        r[k] = float(fa[k])
                if op.startswith('RP') and r.get('rp_pairs', 1) == 0:
                    flags.append('RP_NO_PAIRS')
                if r.get('solver_limit_days', 0) > 0:
                    flags.append('SOLVER_LIMIT')
                if r.get('coef_interp_unavailable_days', 0) > 0:
                    flags.append('COEF_INTERP_UNAVAILABLE')
                if r.get('no_dose_match_days', 0) > 0:
                    flags.append('NO_DOSE_MATCH_DAYS')
            r['flags'] = '|'.join(flags)
            out.append(r)
        # 测量层回退域（与母体 K 腿有效域的交）
        for p in E.P8:
            st_ = seg.struct(p)
            k0 = st_.q0
            for f in ('S', 'M', 'Q', 'C1'):
                kf = seg.kf(f)
                base = np.isfinite(k0)
                out.append(dict(segment=pname, target_id='FALLBACK_DOMAIN|%s|%s' % (f, p), meas=f, mother=p, op='FALLBACK_DOMAIN',
                                fallback_native_kf_missing=float((base & ~np.isfinite(kf)).sum() / max(base.sum(), 1)),
                                fallback_szl_inc_z_missing=float((base & np.isfinite(kf) & ~np.isfinite(seg.zT)).sum() / max(base.sum(), 1))))
    Fm = pd.DataFrame(out)
    tag = 'post' if tuple(segs) == tuple(K.POST_SEGS) else 'deriv'      # X04：后段在授权后同代码补算，另写 _post 文件，不覆盖推导段
    p = K.P('registry', 'mask_facts_%s_E6k.csv' % tag)
    K.atomic_write_csv(p, Fm)
    res = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), stage='masks', segments=list(segs), rows=len(Fm),
               flags=Fm['flags'].dropna().str.split('|').explode().value_counts().to_dict() if 'flags' in Fm.columns else {},
               note='只触发预冻结回退 / 不适用标注；不生成阈值、不挑臂；不读收益')
    pj = K.P('registration', 'a1_auto_masks_E6k.json' if tag == 'deriv' else 'a1_auto_masks_post_E6k.json')
    K.atomic_write_json(pj, res)
    K.write_receipt('a1_auto_masks' if tag == 'deriv' else 'a1_auto_masks_post', [p, pj], 'SUCCEEDED', rows=len(Fm))
    print(json.dumps(res['flags'], ensure_ascii=False), len(Fm), flush=True)
    return 0


def masks_finish():
    """首跑已写出 mask_facts_deriv_E6k.csv 后在汇总处因 df.flags（pandas 属性）崩溃：读已写出的 CSV 补 JSON 与回执，不重算、不覆盖。"""
    p = K.P('registry', 'mask_facts_deriv_E6k.csv')
    Fm = pd.read_csv(p)
    res = dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), stage='masks', segments=list(K.DERIV_SEGS), rows=len(Fm),
               flags=Fm['flags'].dropna().str.split('|').explode().value_counts().to_dict(),
               note='只触发预冻结回退 / 不适用标注；不生成阈值、不挑臂；不读收益；首跑汇总步崩溃（df.flags 属性冲突）后由已写出 CSV 补齐')
    K.atomic_write_json(K.P('registration', 'a1_auto_masks_E6k.json'), res)
    K.write_receipt('a1_auto_masks', [p, K.P('registration', 'a1_auto_masks_E6k.json')], 'SUCCEEDED', rows=len(Fm), finished_from_csv=True)
    print(json.dumps(res['flags'], ensure_ascii=False), len(Fm), flush=True)
    return 0


def main():
    if '--pre' in sys.argv:
        return pre()
    if '--masks-finish' in sys.argv:
        return masks_finish()
    if '--masks-post' in sys.argv:                                  # X04：两后段授权后、seal_post 之后补算
        for s in K.POST_SEGS:
            K.post_gate(s, 'A1-auto 掩码事实（X04 后段补算）')
        import e6k_seal as SEAL
        ok, bad = SEAL.verify('post')
        if not ok:
            raise RuntimeError('seal_post 核对失败：%s' % bad[:5])
        return masks(K.POST_SEGS)
    if '--masks' in sys.argv:
        return masks(K.DERIV_SEGS)
    raise SystemExit('用法：--pre | --masks | --masks-post | --draft')


if __name__ == '__main__':
    sys.exit(main())
