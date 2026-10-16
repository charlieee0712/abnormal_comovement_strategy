# -*- coding: utf-8 -*-
"""E6m 封存（附录 D-2；brief §5 S3 / S4；e6l_seal 同构）：seal_deriv.json / seal_post.json。
内容：该阶段两段的全部名单 / 附属名单 / Stage A / 账户 / 附属账户 / 随机分片的文件 sha；登记任务的回执计数；队列缺失（应有任务无 SUCCEEDED 回执）
与未解决失败（FAILED 且无后续 SUCCEEDED 重跑）；MC 增补完成回执（mc_done_<段>）。all_ok = 缺失 0 且未解决失败 0 且 MC 完成。
队列推算与 e6m_s_queue.tasks 同源（同一函数），分片常量不另写。
require(phase)：读结果前调用（e6m_s_stats / e6m_s_bootstrap / 政策 / 报告）——封存文件存在、all_ok、所列文件 sha 未变，否则拒绝。
  seal deriv|post     写封存
  verify deriv|post   只核（不写）"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time
import argparse

import e6m_core as M

DIRS = ('masks', 'masks_aux', 'stage_a', 'accounts', 'accounts_aux')


def segs_of(phase):
    return tuple(M.DERIV_SEGS) if phase == 'deriv' else tuple(M.POST_SEGS)


def seal_path(phase):
    return M.P('seal_%s.json' % phase)


def receipt(task_id):
    p = M.P('task_status', '%s.receipt.json' % re.sub(r'[:/|]', '_', task_id))
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None


def phase_files(phase):
    out = []
    for s in segs_of(phase):
        for d in DIRS:
            out += sorted(f for f in glob.glob(M.P(d, s, '*')) if os.path.isfile(f))
        out += sorted(glob.glob(M.P('randoms', '*', s, '*.npz')))
    return out


def seal(phase):
    import e6m_s_queue as Q
    import e6m_stage0_S as S0
    segs = segs_of(phase)
    exp = [t['task_id'] for ph in ('masks', 'aux', 'stage_a', 'memage', 'accounts', 'randoms') for t in Q.tasks(ph, segs)]
    st = {t: (receipt(t) or {}).get('status', 'MISSING') for t in exp}
    missing = sorted(t for t, s in st.items() if s != 'SUCCEEDED')
    failed = []
    fams = ('S_masks_', 'S_aux_', 'S_stage_a_', 'S_memage_', 'S_accounts_', 'S_rand_')    # 只看阶段 S 队列任务族（开发期 S_dev_* 等不计）
    for p in glob.glob(M.P('task_status', '*.receipt.json')):
        r = json.load(open(p, encoding='utf-8'))
        tid = r.get('task_id', '')
        if r.get('status') == 'FAILED' and tid.startswith(fams) and any(('_%s_' % s) in tid for s in segs):
            base = re.sub(r'_rerun\d*$', '', r['task_id'])
            ok_later = any((receipt(base + suf) or {}).get('status') == 'SUCCEEDED' for suf in ('', '_rerun') + tuple('_rerun%d' % k for k in range(2, 10)))
            if not ok_later:
                failed.append(r['task_id'])
    mc = {s: (receipt('mc_done_%s' % s) or {}).get('status', 'MISSING') for s in segs}
    files = phase_files(phase)
    H = S0.Hasher(workers=8)
    sh = H.many(files)
    man = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), phase=phase, segments=list(segs), machine=M.MACHINE, n_files=len(files),
               files={M.rel(f): sh[f] for f in files}, tasks_expected=len(exp), receipts=dict((k, sum(1 for v in st.values() if v == k)) for k in set(st.values())),
               queue_missing=missing, failed_unresolved=sorted(failed), mc_done=mc,
               all_ok=not missing and not failed and all(v == 'SUCCEEDED' for v in mc.values()))
    p = seal_path(phase)
    M.atomic_write_json(p, man)
    M.write_receipt(os.environ.get('E6M_TASK', 'seal_%s' % phase), [p], status='SUCCEEDED' if man['all_ok'] else 'FAILED', code=[__file__, M.__file__],
                    n_files=len(files), queue_missing=len(missing), failed_unresolved=len(failed), mc_done=mc)
    return man


def require(phase):
    """读结果前的门：封存存在、all_ok、文件 sha 未变（全量重算）。"""
    import e6m_stage0_S as S0
    p = seal_path(phase)
    if not os.path.exists(p):
        raise RuntimeError('封存门：%s 不存在（先封存再读）' % os.path.basename(p))
    man = json.load(open(p, encoding='utf-8'))
    if not man.get('all_ok'):
        raise RuntimeError('封存门：%s all_ok = false' % os.path.basename(p))
    files = [M.P(r) for r in man['files']]
    sh = S0.Hasher(workers=8).many(files)
    bad = [M.rel(f) for f in files if sh[f] != man['files'][M.rel(f)]]
    if bad:
        raise RuntimeError('封存门：%d 个文件 sha 已变（%s…）' % (len(bad), bad[:3]))
    return man


def require_for(path, seg):
    """读真实账户 / 随机目录（M.P('accounts' | 'accounts_aux' | 'randoms')）时按段所属阶段过封存门；其它目录（合成 / 开发）不拦。"""
    real = [os.path.realpath(M.P(d)) for d in ('accounts', 'accounts_aux', 'randoms')]
    rp = os.path.realpath(path or '')
    if any(rp == r or rp.startswith(r + os.sep) for r in real):
        return require('deriv' if seg in M.DERIV_SEGS else 'post')
    return None


def selftest():
    """夹具：临时工作目录（复制 registry/），伪造推导段全部应有任务的 SUCCEEDED 回执、两段 accounts 文件与 mc_done →
    seal 应 all_ok；删一个回执 → 缺失 1；改一个账户文件一个字节 → require 拒绝；require_for 对开发目录不拦。"""
    import shutil
    import e6m_s_queue as Q
    real_work = M.work()
    fx = os.path.join(real_work, 'tmp', 'seal_fixture')
    shutil.rmtree(fx, ignore_errors=True)
    os.makedirs(os.path.join(fx, 'task_status'))
    shutil.copytree(os.path.join(real_work, 'registry'), os.path.join(fx, 'registry'))
    os.environ['E6M_WORK'] = fx
    res = []
    try:
        segs = segs_of('deriv')
        exp = [t['task_id'] for ph in ('masks', 'aux', 'stage_a', 'memage', 'accounts', 'randoms') for t in Q.tasks(ph, segs)]
        for t in exp + ['mc_done_%s' % s for s in segs]:
            M.atomic_write_json(M.P('task_status', '%s.receipt.json' % re.sub(r'[:/|]', '_', t)), dict(task_id=t, status='SUCCEEDED'))
        for s in segs:
            os.makedirs(M.P('accounts', s))
            with open(M.P('accounts', s, 'A4b.npz'), 'wb') as fh:
                fh.write(b'fixture-%s' % s.encode())
        m1 = seal('deriv')
        res.append(('应有任务全 SUCCEEDED + mc_done → all_ok（%d 任务）' % len(exp), m1['all_ok'] and m1['n_files'] == 2))
        os.remove(M.P('task_status', '%s.receipt.json' % exp[7]))
        m2 = seal('deriv')
        res.append(('删一个回执 → 缺失 1、all_ok = false', (not m2['all_ok']) and len(m2['queue_missing']) == 1))
        M.atomic_write_json(M.P('task_status', '%s.receipt.json' % exp[7]), dict(task_id=exp[7], status='SUCCEEDED'))
        seal('deriv')
        res.append(('require 通过（文件未变）', bool(require('deriv'))))
        with open(M.P('accounts', segs[0], 'A4b.npz'), 'ab') as fh:
            fh.write(b'x')
        try:
            require('deriv')
            res.append(('改一个字节 → require 拒绝', False))
        except RuntimeError:
            res.append(('改一个字节 → require 拒绝', True))
        res.append(('require_for 对开发目录不拦', require_for(M.P('stageS_dev', 'synth', 'accounts'), segs[0]) is None))
        M.atomic_write_json(M.P('task_status', 'S_dev_stage0_ops_%s.receipt.json' % segs[0]), dict(task_id='S_dev_stage0_ops_%s' % segs[0], status='FAILED'))
        m3 = seal('deriv')
        res.append(('开发期带段名的 FAILED 回执不计入未解决失败', not m3['failed_unresolved']))
        M.atomic_write_json(M.P('task_status', 'S_accounts_%s_A4b_x.receipt.json' % segs[0]), dict(task_id='S_accounts_%s_A4b_x' % segs[0], status='FAILED'))
        m4 = seal('deriv')
        res.append(('阶段 S 队列族的 FAILED 回执计入未解决失败', m4['failed_unresolved'] == ['S_accounts_%s_A4b_x' % segs[0]]))
        try:
            require('post')
            res.append(('无 seal_post → require 拒绝', False))
        except RuntimeError:
            res.append(('无 seal_post → require 拒绝', True))
    finally:
        os.environ['E6M_WORK'] = real_work
        shutil.rmtree(fx, ignore_errors=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['seal', 'verify', 'selftest'])
    ap.add_argument('phase', nargs='?', default='deriv', choices=['deriv', 'post'])
    a = ap.parse_args()
    if a.task == 'selftest':
        res = selftest()
        for name, ok in res:
            print('%s  %s' % ('PASS' if ok else 'FAIL', name))
        return 0 if all(ok for _, ok in res) else 1
    if a.task == 'seal':
        man = seal(a.phase)
        print(json.dumps(dict(phase=a.phase, n_files=man['n_files'], missing=len(man['queue_missing']), failed=len(man['failed_unresolved']),
                              mc_done=man['mc_done'], all_ok=man['all_ok']), ensure_ascii=False))
        return 0 if man['all_ok'] else 1
    man = require(a.phase)
    print(json.dumps(dict(phase=a.phase, verified_files=man['n_files'], all_ok=True), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
