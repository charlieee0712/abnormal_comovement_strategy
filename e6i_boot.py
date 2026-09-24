# -*- coding: utf-8 -*-
"""E6i 进程启动钩子 —— 必须是入口脚本的第一个 import (在 numpy / pandas / pyarrow 之前)。

pyarrow 13 在 `import pyarrow.fs` 时无条件 ensure_s3_initialized(), AWS SDK 的事件循环组
按物理核数起 192 个 AwsEventLoop 线程 (与 taskset 亲和性无关; initialize_s3 的
num_event_loop_threads 参数在 13.0.0 不生效)。这就是 E6g/E6h 登记为 I7 "来源未查明"的
~205 线程/进程。本项目从不用 S3: 预先把 pyarrow._s3fs 置 None, pyarrow.fs 走它自己的
ImportError 分支 (S3FileSystem 记为未导入), parquet 读取照常 —— 实测 205 -> 13 线程/进程。
另把 BLAS / OMP 线程上限设为 4 (brief §2 并发条)。
"""
import os
import sys

sys.modules.setdefault('pyarrow._s3fs', None)
for _k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_MAX_THREADS'):
    os.environ.setdefault(_k, '4')
