# -*- coding: utf-8 -*-
"""E6l 代码变更登记（brief A10 固定 §C；附录 D-3；E6k C-7 格式）。基线 = source_manifest.json 的 e6l_code_sha256_at_stage0（Stage 0 收口时 18 个文件）；
版本存档 = 部署脚本逐版本另存（tmp/e6l_stage/versions/<文件>.<sha16> 与 deploy_log.txt）。对每个 Stage 0 之后改动或新增的 e6l_* 文件：
版本链（sha16、部署时刻）→ 相邻版本 unified diff 存 results/code_register/ → 反向还原核验（difflib.ndiff + restore：由 after 与差异逐字节重建 before）。
说明列（范围 / 触发 / 影响面 / 等价证据）取执行端工作笔记 results/code_register/change_notes.json（逐文件）。输出 reports/E6l_code_change_register.md。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import json
import difflib
import hashlib

import pandas as pd

import e6l_core as L

VERS = '/mnt/sda2/lichenchen/tmp/e6l_stage/versions'


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def main():
    sm = json.load(open(L.P('source_manifest.json'), encoding='utf-8'))
    base = {k: v[:16] for k, v in sm['e6l_code_sha256_at_stage0'].items()}
    notes_p = L.P('results', 'code_register', 'change_notes.json')
    notes = json.load(open(notes_p, encoding='utf-8')) if os.path.exists(notes_p) else {}
    log = [ln.strip().split(' ', 2) for ln in open(os.path.join(VERS, 'deploy_log.txt'), encoding='utf-8') if ln.strip()]
    od = L.P('results', 'code_register')
    os.makedirs(od, exist_ok=True)
    cur = {os.path.basename(p): sha16(open(p, 'rb').read()) for p in glob.glob(os.path.join(L.CODE, 'e6l_*'))}
    md = ['# E6l 代码变更登记（固定 §C；Stage 0 之后的 e6l_* 改动逐文件）', '',
          '用途：brief A10 / 附录 D-3。基线 = `source_manifest.json` 的 `e6l_code_sha256_at_stage0`（Stage 0 收口 13:4x，18 个文件）。每个版本由部署脚本另存'
          '（`tmp/e6l_stage/versions/`，研究临时目录）；相邻版本 unified diff 存 `results/code_register/`；反向还原 = 用 after 版本与差异逐字节重建 before 版本（difflib）。'
          '语义改动若影响已授权对象，须隔离后代并重新授权——本轮全部改动的影响面见"影响面"列。', '',
          '| 文件 | 基线 sha16 | 最终 sha16 | 版本数 | 版本链（sha16 @ 时刻） | 范围 / 触发 | 影响面 | 等价证据 | 反向还原 |', '|---|---|---|---|---|---|---|---|---|']
    rows = []
    for f in sorted(cur):
        chain = []
        seen = set()
        for h, fn, ts in [(x[0], x[1], x[2] if len(x) > 2 else '') for x in log]:
            if fn == f and h not in seen:
                chain.append((h, ts))
                seen.add(h)
        b0 = base.get(f)
        after_stage0 = [c for c in chain if c[1] >= '2026-09-30 13:4'] if b0 else chain
        if b0 == cur[f] and not [c for c in after_stage0 if c[0] != b0]:
            continue
        seq = ([(b0, 'Stage 0 基线')] if b0 else [('NEW', '新文件')]) + [c for c in after_stage0 if c[0] != b0]
        ok_all = True
        for (h1, _), (h2, t2) in zip(seq[:-1], seq[1:]):
            if h1 == 'NEW':
                continue
            p1 = os.path.join(VERS, '%s.%s' % (f, h1))
            p2 = os.path.join(VERS, '%s.%s' % (f, h2))
            if not (os.path.exists(p1) and os.path.exists(p2)):
                ok_all = False
                continue
            a = open(p1, 'rb').read().decode('utf-8').splitlines(keepends=True)
            b = open(p2, 'rb').read().decode('utf-8').splitlines(keepends=True)
            diff = ''.join(difflib.unified_diff(a, b, fromfile='%s@%s' % (f, h1), tofile='%s@%s' % (f, h2)))
            L.atomic_write_text(os.path.join(od, '%s.%s_to_%s.diff' % (f, h1, h2)), diff)
            restored = ''.join(difflib.restore(list(difflib.ndiff(a, b)), 1))
            ok_all &= sha16(restored.encode('utf-8')) == h1
        nt = notes.get(f, {})
        rows.append(dict(file=f, base=b0 or 'NEW', final=cur[f], versions=len(seq), chain=' → '.join('%s@%s' % (h[:8], t[11:19] if len(t) > 11 else t) for h, t in seq),
                         scope=nt.get('scope', 'SEE_WORKLOG'), impact=nt.get('impact', 'SEE_WORKLOG'), evidence=nt.get('evidence', 'SEE_WORKLOG'),
                         reverse_ok=ok_all))
        md.append('| %s | %s | %s | %d | %s | %s | %s | %s | %s |' % (f, (b0 or 'NEW'), cur[f], len(seq), rows[-1]['chain'], rows[-1]['scope'], rows[-1]['impact'],
                                                                   rows[-1]['evidence'], 'PASS' if ok_all else 'CHECK'))
    L.atomic_write_csv(os.path.join(od, 'code_change_register.csv'), pd.DataFrame(rows))
    md += ['', '- 未改动的基线文件（sha 与 Stage 0 相同）不列；四地基与 e6e–e6k 只读（`stage0/c1_identity_rerun/readonly_code_baseline.json` 与闭包门复核）。']
    p = L.P('reports', 'E6l_code_change_register.md')
    L.atomic_write_text(p, '\n'.join(md) + '\n')
    L.write_receipt(L.next_rerun('code_change_register'), [p, os.path.join(od, 'code_change_register.csv')], 'SUCCEEDED', files=len(rows))
    print(pd.DataFrame(rows)[['file', 'base', 'final', 'versions', 'reverse_ok']].to_string(), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
