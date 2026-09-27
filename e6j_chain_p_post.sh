#!/bin/sh
# E6j 执行端等待链（brief §14：并发 ≤ 24、BLAS ≤ 4、ulimit -u 4096、taskset 同队列文件）：
#  1) 诊断链（PID 348558）结束 → P 诊断补充四段（-P 4；与 P 随机 -P 20 合计 24）
#  2) P 随机队列（PID 341668）结束（B 随机链同刻以 -P 20 启动）→ 换入允许 MC 增补分片的 e6j_run_prand.py → 封存 P v1
#  3) MC 增补循环：e6j_mc_topup.py（只读 MCSE）→ 有增补则 -P 4 跑 → 再封存 → 再算，直到无增补（到 8,192 仍不足者列在回执里交用户）
# 任何一步失败即停（不跳过封存）；政策读数（e6j_policy_p.py）由执行端在本链结束后手动运行。
R=/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot
C=/mnt/sda2/lichenchen/code/project_core
L=$R/logs/chain_p_post.log
ulimit -u 4096
cd $C || exit 1
echo "start $(date '+%F %T') pid $$" >> $L
while kill -0 348558 2>/dev/null; do sleep 60; done
echo "diag chain gone $(date '+%F %T')" >> $L
xargs -P 4 -I{} sh -c "{}" < $R/logs/queue_diag_p_extra.txt
echo "diag_extra xargs exit $? $(date '+%F %T')" >> $L
while kill -0 341668 2>/dev/null; do sleep 60; done
echo "P rand queue gone $(date '+%F %T')" >> $L
if [ -f $C/e6j_run_prand.py.next ]; then mv $C/e6j_run_prand.py.next $C/e6j_run_prand.py; fi
sha256sum $C/e6j_run_prand.py >> $L
python3 -B e6j_seal.py --package P >> $L 2>&1 || { echo "seal P v1 not ok -> stop $(date '+%F %T')" >> $L; exit 2; }
i=0
while [ $i -lt 16 ]; do
  i=$((i+1))
  python3 -B e6j_mc_topup.py >> $L 2>&1 || { echo "mc_topup failed -> stop $(date '+%F %T')" >> $L; exit 3; }
  Q=$(ls -t $R/logs/queue_mc_topup_P_round*.txt | head -1)
  if [ ! -s "$Q" ]; then echo "no more topup ($Q) $(date '+%F %T')" >> $L; break; fi
  echo "topup $Q $(wc -l < $Q) shards start $(date '+%F %T')" >> $L
  xargs -P 4 -I{} sh -c "{}" < "$Q"
  python3 -B e6j_seal.py --package P >> $L 2>&1 || { echo "seal after $Q not ok -> stop $(date '+%F %T')" >> $L; exit 4; }
done
echo "chain done $(date '+%F %T')" >> $L
