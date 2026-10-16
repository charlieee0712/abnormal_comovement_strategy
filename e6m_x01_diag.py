# -*- coding: utf-8 -*-
"""诊断（不产生任何研究结果、不读收益）：X01 文本重建垫片下，账户侧模块能否 import，import 期还读哪些文件。
1. 从 E6 REPORT 的印表文本解析 roles 表 → registry/x01_roles_text_reconstructed.csv（另存来源 sha 与行号）；
2. 装垫片，审计钩子（sys.addaudithook 'open'）记录 import 期全部打开的文件；逐个 import 账户侧模块；
3. 核 e6e_core.HB 七因子 = 文本表 worst_pooled == 5；
4. 写 stageN/x01_diag/x01_import_closure.csv / .json 与回执。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse
import importlib

import pandas as pd

import e6m_core as M
import e6m_x01_shim as SH

OPENS = []


def hook(event, args):
    if event == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        p = os.fsdecode(args[0])
        if p.endswith('.py') or p.endswith('.pyc') or '/__pycache__/' in p or p.startswith('/proc') or p.startswith('/dev'):
            return
        if '/site-packages/' in p or '/lib/python3' in p or p.endswith('.so'):
            return
        OPENS.append((CUR[0], p))


CUR = ['']


def parse_report(text_path):
    lines = open(text_path, encoding='utf-8').read().split('\n')
    i0 = next(i for i, l in enumerate(lines) if l.strip().startswith('factor') and 'worst_pooled' in l)
    head = lines[i0].split()
    rows = []
    j = i0 + 1
    while j < len(lines) and lines[j].strip() and not lines[j].startswith('=='):
        parts = lines[j].split()
        if len(parts) != len(head):
            raise RuntimeError('印表行列数不符：第 %d 行' % (j + 1))
        rows.append(parts)
        j += 1
    df = pd.DataFrame(rows, columns=head)
    for c in ('rho_mean', 'tail_share'):
        df[c] = df[c].astype(float)
    df['worst_pooled'] = df['worst_pooled'].astype(int)
    return df, (i0 + 1, j)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--report', required=True, help='E6 REPORT 文本（含 §(B) 印表）')
    a = ap.parse_args()
    t0 = time.time()
    outd = M.P('stageN', 'x01_diag')
    os.makedirs(outd, exist_ok=True)
    df, (l0, l1) = parse_report(a.report)
    recon = M.P('registry', 'x01_roles_text_reconstructed.csv')
    M.atomic_write_csv(recon, df)
    prov = dict(source_text_sha256=M.sha_file(a.report), source_lines='%d-%d' % (l0, l1), rows=len(df),
                consumed_columns=['factor', 'worst_pooled'], recon_sha256=M.sha_file(recon),
                status='TEXT_RECONSTRUCTED_ANCHOR_PENDING', note='原件到达后按 factor 逐行对 worst_pooled（e6e_core 只用这两列）')
    M.atomic_write_json(M.P('registry', 'x01_roles_text_reconstructed.provenance.json'), prov)
    SH.install(recon)
    sys.addaudithook(hook)
    mods = ['e6e_core', 'e6f_core', 'e6g_core', 'e6i_core', 'e6i_ops', 'e6i_randoms', 'e6i_features', 'e6j_engine', 'e6j_fast',
            'e6k_env', 'e6k_ops', 'e6k_acct', 'e6k_random', 'e6l_state', 'e6l_ops', 'e6l_acct']
    res = []
    for m in mods:
        CUR[0] = m
        if not os.path.exists(os.path.join(M.CODE, m + '.py')):
            res.append(dict(module=m, status='NOT_PRESENT', error=''))
            continue
        try:
            importlib.import_module(m)
            res.append(dict(module=m, status='IMPORTED', error=''))
        except Exception as e:                              # noqa: BLE001
            res.append(dict(module=m, status='IMPORT_FAILED', error=M.san('%s: %s' % (type(e).__name__, e))[:300]))
    SH.uninstall()
    K = sys.modules.get('e6e_core')
    hb = {}
    if K is not None:
        want = {r.factor: int(r.worst_pooled) == 5 for r in df.itertuples()}
        hb = {f: dict(hb=bool(K.HB[f]), text=want.get(f)) for f in K.FACTORS}
    rd = pd.DataFrame(res)
    od = pd.DataFrame([dict(module=m, path=M.san(p)) for m, p in OPENS]).drop_duplicates() if OPENS else pd.DataFrame(columns=['module', 'path'])
    M.atomic_write_csv(os.path.join(outd, 'x01_import_closure.csv'), rd)
    M.atomic_write_csv(os.path.join(outd, 'x01_import_opens.csv'), od)
    out = dict(shim=dict(SH.STATE, recon_path=M.san(SH.STATE['recon_path'])), modules=res, hb_vs_text=hb,
               hb_all_match=bool(hb) and all(v['hb'] == v['text'] for v in hb.values()), opens=len(od), wall_s=round(time.time() - t0, 1),
               note='诊断：不产生研究结果、不读收益；垫片只改这一次 roles.csv 读取')
    M.atomic_write_json(os.path.join(outd, 'x01_import_closure.json'), out)
    M.write_receipt(os.environ.get('E6M_TASK', 'N9_x01_diag'), [recon, os.path.join(outd, 'x01_import_closure.csv'), os.path.join(outd, 'x01_import_opens.csv'),
                                                                os.path.join(outd, 'x01_import_closure.json')],
                    status='SUCCEEDED', code=[__file__, SH.__file__, M.__file__], inputs=[a.report])
    print(rd.to_string(index=False))
    print(json.dumps(dict(shim=out['shim'], hb_all_match=out['hb_all_match'], hb=hb), ensure_ascii=False))
    print(od.to_string(index=False) if len(od) else 'import 期无数据文件打开（垫片重定向之外）')
    return 0


if __name__ == '__main__':
    sys.exit(main())
