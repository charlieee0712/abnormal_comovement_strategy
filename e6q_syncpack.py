# -*- coding: utf-8 -*-
"""E6q 本机同步包（brief §8.2）：从 handoff/E6q_<ts>/ 按优先序选文件，本机落盘 ≤ 300 MB（按 10^6 字节计）：
⓪ verify/ 全部 + HANDOFF_SHA256.txt（总是纳入，计入总量）→ ① reports 全部 → ② 全部合同表（附录 B：registration / statistics / events / diagnostics 的表与 json、
trades/INDEX、accounts/daily/INDEX、code_register）→ ③–⑤ 全部 201 账户日序列（主 32 与锚 → 父 / 参照 → 其余）→ ⑥ 主 32 与锚的成交分片（三锚 → H20 主对象 → 其余）
→ ⑦ 父 / 参照的成交分片 → ⑧ M3 逐请求明细 → ⑨ 代码副本。
体积处理：单个 ≥ 1 MB 的文件以 gzip 无损存放（文件名加 .gz，mtime = 0 可复现），按存放字节计入上限；某项装不下即跳过、继续尝试后续较小项（不挤占更高优先级项）。
写 SYNC_LIST.tsv / SYNC_SHA256.txt / SYNC_GZ_ORIGINAL_SHA256.txt，打包 tmp/sync_<名>/pack.tgz 并切 8 MB 分块 + SHA256SUMS。用法：python3 e6q_syncpack.py <handoff 目录名>"""
import os
import sys
import gzip
import json
import shutil
import tarfile
import hashlib

import pandas as pd

import e6q_core as O

LIMIT = 300 * 1000 * 1000
GZ_MIN = 1000 * 1000
PART = 8 * 1024 * 1024
ANCHORS = ('E6Q-9f826422e6d4c39c', 'E6Q-b5c68d2c70eb5e19', 'E6Q-d78b9785b0594c1e')


def gz_copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(src, 'rb') as fi, open(dst, 'wb') as raw:
        with gzip.GzipFile(filename='', mode='wb', compresslevel=6, fileobj=raw, mtime=0) as fo:
            shutil.copyfileobj(fi, fo, 1 << 24)
    return os.path.getsize(dst), O.sha_file(dst)


def main(name):
    if name == 'LATEST':
        name = os.path.basename(open(O.P('handoff', 'LATEST_E6q.txt'), encoding='utf-8').read().strip())
    hd = O.P('handoff', name)
    sha = {}
    for line in open(os.path.join(hd, 'HANDOFF_SHA256.txt'), encoding='utf-8'):
        if line.strip():
            s, r = line.rstrip('\n').split('  ', 1)
            sha[r] = s
    sha.setdefault('HANDOFF_SHA256.txt', O.sha_file(os.path.join(hd, 'HANDOFF_SHA256.txt')))
    R = pd.read_csv(os.path.join(hd, 'registration', 'registry_E6q.csv'), keep_default_na=False, dtype=str)
    Rl = R.set_index('logical_id')
    h = R.set_index('exec_id').exec_hash
    top = set(R[R.is_primary32 == '1'].exec_id) | {Rl.loc[l].exec_id for l in ANCHORS if l in Rl.index}
    refs = set()
    for e in top:
        r = R.set_index('exec_id').loc[e]
        refs |= {x for x in (r.parent_same_arm_exec_id, r.native_same_trigger_exec_id, r.cash_same_trigger_exec_id) if x}
    refs -= top
    pri = []
    rel = sorted(sha)
    add = lambda r, k: pri.append((k, r))
    for r in rel:
        if r.startswith('verify/') or r == 'HANDOFF_SHA256.txt':
            add(r, 0)
    for r in rel:
        if r.startswith('reports/'):
            add(r, 1)
    BIG_LOW = ('events/m3_parent_orders_E6q.csv',)   # 逐请求明细（百万行级）：47 交接件完整保存，本机同步排在全部日序列之后
    for r in rel:
        t = r.split('/')[0]
        if r in BIG_LOW:
            continue
        if t in ('registration', 'statistics', 'events', 'diagnostics') or r in ('trades/INDEX.csv', 'accounts/daily/INDEX.csv') or (t == 'code_register' and not r.startswith('code_register/src/')):
            add(r, 2)
    # brief §8.2：日序列全部 201（各层按"主 32 与锚 → 父 / 参照 → 其余"）先于成交分片；成交分片再按重要性截断：三锚 → H20 主对象（LEVEL / T1a，
    # 臂按 NATIVE → M3 5 亿 → M1 → M2 1 亿 → M2 5 亿 → M3 1 亿 → M4）→ 其余主 32 → 父 / 参照（装不下的写进 SYNC_LIST，47 交接件完整）
    Ri = R.set_index('exec_id')
    anc = [Rl.loc[l].exec_id for l in ANCHORS if l in Rl.index]
    AO = {a: i for i, a in enumerate(('NATIVE', 'EXIT_GATE_LIQ_5E8', 'REINVEST_NEW', 'REINVEST_LIQ_1E8', 'REINVEST_LIQ_5E8', 'EXIT_GATE_LIQ_1E8', 'EXIT_HALF'))}
    TO = {t: i for i, t in enumerate(('T1b_LEVEL', 'T1a', 'UNION_T1a_T8', 'T8'))}
    imp = lambda e: (0 if e in anc else 1, 0 if Ri.loc[e, 'H'] == '20' else 1, TO.get(Ri.loc[e, 'trigger'], 9), AO.get(Ri.loc[e, 'arm'], 9), e)
    for e in sorted(top, key=imp):
        add('accounts/daily/%s.csv' % h[e], 3)
    for e in sorted(refs, key=imp):
        add('accounts/daily/%s.csv' % h[e], 4)
    for e in sorted(set(R.exec_id) - top - refs):
        add('accounts/daily/%s.csv' % h[e], 5)
    for e in sorted(top, key=imp):
        add('trades/%s.csv' % h[e], 6)
    for e in sorted(refs, key=imp):
        add('trades/%s.csv' % h[e], 7)
    for r in BIG_LOW:
        add(r, 8)
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
                          trades_included=int(inc.priority.isin([6, 7]).sum()), trades_total=int(L.priority.isin([6, 7]).sum()),
                          daily_included=int(inc.priority.isin([3, 4, 5]).sum()), daily_total=int(L.priority.isin([3, 4, 5]).sum())), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
