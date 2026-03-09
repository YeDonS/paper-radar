#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZOTERO = ROOT / 'scripts' / 'zotero_profile.py'
OUT = ROOT / 'output'

ALLOW = {
    'storage','ssd','flash','nvme','wisckey','rocksdb','lsm','filesystem','tiered','disaggregated','cxl','cache','prefetch','tlb','serving','inference','training','gpu','cluster','datacenter','persistent','memory','kv','simplessd'
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    raw = subprocess.check_output(['python3', str(ZOTERO), '--top', '80'], text=True)
    data = json.loads(raw)
    weights = {}
    for item in data.get('top_terms', []):
        term = item['term'].lower()
        count = int(item['count'])
        if term in ALLOW:
            weights[term] = min(8, max(2, count))
    out = {'source': data.get('db'), 'weights': weights}
    (OUT / 'personalization.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
