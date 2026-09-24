#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 3 首次观察封存回执 (brief §7 / §8; plan Stage 3 "两段封存 receipt"):
两后段 (2019-2023 / 2024-2026) 按同一 manifest 全部算完后、任何后段统计 / 报告读取之前运行:
逐文件记 sha256 / 字节 / 行数 (后段账户、M1 / M2、Z-MAP、换入换出、vs H5、状态表), 并核对:
  * 记录 B 批准文件与冻结 manifest 的 sha 与批准时一致;
  * stage3 状态表: 两后段每路线 SUCCEEDED + NOT_APPLICABLE + FAILED_TECH = A0 登记数 (M1 / M2 另列);
写 registry/first_look_receipts.json (+ .md) 与 task_status/first_look.receipt.json。回执之后才允许读后段结果。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import hashlib

import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def main():
    t0 = time.time()
    appr_p = I.APPROVAL_FILE
    appr = json.load(open(appr_p))
    man_p = os.path.join(I.RES, 'registry', 'record_B_candidate_manifest.json')
    man_ok = sha(man_p) == appr['manifest_sha256']
    st_p = os.path.join(I.RES, 'registry', 'stage3_status_table.csv')
    st = pd.read_csv(st_p)
    main_st = st[~st.route.isin(['M1', 'M2'])]
    status_ok = bool(((main_st.succeeded + main_st.not_applicable + main_st.failed_tech) == main_st.a0_count).all())
    segs_ok = sorted(st.segment.unique()) == sorted(I.POST_SEGS)
    files = []
    pats = []
    for seg in I.POST_SEGS:
        pats += [os.path.join(I.RES, 'accounts', seg, '*'), os.path.join(I.RES, 'randoms', seg, '*'),
                 os.path.join(I.RES, 'm2', seg, '*.csv'), os.path.join(I.RES, 'm2', seg, 'calendar.npy'),
                 os.path.join(I.RES, 'statistics', 'zmap_summary_%s.csv' % seg),
                 os.path.join(I.RES, 'statistics', 'vs_prodH5_%s.csv' % seg),
                 os.path.join(I.RES, 'statistics', 'swap_in_out_%s_*.csv' % seg)]
    pats += [os.path.join(I.RES, 'statistics', 'vs_prodH5_post_full.csv'),
             os.path.join(I.RES, 'statistics', 'vs_prodH5_all4.csv'), st_p]
    for pat in pats:
        for p in sorted(glob.glob(pat)):
            if os.path.isdir(p) or os.path.basename(p).startswith('.tmp_'):
                continue
            rec = dict(path=os.path.relpath(p, I.RES), bytes=os.path.getsize(p), sha256=sha(p))
            if p.endswith('.csv'):
                rec['rows'] = int(sum(1 for _ in open(p, 'rb')) - 1)
            files.append(rec)
    out = dict(stage='stage3_first_look', written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               approval_id=appr['approval_id'], approval_sha256=sha(appr_p), manifest_sha256=appr['manifest_sha256'],
               manifest_unchanged=man_ok, status_table_sums_ok=status_ok, segments_ok=segs_ok,
               status_totals=main_st.groupby('segment')[['a0_count', 'succeeded', 'not_applicable',
                                                         'failed_tech']].sum().reset_index().to_dict('records'),
               extra_routes=st[st.route.isin(['M1', 'M2'])].to_dict('records'),
               n_files=len(files), total_bytes=int(sum(f['bytes'] for f in files)), files=files,
               rule='两后段同一 manifest 全部计算后封存; 本回执之前不读任何后段结果; 不看 2019-23 后改 2024-26')
    if not (man_ok and status_ok and segs_ok):
        out['status'] = 'FAILED_CHECK'
        I.atomic_write_json(os.path.join(I.RES, 'registry', 'first_look_receipts.json'), out)
        raise SystemExit('首次观察回执核对失败: manifest=%s 状态和=%s 段=%s' % (man_ok, status_ok, segs_ok))
    out['status'] = 'SEALED'
    p = os.path.join(I.RES, 'registry', 'first_look_receipts.json')
    I.atomic_write_json(p, out)
    md = ['# E6i Stage 3 首次观察回执（%s）\n' % out['written_at'],
          '- 记录 B：`%s`（批准文件 sha `%s…`；冻结 manifest sha `%s…`，未变：%s）'
          % (appr['approval_id'], out['approval_sha256'][:12], appr['manifest_sha256'][:12], man_ok),
          '- 状态表（stage3）逐路线状态和 = A0 登记数：%s；两后段：%s' % (status_ok, ' / '.join(I.POST_SEGS)),
          '- 封存文件 %d 个，合计 %.1f MB（逐文件 sha256 见 json）' % (len(files), out['total_bytes'] / 1e6),
          '- 规则：%s\n' % out['rule']]
    open(os.path.join(I.RES, 'registry', 'first_look_receipts.md'), 'w', encoding='utf-8').write('\n'.join(md))
    I.write_receipt(os.path.join(I.RES, 'task_status', 'first_look.receipt.json'), 'stage3:first_look', [p],
                    n_files=len(files), elapsed_s=round(time.time() - t0, 1))
    print('首次观察回执: %d 文件 %.1f MB; manifest 未变 %s; 状态和 %s; %.0fs' % (
        len(files), out['total_bytes'] / 1e6, man_ok, status_ok, time.time() - t0))


if __name__ == '__main__':
    main()
