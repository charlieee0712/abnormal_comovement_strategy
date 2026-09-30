# -*- coding: utf-8 -*-
"""E6l A1-auto（brief §4；plan §13.2；附录 A6-3 / B）。机械对账；任一 FAIL 阻断 B 草稿与冻结。不读任何收益。
  --pre    E6k 七项（登记对账 / 五列 profile 文本 / 卡 queries / 词表 / 锁定值 / 固定输出 / 暴露台账）+ 本轮 ⑧–⑫：
           ⑧ STATE 对象带状态变量定义 sha（= 当前 e6l_state.py）与 UNKNOWN 回退 b10；⑨ INV 对象 H 进状态键与目标 ID；
           ⑩ 平滑对象带核 ID / 窗 / 有效数规则 / λ；⑪ R-MARK 对象带分区合同且随机登记三机制 × 180；⑫ 状态词扫描（registry / registration 全部
           CSV / JSON / MD）无 N/A / NA / nan / null 作状态 → registration/a1_auto_E6l.json + a1_auto_E6l.csv
  --draft  记录 B 草稿字段齐（part1 之后；方式 B 不停）"""
import e6l_boot  # noqa: F401
import os
import re
import sys
import glob
import json

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_registry as RG

FAMILIES = ('PARENT', 'OLD_RULE', 'NATIVE', 'SMOOTH', 'HG', 'MEMORY', 'STATE')
EXPOSURES = ('SOURCE_PARENT', L.LABEL_SECOND, L.LABEL_FIRST_LOOK)
LOCKED = dict(alpha=[0.125, 0.25, 0.5], H=list(range(1, 21)), random_H=[1, 2, 3, 5, 10, 20], rmark_H=[1, 5, 20], b=[5, 10, 15, 20, 30],
              decay_L=[2, 5], inv_b=10, lag1_b=10, delta=0.10, MC_Z=2.0, MC_TARGET=0.03, paths_initial=1024, topup=512, cap=8192,
              boot_L=[20, 60], boot_n=2000, hac_lag='H', hac_sens=['max(2H, 20)', 60], mean_b_div=3, state_schedules=list(RG.STATE))


