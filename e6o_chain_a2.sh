#!/bin/bash
# E6o A2 链（推导段；不写任何后段数据）：账户（重跑，引擎 v2）→ 手工逐日账核对 → 影子风险集 → 随机 / 水平控制（全部预登记机制，128 路径）→ G1。
set -u
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261017_2138_E6o_account_exit_stage" && pwd)
export E6O_WORK=$W OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$W/tmp/numba_cache
cd "$C"
PIN="taskset -c 96-191,288-383"
[ -f $W/task_status/accounts_A2.csv ] && mv $W/task_status/accounts_A2.csv $W/task_status/accounts_A2_superseded_$(date +%H%M%S).csv
$PIN python3 e6o_run.py accounts --phase A2 --workers 64 > $W/logs/accounts_A2r4.log 2>&1 || { echo "accounts A2 FAILED"; exit 1; }
$PIN python3 e6o_refcheck.py > $W/logs/refcheck.log 2>&1 || { echo "refcheck FAILED"; exit 1; }
$PIN python3 e6o_run.py shadow --phase A2 --workers 12 > $W/logs/shadow_A2.log 2>&1 || { echo "shadow A2 FAILED"; exit 1; }
$PIN python3 e6o_run.py randoms --phase A2 --workers 96 --batch 16 > $W/logs/randoms_A2.log 2>&1 || { echo "randoms A2 FAILED"; exit 1; }
$PIN python3 e6o_g1.py > $W/logs/g1.log 2>&1 || { echo "G1 FAILED"; exit 1; }
echo "chain_a2 done $(date '+%F %T')"
