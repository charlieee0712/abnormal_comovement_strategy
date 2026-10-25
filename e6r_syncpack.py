# -*- coding: utf-8 -*-
"""E6r 本机同步包（brief §8：≤ 300 MB，按 10^6 字节计）：从 handoff/E6r_<ts>/ 按优先序选文件——
⓪ verify/ 全部 + HANDOFF_SHA256.txt（总是纳入，计入总量）→ ① reports 全部 → ② 全部合同表（registration / statistics / events / diagnostics 的表与 json、
trades/INDEX、accounts/daily/INDEX、code_register 登记）→ ③–⑤ 全部 350 账户日序列（锚 = 主 9 / E 对象 / 前沿 / 规模参照 → 其参照 → 其余）→ ⑥ 锚的成交 → ⑦ 参照的成交 → ⑨ 代码副本。
单个 ≥ 1 MB 的非 gz 文件以 gzip 无损存放（文件名加 .gz，mtime = 0 可复现），已是 .gz 的原样；按存放字节计入上限；装不下即跳过、继续尝试后续较小项。
写 SYNC_LIST.tsv / SYNC_SHA256.txt / SYNC_GZ_ORIGINAL_SHA256.txt，打包 tmp/sync_<名>/pack.tgz 并切 8 MB 分块 + SHA256SUMS。用法：python3 e6r_syncpack.py <handoff 目录名 | LATEST>"""
import os
import sys
import gzip
import json
import shutil
import tarfile
import hashlib

import pandas as pd

import e6r_core as O

LIMIT = 300 * 1000 * 1000
GZ_MIN = 1000 * 1000
PART = 8 * 1024 * 1024


def gz_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, 'rb') as fi, open(dst, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', compresslevel=6, fileobj=raw, mtime=0) as fo:
            shutil.copyfileobj(fi, fo, 1 << 24)
    return os.path.getsize(dst), O.sha_file(dst)


def main(name):
    if name == 'LATEST':
        name = os.path.basename(open(O.P('handoff', 'LATEST_E6r.txt'), encoding='utf-8').read().strip())
    hd = O.P('handoff', name)
    sha = {}
    for line in open(os.path.join(hd, 'HANDOFF_SHA256.txt'), encoding='utf-8'):
        if line.strip():
            s, r = line.rstrip('\n').split('  ', 1)
            sha[r] = s
    sha.setdefault('HANDOFF_SHA256.txt', O.sha_file(os.path.join(hd, 'HANDOFF_SHA256.txt')))
    R = pd.read_csv(os.path.join(hd, 'registration', 'registry_E6r.csv'), keep_default_na=False, dtype=str)
    Ri = R.set_index('exec_id')
    lid2e = dict(zip(R.logical_id, R.exec_id))
    prim = json.load(open(os.path.join(hd, 'registration', 'spec', 'primary.json'), encoding='utf-8'))
    cl = json.load(open(os.path.join(hd, 'registration', 'spec', 'claims.json'), encoding='utf-8'))
    top = [lid2e[l] for l in prim['primary9']] + [lid2e[c[k]] for c in cl for k in ('owner', 'reference')] + [lid2e[prim['frontier']] if isinstance(prim['frontier'], str)
                                                                                                          else lid2e.get(str(prim['frontier']), '')]
    top += [lid2e[l] for l in prim.get('scale_references', []) if l in lid2e]
    top = [e for i, e in enumerate(top) if e and e not in top[:i]]
    refs = []
    for e in top:
        r = Ri.loc[e]
        for x in (r.policy_reference_exec_id, r.noexit_same_overlay_exec_id, r.flat_same_exit_exec_id, r.native_same_trigger_flat_exec_id):
            if x and x not in top and x not in refs:
                refs.append(x)
    h = Ri.exec_hash
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
        t = r.split('/')[0]
        if t in ('registration', 'statistics', 'events', 'diagnostics') or r in ('trades/INDEX.csv', 'accounts/daily/INDEX.csv') or \
                (t == 'code_register' and not r.startswith('code_register/src/')):
            add(r, 2)
    for e in top:
        add('accounts/daily/%s.csv' % h[e], 3)
    for e in refs:
        add('accounts/daily/%s.csv' % h[e], 4)
    for e in sorted(set(R.exec_id) - set(top) - set(refs)):
        add('accounts/daily/%s.csv' % h[e], 5)
    for e in top:
        add('trades/%s.csv.gz' % h[e], 6)
    for e in refs:
        add('trades/%s.csv.gz' % h[e], 7)
    for r in rel:
        if r.startswith('code_register/src/'):
            add(r, 9)
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
        if b >= GZ_MIN and not r.endswith('.gz'):
            sb, ss = gz_copy(src, os.path.join(sd, 'gz', r + '.gz'))
            form = 'gz'
        else:
            sb, ss, form = b, sha[r], 'raw'
        inc = k == 0 or tot + sb <= LIMIT
        if inc:
            tot += sb
        elif form == 'gz':
            os.remove(os.path.join(sd, 'gz', r + '.gz'))
        rows.append(dict(priority=k, path=r, bytes=b, sha256=sha[r], included=int(inc), stored_as=(r + '.gz') if form == 'gz' else r, stored_bytes=sb, stored_sha256=ss))
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
            with open(os.path.join(sd, 'part.%03d' % i), 'wb') as out:
                out.write(buf)
            sums.append('%s  part.%03d' % (hashlib.sha256(buf).hexdigest(), i))
            i += 1
    sums.append('%s  pack.tgz' % O.sha_file(pk))
    with open(os.path.join(sd, 'SHA256SUMS'), 'w') as fh:
        fh.write('\n'.join(sums) + '\n')
    ex = L[L.included == 0]
    print(json.dumps(dict(selected=int(len(inc)), excluded=int(len(ex)), stored_bytes=int(tot), gz_files=int(len(gzr)), pack_bytes=os.path.getsize(pk), parts=len(sums) - 1,
                          excluded_by_priority={int(k): int(v) for k, v in ex.groupby('priority').size().items()},
                          trades_included=int(inc.priority.isin([6, 7]).sum()), trades_total=int(L.priority.isin([6, 7]).sum()),
                          daily_included=int(inc.priority.isin([3, 4, 5]).sum()), daily_total=int(L.priority.isin([3, 4, 5]).sum())), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
