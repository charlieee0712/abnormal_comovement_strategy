#!/bin/bash
# E6k 两后段续链（2026-09-29：RP 恢复路径部署、原链脚本停止后）：等首轮 xargs（显式 PID）结束 → 按回执补跑未成功的队列行（最多 3 轮）→
# MC 增补（规划前核队列完整；512 一批至 8,192）→ seal_post（核队列每行回执）→ X04 后段补算（A1-auto 掩码事实）→ 分析链 full。
# 用法：e6k_chain_post2.sh <首轮 xargs PID> [并发]
set -u
cd /mnt/sda2/lichenchen/code/project_core
R=/mnt/sda2/lichenchen/results/20260928_2325_E6k_k_binding_stage
XPID=$1
P=${2:-64}
W=$R/logs/worker_done.txt
L=$R/logs/chain_post2.log
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
while kill -0 "$XPID" 2>/dev/null; do sleep 30; done
echo "QUEUE_DONE_POST $(date +%F_%T)" >> $W
for round in 1 2 3; do
  python3 e6k_queue_failed.py post $R/logs/queue_rerun_post_$round.txt >> $L 2>&1
  n=$(grep -c . $R/logs/queue_rerun_post_$round.txt)
  echo "$(date '+%F %T') RERUN post round $round: $n lines" >> $W
  [ "$n" -eq 0 ] && break
  xargs -P $P -L 1 ./e6k_worker.sh < $R/logs/queue_rerun_post_$round.txt
done
n=$(python3 e6k_queue_failed.py post $R/logs/queue_rerun_post_check.txt 2>>$L | awk '{print $1}')
if [ "$n" != "0" ]; then echo "RERUN_INCOMPLETE $(date +%F_%T) $n" >> $W; exit 2; fi
for round in $(seq 1 16); do
  for s in 2019-2023 2024-2026; do
    taskset -c 96-191,288-383 python3 e6k_stats.py --segment $s --phase post --mc-plan >> $R/logs/mc_plan_post.log 2>&1 || { echo "MC_PLAN_FAIL $(date +%F_%T) $s" >> $W; exit 2; }
  done
  python3 e6k_queue_topup.py post $R/logs/queue_topup_post_$round.txt >> $R/logs/mc_plan_post.log 2>&1
  n=$(grep -c . $R/logs/queue_topup_post_$round.txt)
  echo "$(date '+%F %T') MC post round $round: $n shards" >> $W
  [ "$n" -eq 0 ] && break
  xargs -P $P -L 1 ./e6k_worker.sh < $R/logs/queue_topup_post_$round.txt
done
echo "MC_DONE_post $(date +%F_%T)" >> $W
python3 e6k_seal.py --package post >> $L 2>&1 || { echo "SEAL_POST_FAIL $(date +%F_%T)" >> $W; exit 2; }
echo "SEAL_POST_DONE $(date +%F_%T)" >> $W
taskset -c 96-191,288-383 python3 e6k_a1_auto.py --masks-post >> $L 2>&1 || echo "A1_MASKS_POST_FAIL $(date +%F_%T)" >> $W
./e6k_chain_analysis.sh full
echo "CHAIN_POST2_DONE $(date +%F_%T)" >> $W
