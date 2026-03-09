#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RADAR = ROOT / 'scripts' / 'paper_radar.py'
PERSONALIZE = ROOT / 'scripts' / 'personalize_from_zotero.py'
CURATED = ROOT / 'scripts' / 'zotero_curated_pool.py'
CANONICAL = ROOT / 'scripts' / 'build_canonical_pool.py'
ASSET = ROOT / 'assets' / 'dashboard.html'
OUT = ROOT / 'output'


def venue_tags(text):
    t = (text or '').lower()
    tags = []
    if any(k in t for k in ['ssd','flash','nvme','file system','filesystem','storage','lsm','rocksdb','persistent memory','wisckey','tiered','kv store','key-value']):
        tags.append('FAST-style')
    if any(k in t for k in ['cache','prefetch','tlb','cxl','chiplet','microarchitecture','memory system','accelerator','dram','nvm']):
        tags.append('HPCA-style')
    if any(k in t for k in ['distributed','cluster','datacenter','runtime','scheduler','resource','operating system','kernel','serverless']):
        tags.append('OSDI/ATC/EuroSys-style')
    if any(k in t for k in ['eda','chip design','placement','routing','iccad','dac','hardware design']):
        tags.append('DAC/ICCAD-style')
    if any(k in t for k in ['llm','inference','training','gpu','moe','serving']):
        tags.append('AI Infra')
    return tags or ['General Systems']


def canonical_boost(title, summary, canonical_rows):
    text = f"{title} {summary}".lower()
    best = 0
    matched = []
    for row in canonical_rows:
        overlap = 0
        for kw in row.get('keywords', []):
            kw = kw.lower()
            if kw and kw in text:
                overlap += 1
        if overlap >= 2:
            matched.append(row['title'])
            best = max(best, min(10, overlap * 2))
    return best, matched[:3]


def score_profile(tags, title, summary, raw_score, canonical_rows):
    text = f"{title}\n{summary}".lower()
    score = raw_score
    if 'FAST-style' in tags:
        score += 10
    if 'HPCA-style' in tags:
        score += 7
    if 'OSDI/ATC/EuroSys-style' in tags:
        score += 4
    if 'DAC/ICCAD-style' in tags:
        score += 2
    if 'AI Infra' in tags:
        score -= 6
    if 'AI Infra' in tags and any(t in tags for t in ['FAST-style', 'HPCA-style', 'OSDI/ATC/EuroSys-style']):
        score += 3
    if any(k in text for k in ['storage','ssd','nvme','lsm','rocksdb','wisckey','filesystem','file system','tiered']):
        score += 6
    if any(k in text for k in ['cxl','cache','prefetch','tlb','memory system','chiplet']):
        score += 5
    if any(k in text for k in ['llm','diffusion','speech recognition','talking head']) and not any(k in text for k in ['storage','runtime','scheduler','cluster','serving']):
        score -= 5
    boost, matched = canonical_boost(title, summary, canonical_rows)
    score += boost
    return score, matched


def one_liner(entry):
    text = (entry.get('summary') or '').strip().lower()
    if any(k in text for k in ['storage','ssd','filesystem','file system','lsm','rocksdb','tiered']):
        return '存储味比较正，先看 bottleneck 有没有抓对。'
    if any(k in text for k in ['memory','cache','cxl','chiplet','microarchitecture']):
        return '偏内存/架构味，值得看是不是有真货而不是只会画图。'
    if 'serverless' in text and 'llm' in text:
        return '算是 AI infra 里比较像系统活的，能看。'
    if any(k in text for k in ['llm','inference','training']):
        return 'AI infra 方向，但得警惕是不是只是模型套壳。'
    return '先扫摘要和实验，别被标题党骗了。'


def tier(score):
    if score >= 26:
        return '必看'
    if score >= 14:
        return '可扫'
    return '先别看'


def pure_ai(tags):
    return 'AI Infra' in tags and not any(t in tags for t in ['FAST-style', 'HPCA-style', 'OSDI/ATC/EuroSys-style', 'DAC/ICCAD-style'])


def cap_ai_ratio(items, limit_ai=2):
    out, ai_count = [], 0
    for item in items:
        if pure_ai(item['venue_tags']):
            if ai_count >= limit_ai:
                continue
            ai_count += 1
        out.append(item)
    return out


