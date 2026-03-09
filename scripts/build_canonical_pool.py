#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'references' / 'canonical-papers.json'
OUT = ROOT / 'output' / 'canonical.json'


def infer_tags(area):
    tags = []
    s = set(area or [])
    if {'storage', 'kv', 'lsm', 'ssd', 'filesystem'} & s:
        tags.append('FAST-style')
    if {'architecture', 'memory', 'cxl'} & s:
        tags.append('HPCA-style')
    if {'systems', 'datacenter'} & s:
        tags.append('OSDI/ATC/EuroSys-style')
    return tags or ['Systems']


def keywords(area, title):
    parts = list(area or []) + [x.lower() for x in title.replace(':', ' ').replace('-', ' ').split() if len(x) > 3]
    seen = []
    for p in parts:
        if p not in seen:
            seen.append(p)
    return seen[:12]


def main():
    data = json.loads(REF.read_text())
    out = []
    for i, row in enumerate(data, 1):
        out.append({
            'id': f'canon-{i}',
            'title': row['title'],
            'venue': row['venue'],
            'year': row['year'],
            'venue_tags': infer_tags(row.get('area', [])),
            'keywords': keywords(row.get('area', []), row['title']),
            'tier': '白名单',
            'score': 100 - i,
            'one_liner': row['why'],
            'why': f"{row['venue']} {row['year']}；{', '.join(row.get('area', []))}",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(str(OUT))
    print(json.dumps(out[:5], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
