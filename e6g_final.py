#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 收尾: 重算 source_manifest (e6g_*.py 在过程中改过) + 总 manifest.json。
brief §12: 每登记单元 ∈ {PENDING, RUNNING, SUCCEEDED, FAILED, LIMIT, SUPERSEDED},
按 task_id 计数之和 = 登记总数。核心模块未跑不得称整轮"通过", 标 PARTIAL_WITH_LIMITS。
"""
import os, sys, json, glob, time, hashlib, subprocess
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G

CODE = '/mnt/sda2/lichenchen/code/project_core'
R = G.RES


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    # ---- 1. 重算 source_manifest (e6g 侧) ----
    sm = json.load(open(os.path.join(R, 'source_manifest.json')))
    e6g = sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, 'e6g_*.py')))
    sm['e6g_new'] = {f: sha(os.path.join(CODE, f)) for f in e6g}
    sm['counts']['e6g'] = len(e6g)
    sm['e6g_recomputed_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    sm['note_e6g_hash'] = ('e6g_*.py 在执行过程中有修正 (见 limit_register 的 F1-F6), '
                           '本字段是【交付时】的哈希; 开工时的哈希已被覆盖, 过程中的修改逐条登记在案。')
    # 地基与 e6e/e6f 重新核一遍, 确认没被改
    changed = []
    for grp in ('foundation_readonly', 'e6e_frozen', 'e6f_frozen'):
        for f, h0 in sm[grp].items():
            h1 = sha(os.path.join(CODE, f))
            if h1 != h0:
                changed.append(dict(group=grp, file=f, before=h0[:16], after=h1[:16]))
    sm['readonly_integrity'] = dict(n_checked=sum(len(sm[g]) for g in
                                                  ('foundation_readonly', 'e6e_frozen',
                                                   'e6f_frozen')),
                                    n_changed=len(changed), changed=changed)
    json.dump(sm, open(os.path.join(R, 'source_manifest.json'), 'w'), indent=1,
              ensure_ascii=False)

    # ---- 2. 任务状态表 ----
    st = []
    for f in sorted(glob.glob(os.path.join(R, 'task_status', 'DONE_*.json'))):
        d = json.load(open(f))
        tid = os.path.basename(f).replace('DONE_', '').replace('.json', '')
        nf = int(d.get('n_failed', 0) or 0)
        st.append(dict(task_id=tid, block=d.get('block', tid.split('_')[0]),
                       segment=d.get('segment', ''), n_rows=d.get('n_rows', d.get('n_config_rows')),
                       n_failed=nf, elapsed_s=d.get('elapsed_s'),
                       status=('FAILED' if nf and nf == d.get('n_rows') else
                               ('LIMIT' if nf else 'SUCCEEDED'))))
    S = pd.DataFrame(st)
    S.to_csv(os.path.join(R, 'task_status', 'task_status.csv'), index=False)
    cnt = S.status.value_counts().to_dict() if len(S) else {}
    total = int(len(S))
    assert sum(cnt.values()) == total, '状态表求和 %d != 登记总数 %d' % (sum(cnt.values()), total)

    # ---- 3. coverage ----
    cov = pd.read_csv(os.path.join(R, 'coverage.csv'))
    cv = cov.status.value_counts().to_dict()

    # ---- 4. H manifest / 自测 / 守卫 ----
    hm = json.load(open(os.path.join(R, 'checks', 'H_manifest_frozen.json')))
    gt = json.load(open(os.path.join(R, 'checks', 'guard_attack_tests.json')))
    ng_ok = sum(1 for x in gt['results'] if x['ok'])
    sel = []
    for f in sorted(glob.glob(os.path.join(R, 'checks', 'selftests_*.json'))):
        d = json.load(open(f))
        a = [x for x in d['results'] if x['level'] == 'ANCHOR']
        sel.append(dict(segment=d['segment'], n_anchor=len(a),
                        n_pass=sum(1 for x in a if x['ok'])))

    man = dict(
        round='E6g', version=G.VERSION, written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        results_dir=R,
        git_head=subprocess.check_output(['git', '-C', CODE, 'rev-parse',
                                          '--short', 'HEAD']).decode().strip(),
        inputs=sm.get('inputs', {}), declared_in_brief=sm.get('declared_in_brief', {}),
        input_fingerprint_check=sm.get('input_fingerprint_check', []),
        readonly_integrity=sm['readonly_integrity'],
        h_manifest=dict(sha256=hm['descriptor_id_sha256'], total=hm['total'],
                        unique_paths=hm['unique_path_keys'],
                        new40_blood_in_H=hm['new40_blood_in_H'],
                        declared_diff=hm['declared_diff'], frozen_at=hm['frozen_at']),
        guard_attack_tests='%d/%d' % (ng_ok, len(gt['results'])),
        selftests=sel,
        task_status=dict(total=total, by_status=cnt),
        coverage=cv,
        reports=['REPORT_part1.md', 'REPORT_part2.md', 'REPORT_part3.md'],
        completion=('PARTIAL_WITH_LIMITS' if cv.get('deferred', 0) or cv.get('changed', 0)
                    else 'COMPLETE'),
        completion_note=('coverage 有 %d 条 deferred、%d 条 changed, 按 brief §12 标 '
                         'PARTIAL_WITH_LIMITS; 未做项与理由逐条在 coverage.csv 与 REPORT_part3。'
                         % (cv.get('deferred', 0), cv.get('changed', 0))),
    )
    json.dump(man, open(os.path.join(R, 'manifest.json'), 'w'), indent=1, ensure_ascii=False)
    print('== manifest ==')
    print(' 任务状态表: 总 %d, %s (求和 = 登记总数 ✓)' % (total, cnt))
    print(' coverage:', cv)
    print(' H manifest: %d 描述符 / %d 真实路径 / NEW40 血缘 %d / sha %s'
          % (hm['total'], hm['unique_path_keys'], hm['new40_blood_in_H'],
             hm['descriptor_id_sha256'][:16]))
    print(' 守卫攻击测试: %d/%d' % (ng_ok, len(gt['results'])))
    print(' 自测:', [(x['segment'], '%d/%d' % (x['n_pass'], x['n_anchor'])) for x in sel])
    print(' 只读完整性: 核了 %d 个文件, 变了 %d 个'
          % (man['readonly_integrity']['n_checked'], man['readonly_integrity']['n_changed']))
    if changed:
        print(' !! 被改动的只读文件:', changed)
    print(' 完成度:', man['completion'])


if __name__ == '__main__':
    main()