def main():
    ap = argparse.ArgumentParser(description='Render markdown digest + pretty dashboard for paper radar')
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--top', type=int, default=10)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.check_output(['python3', str(PERSONALIZE)], text=True)
    except Exception:
        pass
    subprocess.check_output(['python3', str(CANONICAL)], text=True)

    raw = subprocess.check_output(['python3', str(RADAR), '--days', str(args.days), '--top', '30', '--json'], text=True)
    rows = json.loads(raw)
    curated_rows = json.loads(subprocess.check_output(['python3', str(CURATED), '--top', '8'], text=True))
    canonical_rows = json.loads((OUT / 'canonical.json').read_text())

    items = []
    counts = Counter()
    for row in rows:
        e = row['entry']
        text = f"{e['title']}\n{e['summary']}"
        tags = venue_tags(text)
        adj, matched = score_profile(tags, e['title'], e['summary'], row['score'], canonical_rows)
        why = row['reasons'][:6]
        if matched:
            why.append('canon:' + ' / '.join(matched))
        items.append({
            'source': 'recent',
            'score': adj,
            'tier': tier(adj),
            'title': e['title'],
            'authors': e['authors'][:5],
            'link': e['link'],
            'why': '；'.join(why),
            'venue_tags': tags,
            'one_liner': one_liner(e),
            'summary': e['summary'],
            'matched_canonical': matched,
        })

    items.sort(key=lambda x: x['score'], reverse=True)
    items = cap_ai_ratio(items, limit_ai=2)
    prefer = [x for x in items if any(t in x['venue_tags'] for t in ['FAST-style', 'HPCA-style', 'OSDI/ATC/EuroSys-style']) or x['matched_canonical']]
    backup = [x for x in items if x not in prefer]
    items = (prefer + backup)[:args.top]

    curated = []
    for row in curated_rows:
        tags = row.get('tags') or ['Systems']
        for t in tags:
            counts[t] += 1
        curated.append({
            'source': 'curated',
            'score': row['score'] + 20,
            'tier': '经典',
            'title': row['title'],
            'authors': [],
            'link': '',
            'why': '；'.join(tags) + '；来自 Zotero 现有论文池',
            'venue_tags': tags,
            'one_liner': '这类更像你的长期主线，适合精读和做研究借鉴。',
            'summary': row.get('abstract') or '',
            'publicationTitle': row.get('publicationTitle'),
            'date': row.get('date'),
            'itemID': row.get('itemID'),
        })

    for item in canonical_rows:
        for t in item['venue_tags']:
            counts[t] += 1
    for item in items:
        for t in item['venue_tags']:
            counts[t] += 1

    tier_counts = Counter(item['tier'] for item in items)
    payload = {
        'meta': {
            'days': args.days,
            'fetched': 120,
            'matched': len(rows),
            'tag_counts': dict(counts),
            'tier_counts': dict(tier_counts),
        },
        'featured_analysis': {
            'title': 'WiscKey 精读样板',
            'path': './wisckey-analysis.html'
        },
        'canonical': canonical_rows,
        'curated': curated,
        'items': items,
    }
    (OUT / 'latest.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    md = ['# Paper Radar Digest', '', f'- window: last {args.days} days', f'- shown: {len(items)}', '']
    md += ['## 精读样板', '', '- WiscKey 精读样板：见 `wisckey-analysis.html`', '']
    md += ['## 顶会 / 经典白名单池', '']
    for i, p in enumerate(canonical_rows, 1):
        md += [f'### 白名单-{i}. {p["title"]}', f'- venue: {p["why"]}', f'- tags: {", ".join(p["venue_tags"])}', f'- take: {p["one_liner"]}', '']
    md += ['## Zotero 经典相关论文', '']
    for i, p in enumerate(curated, 1):
        md += [f'### 经典-{i}. {p["title"]}', f'- score: {p["score"]}', f'- tags: {", ".join(p["venue_tags"])}', f'- why: {p["why"]}', f'- take: {p["one_liner"]}', '']
    for group in ['必看', '可扫', '先别看']:
        subset = [x for x in items if x['tier'] == group]
        if not subset:
            continue
        md += [f'## {group}', '']
        for i, p in enumerate(subset, 1):
            md += [f'### {group}-{i}. {p["title"]}', f'- score: {p["score"]}', f'- tags: {", ".join(p["venue_tags"])}', f'- why: {p["why"]}', f'- take: {p["one_liner"]}', f'- link: {p["link"]}', '']
    (OUT / 'latest.md').write_text('\n'.join(md))
    shutil.copy2(ASSET, OUT / 'index.html')
    try:
        subprocess.check_output(['python3', str(ROOT / 'scripts' / 'archive_snapshot.py')], text=True)
    except Exception:
        pass
    print(str(OUT / 'index.html'))
    print(str(OUT / 'latest.md'))

if __name__ == '__main__':
    main()
