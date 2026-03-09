#!/usr/bin/env python3
import argparse
import collections
import json
import os
import re
import sqlite3
from pathlib import Path

DEFAULT_DB = Path.home() / 'Zotero' / 'zotero.sqlite'
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.-]{2,}")
STOP = {
    'using','based','system','systems','toward','towards','from','with','without','into','their','paper','papers','study','approach','efficient','scalable','large','model','models','language','learning','data','analysis','design','via','over','under','for','the','and','new'
}


def tokenize(text):
    for t in TOKEN_RE.findall((text or '').lower()):
        if t not in STOP and not t.isdigit():
            yield t


def main():
    ap = argparse.ArgumentParser(description='Extract lightweight interest profile from Zotero sqlite DB')
    ap.add_argument('--db', default=str(DEFAULT_DB))
    ap.add_argument('--top', type=int, default=80)
    args = ap.parse_args()

    db = Path(args.db).expanduser()
    if not db.exists():
        raise SystemExit(f'Zotero DB not found: {db}')

    conn = sqlite3.connect(str(db))
    cur = conn.cursor()
    rows = cur.execute("""
        SELECT itemDataValues.value
        FROM items
        JOIN itemData ON items.itemID = itemData.itemID
        JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
        WHERE items.itemTypeID IN (SELECT itemTypeID FROM itemTypes WHERE typeName IN ('journalArticle','conferencePaper','preprint'))
          AND itemData.fieldID IN (
            SELECT fieldID FROM fields WHERE fieldName IN ('title','abstractNote','publicationTitle','proceedingsTitle')
          )
        ORDER BY items.dateAdded DESC
        LIMIT 4000
    """).fetchall()
    counter = collections.Counter()
    for (text,) in rows:
        counter.update(tokenize(text))
    top = counter.most_common(args.top)
    print(json.dumps({
        'db': str(db),
        'top_terms': [{'term': k, 'count': v} for k, v in top]
    }, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
