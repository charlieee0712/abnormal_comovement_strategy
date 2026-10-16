# -*- coding: utf-8 -*-
"""E6m 阶段 S 副本包 P0–P3（brief A7 / D-6；plan §13.2）。每个主要完成阶段（deriv / post / final）生成并逐件重算 sha 验证；缺副本不伪称产物级复核通过。
  P0_REVIEW    plan / brief 副本、registration、registry、报告与全部表（reports/）、policy 与统计（results/）、封存、回执、限制登记与实施计划、
               主 72 + 父 + 关键对照的逐日账本摘录（ledger_extract_<段>.npz：net8 / gross / turn / pos / sc_child / sc_parent）
  P1_LEDGER    确定性主 / 附属全部逐日账本（accounts / accounts_aux）、名单位图（masks / masks_aux：目标 / 实际持仓稀疏索引）、状态检查点（stage0/cache_cloud）
  P2_RANDOM    随机分片（randoms/，含审计路径 samp 与路径指纹 fp）+ 复放输入（附属清单、键合同版本）
  P3_DATA_REF  行情 / 缓存允许版本的 sha 与列血缘（不复制行情；外部输入表 + 缓存 sha）
目的地：factor_runs/resonance/replica/E6m/<阶段>/<层>/（云机；47 恢复后另存结果目录）。manifest：replica_manifest_<层>_<阶段>.json（files：path / sha256 / bytes / rows / role；
manifest_sha256 = files 规范 JSON 的 sha256）。只增不删：同名目录已存在即拒绝。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import shutil
import argparse

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_replica as R0

DEST = os.path.join(M.RUNS, 'replica', 'E6m')
SEGS = tuple(M.SEGMENTS)


def rel_glob(*pats):
    W = M.work()
    out = set()
    for p in pats:
        for f in glob.glob(os.path.join(W, p), recursive=True):
            if os.path.isfile(f):
                out.add(os.path.relpath(f, W))
    return sorted(out)


def ledger_extract(stage_segs, od):
    """P0：主 72 + 父 + 关键对照（Q0 NATIVE / HG10 / LAG1_10，α .25）逐日账本摘录。"""
    import e6m_s_stats as SS
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    key = set(D[(D.is_primary72 == 'True') | (D.block == 'PARENT')].desc_id)
    key |= set(D[(D.block == 'SOURCE') & (D.alpha == '0.25') & (D.measurement == 'Q0')].desc_id)
    outs = []
    for s in stage_segs:
        if not os.path.isdir(M.P('accounts', s)):
            continue
        d, t, d2t, dH, dates = SS.load(M.P('accounts'), s)
        ids = sorted(k for k in key if k in d)
        arrs = {k: np.vstack([d[i][k] for i in ids]) for k in ('net8', 'gross', 'turn', 'pos', 'sc_child', 'sc_parent')}
        p = os.path.join(od, 'ledger_extract_%s.npz' % s)
        M.atomic_write_npz(p, desc=np.array(ids), dates=np.array([str(x)[:10] for x in dates]), **arrs)
        outs.append(p)
    return outs


def tiers(stage):
    segs = SEGS if stage != 'deriv' else tuple(M.DERIV_SEGS)
    segp = lambda base: ['%s/%s/**' % (base, s) for s in segs]
    return {
        'P0_REVIEW': rel_glob('PLAN_COPY.md', 'registration/*', 'registry/*', 'reports/**', 'results/**/*.csv', 'results/**/*.json', 'seal_*.json',
                              'task_status/*', 'stageN/STAGE_S_IMPL_PLAN.md', 'stageN/limit_register_stageS_draft.md', 'stageN/code_change_register_stageS_dev.md',
                              'stage0_S/**/*.csv', 'stage0_S/**/*.json', 'replica/ledger_extract/*.npz',
                              'supp/S1/*.json', 'supp/S1/*.csv', 'supp/S1/**/*.csv'),          # 补丁二十二：补充件 S1 的 manifest / summary / 事实表
        'P1_LEDGER': rel_glob(*(segp('accounts') + segp('accounts_aux') + segp('masks') + segp('masks_aux') + segp('stage_a'))) +
        rel_glob('stage0/cache_cloud/state_full_E6m_cloud.npz') + (rel_glob('results/full/continuous/*.npz') if stage != 'deriv' else []) +
        (rel_glob('supp/S1/**/*.npz') if stage == 'final' else []),                                   # 补丁二十二：补充件 S1 的名单与账户
        'P2_RANDOM': rel_glob(*['randoms/*/%s/*.npz' % s for s in segs]) + rel_glob('registry/auxiliary_manifest_E6m.csv'),
        'P3_DATA_REF': rel_glob('registry/external_inputs_E6m.csv', 'stage0_S/intake/*.csv', 'stage0/c4_data_*.csv'),
    }


def build(stage, only):
    W = M.work()
    os.makedirs(M.P('replica', 'ledger_extract'), exist_ok=True)
    ledger_extract(SEGS if stage != 'deriv' else tuple(M.DERIV_SEGS), M.P('replica', 'ledger_extract'))
    T = tiers(stage)
    res = {}
    for tier, files in T.items():
        if only and tier not in only:
            continue
        dst = os.path.join(DEST, stage, tier)
        if os.path.exists(dst):
            raise RuntimeError('%s 已存在（只增不删）' % M.san(dst))
        man = R0.manifest(W, files, tier, R0.role)
        man['stage'] = 'S:%s' % stage
        for f in files:
            q = os.path.join(dst, f)
            os.makedirs(os.path.dirname(q), exist_ok=True)
            shutil.copy2(os.path.join(W, f), q)
        bad = [x['path'] for x in man['files'] if M.sha_file(os.path.join(dst, x['path'])) != x['sha256']]
        man['verified'] = dict(copied_to=M.san(dst), files=len(files), mismatched=bad)
        p = M.P('replica', 'replica_manifest_%s_%s.json' % (tier, stage))
        M.atomic_write_json(p, man)
        shutil.copy2(p, os.path.join(dst, os.path.basename(p)))
        res[tier] = dict(files=len(files), bytes=man['total_bytes'], mismatched=len(bad), manifest=M.rel(p))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', required=True, choices=['deriv', 'post', 'final'])
    ap.add_argument('--only', default='', help='逗号分隔的层名（默认全部）')
    ap.add_argument('--plan', action='store_true', help='只列各层文件数与体积，不复制')
    a = ap.parse_args()
    t0 = time.time()
    if a.plan:
        T = tiers(a.stage)
        W = M.work()
        print(json.dumps({k: dict(files=len(v), gb=round(sum(os.path.getsize(os.path.join(W, f)) for f in v) / 1e9, 3)) for k, v in T.items()}, ensure_ascii=False))
        return 0
    res = build(a.stage, [x for x in a.only.split(',') if x])
    ok = all(v['mismatched'] == 0 for v in res.values())
    M.write_receipt(os.environ.get('E6M_TASK', 'S_replica_%s' % a.stage), [M.P(v['manifest']) for v in res.values()], status='SUCCEEDED' if ok else 'FAILED',
                    code=[__file__, M.__file__], tiers=res, wall_s=round(time.time() - t0, 1))
    print(json.dumps(res, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