def pre():
    reg = L.P('registry')
    rgn = L.P('registration')
    rows = []

    def chk(item, what, ok, detail=''):
        rows.append(dict(item=item, what=what, status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), detail=L.txt(detail)[:400]))
    D = L.read_csv_keep(os.path.join(reg, 'descriptors_E6l.csv'))
    A = L.read_csv_keep(os.path.join(reg, 'accessory_E6l.csv'))
    T2O = L.read_csv_keep(os.path.join(reg, 'task_to_objects_E6l.csv'))
    Q2O = L.read_csv_keep(os.path.join(reg, 'question_to_objects_E6l.csv'))
    C = L.read_csv_keep(os.path.join(reg, 'cards_E6l.csv'))
    Cb = L.read_csv_keep(os.path.join(reg, 'cards_stageB_E6l.csv'))
    Qy = L.read_csv_keep(os.path.join(reg, 'query_registry_E6l.csv'))
    X = L.read_csv_keep(os.path.join(reg, 'selection_exposure_ledger_E6l.csv'))
    RR = L.read_csv_keep(os.path.join(reg, 'randoms_E6l.csv'))
    FX = L.read_csv_keep(os.path.join(reg, 'fixed_outputs_E6l.csv'))
    a0 = json.load(open(os.path.join(rgn, 'a0_manifest_E6l.json'), encoding='utf-8'))
    pp = json.load(open(os.path.join(rgn, 'policy_profiles_E6l.json'), encoding='utf-8'))
    # 1 登记对账
    chk(1, '描述符 34,120 / 段；与 spec 逐元组 / 块集合 / 随机 / 支持 / 比较 / 附属清单相等', a0['compare']['ok'] and len(D) == 34120,
        json.dumps({k: v for k, v in a0['compare'].items() if k not in ('counts', 'expected')}))
    ids = set(D.desc_id) | set(A.acc_id)
    chk(1, '任务 → 对象：每个描述符 / 附属恰属一个任务', T2O.desc_id.is_unique and set(T2O.desc_id) == ids, '%d 行' % len(T2O))
    qo = set(Q2O.desc_id) - {'ALL_DESCRIPTORS'}
    chk(1, '问题 → 对象：对象全在登记表内；每条 query ≥ 1 个对象', qo <= set(D.desc_id) and Q2O.groupby('query_id').size().min() >= 1 and
        set(Q2O.query_id) == set(Qy.query_id), '%d 条 query' % Q2O.query_id.nunique())
    chk(1, '暴露台账覆盖全部描述符', set(X.desc_id) == set(D.desc_id), json.dumps(X.evidence_exposure.value_counts().to_dict()))
    # 2 profile 文本
    prof = set(pp['size_profiles'])
    chk(2, '五列 size profile 全在（LEGACY_EDIT5 / PROPOSED_PORT3_T / PROPOSED_PORT3_LAG1 / EXEC_DISCLOSE_ONLY / EXEC_LEADER_VS_PARENT）',
        prof == {'LEGACY_EDIT5', 'PROPOSED_PORT3_T', 'PROPOSED_PORT3_LAG1', 'EXEC_DISCLOSE_ONLY', 'EXEC_LEADER_VS_PARENT'}, sorted(prof))
    chk(2, 'policy_provisional = false；PORT3_T 为正式列；LEADER 只披露；LEGACY_EDIT5 未定义段 = UNDEFINED',
        pp['policy_provisional'] is False and 'PROPOSED_PORT3_T' in pp['verdict_profiles'] and pp['disclosure_only_profiles'] == ['EXEC_LEADER_VS_PARENT']
        and 'UNDEFINED' in pp['size_profiles']['LEGACY_EDIT5']['rule'], pp['size_profiles']['PROPOSED_PORT3_T']['role'])
    chk(2, 'PX1–PX8 全在（E6k 逐句转录 + W12 补写）', [it['id'] for it in pp['items']] == ['PX%d' % i for i in range(1, 9)], [it['id'] for it in pp['items']])
    # 3 卡
    plan = open(L.P('PLAN_COPY.md'), encoding='utf-8').read().split('\n')
    chk(3, '16 张卡 queries 非空且都在 query 注册表', len(C) == 16 and all(set(q.split('|')) <= set(Qy.query_id) for q in C.queries))
    chk(3, '卡片标题行号与 PLAN_COPY 原文逐行相同', all(plan[int(r.plan_line) - 1].replace('### ', '') == r.title for r in C.itertuples()))
    chk(3, 'Stage B 卡 16 张：⑮–⑱ 机械字段非空；⑬ = PENDING_DERIV_MDE80；每卡绑定比较 ≥ 1 条（Q16 = 全域方法卡除外）',
        len(Cb) == 16 and all(str(x) not in ('', 'NOT_APPLICABLE') for c in ('t15_account', 't16_timescale', 't17_random', 't18_state') for x in Cb[c])
        and Cb.t13_decidability.str.startswith('PENDING_DERIV_MDE80').all() and bool((Cb[Cb.card != 'Q16'].n_bound_comparisons >= 1).all()),
        dict(zip(Cb.card, Cb.n_bound_comparisons)))
    # 4 词表
    import e6l_env as V
    import e6k_env as E
    dirs = {k: v[2] for k, v in E.MEAS.items() if k in ('S', 'M', 'C1', 'Q')}
    chk(4, '测量方向：Q 族（全部 Q 表达统一由 Q 原值 lo 方向秩 / 源秩均值）大值不利；C1 hi；S / M lo', dirs == {'S': 'lo', 'M': 'lo', 'C1': 'hi', 'Q': 'lo'}, dirs)
    chk(4, '族名在固定词表', set(D.family) <= set(FAMILIES), sorted(set(D.family)))
    chk(4, '暴露标签在固定词表', set(D.evidence_exposure) <= set(EXPOSURES), sorted(set(D.evidence_exposure)))
    chk(4, '测量在登记集合（11 个 Q 表达 + 2 个桥 + C1 / S / M + K0）', set(D.meas) == set(RG.Q + RG.BRIDGE + ('C1', 'S', 'M', 'K0')), sorted(set(D.meas)))
    # 5 锁定值
    chk(5, 'α 网格 / H 网格', sorted(set(D.alpha[D.meas != 'K0'].astype(float))) == LOCKED['alpha'] and sorted(set(D.H.astype(int))) == LOCKED['H'])
    chk(5, '随机 H 集合 {1,2,3,5,10,20}；R-MARK H {1,5,20}', sorted(set(RR[RR.mechanism.isin(RG.POLICY_MECHS)].H.astype(int))) == LOCKED['random_H']
        and sorted(set(RR[RR.mechanism.isin(RG.RMARK)].H.astype(int))) == LOCKED['rmark_H'])
    ops = set(D.op)
    chk(5, '算子集合（NATIVE / HG5·10·15·20·30 / LAG1_10 / DECAY2_10 · DECAY5_10 / INV10 / 四调度）', ops == set(('NATIVE',) + RG.OPS[1:] + RG.MEM + RG.STATE + ('HG20', 'HG30')),
        sorted(ops))
    chk(5, '随机首 1,024 / 增补 512 / 上限 8,192（随机登记）', set(RR.n_paths_initial.astype(int)) == {1024} and set(RR.topup.astype(int)) == {512}
        and set(RR.cap.astype(int)) == {8192})
    chk(5, 'δ .10 / MC_Z 2 / MC_TARGET .03（政策文本）', pp['common_conditions']['delta_main'] == 0.1 and pp['common_conditions']['MC']['MC_Z'] == 2.0
        and pp['common_conditions']['MC']['MC_TARGET'] == 0.03)
    chk(5, '锁定值清单（bootstrap 2,000 × L 20 / 60；HAC H / max(2H,20) / 60；Mmean b/3）', None, json.dumps(LOCKED, ensure_ascii=False))
    # 6 固定输出
    sk = L.P('results', 'skeleton')
    miss = [t for t in FX.table if not os.path.exists(os.path.join(sk, '%s.csv' % t))]
    missq = [q for q in Qy.query_id if not os.path.exists(os.path.join(sk, '%s.csv' % q.replace('-', '_')))]
    chk(6, '固定输出 %d 张 + query %d 张骨架存在' % (len(FX), len(Qy)), not miss and not missq, 'miss %s %s' % (miss, missq))
    # 7 暴露台账
    newop = D.evidence_exposure == L.LABEL_FIRST_LOOK
    chk(7, '新算子 replacement_preference_status = NOT_AUTHORIZED；其余 NOT_APPLICABLE；deployment_authorized 全 False',
        bool((D.replacement_preference_status[newop] == 'NOT_AUTHORIZED').all() and (D.replacement_preference_status[~newop] == 'NOT_APPLICABLE').all()
             and (D.deployment_authorized.astype(str) == 'False').all()))
    sec = D.evidence_exposure == L.LABEL_SECOND
    chk(7, 'SECOND_EVALUATION 对象 = 有 E6k 同构 desc_id 的非母体对象（%d）' % int(sec.sum()),
        bool(((D.e6k_equiv != 'NOT_APPLICABLE') & (D.family != 'PARENT')).equals(sec)))
    # ⑧
    stt = D[D.op.isin(RG.STATE)]
    ssha = L.sha_file(os.path.join(L.CODE, 'e6l_state.py'))
    chk(8, 'STATE 对象（%d）带状态变量定义 sha（= 当前 e6l_state.py）与 UNKNOWN 回退 b10' % len(stt),
        bool((stt.state_def_sha256 == ssha).all() and (stt.unknown_fallback == 'b10').all() and (stt.state_var == 'Vol3').all()), ssha[:16])
    # ⑨
    inv = D[D.op == 'INV10']
    chk(9, 'INV 对象（%d）H 进状态键与目标 ID' % len(inv), bool((inv.inv_state_key == 'H' + inv.H.astype(str)).all()
                                                            and all(t.endswith('|H%s' % h) for t, h in zip(inv.target_id, inv.H.astype(str)))))
    # ⑩
    sm = D[D.meas.str.startswith('Q_')]
    okk = (sm.kernel_id != 'NOT_APPLICABLE').all() and (sm.kernel_window != 'NOT_APPLICABLE').all() and (sm.kernel_min_valid != 'NOT_APPLICABLE').all()
    dew = sm[sm.meas.isin(['Q_DEW3', 'Q_DEW5'])]
    chk(10, '平滑 / 秩对象（%d）带核 ID / 名义窗 / 最少有效数；DEW 带 λ' % len(sm), bool(okk and (dew.kernel_lambda != 'NOT_APPLICABLE').all()),
        json.dumps(sm.groupby('meas').kernel_id.first().to_dict(), ensure_ascii=False)[:380])
    # ⑪
    rm = D[D.rmark.astype(str) == 'True']
    chk(11, 'R-MARK 对象（%d）带分区合同；随机登记三机制各 180' % len(rm), bool(len(rm) == 180 and (rm.rmark_partition != 'NOT_APPLICABLE').all()
                                                                    and all((RR.mechanism == m).sum() == 180 for m in RG.RMARK)))
    # ⑫ 状态词
    bad = []
    files = glob.glob(os.path.join(reg, '*.csv')) + glob.glob(os.path.join(rgn, '*.csv'))
    for f in files:
        df = pd.read_csv(f, keep_default_na=False, na_values=[], dtype=str)
        for c in df.columns:
            hit = L.status_scan_values(df[c].values)
            if hit:
                bad.append('%s:%s:%s' % (os.path.basename(f), c, hit))
    for f in [x for x in glob.glob(os.path.join(rgn, '*.json')) if not os.path.basename(x).startswith('a1_auto_E6l')] + glob.glob(os.path.join(rgn, '*.md')):
        txt = open(f, encoding='utf-8').read()
        for w in ('"N/A"', '"NA"', '"nan"', '"null"', ': null', 'NaN'):
            if w in txt:
                bad.append('%s:%s' % (os.path.basename(f), w))
    chk(12, '状态词扫描（%d 个 CSV + registration JSON / MD）无 N/A / NA / nan / null 作状态' % len(files), not bad, '; '.join(bad[:8]))
    df = pd.DataFrame(rows)
    allp = not (df.status == 'FAIL').any()
    stem = L.next_rerun('a1_auto_pre')                         # a1_auto_pre → _rerun → _rerun2 …（FAILED 回执不覆盖）
    p = os.path.join(rgn, 'a1_auto_E6l%s.json' % stem[len('a1_auto_pre'):])
    L.atomic_write_json(p, dict(written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), stage='pre', all_pass=bool(allp),
                                counts=df.status.value_counts().to_dict(), rows=df.to_dict('records'), no_returns_read_before=True))
    pc = L.P('results', 'stage_a', 'a1_auto_pre_E6l%s.csv' % stem[len('a1_auto_pre'):])
    L.atomic_write_csv(pc, df)
    L.write_receipt(stem, [p, pc], 'SUCCEEDED' if allp else 'FAILED',
                    counts=df.status.value_counts().to_dict())
    print(df.to_string(max_colwidth=100), flush=True)
    print(df.status.value_counts().to_dict(), 'ALL PASS' if allp else 'HAS FAIL', flush=True)
    return 0 if allp else 2


def main():
    if '--pre' in sys.argv:
        return pre()
    raise SystemExit('用法：--pre')


if __name__ == '__main__':
    sys.exit(main())
