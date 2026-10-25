#!/bin/bash
# E6o 停止全部 e6o 运行进程（脚本自身命令行不含匹配串）
pkill -f "bash e6o_chain_" ; pkill -f "python3 e6o_" ; sleep 2; pgrep -fc "python3 e6o_" || true
