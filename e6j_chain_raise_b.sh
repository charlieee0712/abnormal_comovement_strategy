#!/bin/sh
# E6j：用户 2026-09-27 同意并发放宽到 64。P 随机队列（341668）结束后，B 随机链（354272）以 -P 20 启动其 xargs；
# 本脚本找到该 xargs（按父 PID + 进程名，不按命令行匹配）并发 40 次 SIGUSR1 → 60（MC 增补另占 ≤ 4，合计 ≤ 64）。
R=/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot
L=$R/logs/chain_raise_b.log
echo "start $(date '+%F %T') pid $$" >> $L
while kill -0 341668 2>/dev/null; do sleep 30; done
X=""
for i in $(seq 1 120); do
  X=$(pgrep -P 354272 -x xargs)
  [ -n "$X" ] && break
  sleep 5
done
if [ -z "$X" ]; then echo "B xargs not found -> stop $(date '+%F %T')" >> $L; exit 1; fi
echo "B xargs pid $X $(ps -o lstart= -p $X) $(ps -o cmd= -p $X | cut -c1-60)" >> $L
for i in $(seq 1 40); do kill -USR1 $X; sleep 0.5; done
sleep 30
echo "raised: children $(pgrep -P $X | wc -l) $(date '+%F %T')" >> $L
