#!/bin/bash
# E6q B → 交付衔接（47 端）：等 B 链最后一步（closure gates，第 18 步）通过，再串行跑 handoff（交接目录 + 全件扫描 + 决策端脚本）→ gates_post → 同步包。
# B 链任一步失败（链目录出现 .failed）→ 退出 1，不建交接目录。用法：(setsid nohup bash e6q_after_b.sh > $W/logs/after_b.log 2>&1 < /dev/null &)
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261023_0040_E6q_sell_reinvest_split" && pwd)
M=$W/task_status/chain
while true; do
  if ls $M/*.failed > /dev/null 2>&1; then
    echo "[$(date '+%F %T')] 链目录有失败标记，不建交接目录"; ls $M/*.failed; exit 1
  fi
  if [ -f $M/18_e6q_closure.py_gates.done ]; then break; fi
  sleep 60
done
echo "[$(date '+%F %T')] B 链闭包门通过：交接 → gates_post → 同步包"
cd "$C"
bash e6q_chain.sh e6q_closure.py:handoff e6q_closure.py:gates_post e6q_syncpack.py:LATEST
echo "[$(date '+%F %T')] 交付衔接链结束 rc=$?"
