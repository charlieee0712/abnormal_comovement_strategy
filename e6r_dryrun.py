# -*- coding: utf-8 -*-
"""E6r S0-L 后段空跑（brief §2 S0-L / §4："交付链断 → 修后再进"；E6o–E6q 经验）：在 tmp/dryrun 下用推导段日行循环复制成后段（stats --fake_post）跑统计 / 政策 / 诊断 /
claims / 报告 / 注记 / 收尾（恒等 / stage0 / SCHEMA / deploy_log / 门），再把注册件、spec 指纹、决策端脚本放进同一测试根，以相对路径运行决策端脚本，
检查每个探针都有状态行（结果不作门；只为正式尾段一次过）。只读 A2 产物（推导段），不读、不写任何后段账户。
用法：python3 e6r_dryrun.py prep | dscript | s0l"""
import os
import sys
import json
import shutil
import subprocess

import pandas as pd

import e6r_core as O

ROOT = 'tmp/dryrun'


def prep():
    r = O.P(*ROOT.split('/'))
    if os.path.exists(r):
        shutil.rmtree(r)
    os.makedirs(r)
    for sub in ('registration', 'verify/spec'):
        shutil.copytree(O.P(*sub.split('/')), os.path.join(r, sub))
    for rel in ('verify/identities_E6r_stage0.csv', 'verify/identities_E6r_g1.csv', 'verify/curve_replication_E6r.csv', 'diagnostics/G1_E6r.csv',
                'diagnostics/stage0_E6r_part1.csv', 'diagnostics/stage0_E6r_part2.csv', 'diagnostics/entry_tertiles_E6r.csv', 'statistics/policy_mapping_E6r.csv'):
        if os.path.exists(O.P(*rel.split('/'))):
            dst = os.path.join(r, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(O.P(*rel.split('/')), dst)
    # 空跑用占位 seal（正式 seal_A2 在 S0-L 通过后才写）
    json.dump(dict(written_at='0000-00-00 00:00:00 (dryrun)', n_files=0, sha256_manifest=''), open(os.path.join(r, 'registration', 'seal_A2.json'), 'w', encoding='utf-8'))
    json.dump(dict(written_at='9999-12-31 00:00:00', n_files=0, sha256_manifest='', first_post_segment_write_at='9999-12-31 00:00:00 (dryrun)'),
              open(os.path.join(r, 'registration', 'seal_final.json'), 'w', encoding='utf-8'))
    d = os.path.join(r, 'verify', 'decision')
    os.makedirs(d, exist_ok=True)
    shutil.copy2(O.P('verify', 'decision', 'E6r_D_stage2.py'), os.path.join(d, 'E6r_D_stage2.py'))
    print('prep ok', flush=True)


def dscript():
    r = O.P(*ROOT.split('/'))
    files = []
    for dp, dn, fn in os.walk(r):
        dn[:] = [x for x in dn if x not in ('out_dry',)]
        for f in fn:
            if f != 'HANDOFF_SHA256.txt':
                p = os.path.join(dp, f)
                files.append('%s  %s' % (O.sha_file(p), os.path.relpath(p, r)))
    with open(os.path.join(r, 'HANDOFF_SHA256.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(sorted(files, key=lambda x: x.split('  ', 1)[1])) + '\n')
    ds = os.path.join(r, 'verify', 'decision', 'E6r_D_stage2.py')
    assert O.sha_file(ds) == O.D_SCRIPT_SHA256
    env = dict(os.environ, PYTHONPYCACHEPREFIX=O.P('tmp', 'pyc_d'), PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run([sys.executable, 'verify/decision/E6r_D_stage2.py', '--root', '.', '--handoff', '.', '--out', 'out_dry'], cwd=r, env=env, capture_output=True, text=True)
    out = os.path.join(r, 'out_dry', 'E6r_D_probes_stage2.csv')
    if os.path.exists(out):
        D = pd.read_csv(out, keep_default_na=False)
        print(D[['probe_id', 'status', 'detail']].to_string(max_colwidth=200)[:20000], flush=True)
    print('rc', p.returncode, O.san((p.stdout + p.stderr)[-3000:]), flush=True)


def s0l():
    """S0-L 行：空跑各步完成标记 + 决策端脚本在空跑根上的探针状态分布（结果不作门）→ diagnostics/stage0_E6r_part3.csv。"""
    r = O.P(*ROOT.split('/'))
    rows = []
    out = os.path.join(r, 'out_dry', 'E6r_D_probes_stage2.csv')
    if os.path.exists(out):
        D = pd.read_csv(out, keep_default_na=False)
        for st, n in D.status.value_counts().items():
            rows.append(dict(probe_id='S0-L', item='D 脚本空跑（假后段）', key='DRYRUN_D_PROBES_%s' % st, value=int(n), unit='count', status='INFO',
                             source_file='tmp/dryrun/out_dry/E6r_D_probes_stage2.csv', note='结果不作门；只证明交付链与每个探针都有状态行'))
        rows.append(dict(probe_id='S0-L', item='D 脚本空跑', key='DRYRUN_D_PROBES_TOTAL', value=len(D), unit='count', status='PASS' if len(D) == 40 else 'DIFFERS',
                         source_file='tmp/dryrun/out_dry/E6r_D_probes_stage2.csv', note='40 个探针都有状态行'))
    cl = os.path.join(r, 'verify', 'closure_E6r.csv')
    if os.path.exists(cl):
        C = pd.read_csv(cl, keep_default_na=False)
        rows.append(dict(probe_id='S0-L', item='闭包门空跑', key='DRYRUN_GATES_PASS', value=int((C.status == 'PASS').sum()), unit='count', status='INFO',
                         source_file='tmp/dryrun/verify/closure_E6r.csv', note='假后段 + 占位 seal：⑱ 等时序门预期不过；只看链条是否走通'))
    if not rows:
        rows.append(dict(probe_id='S0-L', item='空跑', key='DRYRUN_MISSING', value='', unit='none', status='DIFFERS', source_file='', note='空跑输出缺失'))
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6r_part3.csv'), pd.DataFrame(rows))
    print(json.dumps(dict(rows=len(rows)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    {'prep': prep, 'dscript': dscript, 's0l': s0l}[sys.argv[1]]()
