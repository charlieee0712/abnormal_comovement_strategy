#!/bin/bash
# E6k 两后段链（授权后才启动）：条件回执 all_pass → 两后段队列（确定性 + 随机首轮）→ MC 增补（512 一批至 8,192）→ seal_post。
# 读数与报告另由执行端逐步运行（封存之后）。
set -u
cd /mnt/sda2/lichenchen/code/project_core
R=/mnt/sda2/lichenchen/results/20260928_2325_E6k_k_binding_stage
P=${1:-64}
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 e6k_record_b.py --conditions >> $R/logs/chain_post.log 2>&1 || { echo "CONDITIONS_FAIL $(date +%F_%T)" >> $R/logs/worker_done.txt; exit 2; }
python3 e6k_queue.py 2019-2023,2024-2026 $R/logs/queue_post.txt >> $R/logs/chain_post.log 2>&1
echo "POST_QUEUE_START $(date +%F_%T)" >> $R/logs/worker_done.txt
xargs -P $P -L 1 ./e6k_worker.sh < $R/logs/queue_post.txt
echo "QUEUE_DONE_POST $(date +%F_%T)" >> $R/logs/worker_done.txt
for round in $(seq 1 16); do
  for s in 2019-2023 2024-2026; do
    taskset -c 96-191,288-383 python3 e6k_stats.py --segment $s --phase post --mc-plan >> $R/logs/mc_plan_post.log 2>&1
  done
  python3 e6k_queue_topup.py post $R/logs/queue_topup_post_$round.txt >> $R/logs/mc_plan_post.log 2>&1
  n=$(grep -c . $R/logs/queue_topup_post_$round.txt)
  echo "$(date '+%F %T') MC post round $round: $n shards" >> $R/logs/worker_done.txt
  [ "$n" -eq 0 ] && break
  xargs -P $P -L 1 ./e6k_worker.sh < $R/logs/queue_topup_post_$round.txt
done
echo "MC_DONE_post $(date +%F_%T)" >> $R/logs/worker_done.txt
python3 e6k_seal.py --package post >> $R/logs/chain_post.log 2>&1 && echo "SEAL_POST_DONE $(date +%F_%T)" >> $R/logs/worker_done.txt
