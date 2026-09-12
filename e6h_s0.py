#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 阶段 0: 源清单。冻结四地基 + 七 e6e + 十九 e6f + 二十八 e6g 的 SHA、
运行库版本、HEAD / dirty / untracked、输入指纹 (声明值与实际值并列)。

brief §2 第一条。本脚本【只读】源码, 不改任何东西。
"""
from __future__ import annotations
import os
import sys
import json
import glob
import time
import platform
import subprocess

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

CODE = H.CODE
RES = H.RES

FOUNDATION = ['data_loader.py', 'features_daily.py', 'event_study.py',
              'pool_screening_v2.py']

# brief §3 输入指纹: (文件, brief/plan 声明的值, 说明)
DECLARED = {
    'E6h_plan_web_final.md': (
        '1eff57b67965a11d876caa073fd2c6f3b968fc27d92635c15a389c55c55cb67c',
        'brief §用途 声明; 逐位相符'),
    'E6h_proposal.md': (
        '93c698ea373367e14c55e7c389260d12f034ba4ba48158738f7ae38ebded42af',
        'brief 与 plan 附录 C 记的是【加勘误块之前】的字节; brief 已自记 WARN'),
    'E6g_REVIEW.md': (
        'ef36aa7fb3479f90a1b8e2d895487918ff6856df3e73e67de10b3792223d15dd',
        'plan 附录 C 记的字节; brief 写"与 plan 一致"但该文件其后也被补了负号勘误'),
}
COPY_OF = {'E6h_plan_web_final.md': 'PLAN_COPY.md',
           'E6h_proposal.md': 'E6h_proposal_copy.md',
           'E6g_REVIEW.md': 'E6g_REVIEW_copy.md',
           'E6h_need_driven_routing.md': 'brief_copy.md'}


def git(*a):
    return subprocess.check_output(['git', '-C', CODE] + list(a)).decode().strip()


def main():
    os.makedirs(RES, exist_ok=True)
    man = dict(round='E6h', version=H.VERSION,
               written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               results_dir=RES, code_dir=CODE)

    # ---- 1. 源码 SHA ----
    groups = {}
    groups['foundation_readonly'] = {f: H.sha_file(os.path.join(CODE, f))
                                     for f in FOUNDATION}
    for tag, pat in (('e6e_frozen', 'e6e_*.py'), ('e6f_frozen', 'e6f_*.py'),
                     ('e6g_frozen', 'e6g_*.py')):
        fs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, pat)))
        groups[tag] = {f: H.sha_file(os.path.join(CODE, f)) for f in fs}
    groups['e6h_new'] = {os.path.basename(p): H.sha_file(p)
                         for p in sorted(glob.glob(os.path.join(CODE, 'e6h_*.py')))}
    man.update(groups)
    man['counts'] = {k: len(v) for k, v in groups.items()}
    # 也把 engine.py / comprehensive_factor_diagnosis.py 记上 (被 import 但不在四地基)
    extra = ['comprehensive_factor_diagnosis.py', 'engine.py']
    man['other_imported'] = {f: H.sha_file(os.path.join(CODE, f))
                             for f in extra if os.path.exists(os.path.join(CODE, f))}

    # ---- 2. 环境 ----
    import numpy, pandas
    env = dict(python=platform.python_version(), numpy=numpy.__version__,
               pandas=pandas.__version__, platform=platform.platform())
    for m in ('sklearn', 'scipy', 'pyarrow'):
        try:
            env[m] = __import__(m).__version__
        except Exception as e:
            env[m] = 'UNAVAILABLE: %s' % str(e)[:60]
    man['env'] = env

    # ---- 3. git ----
    man['git'] = dict(
        head=git('rev-parse', '--short', 'HEAD'),
        head_subject=git('log', '-1', '--format=%s'),
        dirty=[l for l in git('status', '--porcelain').split('\n')
               if l and not l.startswith('??')],
        untracked=[l[3:] for l in git('status', '--porcelain').split('\n')
                   if l.startswith('??')])

    # ---- 4. 输入指纹: 声明 vs 实际 ----
    fps, warns = [], []
    for name, copyname in COPY_OF.items():
        p = os.path.join(RES, copyname)
        actual = H.sha_file(p) if os.path.exists(p) else None
        dec, note = DECLARED.get(name, (None, 'brief 未声明'))
        row = dict(input=name, copy_in_results=copyname, actual_sha256=actual,
                   declared_sha256=dec, matches=(dec == actual) if dec else None,
                   note=note)
        fps.append(row)
        if dec and actual and dec != actual:
            warns.append(dict(
                level='WARN', input=name, declared=dec[:16], actual=actual[:16],
                explain=note,
                impact=('不阻断: 两个文件都是在 plan 产出后被补了同一处负号勘误 '
                        '(proposal 顶部勘误块 / E6g_REVIEW §Q1 补记 = 复盘 #33), '
                        '内容只增不减。以【实际字节】为准, 两个哈希都进本清单。')))
    man['input_fingerprints'] = fps
    man['warnings'] = warns

    # ---- 5. E6g 产物依赖 ----
    e6g = H.E6G_DIR
    deps = ['registry/key_registry.csv', 'E6h_registration_draft.md',
            'H0/H_manifest.csv', 'checks/H_manifest_frozen.json',
            'engine_contract.md', 'coverage.csv', 'manifest.json',
            'limit_register.md', 'source_corrections_E6g.md']
    man['e6g_inputs'] = {
        d: (dict(exists=True, sha256=H.sha_file(os.path.join(e6g, d)),
                 bytes=os.path.getsize(os.path.join(e6g, d)))
            if os.path.exists(os.path.join(e6g, d)) else dict(exists=False))
        for d in deps}
    man['e6g_dir'] = e6g

    # ---- 6. 注册表规模 ----
    man['registry'] = dict(U35=len(H.U35), NEW40=len(H.NEW40), U74=len(H.U74),
                           derived=sorted(H.DERIVED), n_derived=len(H.DERIVED),
                           registered_total=len(H.REGISTERED),
                           rule_objects=sorted(H.RULE_OBJECTS))
    man['guard'] = dict(deriv_segs=list(H.DERIV_SEGS), post_segs=list(H.POST_SEGS),
                        protected_label_end=H.PROTECTED_LABEL_END,
                        market_data_end_max=H.MARKET_DATA_END_MAX,
                        record_B_loaded=H.load_approval()['loaded'])

    with open(os.path.join(RES, 'source_manifest.json'), 'w') as fh:
        json.dump(man, fh, indent=1, ensure_ascii=False)

    print('== E6h source_manifest ==')
    print(' 源码: 地基 %d / e6e %d / e6f %d / e6g %d / e6h %d'
          % (man['counts']['foundation_readonly'], man['counts']['e6e_frozen'],
             man['counts']['e6f_frozen'], man['counts']['e6g_frozen'],
             man['counts']['e6h_new']))
    print(' 环境: python %s numpy %s pandas %s sklearn %s scipy %s'
          % (env['python'], env['numpy'], env['pandas'], env['sklearn'], env['scipy']))
    print(' git : HEAD %s  dirty %d  untracked %d'
          % (man['git']['head'], len(man['git']['dirty']), len(man['git']['untracked'])))
    print(' 输入指纹:')
    for r in fps:
        m = {True: '相符', False: '**不符**', None: '(brief 未声明)'}[r['matches']]
        print('   %-28s %s  %s' % (r['input'], (r['actual_sha256'] or '?')[:16], m))
    if warns:
        print(' WARN %d 条 (不阻断):' % len(warns))
        for w in warns:
            print('   %s: 声明 %s / 实际 %s' % (w['input'], w['declared'], w['actual']))
            print('     %s' % w['explain'])
    miss = [d for d, v in man['e6g_inputs'].items() if not v['exists']]
    print(' E6g 依赖: %d/%d 存在%s'
          % (len(deps) - len(miss), len(deps), ('; 缺 %s' % miss) if miss else ''))
    print(' 注册: U74 %d + 派生 %d = %d; 规则对象 %d; 记录 B 已批准=%s'
          % (len(H.U74), len(H.DERIVED), len(H.REGISTERED), len(H.RULE_OBJECTS),
             man['guard']['record_B_loaded']))


if __name__ == '__main__':
    main()
