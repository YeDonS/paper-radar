#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

DB = Path.home() / 'Zotero' / 'zotero.sqlite'
TOP_VENUES = {
    'FAST': ['fast', 'file and storage technologies'],
    'HPCA': ['hpca', 'high-performance computer architecture'],
    'DAC': ['dac', 'design automation conference'],
    'EuroSys': ['eurosys'],
    'OSDI': ['osdi', 'operating systems design and implementation'],
    'ICCAD': ['iccad', 'computer-aided design'],
    'ATC': ['usenix atc', 'annual technical conference'],
}


def match_venue(text):
    t = (text or '').lower()
    for name, pats in TOP_VENUES.items():
        if any(p in t for p in pats):
            return name
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DB))
    ap.add_argument('--limit', type=int, default=2000)
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
        venue_text = ' | '.join(filter(None, [r['publicationTitle'], r['proceedingsTitle']]))
        venue = match_venue(venue_text)
        if not venue:
            continue
        out.append({
            'itemID': r['itemID'],
            'venue': venue,
            'title': r['title'],
            'abstract': r['abstract'],
            'publicationTitle': r['publicationTitle'],
            'proceedingsTitle': r['proceedingsTitle'],
            'date': r['date'],
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
