# -*- coding: utf-8 -*-
"""E6p 假数据空跑（brief §4 A2："假数据空跑交付链"）：在 tmp/dryrun 下用推导段日行循环复制成后段（假数据）跑完统计 / 政策 / 诊断 / 恒等 / 卡 / 报告 / SCHEMA，
再把注册件、spec 指纹、决策端脚本放进同一测试根，以相对路径运行决策端脚本，检查每个探针都有状态行（结果不作门；只为正式尾段一次过）。
用法：python3 e6p_dryrun.py prep | dscript"""
import os
import sys
import json
import shutil
import subprocess

import pandas as pd

import e6p_core as O

ROOT = 'tmp/dryrun'


def prep():
    r = O.P(ROOT)
    for sub in ('registration', 'verify/spec', 'code_register'):
        src = O.P(sub)
        dst = os.path.join(r, sub)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    for rel in ('verify/identities_E6p_stage0.csv', 'diagnostics/G1_E6p.csv'):
        os.makedirs(os.path.dirname(os.path.join(r, rel)), exist_ok=True)
        shutil.copy2(O.P(rel), os.path.join(r, rel))
    s2 = json.load(open(O.P('registration', 'seal_A2.json')))
    json.dump(dict(written_at=s2['written_at'], n_files=0, sha256_manifest='', first_post_segment_write_at='9999-12-31 00:00:00 (dryrun)'),
              open(os.path.join(r, 'registration', 'seal_final.json'), 'w'))
    print('prep ok', flush=True)


def dscript():
    r = O.P(ROOT)
    files = []
    for dp, dn, fn in os.walk(r):
        dn[:] = [d for d in dn if d not in ('out_dry',)]
        for f in fn:
            if f != 'HANDOFF_SHA256.txt':
                p = os.path.join(dp, f)
                files.append('%s  %s' % (O.sha_file(p), os.path.relpath(p, r)))
    open(os.path.join(r, 'HANDOFF_SHA256.txt'), 'w').write('\n'.join(sorted(files, key=lambda x: x.split('  ', 1)[1])) + '\n')
    ds = O.P('verify', 'decision', 'E6p_D_stage2.py')
    assert O.sha_file(ds) == O.D_SCRIPT_SHA256
    env = dict(os.environ, PYTHONPYCACHEPREFIX=O.P('tmp', 'pyc_d'), PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run([sys.executable, os.path.relpath(ds, r), '--root', '.', '--handoff', '.', '--out', 'out_dry'], cwd=r, env=env, capture_output=True, text=True)
    out = os.path.join(r, 'out_dry', 'E6p_D_probes_stage2.csv')
    if os.path.exists(out):
        D = pd.read_csv(out, keep_default_na=False)
        print(D.to_string()[:12000], flush=True)
    print('rc', p.returncode, O.san((p.stdout + p.stderr)[-3000:]), flush=True)


if __name__ == '__main__':
    {'prep': prep, 'dscript': dscript}[sys.argv[1]]()
