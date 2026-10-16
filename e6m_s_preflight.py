# -*- coding: utf-8 -*-
"""E6m 阶段 S 开跑前检查（只读源码 / 登记文件，不读收益；runbook all 第一步，s2 冻结前单查 ⑬b）：
  ext   外部输入 X01–X22 / X27 全在（e6m_stage0_S.EXT 路径模式，{seg} 按四段展开）；
  13b   ⑬b 决策端文件齐全（与 e6m_s_a1auto.item13b 同判据）——必须在 Stage B 冻结前到：冻结只写一次，冻结后补写进不了卡片 t09，
        重跑 A1-auto 又会改动冻结清单已记 sha 的文件；
  mode  方式 B 决定文件在（registration/authorization_status_E6m_S.json，w11_mode = B）。
--only 选一项；缺省三项全查。任一项不过即退出码 1，并逐项说明。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json
import argparse

import e6m_core as M
import e6m_stage0_S as S0


def ext_missing():
    root = S0.default_root()
    miss = []
    for k, items in S0.EXT.items():
        for rr, pat, _ in items:
            pats = [pat.replace('{seg}', s) for s in M.SEGMENTS] if '{seg}' in pat else [pat]
            if any(not glob.glob(os.path.join(root, S0.RN[rr], p)) for p in pats):
                miss.append(k)
                break
    return miss


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='all', choices=['all', 'ext', '13b', 'mode'])
    a = ap.parse_args()
    ok = True
    if a.only in ('all', 'ext'):
        miss = ext_missing()
        print('外部输入：%d / %d 在%s' % (len(S0.EXT) - len(miss), len(S0.EXT), '' if not miss else '；缺 ' + ', '.join(miss)))
        ok &= not miss
    if a.only in ('all', '13b'):
        import e6m_s_a1auto as A1
        st, det = A1.item13b()
        print('⑬b 决策端文件：%s（%s）' % (st, det))
        ok &= st == 'PASS'
    if a.only in ('all', 'mode'):
        p = M.P('registration', 'authorization_status_E6m_S.json')
        mode = json.load(open(p, encoding='utf-8')).get('w11_mode') if os.path.exists(p) else None
        print('记录 B 方式：%s' % (mode or '阶段 S 决定文件缺（方式 A 走 s1 → s3 再停等，不用 all）'))
        ok &= mode == 'B'
    print('preflight（%s）：%s' % (a.only, 'PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
