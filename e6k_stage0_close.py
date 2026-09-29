# -*- coding: utf-8 -*-
"""E6k Stage 0 收口：六类回执汇总 → source_manifest.json（brief §1.1 / §2；附录 A1-1 … A6-6）。
每类取最新成功回执（FAILED 须由同名 _rerun 成功覆盖，协议 v1.1 ⑤）；写环境版本（不写任何文件路径 / 账号）、输入与代码 sha、Stage 0 状态。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import json
import subprocess

import pandas as pd

import e6k_core as K

CATS = {
    '1_identity': ['stage0_c1_identity'],
    '2_source': ['stage0_c2_source_prod'] + ['stage0_c2_source_engine_%s' % s for s in K.SEGMENTS],
    '3_new_operators_deriv': ['stage0_c3_ops_%s' % s for s in K.DERIV_SEGS],
    '4_data_clock': ['stage0_c4_data_%s' % s for s in K.SEGMENTS],
    '5_random_state': ['stage0_c5_random'],
    '6_output_resources': ['stage0_c6_output'],
}


def receipt(name):
    ts = K.P('task_status')
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
    for f in sorted(glob.glob(K.P('*_copy.md'))) + [K.P('PLAN_COPY.md'), K.P('engine_contract.md'), K.P('source_resolution.md')]:
        if os.path.exists(f):
            docs[os.path.basename(f)] = K.sha_file(f)
    base = json.load(open(K.P('stage0', 'c1_identity_rerun', 'readonly_code_baseline.json'), encoding='utf-8'))['sha256']
    e6k = {os.path.basename(p): K.sha_file(p) for p in sorted(glob.glob(os.path.join(K.CODE, 'e6k_*.py')))}
    e5a = {os.path.basename(p): K.sha_file(p) for p in sorted(glob.glob(os.path.join(K.E5A_RES, '*.csv')))}
    tr = json.load(open(K.P('stage0', 'plan_tests', 'out', 'test_results.json'), encoding='utf-8'))
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=K.CODE, capture_output=True, text=True).stdout.strip()
    env = K.env_versions()
    try:
        import polars
        env['polars'] = polars.__version__
        env['polars_install'] = 'pip --target 私有目录（不改共享 conda 环境；e6k_boot 追加 sys.path 末尾）'
    except Exception:                                                    # noqa: BLE001
        env['polars'] = None
    env['permutation_generator'] = 'splitmix64x2-counter(key^block*C1^ticker*C2)>>11 * 2^-53; key=blake2b-64(canonical_json)'
    env['bootstrap_generator'] = 'blake2b-128(canonical_json(key)) -> SeedSequence -> PCG64'
    man = dict(version=K.VERSION, written_at=pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'), git_head=head, env=env,
               docs_sha256=docs, local_exec_briefs_hashes=K.sha_file(K.P('stage0', 'local_exec_briefs_hashes.json')),
               readonly_code_sha256=base, e6k_code_sha256_at_stage0=e6k, e5a_sha256=e5a,
               plan_tests=dict(total=tr['total'], passed=tr['passed'], script_sha256=tr['script_sha256'], python=tr['python'], numpy=tr['numpy'],
                               scipy=tr['scipy']),
               stage0=stage0, stage0_all_pass=bool(all_ok), market_data_end_max=K.MARKET_DATA_END_MAX,
               discrepancies='source_resolution.md（15 条，均不改登记语义）',
               notes=['A6-3 / A3-12 在 profile 产物上抽样 455 / 154（附录 500 / 200）；推导段真实账户落盘后按足额样本复核（闭包门）',
                      'Stage 0 第 3 类只在推导两段（执行端补充 X04）；后段在授权后同代码补算'])
    p = K.P('source_manifest.json')
    if os.path.exists(p):
        raise RuntimeError('source_manifest.json 已存在（只增不删；如需更新另写 _v2）')
    K.atomic_write_json(p, man)
    K.write_receipt('stage0_close', [p], 'SUCCEEDED' if all_ok else 'FAILED', stage0_all_pass=bool(all_ok))
    print(json.dumps({k: v['ok'] for k, v in stage0.items()}, ensure_ascii=False), 'ALL PASS' if all_ok else 'NOT ALL PASS', flush=True)
    return 0 if all_ok else 2


if __name__ == '__main__':
    sys.exit(main())
