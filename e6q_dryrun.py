# -*- coding: utf-8 -*-
"""E6q 假数据空跑（brief §4 A2："假数据空跑交付链"）：在 tmp/dryrun 下用推导段日行循环复制成后段（假数据，stats --fake_post）跑统计 / 政策 / 诊断 / claims / 报告 / 注记 /
收尾（恒等 / stage0 / SCHEMA / deploy_log / 门），再把注册件、spec 指纹、决策端脚本放进同一测试根，以相对路径运行决策端脚本，检查每个探针都有状态行（结果不作门；只为正式尾段一次过）。
空跑只读 A2 产物（推导段），不读、不写任何后段账户。用法：python3 e6q_dryrun.py prep | dscript"""
import os
import sys
import json
import shutil
import subprocess

import pandas as pd

import e6q_core as O

ROOT = 'tmp/dryrun'


def prep():
    r = O.P(*ROOT.split('/'))
    if os.path.exists(r):
        shutil.rmtree(r)
    os.makedirs(r)
    for sub in ('registration', 'verify/spec'):
        shutil.copytree(O.P(*sub.split('/')), os.path.join(r, sub))
    for rel in ('verify/identities_E6q_stage0.csv', 'verify/selftest_identities_E6q.csv', 'verify/impact_reconciliation_E6q.csv', 'verify/impact_reconciliation_ladder_E6q.csv',
                'verify/impact_reconciliation_daily_bridge_E6q.csv', 'diagnostics/G1_E6q.csv', 'diagnostics/stage0_E6q_part1.csv', 'diagnostics/stage0_E6q_part2.csv',
                'reports/E6q_S0A_reconciliation.md'):
        dst = os.path.join(r, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(O.P(*rel.split('/')), dst)
    s2 = json.load(open(O.P('registration', 'seal_A2.json'), encoding='utf-8'))
    json.dump(dict(written_at=s2['written_at'], n_files=0, sha256_manifest='', first_post_segment_write_at='9999-12-31 00:00:00 (dryrun)'),
              open(os.path.join(r, 'registration', 'seal_final.json'), 'w', encoding='utf-8'))
    d = os.path.join(r, 'verify', 'decision')
    os.makedirs(d, exist_ok=True)
    shutil.copy2(O.P('verify', 'decision', 'E6q_D_stage2.py'), os.path.join(d, 'E6q_D_stage2.py'))
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
    ds = os.path.join(r, 'verify', 'decision', 'E6q_D_stage2.py')
    assert O.sha_file(ds) == O.D_SCRIPT_SHA256
    env = dict(os.environ, PYTHONPYCACHEPREFIX=O.P('tmp', 'pyc_d'), PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run([sys.executable, 'verify/decision/E6q_D_stage2.py', '--root', '.', '--handoff', '.', '--out', 'out_dry'], cwd=r, env=env, capture_output=True, text=True)
    out = os.path.join(r, 'out_dry', 'E6q_D_probes_stage2.csv')
    if os.path.exists(out):
        D = pd.read_csv(out, keep_default_na=False)
        cols = [c for c in D.columns if c in ('probe_id', 'probe', 'name', 'status', 'detail', 'message')]
        print(D[cols].to_string(max_colwidth=160)[:16000] if cols else D.to_string()[:16000], flush=True)
    print('rc', p.returncode, O.san((p.stdout + p.stderr)[-4000:]), flush=True)


if __name__ == '__main__':
    {'prep': prep, 'dscript': dscript}[sys.argv[1]]()
