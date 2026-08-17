#!/bin/bash
# scribe · 本地录音转写 — 一键启动
cd "$(dirname "$0")"
PORT="${SCRIBE_PORT:-8399}"

echo "────────────────────────────────────────"
echo "  scribe · 本地录音转写"
echo "  首次启动加载模型约 15 秒，之后常驻"
echo "────────────────────────────────────────"

# 优先使用项目内置 venv（自包含分发），否则退回系统 python3
if [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"
else
    PY="python3"
    echo "提示：未检测到 .venv，使用系统 python3（需已 pip install -r requirements.txt）"
fi

# 启动后自动打开浏览器（等模型加载完成的宽限）
(sleep 3; open "http://localhost:${PORT}" 2>/dev/null || xdg-open "http://localhost:${PORT}" 2>/dev/null) &

exec "$PY" server.py
