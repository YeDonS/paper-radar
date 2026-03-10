#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

PORT="${PORT:-8765}"
HOST="${HOST:-127.0.0.1}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 没装，先装 Python 再说。"
  exit 1
fi

if [ -f requirements.txt ]; then
  echo "[1/4] 安装/确认依赖"
  python3 -m pip install --user -r requirements.txt
fi

echo "[2/4] 构建 radar 页面"
python3 scripts/build_site.py

echo "[3/4] 检查端口 $PORT"
if lsof -i TCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "端口 $PORT 已被占用。先看看是谁："
  lsof -i TCP:"$PORT" -sTCP:LISTEN
  echo "要么换 PORT，要么先把占用进程干掉。"
  exit 1
fi

echo "[4/4] 启动本地实时精读服务"
echo "打开浏览器： http://$HOST:$PORT"
echo "点实时精读时，现在会先显示生成中；失败会明确报错，不再偷偷退回。"
exec env PORT="$PORT" HOST="$HOST" python3 scripts/serve_local.py
