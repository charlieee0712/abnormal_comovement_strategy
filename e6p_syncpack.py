# -*- coding: utf-8 -*-
"""E6p 本机同步包（brief §8.2）：从 handoff/E6p_<ts>/ 按优先序选文件，本机落盘 ≤ 300 MB（按 10^6 字节计，同时满足 MiB 口径）：
⓪ verify/ 全部 + HANDOFF_SHA256.txt（brief 句式中 verify 与 sha 清单在截断清单之外 → 总是纳入，计入总量）→ ① reports 全部 →
② 全部合同表（附录 B.1–B.21：registration / statistics / events / diagnostics / verify 的表与 json、trades/INDEX、accounts/daily/INDEX）→
③ 主对象两只与其同 H 父 / H5 NATIVE 父的 trades 分区 → ④ accounts/daily：主对象家族（D 脚本 S18 的目标账户）→ primary72 → 全部 PARENT →
主对象两只的 D95 / CASH_REMAIN / RECYCLE 变体 → 镜像。
体积处理：单个 ≥ 20 MB 的文件（成本曲线表、成交分片）以 gzip 无损存放（文件名加 .gz，mtime = 0 可复现），按存放字节计入上限；其余原样。
某项装不下即跳过、继续尝试后续较小项（不挤占任何更高优先级项）。写 SYNC_LIST.tsv（优先级 / 原始字节 / 原始 sha / 是否纳入 / 存放形式 / 存放字节 / 存放 sha）、
SYNC_SHA256.txt（存放文件）、SYNC_GZ_ORIGINAL_SHA256.txt（gz 文件解压后的原始 sha），打包 tmp/sync_<名>/pack.tgz 并切 8 MB 分块 + SHA256SUMS。
用法：python3 e6p_syncpack.py <handoff 目录名>"""
import os
import sys
import gzip
import json
import shutil
import tarfile
import hashlib

import pandas as pd

import e6p_core as O

LIMIT = 300 * 1000 * 1000
GZ_MIN = 20 * 1000 * 1000
PART = 8 * 1024 * 1024


