#!/bin/zsh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/build_site.py
git add .
git commit -m "chore: sync paper radar updates" || true
git push origin main
