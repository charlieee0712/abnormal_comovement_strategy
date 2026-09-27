#!/bin/sh
# E6j：空槽时用最终代码重算 B 测时分片（2010-2014 R2 B3C 路径 0–31）到 randoms/B_test，并与原分片逐值比对（约 2 分钟、1 个进程）。
# 空槽 = 等待链的 P 诊断补充结束之后；若那时 P 随机已结束（增补占 4 槽），等增补链结束再跑。
R=/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot
C=/mnt/sda2/lichenchen/code/project_core
L=$R/logs/chain_p_post.log
ulimit -u 4096
cd $C || exit 1
while ! grep -q "diag_extra xargs exit" $L 2>/dev/null; do sleep 60; done
if ! kill -0 341668 2>/dev/null; then
  while ! grep -qE "chain done|-> stop" $L; do sleep 60; done
fi
echo "b_test start $(date '+%F %T')" >> $R/logs/chain_b_test.log
taskset -c 96-191,288-383 python3 -u -B e6j_run_brand.py --segment 2010-2014 --mother R2 --block B3C --path0 0 --paths 32 --test > $R/logs/run_brand_test_2010-2014_R2_B3C_p0.stdout 2>&1
echo "b_test run exit $? $(date '+%F %T')" >> $R/logs/chain_b_test.log
taskset -c 96-191,288-383 python3 -B e6j_check_b_test_shard.py >> $R/logs/chain_b_test.log 2>&1
echo "b_test check exit $? $(date '+%F %T')" >> $R/logs/chain_b_test.log
