#!/usr/bin/env python3
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
ARCH = OUT / 'archive'


def main():
    ts = datetime.now().strftime('%Y-%m-%d')
    day = ARCH / ts
    day.mkdir(parents=True, exist_ok=True)
    for name in ['latest.json', 'latest.md', 'index.html', 'wisckey-analysis.html']:
        src = OUT / name
        if src.exists():
            shutil.copy2(src, day / name)
    index = ARCH / 'index.json'
    items = []
    if index.exists():
        try:
            items = json.loads(index.read_text())
        except Exception:
            items = []
    if ts not in items:
        items.insert(0, ts)
    index.write_text(json.dumps(items[:30], ensure_ascii=False, indent=2))
    print(str(day))

if __name__ == '__main__':
    main()
