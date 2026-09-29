#!/bin/bash
# E6k 队列工作者（xargs -L 1 调用）：det <段> <母体|测量> | rand <段> <母体|测量> <机制> <起始路径> <路径数>
# 每任务独立日志；结束写 worker_done.txt（rc 记录；FAILED 由回执与 _rerun 规则处理）。只用 node1 核（taskset），BLAS 单线程。
set -u
cd /mnt/sda2/lichenchen/code/project_core
R=/mnt/sda2/lichenchen/results/20260928_2325_E6k_k_binding_stage
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 POLARS_MAX_THREADS=1 NUMBA_NUM_THREADS=1
kind=$1; seg=$2; task=$3
tag=$(echo "$*" | tr ' |' '__')
log=$R/logs/w/$tag.log
mkdir -p $R/logs/w
if [ "$kind" = det ]; then
  taskset -c 96-191,288-383 python3 e6k_run_det.py --segment "$seg" --task "$task" > "$log" 2>&1
else
  taskset -c 96-191,288-383 python3 e6k_run_rand.py --segment "$seg" --task "$task" --mech "$4" --path0 "$5" --npaths "$6" > "$log" 2>&1
fi
rc=$?
echo "$(date '+%F %T') rc=$rc $*" >> $R/logs/worker_done.txt
exit 0
