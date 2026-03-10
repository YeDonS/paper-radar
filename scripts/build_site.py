#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'


def maybe_snapshot_existing_output():
    latest = OUT / 'latest.json'
    index = OUT / 'index.html'
    if latest.exists() and index.exists():
        subprocess.call(['python3', str(ROOT / 'scripts' / 'archive_snapshot.py')])


def main():
    maybe_snapshot_existing_output()
    subprocess.check_call(['python3', str(ROOT / 'scripts' / 'render_digest.py'), '--days', '7', '--top', '12'])
    print('site built')

if __name__ == '__main__':
    main()
