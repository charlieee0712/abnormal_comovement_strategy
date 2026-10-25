#!/bin/bash
# E6q A2 → B 衔接（47 端）：等 A2 链的 g1（seal_A2）完成标记出现且 seal_A2.json 存在，再启动 B 链与假数据空跑链（两链并行，核心名单同 e6q_chain.sh）。
# A2 链任一步失败 → 不启动任何后段写入，退出 1。用法：setsid nohup bash e6q_after_a2.sh > $W/logs/after_a2.log 2>&1 &
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261023_0040_E6q_sell_reinvest_split" && pwd)
M=$W/task_status/chain
while true; do
  if ls $M/*.failed > /dev/null 2>&1; then
    echo "[$(date '+%F %T')] A2 链有失败标记，不启动 B" ; exit 1
  fi
  if ls $M/*_e6q_g1.py.done > /dev/null 2>&1 && [ -f $W/registration/seal_A2.json ]; then break; fi
  sleep 20
done
echo "[$(date '+%F %T')] seal_A2 已在：启动 B 链与空跑链"
cd "$C"
setsid nohup bash e6q_chain.sh \
  e6q_run.py:accounts:--phase:B:--workers:96 e6q_run.py:feedback:--phase:B:--workers:96 e6q_run.py:warm:--phase:B:--workers:96 \
  e6q_run.py:shadow:--phase:B:--workers:96 e6q_run.py:randoms:--phase:B:--workers:96 e6q_run.py:topup:--phase:B:--workers:96 \
  e6q_stats.py:--phase:B:--workers:96 e6q_policy.py e6q_diag.py:--phase:B:--workers:96 e6q_claims.py:--phase:B e6q_reports.py \
  e6q_closure.py:identities e6q_closure.py:stage0 e6q_closure.py:deploy_log e6q_notes.py e6q_closure.py:schema e6q_closure.py:seal_final \
  e6q_closure.py:gates > $W/logs/chain_B_launcher.log 2>&1 < /dev/null &
sleep 5
setsid nohup bash e6q_chain.sh \
  e6q_dryrun.py:prep e6q_stats.py:--phase:A2:--fake_post:--dry_extras:--root:tmp/dryrun:--workers:48 e6q_policy.py:--root:tmp/dryrun \
  e6q_diag.py:--phase:A2:--root:tmp/dryrun:--workers:48 e6q_claims.py:--phase:A2:--root:tmp/dryrun e6q_reports.py:--root:tmp/dryrun \
  e6q_closure.py:identities:--root:tmp/dryrun e6q_closure.py:stage0:--root:tmp/dryrun e6q_closure.py:deploy_log:--root:tmp/dryrun \
  e6q_notes.py:--root:tmp/dryrun e6q_closure.py:schema:--root:tmp/dryrun e6q_dryrun.py:dscript e6q_closure.py:gates:--root:tmp/dryrun \
  > $W/logs/chain_dry_launcher.log 2>&1 < /dev/null &
echo "[$(date '+%F %T')] 两链已启动"