def gz_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, 'rb') as fi, open(dst, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', compresslevel=6, fileobj=raw, mtime=0) as fo:
            shutil.copyfileobj(fi, fo, 1 << 24)
    return os.path.getsize(dst), O.sha_file(dst)


def main(name):
    hd = O.P('handoff', name)
    sha = {}
    for line in open(os.path.join(hd, 'HANDOFF_SHA256.txt'), encoding='utf-8'):
        if line.strip():
            s, r = line.rstrip('\n').split('  ', 1)
            sha[r] = s
    sha.setdefault('HANDOFF_SHA256.txt', O.sha_file(os.path.join(hd, 'HANDOFF_SHA256.txt')))
    R = pd.read_csv(os.path.join(hd, 'registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    main_ = R[R.is_main_object == '1']
    fam = set(main_.exec_id) | set(main_.parent_same_h_exec_id) | set(main_.parent_h5_native_exec_id)
    h = R.set_index('exec_id').exec_hash
    pri = []
    rel = sorted(sha)
    add = lambda r, k: pri.append((k, r))
    for r in rel:
        if r.startswith('verify/') or r == 'HANDOFF_SHA256.txt':
            add(r, 0)
    for r in rel:
        if r.startswith('reports/'):
            add(r, 1)
    for r in rel:
        top = r.split('/')[0]
        if top in ('registration', 'statistics', 'events', 'diagnostics') or r in ('trades/INDEX.csv', 'accounts/daily/INDEX.csv') or \
                top == 'code_register' and r.endswith('.csv'):
            add(r, 2)
    for e in sorted(fam):
        add('trades/%s.csv' % h[e], 3)
    acc = R[(R.role == 'ACCOUNT') & (R.form == O.MAIN_FORM) & (R.renew == '0')]
    capok = ((acc.deploy == 'NATIVE') & (acc.cap == 'SOURCE')) | (acc.deploy.isin(['D80', 'D95']) & (acc.cap == 'RELATIVE_UPPER'))
    tgt = acc[capok & (acc.memory == 'HG10') & (((acc.H == '20') & acc.deploy.isin(['NATIVE', 'D80', 'D95']) & acc.trigger.isin(['T1a', 'T1b_LEVEL', 'NONE'])) |
                                                ((acc.H == '5') & (acc.deploy == 'NATIVE') & (acc.trigger == 'NONE')))]
    p72 = R[R.is_primary72 == '1']
    par = R[R.block == 'PARENT'].assign(_m=lambda d: (d.memory != 'HG10').astype(int), _h=lambda d: d.H.astype(int)).sort_values(['_m', '_h', 'deploy', 'memory', 'execution_profile'])
    var = acc[(acc.memory == 'HG10') & (acc.H == '20') & acc.trigger.isin(['T1a', 'T1b_LEVEL']) &
              acc.deploy.isin(['D95', 'CASH_REMAIN', 'RECYCLE_HALF', 'RECYCLE_COST0', 'RECYCLE_COSTNET'])]
    mir = R[(R.role == 'MIRROR') & R.owner_logical_id.isin(set(main_.logical_id))]
    for grp in (tgt, p72, par, var, mir):
        for e in grp.exec_id:
            add('accounts/daily/%s.csv' % h[e], 4)
    sd = O.P('tmp', 'sync_%s' % name)
    if os.path.exists(sd):
        shutil.rmtree(sd)
    os.makedirs(sd)
    seen, rows, tot = set(), [], 0
    for k, r in pri:
        if r in seen or r not in sha:
            continue
        seen.add(r)
        src = os.path.join(hd, r)
        b = os.path.getsize(src)
        if b >= GZ_MIN:
            sb, ss = gz_copy(src, os.path.join(sd, 'gz', r + '.gz'))
            form = 'gz'
        else:
            sb, ss, form = b, sha[r], 'raw'
        inc = k == 0 or tot + sb <= LIMIT
        if inc:
            tot += sb
        elif form == 'gz':
            os.remove(os.path.join(sd, 'gz', r + '.gz'))
        rows.append(dict(priority=k, path=r, bytes=b, sha256=sha[r], included=int(inc), stored_as=(r + '.gz') if form == 'gz' else r,
                         stored_bytes=sb, stored_sha256=ss))
    L = pd.DataFrame(rows)
    L.to_csv(os.path.join(sd, 'SYNC_LIST.tsv'), sep='\t', index=False)
    inc = L[L.included == 1]
    with open(os.path.join(sd, 'SYNC_SHA256.txt'), 'w', encoding='utf-8') as fh:
        fh.write(''.join('%s  %s\n' % (r.stored_sha256, r.stored_as) for r in inc.itertuples(index=False)))
    gzr = inc[inc.stored_as != inc.path]
    with open(os.path.join(sd, 'SYNC_GZ_ORIGINAL_SHA256.txt'), 'w', encoding='utf-8') as fh:
        fh.write(''.join('%s  %s\n' % (r.sha256, r.path) for r in gzr.itertuples(index=False)))
    pk = os.path.join(sd, 'pack.tgz')
    with tarfile.open(pk, 'w:gz', compresslevel=6) as tf:
        for r in inc.itertuples(index=False):
            src = os.path.join(sd, 'gz', r.stored_as) if r.stored_as != r.path else os.path.join(hd, r.path)
            tf.add(src, arcname='%s/%s' % (name, r.stored_as))
        for f in ('SYNC_LIST.tsv', 'SYNC_SHA256.txt', 'SYNC_GZ_ORIGINAL_SHA256.txt'):
            tf.add(os.path.join(sd, f), arcname='%s/%s' % (name, f))
    sums = []
    with open(pk, 'rb') as fh:
        i = 0
        while True:
            buf = fh.read(PART)
            if not buf:
                break
            pn = os.path.join(sd, 'part.%03d' % i)
            with open(pn, 'wb') as out:
                out.write(buf)
            sums.append('%s  part.%03d' % (hashlib.sha256(buf).hexdigest(), i))
            i += 1
    sums.append('%s  pack.tgz' % O.sha_file(pk))
    with open(os.path.join(sd, 'SHA256SUMS'), 'w') as fh:
        fh.write('\n'.join(sums) + '\n')
    ex = L[L.included == 0]
    print(json.dumps(dict(selected=int(len(inc)), excluded=int(len(ex)), stored_bytes=int(tot), raw_bytes_selected=int(inc.bytes.sum()), gz_files=int(len(gzr)),
                          pack_bytes=os.path.getsize(pk), parts=len(sums) - 1, excluded_by_priority=ex.groupby('priority').size().to_dict(),
                          daily_included=int(((inc.priority == 4)).sum()), daily_total=int((L.priority == 4).sum())), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
