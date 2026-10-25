#!/bin/bash
# 等待条件（47 端）：bash e6q_wait.sh <秒> <文件> [<文件> …]：任一文件出现即返回 0；超时返回 1（只读、不改任何产物）。
T="$1"; shift
end=$(( $(date +%s) + T ))
while [ "$(date +%s)" -lt "$end" ]; do
  for f in "$@"; do
    if [ -e "$f" ]; then echo "found $(basename "$f")"; exit 0; fi
  done
  sleep 5
done
echo "timeout"
exit 1
