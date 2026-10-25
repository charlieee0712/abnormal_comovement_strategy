#!/bin/bash
# E6r A2 → B 衔接（47 端）：等 A2 链完成标记（A2.complete），依次：第一道终跑（g1，GW07 别名）→ 正式 S0-L 空跑链（DRYF；门只记录不阻断）→ s0l（stage0 part3）
# → seal_A2 → 启动 B 链。任一步失败 → 不写 seal、不启动任何后段，退出 1。用法：setsid nohup bash e6r_after_a2.sh > $W/logs/after_a2.log 2>&1 &
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261024_1250_E6r_entry_quality_roles" && pwd)
M=$W/task_status/chain
while true; do
  if ls $M/A2_*.failed > /dev/null 2>&1; then echo "[$(date '+%F %T')] A2 链有失败标记，不继续"; exit 1; fi
  if [ -f $M/A2.complete ]; then break; fi
  sleep 30
done
echo "[$(date '+%F %T')] A2 链完成：第一道终跑 + 正式空跑"
cd "$C"
bash e6r_chain.sh G1F e6r_g1.py || { echo "g1 失败"; exit 1; }
rm -rf $W/tmp/dryrun_debug && [ -d $W/tmp/dryrun ] && mv $W/tmp/dryrun $W/tmp/dryrun_debug
bash e6r_chain.sh DRYF e6r_dryrun.py:prep e6r_stats.py:--phase:A2:--fake_post:--dry_extras:--root:tmp/dryrun:--workers:64 e6r_policy.py:--root:tmp/dryrun \
  e6r_diag.py:--phase:A2:--root:tmp/dryrun e6r_claims.py:--root:tmp/dryrun e6r_reports.py:--root:tmp/dryrun e6r_closure.py:identities:--root:tmp/dryrun \
  e6r_closure.py:stage0:--root:tmp/dryrun e6r_closure.py:deploy_log:--root:tmp/dryrun e6r_notes.py:--root:tmp/dryrun e6r_closure.py:schema:--root:tmp/dryrun \
  e6r_dryrun.py:dscript e6r_closure.py:gates_dry:--root:tmp/dryrun e6r_dryrun.py:s0l || { echo "空跑链失败（交付链断）：不写 seal"; exit 1; }
bash e6r_chain.sh SEAL e6r_closure.py:seal_A2 || { echo "seal_A2 失败"; exit 1; }
echo "[$(date '+%F %T')] seal_A2 已写：启动 B 链"
bash e6r_chain.sh B e6r_run.py:accounts:--phase:B:--workers:96 e6r_run.py:feedback:--phase:B:--workers:96 e6r_run.py:shadow:--phase:B:--workers:96 \
  e6r_run.py:randoms:--phase:B:--workers:96:--batch:8 e6r_run.py:topup:--phase:B:--workers:96:--batch:8 e6r_stats.py:--phase:B:--workers:64 e6r_policy.py \
  e6r_diag.py:--phase:B e6r_claims.py e6r_reports.py e6r_closure.py:identities e6r_closure.py:stage0 e6r_closure.py:deploy_log e6r_closure.py:schema \
  e6r_closure.py:seal_final e6r_closure.py:gates
echo "[$(date '+%F %T')] B 链结束 rc=$?"
