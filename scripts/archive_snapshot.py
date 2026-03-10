#!/usr/bin/env python3
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
ARCH = OUT / 'archive'

ARCHIVE_INDEX_HTML = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Paper Radar Archive</title><style>
body{margin:0;font-family:Inter,system-ui,sans-serif;background:#0b1020;color:#ecf2ff}.wrap{max-width:960px;margin:0 auto;padding:32px 20px}.card{background:#121a30;border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:16px;margin:12px 0}a{color:#c8d6ff;text-decoration:none}.muted{color:#9fb0d1}
</style></head><body><div class="wrap"><h1>Paper Radar Archive</h1><p class="muted">历史快照入口。每一天都是当时那版 radar 的静态留档。</p><div id="list"></div></div><script>
fetch('./index.json').then(r=>r.json()).then(items=>{document.getElementById('list').innerHTML=(items||[]).map(d=>`<div class="card"><a href='./${d}/index.html'>${d}</a></div>`).join('') || '<div class="card muted">暂无归档</div>';}).catch(()=>{document.getElementById('list').innerHTML='<div class="card muted">归档索引加载失败</div>';});
</script></body></html>'''


def copy_any(src: Path, dst: Path):
    if not src.exists():
        return
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main():
    ts = datetime.now().strftime('%Y-%m-%d')
    day = ARCH / ts
    day.mkdir(parents=True, exist_ok=True)

    for name in ['latest.json', 'latest.md', 'index.html', 'wisckey-analysis.html']:
        copy_any(OUT / name, day / name)
    copy_any(OUT / 'analysis', day / 'analysis')

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
    (ARCH / 'index.html').write_text(ARCHIVE_INDEX_HTML)
    print(str(day))

if __name__ == '__main__':
    main()
