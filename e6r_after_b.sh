#!/bin/bash
# E6r B → 交付衔接（47 端）：等 B 链完成标记（B.complete = 后段全部步骤与闭包门 ①–㉓ 通过），依次：REVIEW 注记 → 交接（handoff 目录 + 扫描 + 清单 + 决策端脚本）
# → 交付后闭包门（含 ㉓ D 输出 / ㉔ 扫描）→ 本机同步包。B 链有失败标记 → 不交付，退出 1。用法：setsid nohup bash e6r_after_b.sh > $W/logs/after_b.log 2>&1 &
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261024_1250_E6r_entry_quality_roles" && pwd)
M=$W/task_status/chain
TAG=${1:-B}
while true; do
  if ls $M/${TAG}_*.failed > /dev/null 2>&1; then echo "[$(date '+%F %T')] ${TAG} 链有失败标记，不交付"; exit 1; fi
  if [ -f $M/${TAG}.complete ]; then break; fi
  sleep 30
done
echo "[$(date '+%F %T')] B 链完成：注记 → 交接 → 交付后门 → 同步包"
cd "$C"
bash e6r_chain.sh C e6r_notes.py e6r_closure.py:handoff e6r_closure.py:gates_post e6r_syncpack.py:LATEST
echo "[$(date '+%F %T')] C 链结束 rc=$?"
