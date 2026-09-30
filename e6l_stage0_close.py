# -*- coding: utf-8 -*-
"""E6l Stage 0 收口：六类回执汇总 → source_manifest.json（brief §2；附录 A1 … A6）。
每类取最新成功回执（FAILED 须由同名 _rerun 成功覆盖，协议 v1.1 ⑤）；写环境版本（不写任何路径 / 账号）、输入与代码 sha（e6l_code_sha256_at_stage0
= 之后代码变更登记的"变更前"基线）、Stage 0 状态。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import json
import subprocess

import pandas as pd

import e6l_core as L

CATS = {
    '1_identity': ['stage0_c1_identity'],
    '2_source': ['stage0_c2_source_prod'] + ['stage0_c2_source_engine_%s' % s for s in L.SEGMENTS],
    '3_new_operators_deriv': ['stage0_c3_ops_%s' % s for s in L.DERIV_SEGS],
    '4_data_clock': ['stage0_c4_state'] + ['stage0_c4_data_%s' % s for s in L.SEGMENTS],
    '5_random_state': ['stage0_c5_random'],
    '6_output_resources': ['stage0_c6_fast', 'stage0_c6_output'],
}


def receipt(name):
    ts = L.P('task_status')
    base = os.path.join(ts, name + '.receipt.json')
    rer = os.path.join(ts, name + '_rerun.receipt.json')
    out = []
    for p in (base, rer):
        if os.path.exists(p):
            out.append(json.load(open(p, encoding='utf-8')))
    if not out:
        return None, 'MISSING'
    last = out[-1]
    return last, last['status'] if (len(out) == 1 or out[-1]['task_id'].endswith('_rerun')) else 'AMBIGUOUS'


def main():
    stage0 = {}
    all_ok = True
    for cat, names in CATS.items():
        sts = []
        for n in names:
            r, st = receipt(n)
            sts.append(dict(task=n if r is None else r['task_id'], status=st))
        ok = all(s['status'] == 'SUCCEEDED' for s in sts)
        all_ok &= ok
        stage0[cat] = dict(receipts=sts, ok=ok)
    docs = {}
    for f in sorted(glob.glob(L.P('*_copy.md'))) + [L.P('PLAN_COPY.md'), L.P('engine_contract.md'), L.P('source_resolution.md')]:
        if os.path.exists(f):
            docs[os.path.basename(f)] = L.sha_file(f)
    base = json.load(open(L.P('stage0', 'c1_identity_rerun', 'readonly_code_baseline.json'), encoding='utf-8'))['sha256']
    e6l = {os.path.basename(p): L.sha_file(p) for p in sorted(glob.glob(os.path.join(L.CODE, 'e6l_*')))}
    e5a = {os.path.basename(p): L.sha_file(p) for p in sorted(glob.glob(os.path.join(L.E5A_RES, '*.csv')))}
    tr = json.load(open(L.P('stage0', 'plan_tests', 'out', 'results.json'), encoding='utf-8'))
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=L.CODE, capture_output=True, text=True).stdout.strip()
    env = L.env_versions()
    env['polars'] = 'NOT_USED'
    env['numba_cache'] = 'NUMBA_CACHE_DIR = 研究临时目录（不写共享环境）；e6l_fast 全部 njit(cache=True, error_model="numpy")'
    env['permutation_generator'] = 'splitmix64x2-counter(key^block*C1^ticker*C2)>>11 * 2^-53; key=blake2b-64(canonical_json)'
    env['bootstrap_generator'] = 'blake2b-128(canonical_json(key)) -> SeedSequence -> PCG64'
    env['cpu_binding'] = 'taskset -c 96-191,288-383；并发 ≤ 64；BLAS 线程 4'
    tim = L.P('stage0', 'c6_output', 'timing_extrapolation.json')
    man = dict(version=L.VERSION, written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), git_head=head, env=env,
               docs_sha256=docs, local_exec_briefs_hashes=L.sha_file(L.P('stage0', 'local_exec_briefs_hashes.json')),
               readonly_code_sha256=base, e6l_code_sha256_at_stage0=e6l, e5a_sha256=e5a,
               plan_tests=dict(total=tr.get('tests_run'), passed=tr.get('passed'), script_sha256=tr.get('script_sha256'),
                               environment=tr.get('environment'), kind=tr.get('kind')),
               timing_extrapolation=json.load(open(tim, encoding='utf-8')) if os.path.exists(tim) else 'MISSING',
               stage0=stage0, stage0_all_pass=bool(all_ok), market_data_end_max=L.MARKET_DATA_END_MAX,
               discrepancies='source_resolution.md（全部不改登记语义；逐条带证据文件）')
    p = L.P('source_manifest.json')
    if os.path.exists(p):
        raise RuntimeError('source_manifest.json 已存在（只增不删；如需更新另写 _v2）')
    L.atomic_write_json(p, man)
    L.write_receipt('stage0_close', [p], 'SUCCEEDED' if all_ok else 'FAILED', stage0_all_pass=bool(all_ok))
    print(json.dumps({k: v['ok'] for k, v in stage0.items()}, ensure_ascii=False), 'ALL PASS' if all_ok else 'NOT ALL PASS', flush=True)
    return 0 if all_ok else 2


if __name__ == '__main__':
    sys.exit(main())
