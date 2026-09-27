# -*- coding: utf-8 -*-
"""E6j 封存回执（plan §10.4 / §10.2；brief §8）：先计算、封存内容 hash 与回执、再读取统计与报告。
  --package P        accounts/P 与 randoms/P 全部四段 → registration/seal_P.json（MC 增补后追加 seal_P_v2.json …）
  --package B_post   accounts/B 与 randoms/B 的两后段 → registration/seal_B_post.json（同上）
版本只增不删：新版本先核对此前各版登记的文件 hash 全部未变，再登记当前全部文件并列出新增文件。
回执：基础任务数量 = 预期（P：6 形态 × 4 段原生 + 96 随机；B_post：2 × 28 原生 + 2 × 185 随机分片），MC 增补分片（路径区间 ≥ 1,024）
数量动态、须全部 SUCCEEDED 且与文件一一对应。读取程序 verify() 核对最新版本及此前各版。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time

import e6j_core as J

RES = J.RES
TOPUP_P = re.compile(r'_p(\d+)$')                    # run_prand_<段>_<形态>_<臂>_p<path0>
TOPUP_B = re.compile(r'__p(\d+)_(\d+)$')             # run_brand_<段>_<母体>__<块>__p<a>_<b>：a ≥ 1024 为增补


def files_of(dirs):
    out = []
    for d in dirs:
        for p in sorted(glob.glob(os.path.join(d, '**', '*'), recursive=True)):
            if os.path.isfile(p):
                out.append(p)
    return out


def seal_path(pkg, v):
    return os.path.join(RES, 'registration', ('seal_%s.json' % pkg) if v == 1 else ('seal_%s_v%d.json' % (pkg, v)))


def versions(pkg):
    vs, v = [], 1
    while os.path.exists(seal_path(pkg, v)):
        vs.append(v); v += 1
    return vs


def receipts(pkg):
    """返回 (基础回执名 → 状态, 增补回执名 → 状态, 基础预期数)。"""
    ts = os.path.join(RES, 'task_status')
    name = lambda p: os.path.basename(p)[:-len('.receipt.json')]
    if pkg == 'P':
        rp = glob.glob(os.path.join(ts, 'run_p_*.receipt.json'))
        rr = glob.glob(os.path.join(ts, 'run_prand_*.receipt.json'))
        base = {name(p): json.load(open(p))['status'] for p in rp}
        top = {}
        for p in rr:
            n = name(p); m = TOPUP_P.search(n)
            (top if (m and int(m.group(1)) >= 1024) else base)[n] = json.load(open(p))['status']
        return base, top, 6 * 4 + 96
    if pkg == 'B_post':
        base, top = {}, {}
        for s in J.POST_SEGS:
            for p in glob.glob(os.path.join(ts, 'run_b_%s_*.receipt.json' % s)):
                base[name(p)] = json.load(open(p))['status']
            for p in glob.glob(os.path.join(ts, 'run_brand_%s_*.receipt.json' % s)):
                n = name(p); m = TOPUP_B.search(n)
                (top if (m and int(m.group(1)) >= 1024) else base)[n] = json.load(open(p))['status']
        return base, top, 2 * 28 + 2 * 185
    raise ValueError(pkg)


def dirs_of(pkg):
    """P：四段账户 + 随机 + P 诊断（含后段真实差，同样先封存再读）；B_post：两后段账户 + 随机 + B 诊断。"""
    if pkg == 'P':
        return ([os.path.join(RES, 'accounts', 'P', s) for s in J.SEGMENTS] + [os.path.join(RES, 'randoms', 'P', s) for s in J.SEGMENTS]
                + [os.path.join(RES, 'diagnostics', 'P', s) for s in J.SEGMENTS])
    return ([os.path.join(RES, 'accounts', 'B', s) for s in J.POST_SEGS] + [os.path.join(RES, 'randoms', 'B', s) for s in J.POST_SEGS]
            + [os.path.join(RES, 'diagnostics', 'B', s) for s in J.POST_SEGS])


def topup_files(pkg, fl):
    if pkg == 'P':
        return sorted(f for f in fl if re.search(r'__[A-Z0-9]+_p(\d+)\.npz$', f) and int(re.search(r'_p(\d+)\.npz$', f).group(1)) >= 1024)
    return sorted(f for f in fl if re.search(r'__p(\d+)_(\d+)\.npz$', f) and int(re.search(r'__p(\d+)_\d+\.npz$', f).group(1)) >= 1024)


def main(pkg):
    vs = versions(pkg)
    v = (vs[-1] + 1) if vs else 1
    prev = {}
    for pv in vs:                                            # 此前各版登记的文件必须未变
        s = json.load(open(seal_path(pkg, pv)))
        bad = [f for f, h in s['files'].items() if J.sha_file(os.path.join(RES, f)) != h]
        if bad:
            raise RuntimeError('封存 v%d 登记的 %d 个文件已变化（例 %s）：不得追加新版本' % (pv, len(bad), bad[:3]))
        prev.update(s['files'])
    base, top, expect = receipts(pkg)
    fl = [p for p in files_of(dirs_of(pkg)) if 'profile' not in os.path.basename(p)]
    tf = topup_files(pkg, [os.path.relpath(p, RES) for p in fl])
    ok = (len(base) == expect and all(x == 'SUCCEEDED' for x in base.values()) and all(x == 'SUCCEEDED' for x in top.values())
          and len(tf) == len(top))
    files = {os.path.relpath(p, RES): J.sha_file(p) for p in fl}
    seal = dict(package=pkg, version=v, sealed_at=time.strftime('%Y-%m-%d %H:%M:%S'), receipts_base=len(base), receipts_base_expected=expect,
                receipts_topup=len(top), topup_files=len(tf), all_succeeded=ok, previous_versions=vs,
                new_files=sorted(set(files) - set(prev)), files=files)
    out = seal_path(pkg, v)
    if os.path.exists(out):
        raise RuntimeError('封存回执已存在（只增不删）：%s' % out)
    J.atomic_write_json(out, seal)
    print(pkg, 'v%d' % v, 'base receipts', len(base), '/', expect, 'topup', len(top), '/', len(tf), 'ok', ok, 'files', len(files),
          'new', len(seal['new_files']))
    return 0 if ok else 2


def verify(pkg):
    """最新版本全部文件 hash 一致、回执齐全；此前各版文件亦须未变。返回 (ok, 不符文件列表)。"""
    vs = versions(pkg)
    if not vs:
        return False, ['<无封存回执>']
    bad, ok = [], True
    for pv in vs:
        s = json.load(open(seal_path(pkg, pv)))
        bad += [f for f, h in s['files'].items() if J.sha_file(os.path.join(RES, f)) != h]
        if pv == vs[-1]:
            ok = bool(s['all_succeeded'])
            cur = [os.path.relpath(p, RES) for p in files_of(dirs_of(pkg)) if 'profile' not in os.path.basename(p)]
            bad += ['<未封存> ' + f for f in cur if f not in s['files']]      # 封存后新增文件：须先追加新版本再读
    return (not bad) and ok, sorted(set(bad))


if __name__ == '__main__':
    sys.exit(main(sys.argv[sys.argv.index('--package') + 1]))
