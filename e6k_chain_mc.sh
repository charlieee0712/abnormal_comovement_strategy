#!/bin/bash
# E6k MC 增补链（执行端补充 X15）：等首轮队列 QUEUE_DONE → 逐轮 MC 规划（只读随机路径离散度）→ 512 一批增补 → 直到全部组 ≤ .03 或 8,192 上限。
# 用法：e6k_chain_mc.sh <阶段 deriv|post> <段1,段2> <并发>
set -u
cd /mnt/sda2/lichenchen/code/project_core
R=/mnt/sda2/lichenchen/results/20260928_2325_E6k_k_binding_stage
phase=$1; segs=$2; P=$3
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
until grep -q "QUEUE_DONE" $R/logs/worker_done.txt; do sleep 30; done
for round in $(seq 1 16); do
  for s in $(echo $segs | tr ',' ' '); do
    taskset -c 96-191,288-383 python3 e6k_stats.py --segment $s --phase $phase --mc-plan >> $R/logs/mc_plan_$phase.log 2>&1
  done
  python3 e6k_queue_topup.py $phase $R/logs/queue_topup_${phase}_$round.txt >> $R/logs/mc_plan_$phase.log 2>&1
  n=$(grep -c . $R/logs/queue_topup_${phase}_$round.txt)
  echo "$(date '+%F %T') MC round $round: $n shards" >> $R/logs/worker_done.txt
  [ "$n" -eq 0 ] && break
  xargs -P $P -L 1 ./e6k_worker.sh < $R/logs/queue_topup_${phase}_$round.txt
done
echo "MC_DONE_$phase $(date +%F_%T)" >> $R/logs/worker_done.txt
