#!/usr/bin/env python3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    subprocess.check_call(['python3', str(ROOT / 'scripts' / 'render_digest.py'), '--days', '7', '--top', '12'])
    print('site built')

if __name__ == '__main__':
    main()
