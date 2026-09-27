# -*- coding: utf-8 -*-
"""E6j：B 测时分片（randoms/B/2010-2014/R2__B3C__p0_32.npz，较早存储版本）与最终代码重算（randoms/B_test/2010-2014/R2__B3C__p0_32.npz）逐值比对。
比对 desc / mechs / years 相同，ann（逐路径 × 描述符年化 net8 / gross / turn）与 yearly 逐值差；新文件另带逐路径指纹，供 STREAMED_REPLAYABLE 引用。
推导段文件，不涉封存。写 checks/b_test_shard_validation.csv。"""
import e6j_boot  # noqa: F401
import os
import sys

import numpy as np
import pandas as pd

import e6j_core as J


def main():
    old = np.load(os.path.join(J.RES, 'randoms', 'B', '2010-2014', 'R2__B3C__p0_32.npz'), allow_pickle=False)
    new = np.load(os.path.join(J.RES, 'randoms', 'B_test', '2010-2014', 'R2__B3C__p0_32.npz'), allow_pickle=False)
    rows = []
    for k in ('desc', 'mechs', 'years'):
        rows.append(dict(item=k, status='PASS' if np.array_equal(old[k], new[k]) else 'FAIL', detail='逐元素相同' if np.array_equal(old[k], new[k]) else 'differ'))
    for k in ('ann', 'yearly'):
        a, b = old[k].astype(float), new[k].astype(float)
        same_nan = bool(np.array_equal(np.isnan(a), np.isnan(b)))
        mx = float(np.nanmax(np.abs(a - b))) if a.shape == b.shape else np.inf
        rows.append(dict(item=k, status='PASS' if (a.shape == b.shape and same_nan and mx == 0.0) else 'FAIL',
                         detail='shape %s / %s；NaN 位置相同 %s；最大绝对差 %.3g' % (a.shape, b.shape, same_nan, mx)))
    rows.append(dict(item='new_fields', status='INFO', detail='新文件字段：%s' % ','.join(new.files)))
    df = pd.DataFrame(rows)
    p = os.path.join(J.RES, 'checks', 'b_test_shard_validation.csv'); J.atomic_write_csv(p, df)
    ok = bool((df.status != 'FAIL').all())
    J.write_receipt('check_b_test_shard', [p], 'SUCCEEDED' if ok else 'FAILED', all_pass=ok)
    print(df.to_string())
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
