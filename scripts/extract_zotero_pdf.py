#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path

DB = Path.home() / 'Zotero' / 'zotero.sqlite'
STORAGE = Path.home() / 'Zotero' / 'storage'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=str(DB))
    ap.add_argument('--item-id', type=int, required=True)
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT itemAttachments.itemID, itemAttachments.parentItemID, itemAttachments.contentType, itemAttachments.path, items.key
        FROM itemAttachments
        JOIN items ON items.itemID=itemAttachments.itemID
        WHERE itemAttachments.parentItemID=?
    """, (args.item_id,)).fetchall()
    out = []
    for r in rows:
        p = r['path'] or ''
        real = None
        if p.startswith('storage:'):
            real = STORAGE / r['key'] / p.split(':',1)[1]
        out.append({
            'attachmentItemID': r['itemID'],
            'contentType': r['contentType'],
            'path': p,
            'resolvedPath': str(real) if real else None,
            'exists': bool(real and Path(real).exists())
        })
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
