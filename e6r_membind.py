# -*- coding: utf-8 -*-
"""E6r 调度辅助（只管内存放置，不改任何计算）：给本进程设 MPOL_BIND{E6R_MEMBIND_NODES，缺省 0,1} 内存策略，再 exec 目标命令。
用法：python3 e6r_membind.py python3 e6r_run.py randoms ...（策略随 exec 与 fork 继承到池内全部 worker）。
原因：47 的 3.10 内核开着 NUMA 自动均衡；fork 池跨两路运行时，父子共享页被反复迁移（10-25 实测每秒约 1.1 万页迁移、
worker 约 31% 时间卡在页锁），176 进程反而比单路 96 进程慢。MPOL_BIND 不带 MOF 标志，内核不对这些进程做均衡迁移；
nodemask 含全部节点时分配仍按本地节点优先。随机种子与计算路径不变，结果逐位相同。"""
import ctypes
import os
import sys

MPOL_BIND = 2
SYS_SET_MEMPOLICY = 238  # x86_64

nodes = [int(x) for x in os.environ.get('E6R_MEMBIND_NODES', '0,1').split(',')]
mask = ctypes.c_ulong(sum(1 << n for n in nodes))
libc = ctypes.CDLL(None, use_errno=True)
if libc.syscall(SYS_SET_MEMPOLICY, MPOL_BIND, ctypes.byref(mask), ctypes.c_ulong(64)) != 0:
    sys.stderr.write('e6r_membind: set_mempolicy 失败 errno=%d\n' % ctypes.get_errno())
    sys.exit(97)
os.execvp(sys.argv[1], sys.argv[1:])
