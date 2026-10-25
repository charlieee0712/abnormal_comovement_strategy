# -*- coding: utf-8 -*-
"""E6o 合并工具：全局键唯一（plan 附录 B merge_unique 同义；同 exec_id 两份结果 → 报错，不覆盖、不取"最近"的那份）。"""


def merge_unique(shards):
    d = {}
    for shard in shards:
        for k, v in shard.items():
            if k in d:
                raise ValueError('merge collision: %s' % k)
            d[k] = v
    return d


def merge_frames(frames, key):
    import pandas as pd
    df = pd.concat(frames, ignore_index=True)
    dup = df[key].duplicated()
    if dup.any():
        raise ValueError('merge collision: %d 行重复键（例 %s）' % (int(dup.sum()), df.loc[dup, key].iloc[0]))
    return df
