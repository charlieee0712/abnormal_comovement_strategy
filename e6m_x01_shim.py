# -*- coding: utf-8 -*-
"""X01（E6 宽扫描 roles.csv）文本重建垫片。用于诊断，也是待用户授权的"云机阶段 S 备选"件。
- 不改任何源模块，不写 results/。
- e6e_core 在 import 期执行 `pd.read_csv(<E6 宽扫描目录>/roles.csv)`，只用 factor 与 worst_pooled 两列（HB = worst_pooled == 5）。
- 原件存在：垫片不介入，只记 original_present = True。
- 原件不在：这一次读取改读工作目录里的文本重建表 registry/x01_roles_text_reconstructed.csv。
  来源 = E6 REPORT §(B) 用 roles.to_string() 印出的同一张表（e6_wide_scan.py:225 写 csv、:256 印表）。
- 用法：在 import 任何账户侧模块之前 install(path)；import 完成后 uninstall()。"""
import os

import pandas as pd

TARGET_TAIL = os.path.join('20260904_1051_E6_wide_scan', 'roles.csv')
STATE = dict(installed=False, redirected=0, original_present=None, recon_path='')
_orig = [None]


def install(recon_path):
    if _orig[0] is not None:
        return
    _orig[0] = pd.read_csv
    STATE.update(installed=True, recon_path=recon_path)

    def patched(path, *a, **k):
        p = str(path)
        if p.endswith(TARGET_TAIL):
            if os.path.exists(p):
                STATE['original_present'] = True
                return _orig[0](path, *a, **k)
            STATE['original_present'] = False
            STATE['redirected'] += 1
            return _orig[0](recon_path, *a, **k)
        return _orig[0](path, *a, **k)
    pd.read_csv = patched


def uninstall():
    if _orig[0] is not None:
        pd.read_csv = _orig[0]
        _orig[0] = None
