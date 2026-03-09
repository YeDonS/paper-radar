#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

DB = Path.home() / 'Zotero' / 'zotero.sqlite'

KEYWORDS = {
    'FAST-style': ['ssd','flash','nvme','storage','file system','filesystem','lsm','rocksdb','wisckey','tiered','persistent memory','kv'],
    'HPCA-style': ['cxl','cache','prefetch','tlb','memory system','chiplet','microarchitecture','dram','nvm'],
    'Systems': ['distributed','datacenter','runtime','scheduler','serving','io stack'],
}


def score(text):
    t = (text or '').lower()
    tags = []
    s = 0
    for name, kws in KEYWORDS.items():
        hit = False
        for kw in kws:
            if kw in t:
                s += 3 if name == 'FAST-style' else 2
                hit = True
        if hit:
            tags.append(name)
    return s, tags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DB))
    ap.add_argument('--limit', type=int, default=500)
    ap.add_argument('--top', type=int, default=20)
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT items.itemID,
               MAX(CASE WHEN fields.fieldName='title' THEN itemDataValues.value END) AS title,
               MAX(CASE WHEN fields.fieldName='abstractNote' THEN itemDataValues.value END) AS abstract,
               MAX(CASE WHEN fields.fieldName='publicationTitle' THEN itemDataValues.value END) AS publicationTitle,
               MAX(CASE WHEN fields.fieldName='proceedingsTitle' THEN itemDataValues.value END) AS proceedingsTitle,
               MAX(CASE WHEN fields.fieldName='date' THEN itemDataValues.value END) AS date
        FROM items
        JOIN itemData ON items.itemID=itemData.itemID
        JOIN itemDataValues ON itemData.valueID=itemDataValues.valueID
        JOIN fields ON itemData.fieldID=fields.fieldID
        WHERE items.itemTypeID IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ('journalArticle','conferencePaper','preprint'))
        GROUP BY items.itemID
        ORDER BY items.dateAdded DESC
        LIMIT ?
    """, (args.limit,)).fetchall()
    out = []
    for r in rows:
        blob = ' '.join(filter(None, [r['title'], r['abstract'], r['publicationTitle'], r['proceedingsTitle']]))
        s, tags = score(blob)
        if s <= 0:
            continue
        out.append({
            'itemID': r['itemID'], 'score': s, 'tags': tags, 'title': r['title'], 'abstract': r['abstract'],
            'publicationTitle': r['publicationTitle'], 'proceedingsTitle': r['proceedingsTitle'], 'date': r['date']
        })
    out.sort(key=lambda x: x['score'], reverse=True)
    print(json.dumps(out[:args.top], ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
