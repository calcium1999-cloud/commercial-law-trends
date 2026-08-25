#!/bin/bash
# run_weekly.sh — 周自动化运行 shell 包装器
# 清除 TRAE 环境变量干扰，使用项目 .venv Python
set -e

# 清除可能干扰的 Python 环境变量
unset PYTHONHOME PYTHONPATH

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PROJECT_DIR}/.venv/bin/python"

if [ ! -f "$PYTHON" ]; then
    echo "ERROR: .venv Python not found at $PYTHON"
    echo "Run: cd $PROJECT_DIR && .venv/bin/python -m pip install -r requirements.txt"
    exit 1
fi

cd "$PROJECT_DIR"
exec "$PYTHON" scripts/run_weekly.py "$@"
